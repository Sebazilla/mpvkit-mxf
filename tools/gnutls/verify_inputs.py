"""Bind isolated tool, archive and extracted inputs to recorded bytes; no downloads."""
import hashlib,json,os,zipfile
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def verify_zip(archive,expected,target):
 if sha(archive)!=expected:raise SystemExit('input ZIP SHA256 differs: '+str(archive))
 with zipfile.ZipFile(archive) as stream:
  for item in stream.infolist():
   path=target/item.filename
   if not path.resolve().is_relative_to(target.resolve()):raise SystemExit('ZIP member escapes root')
   if item.is_dir():
    if not path.is_dir():raise SystemExit('missing extracted directory')
    continue
   data=stream.read(item);mode=item.external_attr>>16
   if mode&0o170000==0o120000:
    valid=path.is_symlink() and os.readlink(path).encode()==data
   else:valid=path.is_file() and not path.is_symlink() and path.read_bytes()==data
   if not valid:raise SystemExit('extracted input differs: '+str(path))

def verify(root, build=False):
 if not build:
  manifest=json.loads((root/'source/tools/relink-inputs.json').read_text())
  for name,expected in manifest.items():
   p=root/name
   if Path(name).is_absolute() or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('relink input escapes root')
   if sha(p)!=expected:raise SystemExit('relink input differs: '+name)
  print('PASS actual relink payload: '+str(len(manifest))+' files; no source-build host tools',flush=True)
  return
 for name,record in json.loads((root/'source/tools/toolchain-inputs.json').read_text()).items():
  if not build:continue
  p = root / record['path']
  if Path(record['path']).is_absolute() or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('tool path escapes root')
  if sha(p)!=record['sha256']:raise SystemExit('explicit tool input changed: '+name)
 if build:
  for path,expected in json.loads((root/'source/tools/host-toolchain-inputs.json').read_text()).items():
   if sha(Path(path))!=expected:raise SystemExit('host tool payload changed: '+path)
 for name,record in json.loads((root/'source/tools/original-assets.json').read_text()).items():
  verify_zip(root/'verified-inputs'/(name+'.zip'),record['sha256'],root/'verified-inputs'/name)
 from .build_tls import SOURCES,verify_extracted
 for name,(url,digest) in SOURCES.items():
  archive=root/'downloads'/url.rsplit('/',1)[1]
  if sha(archive)!=digest:raise SystemExit('release source archive differs: '+name)
  if (root/'releasesrc'/name).exists():verify_extracted(archive,root/'releasesrc'/name)
 print('PASS verified inputs; build-host verification=' + str(build), flush=True)
if __name__=='__main__':
 import sys
 verify(Path(sys.argv[1]))
