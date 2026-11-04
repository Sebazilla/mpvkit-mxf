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

def verify(root):
 for name,record in json.loads((root/'source/tools/toolchain-inputs.json').read_text()).items():
  if sha(Path(record['path']))!=record['sha256']:raise SystemExit('explicit tool input changed: '+name)
 for name,record in json.loads((root/'source/tools/original-assets.json').read_text()).items():
  verify_zip(root/'verified-inputs'/(name+'.zip'),record['sha256'],root/'verified-inputs'/name)
 from .build_tls import SOURCES,verify_extracted
 for name,(url,digest) in SOURCES.items():
  archive=root/'downloads'/url.rsplit('/',1)[1]
  if sha(archive)!=digest:raise SystemExit('release source archive differs: '+name)
  if (root/'releasesrc'/name).exists():verify_extracted(archive,root/'releasesrc'/name)
 print('PASS pinned tools, original ZIP member contents, release tarball/extracted sources')
if __name__=='__main__':
 import sys
 verify(Path(sys.argv[1]))
