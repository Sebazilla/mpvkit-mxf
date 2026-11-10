"""Verify approved CVE2 release bytes and exact patched source members offline."""
import hashlib,json,os,tarfile
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_sources(root):
 root=Path(root).resolve()
 if root not in {Path('/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4'),Path('/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4-final')}:raise SystemExit('wrong CVE2 root')
 records=json.loads((root/'source/tools/cve2-sources.json').read_text())
 for item in records:
  a=Path('/Volumes/4M2/Dev/rushdeck/tmp/cve2/sources')/item['name']
  if sha(a)!=item['sha256']:raise SystemExit('CVE2 archive differs: '+item['name'])
  target=root/item['target'];allowed=set()
  with tarfile.open(a) as stream:
   for member in stream:
    rel=Path(*Path(member.name).parts[1:]);path=target/rel
    if not path.resolve().is_relative_to(target.resolve()):raise SystemExit('CVE2 member escapes root')
    allowed.add(str(rel))
    if member.isfile():
     expected=item.get('patched',{}).get(str(rel))
     valid=path.is_file() and not path.is_symlink() and (sha(path)==expected if expected else path.read_bytes()==stream.extractfile(member).read())
    elif member.issym():valid=path.is_symlink() and os.readlink(path)==member.linkname
    elif member.isdir():valid=path.is_dir()
    else:raise SystemExit('unsupported CVE2 member')
    if not valid:raise SystemExit('CVE2 extracted source differs: '+str(path))
  for rel,expected in item.get('added',{}).items():
   if sha(target/rel)!=expected:raise SystemExit('CVE2 added patch differs: '+rel)
  # Submodule roots are separately verified by their own records.
 print('PASS approved CVE2 archives and patched extracted source members',flush=True)
