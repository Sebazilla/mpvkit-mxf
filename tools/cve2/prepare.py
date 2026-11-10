#!/usr/bin/env python3
"""Prepare one fresh CVE2 build from verified offline inputs; never reuse outputs."""
import hashlib,json,os,shutil,subprocess,sys,tarfile
from pathlib import Path
ROOT=Path('/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4-final')
FORK=Path(__file__).resolve().parents[2]
BASE=Path('/Volumes/4M2/Dev/rushdeck/mpvkit-dyn2/cve1-dyn3')
ARCHIVES=Path('/Volumes/4M2/Dev/rushdeck/tmp/cve2/sources')

def main():
 if ROOT.exists():raise SystemExit('fresh build root already exists; preserve it and stop')
 if ' on /Volumes/4M2 ' not in subprocess.check_output(['/sbin/mount'],text=True):raise SystemExit('4M2 not mounted')
 if not Path('/tmp/rd-gate-lock/owner').read_text().startswith('mpvlgpl '):raise SystemExit('mpvlgpl lock required')
 records=json.loads((FORK/'tools/cve2-sources.json').read_text())
 for record in records:
  archive=ARCHIVES/record['name']
  if hashlib.sha256(archive.read_bytes()).hexdigest()!=record['sha256']:raise SystemExit('approved archive mismatch: '+record['name'])
 ROOT.mkdir();(ROOT/'source').symlink_to(FORK,target_is_directory=True)
 (ROOT/'toolchain').symlink_to(BASE/'toolchain',target_is_directory=True)
 (ROOT/'verified-inputs').symlink_to(BASE/'verified-inputs',target_is_directory=True)
 (ROOT/'downloads').mkdir()
 for source in (BASE/'downloads').iterdir():
  if source.is_file():shutil.copy2(source,ROOT/'downloads'/source.name)
 for record in records:
  target=ROOT/record['target'];target.mkdir(parents=True,exist_ok=True)
  with tarfile.open(ARCHIVES/record['name']) as stream:
   for member in stream:
    parts=Path(member.name).parts[1:]
    if not parts:continue
    path=target.joinpath(*parts)
    if not path.resolve().is_relative_to(target.resolve()):raise SystemExit('archive escape')
    if member.isdir():path.mkdir(parents=True,exist_ok=True)
    elif member.isfile():
     path.parent.mkdir(parents=True,exist_ok=True)
     with path.open('xb') as f:f.write(stream.extractfile(member).read())
     path.chmod(member.mode & 0o777)
    elif member.issym():
     if not (path.parent/member.linkname).resolve().is_relative_to(target.resolve()):raise SystemExit('symlink escape')
     path.parent.mkdir(parents=True,exist_ok=True);path.symlink_to(member.linkname)
    else:raise SystemExit('unsupported tar member')
  print('PREPARED approved source',record['name'],flush=True)
 for patch in sorted((FORK/'Sources/BuildScripts/patch/libmpv').glob('*.patch')):
  subprocess.run(['/usr/bin/git','apply','--check',str(patch)],cwd=ROOT/'upstream/mpv-0.42.0',check=True)
  subprocess.run(['/usr/bin/git','apply','--verbose',str(patch)],cwd=ROOT/'upstream/mpv-0.42.0',check=True)
 video=ROOT/'upstream/ffmpeg-8.1.3/libavcodec/videotoolbox.c';text=video.read_text()
 for old in ['kCVPixelBufferOpenGLESCompatibilityKey','kCVPixelBufferIOSurfaceOpenGLTextureCompatibilityKey']:
  assert text.count(old)==1;text=text.replace(old,'kCVPixelBufferMetalCompatibilityKey')
 video.write_text(text)
 (ROOT/'ffmpeg-source').symlink_to(ROOT/'upstream/ffmpeg-8.1.3',target_is_directory=True)
 sys.path.insert(0,str(FORK/'tools'))
 from verify_cve2 import verify_sources
 verify_sources(ROOT)
 from build_ffmpeg import SDK_SHA
 from gnutls.verify_inputs import verify_zip,verify
 sdk_archive=ROOT/'downloads/MoltenVK-all.zip'
 assert hashlib.sha256(sdk_archive.read_bytes()).hexdigest()==SDK_SHA
 subprocess.run(['/usr/bin/ditto','-x','-k',str(sdk_archive),str(ROOT/'molten-sdk')],check=True)
 verify_zip(sdk_archive,SDK_SHA,ROOT/'molten-sdk');verify(ROOT)
 print('PASS fresh inputs prepared; no completed prefix/build/stage reused',flush=True)
if __name__=='__main__':main()
