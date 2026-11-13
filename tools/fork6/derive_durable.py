"""Derive a NEW durable dyn6 root, without modifying the source root.
Usage: python3 derive_durable.py BUILD_ROOT NEW_DURABLE_ROOT
Original ZIP members remain exact; active .pc/.la/.ini metadata is rebased.
All copied symlinks become relative and must resolve within the new root.
Compiler logs/configuration strings retain their actual original build paths.
"""
from pathlib import Path
import subprocess,os,shutil,json,sys
src,dst=map(lambda s:Path(s).resolve(),sys.argv[1:])
assert ' on /Volumes/4M2 ' in subprocess.check_output(['/sbin/mount'],text=True)
assert shutil.disk_usage('/Volumes/4M2').free>=40*1000**3 and shutil.disk_usage('/').free>=10*1000**3
assert not dst.exists();dst.mkdir()
subprocess.run(['/usr/bin/git','clone','--no-local',str(src/'source'),str(dst/'source')],check=True)
subprocess.run(['/usr/bin/git','-C',str(dst/'source'),'branch','wp-fork6-dyn6-r1','6a9b30a26b9f3105c05bdea29cf77034444d0b5a'],check=True)
for name in ['toolchain','verified-inputs','downloads','releasesrc','prefix','harfbuzz-prefix','retained-frameworks','archive-split','placebo-prefix','mpv-prefix','placebo-headers','placebo-pc','molten-sdk','ffmpeg-build','upstream']:
 shutil.copytree(src/name,dst/name,symlinks=True)
(dst/'ffmpeg-source').symlink_to('upstream/ffmpeg-8.1.3',target_is_directory=True)
for p in src.glob('*.ini'):shutil.copy2(p,dst/p.name)
links=[];metadata=[]
for p in dst.rglob('*'):
 if p.is_symlink():
  literal=os.readlink(p)
  if literal.startswith(str(src)+'/'):
   target=dst/Path(literal).relative_to(src);p.unlink();p.symlink_to(os.path.relpath(target,p.parent),target_is_directory=target.is_dir())
  assert p.exists(),'dangling link '+str(p)
  assert p.resolve().is_relative_to(dst),'external link '+str(p)
  assert not os.path.isabs(os.readlink(p)),'absolute link '+str(p)
  links.append([str(p.relative_to(dst)),os.readlink(p)])
 elif p.is_file() and p.suffix in {'.pc','.la','.ini'} and not p.is_relative_to(dst/'verified-inputs') and not p.is_relative_to(dst/'source/.git'):
  text=p.read_text();new=text.replace(str(src),str(dst))
  if text!=new:p.chmod(p.stat().st_mode|0o200);p.write_text(new);metadata.append(str(p.relative_to(dst)))
  assert not any(old in new for old in ['/Volumes/4M2/Dev/rushdeck/mpvkit-dyn2','/Volumes/4M2/Dev/rushdeck/mpvkit-dyn4','/Volumes/4M2/Dev/rushdeck/mpvkit-dyn5','/Volumes/4M2/Dev/rushdeck/tmp/'])
print('DERIVED_METADATA',json.dumps(metadata),flush=True)
print('LINK_AUDIT',json.dumps({'count':len(links),'absolute':0,'external':0,'dangling':0,'links':links}),flush=True)
subprocess.run(['/usr/bin/git','--no-optional-locks','-C',str(dst/'source'),'fsck','--full'],check=True)
assert not (dst/'source/.git/objects/info/alternates').exists()
