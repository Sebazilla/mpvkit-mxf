"""Record only the payload read by build_frameworks.py during the assembly/relink.
No Meson, Python 3.14, NASM, Ninja, pkgconf or Homebrew payload is required here.
Run after the source builds, before freezing the final artifact commit.
"""
from pathlib import Path
import os,sys,hashlib,json
r=Path(sys.argv[1]).resolve();sys.path.insert(0,str(r/'source/tools'))
from build_frameworks import DYNAMIC,PERMISSIVE,framework,input_binary,shared_binary
files=set()
def add(p):
 p=Path(p)
 if p.is_dir():
  for q in p.rglob('*'):
   if q.is_file():add(q)
 elif p.is_file():
  assert p.resolve().is_relative_to(r),str(p)
  files.add(p)
 else:raise RuntimeError('missing relink input '+str(p))
for name in DYNAMIC+PERMISSIVE:add(input_binary(r/'verified-inputs',name))
for name in DYNAMIC:
 if name not in {'MoltenVK','Libudfread'}:add(framework(r/'verified-inputs',name))
for arch in ['arm64','x86_64']:
 add(r/'retained-frameworks'/arch/'MoltenVK.framework')
 add(r/'harfbuzz-prefix'/arch/'lib/libharfbuzz.a')
 add(r/'archive-split'/arch/'Libbluray.a');add(r/'archive-split'/arch/'Libudfread.a')
 for name in DYNAMIC:
  from build_frameworks import SOURCE_LIBS
  if name in SOURCE_LIBS:
   prefix=r/('placebo-prefix' if name=='Libplacebo' else 'mpv-prefix' if name=='Libmpv' else 'prefix')/arch
   add(shared_binary(prefix,name))
 for sub in ['gnutls','nettle','libavutil','libavcodec','libavdevice','libavfilter','libavformat','libswscale','libswresample']:
  add(r/'prefix'/arch/'include'/sub)
 add(r/'prefix'/arch/'include/gmp.h')
 add(r/'placebo-prefix'/arch/'include/libplacebo');add(r/'mpv-prefix'/arch/'include/mpv')
 add(r/'ffmpeg-build'/arch/'config.h');add(r/'ffmpeg-build'/arch/'libavutil/ffversion.h')
add(r/'downloads/libbluray-1.4.0.tar.xz');add(r/'releasesrc/libbluray-1.4.0')
manifest={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
(r/'source/tools/relink-inputs.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print('RELINK_INPUTS',len(manifest),flush=True)
