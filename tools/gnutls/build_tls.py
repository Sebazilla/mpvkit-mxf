#!/usr/bin/env python3
"""WP-LGPL: build the exact TLS stack from checked release tarballs, locally."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

if __package__:
    from .wait_for_m3 import wait
else:
    from wait_for_m3 import wait

SOURCES = {
    "gmp-6.2.1": ("https://ftp.gnu.org/gnu/gmp/gmp-6.2.1.tar.xz", "fd4829912cddd12f84181c3451cc752be224643e87fac497b69edddadc49b4f2"),
    "nettle-3.10": ("https://ftp.gnu.org/gnu/nettle/nettle-3.10.tar.gz", "b4c518adb174e484cb4acea54118f02380c7133771e7e9beb98a0787194ee47c"),
    "gnutls-3.8.13": ("https://www.gnupg.org/ftp/gcrypt/gnutls/v3.8/gnutls-3.8.13.tar.xz", "ffed8ec1bf09c2426d4f14aae377de4753b53e537d685e604e99a8b16ca9c97e"),
}


def run(args, cwd, env):
    print("RUN", args, flush=True)
    subprocess.run(args, cwd=cwd, env=env, check=True)


def source(root, name):
    url, digest = SOURCES[name]
    downloads = root / "downloads"
    downloads.mkdir(exist_ok=True)
    archive = downloads / url.rsplit("/", 1)[1]
    if not archive.exists():
        subprocess.run(["/usr/bin/curl", "--fail", "--show-error", "--proto", "=https",
                        "--max-redirs", "0", "-o", str(archive), url], check=True)
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != digest:
        raise SystemExit(f"SHA256 mismatch: {archive.name}: {actual} != {digest}")
    signature = Path(str(archive) + ".sig")
    if not signature.exists():
        subprocess.run(["/usr/bin/curl", "--fail", "--show-error", "--proto", "=https",
                        "--max-redirs", "0", "-o", str(signature), url + ".sig"], check=True)
    print(f"SHA256 {archive.name}: {digest}; signature downloaded, NOT verified", flush=True)
    directory = root / "releasesrc" / name
    if not directory.exists():
        directory.parent.mkdir(exist_ok=True)
        subprocess.run(["/usr/bin/tar", "-xf", str(archive), "-C", str(directory.parent)], check=True)
    verify_extracted(archive, directory)
    return directory



def verify_extracted(archive, directory):
    import tarfile
    import os
    with tarfile.open(archive) as stream:
        for member in stream.getmembers():
            path = directory.parent / member.name
            if not path.resolve().is_relative_to(directory.resolve()):
                raise SystemExit("source member escapes extraction root")
            if member.isfile():
                if path.read_bytes() != stream.extractfile(member).read():
                    raise SystemExit("extracted source differs: " + member.name)
            elif member.issym():
                if not path.is_symlink() or os.readlink(path) != member.linkname:
                    raise SystemExit("source symlink differs: " + member.name)
            elif member.isdir():
                if not path.is_dir(): raise SystemExit("source directory missing")
            else: raise SystemExit("unsupported source archive member")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--arch", choices=["arm64", "x86_64"], default="arm64")
    args = parser.parse_args()
    # Caller holds the mpvlgpl gate lock.
    root = args.root.resolve()
    if root not in {Path("/Volumes/4M2/Dev/rushdeck/mpvkit-dyn2"), Path("/Volumes/4M2/Dev/rushdeck/mpvkit-dyn2/cve1-dyn3"), Path("/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4"), Path("/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4-final")}:
        raise SystemExit("build root must be inside the dedicated M3 fork directory")
    import sys
    sys.path.insert(0, str(root / "source/tools"))
    from gnutls.verify_inputs import verify
    verify(root)
    prefix = root / "prefix" / args.arch
    prefix.mkdir(parents=True, exist_ok=True)
    sdk = subprocess.check_output(["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-path"], text=True).strip()
    common = f"-arch {args.arch} -isysroot {sdk} -target {args.arch}-apple-macos11.0 -mmacosx-version-min=11.0"
    env = dict(os.environ)
    env.update(PATH=f"{root}/toolchain/bin:/usr/bin:/bin:/usr/sbin:/sbin",
               CC="/usr/bin/clang", CXX="/usr/bin/clang++", LC_ALL="C",
               CFLAGS=common,
               CXXFLAGS=common,
               CPPFLAGS=f"{common} -I{prefix}/include", LDFLAGS=f"{common} -L{prefix}/lib",
               PKG_CONFIG_LIBDIR=f"{prefix}/lib/pkgconfig", PKG_CONFIG_PATH=f"{prefix}/lib/pkgconfig")
    configs = {
        "gmp-6.2.1": ["--disable-assembly", "--with-pic", "--disable-fast-install"],
        "nettle-3.10": ["--disable-assembler", "--disable-openssl", "--disable-gcov", "--disable-documentation", "--enable-pic", "--disable-dependency-tracking"],
        "gnutls-3.8.13": ["--with-included-libtasn1", "--with-included-unistring", "--without-brotli", "--without-idn", "--without-p11-kit", "--without-zlib", "--without-zstd", "--enable-hardware-acceleration", "--disable-openssl-compatibility", "--disable-code-coverage", "--disable-doc", "--disable-gtk-doc", "--disable-maintainer-mode", "--disable-manpages", "--disable-nls", "--disable-rpath", "--disable-tests", "--disable-tools", "--disable-full-test-suite", "--with-pic", "--disable-fast-install", "--disable-dependency-tracking"],
    }
    for name, flags in configs.items():
        src = source(root, name)
        build = root / "tls-build" / args.arch / name
        build.mkdir(parents=True, exist_ok=True)
        configuration = [str(src / "configure"), f"--prefix={prefix}", f"--host={args.arch}-apple-darwin", "--build=aarch64-apple-darwin",
                         "--enable-shared", "--disable-static"] + flags
        stamp = json.dumps({"sha256": SOURCES[name][1], "configure": configuration, "cflags": common, "compiler": subprocess.check_output(["/usr/bin/clang", "--version"], text=True)}, sort_keys=True) + "\n"
        if (build / "installed.ok").exists():
            if (build / "installed.ok").read_text() != stamp:
                raise SystemExit("TLS configuration changed: use a fresh tls-build directory for " + name)
            continue
        run(configuration, build, env)
        run(["/usr/bin/make", "-j4"], build, env)
        run(["/usr/bin/make", "install"], build, env)
        (build / "installed.ok").write_text(stamp)


if __name__ == "__main__":
    main()
