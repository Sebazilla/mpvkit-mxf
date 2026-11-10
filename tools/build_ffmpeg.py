#!/usr/bin/env python3
"""Rebuild FFmpeg n8.1 as shared libraries with each original arch's exact features."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

if __package__:
    from .gnutls.wait_for_m3 import wait
else:
    from gnutls.wait_for_m3 import wait

from build_frameworks import framework, input_binary, sha
from fetch_inputs import GitHubOnly, validate
from urllib.request import build_opener

SDK_URL = "https://github.com/mpvkit/moltenvk-build/releases/download/1.4.1/MoltenVK-all.zip"
SDK_SHA = "9f65e1025f49c55394da475e40fbe1da8dbd10382d730ce81ebc4c5ac40104d1"


def run(args, cwd, env):
    print("RUN", args, flush=True)
    subprocess.run([str(x) for x in args], cwd=cwd, env=env, check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--artifacts", type=Path, required=True)
    p.add_argument("--arch", choices=["arm64", "x86_64"], default="arm64")
    p.add_argument("--repeat", action="store_true", help="fresh second build, no prefix install")
    args = p.parse_args()
    # Caller holds the mpvlgpl gate lock.
    root = args.root.resolve()
    if root not in {Path("/Volumes/4M2/Dev/rushdeck/mpvkit-dyn2"), Path("/Volumes/4M2/Dev/rushdeck/mpvkit-dyn2/cve1-dyn3")}:
        raise SystemExit("only the dedicated M3 root is allowed")
    import sys
    sys.path.insert(0, str(root / "source/tools"))
    from gnutls.verify_inputs import verify
    verify(root)
    tools = root / "source/tools"
    manifest = json.loads((tools / "dynamic-inputs.json").read_text())
    for name, expected in manifest.items():
        if sha(input_binary(args.artifacts, name)) != expected:
            raise SystemExit("original input hash differs: " + name)
    source = root / "ffmpeg-source"
    if subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip() != "9047fa1b084f76b1b4d065af2d743df1b40dfb56":
        raise SystemExit("wrong FFmpeg source revision")
    patch = subprocess.check_output(["git", "-C", str(source), "diff", "--no-ext-diff", "--no-textconv", "--full-index", "--binary", "HEAD"])
    if hashlib.sha256(patch).hexdigest() != "79feb56d1e3f999d1d5ad1f90dcf36fbcb9b41e452c8e4a55ac6c1507df77b17":
        raise SystemExit("unexpected FFmpeg patch")
    if subprocess.check_output(["git", "-C", str(source), "ls-files", "--others", "--exclude-standard"]):
        raise SystemExit("untracked FFmpeg input")
    # Same two macOS substitutions as the original fork build recipe.
    video = source / "libavcodec/videotoolbox.c"
    text = video.read_text()
    text = text.replace("kCVPixelBufferOpenGLESCompatibilityKey", "kCVPixelBufferMetalCompatibilityKey")
    text = text.replace("kCVPixelBufferIOSurfaceOpenGLTextureCompatibilityKey", "kCVPixelBufferMetalCompatibilityKey")
    if video.read_text() != text:
        video.write_text(text)
    archive = root / "downloads/MoltenVK-all.zip"
    if not archive.exists():
        validate(SDK_URL)
        with build_opener(GitHubOnly()).open(SDK_URL, timeout=120) as response, archive.open("wb") as stream:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                stream.write(chunk)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SDK_SHA:
        raise SystemExit("MoltenVK SDK SHA256 mismatch")
    sdk_root = root / "molten-sdk"
    if not (sdk_root / "include/vulkan/vulkan.h").exists():
        subprocess.run(["/usr/bin/ditto", "-x", "-k", str(archive), str(sdk_root)], check=True)
    from gnutls.verify_inputs import verify_zip
    verify_zip(archive, SDK_SHA, sdk_root)
    prefix = root / "prefix" / args.arch
    stage = root / "framework-stage" / args.arch
    # One Vulkan implementation must be shared across the three LGPL users.
    # This also rebuilds earlier foundation outputs after changing linkage.
    env_foundation = dict(os.environ)
    subprocess.run(["/usr/bin/python3", str(tools / "build_frameworks.py"), "--root", str(root),
                    "--artifacts", str(args.artifacts), "--arch", args.arch,
                    "--foundation-only", "--resume"], check=True, env=env_foundation)
    includes = prefix / "include"
    pc = prefix / "lib/pkgconfig"
    pc.mkdir(parents=True, exist_ok=True)
    sdk = subprocess.check_output(["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-path"], text=True).strip()

    def headers(name):
        return framework(args.artifacts, name) / "Headers"

    def link(name, target):
        destination = includes / name
        if destination.is_symlink() and destination.resolve() != target.resolve():
            raise SystemExit("refusing to replace existing header symlink")
        if not destination.exists():
            destination.symlink_to(target, target_is_directory=True)

    link("libplacebo", headers("Libplacebo"))
    for dirname, component in [("ass", "Libass"), ("freetype2", "Libfreetype"), ("harfbuzz", "Libharfbuzz"),
                               ("fribidi", "Libfribidi"), ("dav1d", "Libdav1d"), ("shaderc", "Libshaderc_combined")]:
        link(dirname, headers(component) / dirname)
    for dirname in ["vulkan", "vk_video", "MoltenVK"]:
        if (sdk_root / "include" / dirname).exists():
            link(dirname, sdk_root / "include" / dirname)
    for filename, component in [("lcms2.h", "lcms2"), ("lcms2_plugin.h", "lcms2"), ("uavs3d.h", "Libuavs3d")]:
        link(filename, headers(component) / filename)

    def static(name):
        return str(input_binary(args.artifacts, name))

    def dynamic(name):
        return f"-F{stage} -framework {name}"

    def package(name, version, libs, cflags="", requires="", private=""):
        (pc / (name + ".pc")).write_text(
            f"prefix={prefix}\nName: {name}\nDescription: pinned original MPVKit input\nVersion: {version}\n"
            f"Libs: {libs}\nLibs.private: {private}\nCflags: -I{includes} {cflags}\nRequires.private: {requires}\n")

    package("freetype2", "2.14.3", static("Libfreetype"), f"-I{includes}/freetype2", private="-lz -lbz2 -framework CoreServices")
    package("harfbuzz", "14.2.0", static("Libharfbuzz"), f"-I{includes}/harfbuzz", private="-lc++")
    package("fribidi", "1.0.16", dynamic("Libfribidi"), f"-I{includes}/fribidi")
    package("libass", "0.17.5", static("Libass") + " " + static("Libunibreak"), requires="freetype2 harfbuzz fribidi", private="-liconv -framework CoreText -framework CoreFoundation")
    package("vulkan", "1.4.334", dynamic("MoltenVK"), private="-lc++ -framework CoreFoundation -framework CoreGraphics -framework Foundation -framework IOSurface -framework Metal -framework QuartzCore -framework Cocoa -framework IOKit")
    package("shaderc", "2025.5.0", static("Libshaderc_combined"), private="-lc++")
    package("lcms2", "2.17.0", static("lcms2"))
    package("libplacebo", "7.360.1", dynamic("Libplacebo"))
    package("dav1d", "1.5.2", static("Libdav1d"))
    package("uavs3d", "1.2.1", static("Libuavs3d"))
    xml_header = Path(sdk) / "usr/include/libxml2/libxml/xmlversion.h"
    xml_version = re.search(r'#define LIBXML_DOTTED_VERSION\s+"([^"]+)"', xml_header.read_text()).group(1)
    package("libxml-2.0", xml_version, "-lxml2", f"-I{sdk}/usr/include/libxml2")
    original = json.loads((tools / "ffmpeg-configs.json").read_text())[args.arch]
    assert "--enable-gpl" not in original
    flags = [x for x in original if not x.startswith("--prefix=") and x not in {"--disable-shared", "--enable-static", "--enable-nonfree"}]
    flags += ["--disable-nonfree", "--disable-gpl", f"--prefix={prefix}", "--enable-shared", "--disable-static", "--install-name-dir=@rpath",
              "--cc=/usr/bin/clang", "--cxx=/usr/bin/clang++",
              f"--extra-cflags=-arch {args.arch} -isysroot {sdk} -target {args.arch}-apple-macos11.0 -mmacosx-version-min=11.0 -I{includes}",
              f"--extra-ldflags=-arch {args.arch} -isysroot {sdk} -target {args.arch}-apple-macos11.0 -mmacosx-version-min=11.0 -L{prefix}/lib -F{stage} -lc++"]
    build = root / ("ffmpeg-repeat-build" if args.repeat else "ffmpeg-build") / args.arch
    build.mkdir(parents=True, exist_ok=True)
    (build / "configuration-delta.json").write_text(json.dumps({"original": original, "shared": flags}, indent=2) + "\n")
    env = dict(os.environ, PATH=f"{root}/toolchain/bin:/usr/bin:/bin:/usr/sbin:/sbin",
               PKG_CONFIG_LIBDIR=str(pc), PKG_CONFIG_PATH=str(pc) + ":" + str(root / "toolchain/sdl2/lib/pkgconfig"))
    run([source / "configure"] + flags, build, env)
    run(["/usr/bin/make", "-j4"], build, env)
    if not args.repeat:
        run(["/usr/bin/make", "install"], build, env)
    print("PASS FFmpeg shared source build", args.arch)


if __name__ == "__main__":
    main()
