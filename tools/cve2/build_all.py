#!/usr/bin/env python3
"""CVE2 fresh arm64+x86_64 build; holds no implicit gate or publishing authority."""
import os,subprocess,sys
from pathlib import Path
ROOT=Path('/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4-final')
FORK=Path(__file__).resolve().parents[2]

def run(*args):
 print('RUN',list(map(str,args)),flush=True)
 subprocess.run(['/usr/bin/nice','-n','10','/usr/bin/python3',*map(str,args)],check=True,env=dict(os.environ,PATH='/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin',CVE2_BUILD_ROOT=str(ROOT)))
def main():
 if ROOT.exists():raise SystemExit('build_all requires a wholly fresh dyn4-final root')
 run(FORK/'tools/cve2/prepare.py')
 run(FORK/'tools/cve2/build_harfbuzz.py')
 for arch in ['arm64','x86_64']:
  run(FORK/'tools/gnutls/build_tls.py','--root',ROOT,'--arch',arch)
  run(FORK/'tools/build_frameworks.py','--root',ROOT,'--artifacts',ROOT/'verified-inputs','--arch',arch,'--base-foundations-only')
 run(FORK/'tools/cve2/build_placebo.py')
 for arch in ['arm64','x86_64']:
  run(FORK/'tools/build_ffmpeg.py','--root',ROOT,'--artifacts',ROOT/'verified-inputs','--arch',arch)
 run(FORK/'tools/cve2/build_mpv.py')
 for arch in ['arm64','x86_64']:
  run(FORK/'tools/build_frameworks.py','--root',ROOT,'--artifacts',ROOT/'verified-inputs','--arch',arch,'--resume')
 # First-run outputs are preserved, never tagged or overwritten in place.
 retained=Path('/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4/pre-final-artifacts');retained.mkdir()
 for name in ['Dynamic','Static']:
  if (FORK/name).exists():(FORK/name).rename(retained/name)
 run(FORK/'tools/build_frameworks.py','--root',ROOT,'--artifacts',ROOT/'verified-inputs','--combine')
 run(FORK/'tools/cve2/stage_harfbuzz.py')
 print('PASS fresh complete native build from committed recipe; perform all acceptance proofs before publication',flush=True)
if __name__=='__main__':main()
