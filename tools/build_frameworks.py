#!/usr/bin/env python3
"""Relink pinned original PIC archives as separate dynamic macOS frameworks.

The TLS stack and FFmpeg come from the release-source/shared builds. Other libraries
retain the exact object code/configuration from 0.41.0-mxf, including MXF and
mpv's gpl=false. No GPL target is an input. Run only in the dedicated M3 root.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess

if __package__:
    from .gnutls.wait_for_m3 import wait
else:
    from gnutls.wait_for_m3 import wait

DYNAMIC = ["MoltenVK", "gmp", "nettle", "hogweed", "gnutls", "Libfribidi", "Libuchardet", "Libudfread", "Libbluray", "Libplacebo",
           "Libavutil", "Libswresample", "Libswscale", "Libavcodec", "Libavformat", "Libavfilter", "Libavdevice", "Libmpv"]
PERMISSIVE = ["Libass", "Libfreetype", "Libharfbuzz", "Libunibreak", "Libshaderc_combined",
              "lcms2", "Libdovi", "Libdav1d", "Libuavs3d", "Libluajit"]
SYSTEM = ["AVFoundation", "CoreAudio", "AudioToolbox", "CoreVideo", "CoreFoundation", "CoreMedia", "Metal",
          "VideoToolbox", "Foundation", "AppKit", "IOKit", "OpenGL", "IOSurface", "QuartzCore", "Security",
          "CoreServices", "CoreGraphics", "ApplicationServices", "DiskArbitration", "CoreText"]


SOURCE_LIBS = {"gmp": "libgmp", "nettle": "libnettle", "hogweed": "libhogweed", "gnutls": "libgnutls",
               "Libudfread": "libudfread", "Libavutil": "libavutil", "Libavcodec": "libavcodec", "Libavformat": "libavformat",
               "Libavfilter": "libavfilter", "Libavdevice": "libavdevice", "Libswresample": "libswresample", "Libswscale": "libswscale"}


def shared_binary(prefix, name):
    paths = list((prefix / "lib").glob(SOURCE_LIBS[name] + ".[0-9]*.dylib"))
    if not paths:
        raise SystemExit("missing source-built shared library " + name)
    return min(paths, key=lambda p: len(p.name))


def rewrite_loads(binary):
    import re
    loads = subprocess.check_output(["/usr/bin/otool", "-L", str(binary)], text=True)
    for line in loads.splitlines()[1:]:
        dep = line.strip().split(" (", 1)[0]
        for component, stem in SOURCE_LIBS.items():
            if re.fullmatch(re.escape(stem) + r"(?:\.[0-9]+)+\.dylib", Path(dep).name):
                run(["/usr/bin/install_name_tool", "-change", dep, f"@rpath/{component}.framework/{component}", binary])


def run(args):
    print("RUN", args, flush=True)
    subprocess.run([str(a) for a in args], check=True)


def framework(artifacts, name):
    candidates = list((artifacts / name).glob(f"*.xcframework/macos-*/{name}.framework"))
    if len(candidates) != 1:
        raise SystemExit(f"expected one original macOS framework for {name}: {candidates}")
    return candidates[0]


def input_binary(artifacts, name):
    if name == "Libudfread":
        return framework(artifacts, "Libbluray") / "Libbluray"
    if name == "MoltenVK":
        return artifacts / name / "MoltenVK.xcframework/macos-arm64_x86_64/libMoltenVK.a"
    return framework(artifacts, name) / name


def udf_source(root):
    archive = root / "downloads/libbluray-1.4.0.tar.xz"
    if not archive.exists():
        run(["/usr/bin/curl", "--fail", "--show-error", "--proto", "=https", "--max-redirs", "0", "-o", archive,
             "https://download.videolan.org/pub/videolan/libbluray/1.4.0/libbluray-1.4.0.tar.xz"])
    if sha(archive) != "77937baf07eadda4b2b311cf3af4c50269d2ea3165041f5843d96476c4c92777":
        raise SystemExit("libbluray source tarball SHA256 mismatch")
    directory = root / "releasesrc/libbluray-1.4.0"
    if not directory.exists():
        directory.parent.mkdir(exist_ok=True)
        run(["/usr/bin/tar", "-xf", archive, "-C", directory.parent])
    return directory / "contrib/libudfread"


def build_udfread(root, arch):
    source = udf_source(root)
    prefix = root / "prefix" / arch
    build = root / "udfread-build" / arch
    if (prefix / "lib/libudfread.3.dylib").is_file():
        return
    wait()
    sdk = subprocess.check_output(["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-path"], text=True).strip()
    cross = root / ("udfread-" + arch + ".ini")
    cpu = "aarch64" if arch == "arm64" else "x86_64"
    flags = ["-arch", arch, "-isysroot", sdk, "-target", arch + "-apple-macos11.0", "-mmacosx-version-min=11.0"]
    cross.write_text("[binaries]\nc = '/usr/bin/clang'\n[host_machine]\nsystem = 'darwin'\ncpu_family = '" + cpu + "'\ncpu = '" + cpu + "'\nendian = 'little'\n[properties]\nneeds_exe_wrapper = true\n[built-in options]\nc_args = " + repr(flags) + "\nc_link_args = " + repr(flags) + "\n")
    meson = "/opt/homebrew/bin/meson"
    run([meson, "setup", build, source, "--prefix=" + str(prefix), "--cross-file=" + str(cross),
         "--wrap-mode=nodownload", "--buildtype=release", "-Ddefault_library=shared", "-Dembed_udfread=false", "-Denable_examples=false"])
    run([meson, "compile", "-C", build, "-j4"])
    run([meson, "install", "-C", build])


def split_bluray(root, artifacts, arch):
    work = root / "archive-split" / arch
    work.mkdir(parents=True, exist_ok=True)
    original = work / "Libbluray.a"
    udf = work / "Libudfread.a"
    if original.exists() and udf.exists():
        return {"Libbluray": original, "Libudfread": udf}
    run(["/usr/bin/lipo", input_binary(artifacts, "Libbluray"), "-thin", arch, "-output", original])
    members = ["default_blockinput.c.o", "ecma167.c.o", "udfread.c.o", "udfread-version.c.o"]
    listing = subprocess.check_output(["/usr/bin/ar", "-t", str(original)], text=True).splitlines()
    if any(listing.count(member) != 1 for member in members):
        raise SystemExit("libudfread object inventory differs from pinned original archive")
    subprocess.run(["/usr/bin/ar", "-x", str(original)] + members, cwd=work, check=True)
    run(["/usr/bin/libtool", "-static", "-o", udf] + [work / member for member in members])
    run(["/usr/bin/ar", "-d", original] + members)
    run(["/usr/bin/ranlib", original])
    return {"Libbluray": original, "Libudfread": udf}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--artifacts", type=Path, required=True)
    p.add_argument("--record-inputs", action="store_true")
    p.add_argument("--arch", choices=["arm64", "x86_64"], default="arm64")
    p.add_argument("--combine", action="store_true")
    p.add_argument("--foundation-only", action="store_true")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--refresh-foundations", action="store_true")
    args = p.parse_args()
    os.environ["PATH"] = str(args.root / "toolchain/bin") + ":/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    wait()
    root = args.root.resolve()
    if root != Path("/Volumes/4M2/Dev/rushdeck/mpvkit-dyn"):
        raise SystemExit("only the dedicated M3 root is supported")
    fork = root / "source"
    manifest_path = fork / "tools" / "dynamic-inputs.json"
    inputs = {n: sha(input_binary(args.artifacts, n)) for n in DYNAMIC + PERMISSIVE}
    if args.record_inputs:
        manifest_path.write_text(json.dumps(inputs, indent=2, sort_keys=True) + "\n")
        print("recorded input hashes; no compilation performed")
        return
    if json.loads(manifest_path.read_text()) != inputs:
        raise SystemExit("input archive hashes differ from the recorded original artifacts")
    if args.combine:
        combined = root / "framework-stage" / "universal"
        combined.mkdir(parents=True, exist_ok=True)
        for name in DYNAMIC:
            target = combined / f"{name}.framework"
            shutil.copytree(root / "framework-stage/arm64" / target.name, target, symlinks=True)
            binary = (target / name).resolve()
            run(["/usr/bin/lipo", "-create", root / "framework-stage/arm64" / target.name / name,
                 root / "framework-stage/x86_64" / target.name / name, "-output", str(binary) + ".new"])
            os.replace(str(binary) + ".new", binary)
            run(["/usr/bin/codesign", "--force", "--sign", "-", target])
            run(["/usr/bin/xcodebuild", "-create-xcframework", "-framework", target,
                 "-output", fork / "Dynamic" / f"{name}.xcframework"])
        return
    output = root / "framework-stage" / args.arch
    output.mkdir(parents=True, exist_ok=True)
    completed = []
    for name in (DYNAMIC[:10] if args.foundation_only else DYNAMIC):
        target = output / f"{name}.framework"
        if target.exists():
            if not args.resume:
                raise SystemExit(f"refusing to overwrite {target}; use --resume for this build stage")
            if name in DYNAMIC[:10] and not args.refresh_foundations:
                run(["/usr/bin/codesign", "--verify", "--deep", "--strict", target])
                completed.append(name)
                continue
            shutil.rmtree(target)  # Only generated output inside the dedicated stage.
        if name in {"MoltenVK", "Libudfread"}:
            version = target / "Versions/A"
            (version / "Resources").mkdir(parents=True)
            (target / "Versions/Current").symlink_to("A")
            (target / name).symlink_to("Versions/Current/" + name)
            (target / "Resources").symlink_to("Versions/Current/Resources")
            if name == "MoltenVK":
                shutil.copytree(root / "molten-sdk/include", target / "Headers")
                module = 'framework module MoltenVK [system] { header "MoltenVK/mvk_vulkan.h" export * }\n'
            else:
                source = udf_source(root)
                (target / "Headers").mkdir()
                for filename in ["udfread.h", "blockinput.h"]:
                    shutil.copyfile(source / "src" / filename, target / "Headers" / filename)
                text = (source / "src/udfread-version.h.in").read_text()
                for key, value in {"MAJOR": "1", "MINOR": "2", "MICRO": "0"}.items():
                    text = text.replace("@UDFREAD_VERSION_" + key + "@", value)
                (target / "Headers/udfread-version.h").write_text(text)
                module = 'framework module Libudfread [system] { umbrella "." export * }\n'
            (target / "Modules").mkdir()
            (target / "Modules/module.modulemap").write_text(module)
            (version / "Resources/Info.plist").write_bytes(plistlib.dumps({
                "CFBundleExecutable": name, "CFBundleIdentifier": "org.mpvkit." + name, "CFBundleName": name,
                "CFBundlePackageType": "FMWK", "CFBundleShortVersionString": "1.4.1" if name == "MoltenVK" else "1.2.0", "CFBundleVersion": "1",
                "CFBundleSupportedPlatforms": ["MacOSX"], "CFBundleInfoDictionaryVersion": "6.0"}))
        else:
            shutil.copytree(framework(args.artifacts, name), target, symlinks=True)
        # Normalize the original static wrapper to a standard versioned framework.
        version = target / "Versions/A"
        for directory in ("Headers", "Modules"):
            entry = target / directory
            if entry.is_dir() and not entry.is_symlink():
                entry.rename(version / directory)
                entry.symlink_to("Versions/Current/" + directory)
        info = version / "Resources/Info.plist"
        metadata = plistlib.loads(info.read_bytes())
        metadata["MinimumOSVersion"] = "11.0"
        metadata["LSMinimumSystemVersion"] = "11.0"
        info.write_bytes(plistlib.dumps(metadata))
        binary = (target / name).resolve()
        binary.unlink(missing_ok=True)
        if name in SOURCE_LIBS:
            if name == "Libudfread":
                build_udfread(root, args.arch)
            shutil.copyfile(shared_binary(root / "prefix" / args.arch, name), binary)
            prefix = root / "prefix" / args.arch
            if name.startswith("Libav") or name in {"Libswscale", "Libswresample"}:
                shutil.copyfile(root / "ffmpeg-build" / args.arch / "config.h", target / "Headers/config.h")
                if name == "Libavutil":
                    shutil.copyfile(root / "ffmpeg-build" / args.arch / "libavutil/ffversion.h", target / "Headers/ffversion.h")
                    shutil.copyfile(prefix / "include/libavutil/avconfig.h", target / "Headers/avconfig.h")
            elif name == "gmp":
                shutil.copyfile(prefix / "include/gmp.h", target / "Headers/gmp.h")
            elif name in {"gnutls", "nettle", "hogweed"}:
                subdir = "gnutls" if name == "gnutls" else "nettle"
                for header in (prefix / "include" / subdir).glob("*.h"):
                    shutil.copyfile(header, target / "Headers" / header.name)
        else:
            own_archive = split_bluray(root, args.artifacts, args.arch)[name] if name == "Libbluray" else input_binary(args.artifacts, name)
            command = ["/usr/bin/xcrun", "clang++", "-arch", args.arch, "-dynamiclib", "-mmacosx-version-min=11.0",
                       "-Wl,-dead_strip", "-Wl,-install_name,@rpath/" + name + ".framework/" + name,
                       "-Wl,-force_load," + str(own_archive), "-F" + str(output)]
            for dep in completed:
                command += ["-framework", dep]
            command += [str(input_binary(args.artifacts, dep)) for dep in PERMISSIVE]
            for system in SYSTEM:
                command += ["-framework", system]
            swift_lib = subprocess.check_output(["/usr/bin/xcrun", "--find", "swiftc"], text=True).strip()
            swift_dir = Path(swift_lib).parent.parent / "lib/swift/macosx"
            command += ["-L" + str(swift_dir), "-Wl,-rpath,/usr/lib/swift", "-lswiftCore",
                        "-lbz2", "-liconv", "-lexpat", "-lresolv", "-lxml2", "-lz", "-lc++", "-o", str(binary)]
            run(command)
        os.chmod(binary, 0o755)
        run(["/usr/bin/install_name_tool", "-id", f"@rpath/{name}.framework/{name}", binary])
        rewrite_loads(binary)
        # Do not ship inherited signatures for modified binaries.
        subprocess.run(["/usr/bin/codesign", "--remove-signature", str(target)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        run(["/usr/bin/codesign", "--force", "--sign", "-", str(target)])
        completed.append(name)
    print("dynamic frameworks bytes", sum((output / f"{n}.framework" / n).stat().st_size for n in (DYNAMIC[:10] if args.foundation_only else DYNAMIC)))


if __name__ == "__main__":
    main()
