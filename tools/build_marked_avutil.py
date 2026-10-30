#!/usr/bin/env python3
"""Rebuild Libavutil with a marked version function, preserving its ABI exports."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

if __package__:
    from .gnutls.wait_for_m3 import wait
else:
    from gnutls.wait_for_m3 import wait

from build_frameworks import rewrite_loads, run, sha, shared_binary

MARKER = "WP-LGPL-SWAP-20261030"


def exported(path):
    text = subprocess.check_output(["/usr/bin/nm", "-arch", "arm64", "-gU", str(path)], text=True)
    return {line.split()[-1] for line in text.splitlines() if len(line.split()) == 3}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    wait()
    root = args.root.resolve()
    if root != Path("/Volumes/4M2/Dev/rushdeck/mpvkit-dyn"):
        raise SystemExit("marker build must use the dedicated M3 fork root")
    source = root / "ffmpeg-source"
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if revision != "9047fa1b084f76b1b4d065af2d743df1b40dfb56":
        raise SystemExit("FFmpeg source revision differs from original n8.1")
    work = root / "replacement-build"
    work.mkdir(exist_ok=False)
    # Separate source/build copies: neither baseline artifacts nor app are modified.
    shutil.copytree(source, work / "source", symlinks=True)
    shutil.copytree(root / "ffmpeg-build/arm64", work / "build", symlinks=True)
    source_link = work / "build/src"
    if source_link.is_symlink():
        source_link.unlink()
        source_link.symlink_to(work / "source", target_is_directory=True)
    version = work / "source/libavutil/version.c"
    text = version.read_text()
    needle = "return FFMPEG_VERSION;"
    if text.count(needle) != 1:
        raise SystemExit("unexpected av_version_info implementation")
    version.write_text(text.replace(needle, 'return FFMPEG_VERSION "+' + MARKER + '";'))
    (work / "build/libavutil/version.o").unlink()
    filename = shared_binary(root / "prefix/arm64", "Libavutil").name
    built = work / "build/libavutil" / filename
    built.unlink()
    env = dict(os.environ, PATH=f"{root}/toolchain/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin")
    command = ["/usr/bin/make", "-j4", "SRC_PATH=" + str(work / "source"), "libavutil/" + filename]
    print("RUN", command, flush=True)
    subprocess.run(command, cwd=work / "build", env=env, check=True)
    baseline = root / "framework-stage/arm64/Libavutil.framework"
    target = work / baseline.name
    shutil.copytree(baseline, target, symlinks=True)
    binary = (target / "Libavutil").resolve()
    binary.unlink()
    shutil.copyfile(built, binary)
    run(["/usr/bin/install_name_tool", "-id", "@rpath/Libavutil.framework/Libavutil", binary])
    rewrite_loads(binary)
    assert exported(binary) == exported(baseline / "Libavutil"), "ABI export set differs"
    os.chmod(binary, 0o755)
    run(["/usr/bin/codesign", "--force", "--sign", "-", target])
    print("PASS marker framework rebuilt from n8.1 version.c; identical exported symbol set")
    print("MARKER", MARKER, "SHA256", sha(binary))


if __name__ == "__main__":
    main()
