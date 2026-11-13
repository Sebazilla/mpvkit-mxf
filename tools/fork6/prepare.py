"""Prepare a fresh dyn6 input root from an existing verified fork6 cache.
Usage: python3 prepare.py CACHE_ROOT FRESH_ROOT
Does not copy build outputs, source Git state, probes or keys. Use the final tagged
recipe in FRESH_ROOT/source, then generate its tool manifest after this derivation.
"""
from pathlib import Path
import sys, shutil, os, json
src,dst=map(lambda s:Path(s).resolve(),sys.argv[1:])
assert " on /Volumes/4M2 " in __import__('subprocess').check_output(['/sbin/mount'],text=True)
assert not dst.exists()
assert shutil.disk_usage('/Volumes/4M2').free>=40*1000**3 and shutil.disk_usage('/').free>=10*1000**3
dst.mkdir()
for name in ['verified-inputs','downloads','toolchain','harfbuzz-prefix','retained-frameworks','retained-sources','upstream','releasesrc','molten-sdk']:
 shutil.copytree(src/name,dst/name,symlinks=True)
(dst/'ffmpeg-source').symlink_to('upstream/ffmpeg-8.1.3',target_is_directory=True)
for name in ['toolchain','harfbuzz-prefix']:
 for p in (dst/name).rglob('*'):
  if p.is_file() and not p.is_symlink() and p.suffix in {'.pc','.la'}:
   text=p.read_text();new=text.replace(str(src),str(dst))
   if text!=new:p.chmod(p.stat().st_mode|0o200);p.write_text(new)
for arch in ['arm64','x86_64']:
 (dst/('harfbuzz-'+arch+'.ini')).write_text((src/('harfbuzz-'+arch+'.ini')).read_text().replace(str(src),str(dst)))
print('Fresh source/input cache prepared; compiler/host manifests must be checked before building.')
