#!/usr/bin/env python3
"""CVE3 fresh arm64+x86_64 build; holds no implicit gate or publishing authority."""
import os,subprocess,sys,shutil
from pathlib import Path
ROOT=Path('/Volumes/4M2/Dev/rushdeck/tmp/cve3/dyn5')
FORK=Path(__file__).resolve().parents[2]

def run(*args):
 print('RUN',list(map(str,args)),flush=True)
 subprocess.run(['/usr/bin/nice','-n','10','/usr/bin/python3',*map(str,args)],check=True,env=dict(os.environ,PATH='/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin',CVE3_BUILD_ROOT=str(ROOT),PYTHONDONTWRITEBYTECODE='1'))
def main():
 if ROOT.exists():raise SystemExit('build_all requires a wholly fresh dyn5 root')
 run(FORK/'tools/cve3/prepare.py')
 run(FORK/'tools/cve3/retain_harfbuzz.py')
 for arch in ['arm64','x86_64']:
  run(FORK/'tools/gnutls/build_tls.py','--root',ROOT,'--arch',arch)
  run(FORK/'tools/build_frameworks.py','--root',ROOT,'--artifacts',ROOT/'verified-inputs','--arch',arch,'--base-foundations-only')
 run(FORK/'tools/cve3/build_placebo.py')
 for arch in ['arm64','x86_64']:
  run(FORK/'tools/build_ffmpeg.py','--root',ROOT,'--artifacts',ROOT/'verified-inputs','--arch',arch)
 run(FORK/'tools/cve3/build_mpv.py')
 for arch in ['arm64','x86_64']:
  run(FORK/'tools/build_frameworks.py','--root',ROOT,'--artifacts',ROOT/'verified-inputs','--arch',arch,'--resume')
 # Preserve cloned dyn4 artifacts outside candidate output directories.
 retained=ROOT/'cloned-dyn4-artifacts';retained.mkdir()
 for name in ['Dynamic','Static']:
  if (FORK/name).exists():(FORK/name).rename(retained/name)
 run(FORK/'tools/build_frameworks.py','--root',ROOT,'--artifacts',ROOT/'verified-inputs','--combine')
 shutil.copytree(retained/'Static',FORK/'Static',symlinks=True)
 print('PASS fresh native consumer build with explicit MoltenVK/HB takeovers; acceptance proofs required before publication',flush=True)
if __name__=='__main__':main()
