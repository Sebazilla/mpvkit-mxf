#!/usr/bin/env python3
"""Build a marked ABI-compatible avutil in fresh directories; never clean baseline outputs."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
from build_frameworks import rewrite_loads,run,sha,shared_binary
MARKER='WP-LGPL-SWAP-20261030'
def exported(path):
 text=subprocess.check_output(['/usr/bin/nm','-arch','arm64','-gU',str(path)],text=True)
 return {line.split()[-1] for line in text.splitlines() if len(line.split())==3}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args();r=a.root.resolve()
 if r!=Path('/Volumes/4M2/Dev/rushdeck/mpvkit-dyn2'):raise SystemExit('dedicated root required')
 w=r/'replacement-build';w.mkdir(exist_ok=False)
 shutil.copytree(r/'ffmpeg-source',w/'source',symlinks=True)
 v=w/'source/libavutil/version.c';text=v.read_text();needle='return FFMPEG_VERSION;';assert text.count(needle)==1
 v.write_text(text.replace(needle,'return FFMPEG_VERSION "+'+MARKER+'";'))
 b=w/'build';b.mkdir();flags=json.loads((r/'ffmpeg-build/arm64/configuration-delta.json').read_text())['shared']
 env=dict(os.environ,PATH=f'{r}/toolchain/bin:/usr/bin:/bin:/usr/sbin:/sbin',PKG_CONFIG_LIBDIR=str(r/'prefix/arm64/lib/pkgconfig'),PKG_CONFIG_PATH=str(r/'prefix/arm64/lib/pkgconfig')+':'+str(r/'toolchain/sdl2/lib/pkgconfig'))
 subprocess.run([str(w/'source/configure')]+flags,cwd=b,env=env,check=True)
 filename=shared_binary(r/'prefix/arm64','Libavutil').name
 subprocess.run(['/usr/bin/make','-j4','libavutil/'+filename],cwd=b,env=env,check=True)
 baseline=r/'framework-stage/arm64/Libavutil.framework';target=w/baseline.name
 shutil.copytree(baseline,target,symlinks=True);binary=(target/'Libavutil').resolve()
 shutil.copyfile(b/'libavutil'/filename,binary)
 run(['/usr/bin/install_name_tool','-id','@rpath/Libavutil.framework/Libavutil',binary]);rewrite_loads(binary)
 assert exported(binary)==exported(baseline/'Libavutil'),'ABI export set differs'
 os.chmod(binary,0o755);run(['/usr/bin/codesign','--force','--sign','-',target])
 print('PASS marked replacement, identical exported symbol set',MARKER,sha(binary))
if __name__=='__main__':main()
