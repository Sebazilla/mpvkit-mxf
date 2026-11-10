import os,subprocess,hashlib,json
from pathlib import Path
r=Path(os.environ.get('CVE2_BUILD_ROOT','/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4-final')).resolve()
assert ' on /Volumes/4M2 ' in subprocess.check_output(['/sbin/mount'],text=True)
import sys
sys.path.insert(0,str(r/'source/tools'))
from verify_cve2 import verify_sources
verify_sources(r)
assert Path('/tmp/rd-gate-lock/owner').read_text().startswith('mpvlgpl ')
tools=json.loads((r/'source/tools/toolchain-inputs.json').read_text())
for name,rec in tools.items():
 assert hashlib.sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256'],name
if not (r/'toolchain').exists(): (r/'toolchain').symlink_to('/Volumes/4M2/Dev/rushdeck/mpvkit-dyn2/toolchain')
sdk=subprocess.check_output(['/usr/bin/xcrun','--sdk','macosx','--show-sdk-path'],text=True).strip()
env=dict(os.environ,PATH=str(r/'toolchain/bin')+':/usr/bin:/bin:/usr/sbin:/sbin',PKG_CONFIG_PATH='',PKG_CONFIG_LIBDIR=str(r/'empty-pc'))
(r/'empty-pc').mkdir(exist_ok=True)
meson=str(r/'toolchain/bin/meson')
for arch in ['arm64','x86_64']:
 flags=['-arch',arch,'-isysroot',sdk,'-target',arch+'-apple-macos11.0','-mmacosx-version-min=11.0']
 cross=r/('harfbuzz-'+arch+'.ini')
 cross.write_text("[binaries]\nc = '/usr/bin/clang'\ncpp = '/usr/bin/clang++'\nar = '/usr/bin/ar'\nstrip = '/usr/bin/strip'\npkg-config = '"+str(r/'toolchain/bin/pkg-config')+"'\n[host_machine]\nsystem = 'darwin'\ncpu_family = '"+('aarch64' if arch=='arm64' else 'x86_64')+"'\ncpu = '"+arch+"'\nendian = 'little'\n[properties]\nneeds_exe_wrapper = true\n[built-in options]\nc_args = "+repr(flags)+"\ncpp_args = "+repr(flags)+"\nc_link_args = "+repr(flags)+"\ncpp_link_args = "+repr(flags)+"\n")
 build=r/'harfbuzz-build'/arch
 options=['--wrap-mode=nodownload','--buildtype=release','-Ddefault_library=static','-Db_staticpic=true']
 for name in ['wasm','glib','gobject','freetype','icu','cairo','chafa','png','zlib','graphite2','coretext','tests','introspection','docs','utilities','benchmark','subset','raster','vector','gpu','gpu_demo']:
  options+=['-D'+name+'=disabled']
 commands=[[meson,'setup',str(build),str(r/'upstream/harfbuzz-15.0.0'),'--prefix='+str(r/'harfbuzz-prefix'/arch),'--cross-file='+str(cross)]+options,[meson,'compile','-C',str(build),'-j4'],[meson,'install','-C',str(build)]]
 for command in commands:
  print('RUN',command,flush=True);subprocess.run(['/usr/bin/nice','-n','10']+command,env=env,check=True)
 archive=r/'harfbuzz-prefix'/arch/'lib/libharfbuzz.a'
 print('BUILT',arch,archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest(),flush=True)
