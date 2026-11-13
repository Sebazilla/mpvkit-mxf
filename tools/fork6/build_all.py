#!/usr/bin/env python3
import os,subprocess,sys
from pathlib import Path
r=Path(os.environ.get('FORK6_BUILD_ROOT','/Volumes/4M2/Dev/rushdeck/tmp/fork6/round2-build'));f=r/'source'
env=dict(os.environ,PATH=str(r/'toolchain/bin')+':/usr/bin:/bin:/usr/sbin:/sbin',FORK6_BUILD_ROOT=str(r),PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
for k in list(env):
 if k.startswith(('DYLD_','GNUTLS_','PYTHONPATH','PYTHONHOME')) or k in ['CC','CXX','CFLAGS','CXXFLAGS','CPPFLAGS','LDFLAGS','PKG_CONFIG_PATH','PKG_CONFIG_LIBDIR','SDKROOT']:env.pop(k,None)
def run(script,*args):
 subprocess.run(['/usr/bin/nice','-n','10','/usr/bin/python3','-B',str(f/'tools'/script),*map(str,args)],env=env,check=True)
if __name__=='__main__':
 phase=sys.argv[1]
 if phase=='all':
  for args in [('tls','arm64'),('tls','x86_64'),('placebo',),('ffmpeg','arm64'),('ffmpeg','x86_64'),('mpv',),('stage','arm64'),('stage','x86_64'),('combine',)]:run('fork6/build_all.py',*args)
  raise SystemExit(0)
 if phase=='tls':
  arch=sys.argv[2];run('gnutls/build_tls.py','--root',r,'--arch',arch);run('build_frameworks.py','--root',r,'--artifacts',r/'verified-inputs','--arch',arch,'--base-foundations-only')
 elif phase=='placebo':run('fork6/build_placebo.py')
 elif phase=='ffmpeg':run('build_ffmpeg.py','--root',r,'--artifacts',r/'verified-inputs','--arch',sys.argv[2])
 elif phase=='mpv':run('fork6/build_mpv.py')
 elif phase=='stage':run('build_frameworks.py','--root',r,'--artifacts',r/'verified-inputs','--arch',sys.argv[2],'--resume')
 elif phase=='combine':run('build_frameworks.py','--root',r,'--artifacts',r/'verified-inputs','--combine')
 else:raise SystemExit('unknown phase')
