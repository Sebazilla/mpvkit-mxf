SUBMODULES = [{'path': '3rdparty/Vulkan-Headers', 'revision': '74d8a6cb930c68ef617b202c3ff3c59d919e086b', 'repository': 'https://github.com/KhronosGroup/Vulkan-Headers', 'archive': 'https://github.com/KhronosGroup/Vulkan-Headers/archive/74d8a6cb930c68ef617b202c3ff3c59d919e086b.tar.gz', 'filename': 'KhronosGroup-Vulkan-Headers-74d8a6cb930c68ef617b202c3ff3c59d919e086b.tar.gz', 'bytes': 3029927, 'sha256': '75967a8288ff16044a86d1af462b96d2e75c435937efb75f2bb4102ab0382f29'}, {'path': '3rdparty/fast_float', 'revision': '97b54ca9e75f5303507699d27c6b4f4efe4641a1', 'repository': 'https://github.com/fastfloat/fast_float', 'archive': 'https://github.com/fastfloat/fast_float/archive/97b54ca9e75f5303507699d27c6b4f4efe4641a1.tar.gz', 'filename': 'fastfloat-fast_float-97b54ca9e75f5303507699d27c6b4f4efe4641a1.tar.gz', 'bytes': 120200, 'sha256': '2b132274539286e41f37857cac22aa8441d21bd86d55de825a3342b149f66801'}, {'path': '3rdparty/glad', 'revision': '73db193f853e2ee079bf3ca8a64aa2eaf6459043', 'repository': 'https://github.com/Dav1dde/glad', 'archive': 'https://github.com/Dav1dde/glad/archive/73db193f853e2ee079bf3ca8a64aa2eaf6459043.tar.gz', 'filename': 'Dav1dde-glad-73db193f853e2ee079bf3ca8a64aa2eaf6459043.tar.gz', 'bytes': 645779, 'sha256': '33dbeae44d8315ece57e14eba4b1b4a02ac5406d1c4f49cd20048c91522a6b9a'}, {'path': '3rdparty/jinja', 'revision': '15206881c006c79667fe5154fe80c01c65410679', 'repository': 'https://github.com/pallets/jinja', 'archive': 'https://github.com/pallets/jinja/archive/15206881c006c79667fe5154fe80c01c65410679.tar.gz', 'filename': 'pallets-jinja-15206881c006c79667fe5154fe80c01c65410679.tar.gz', 'bytes': 276954, 'sha256': 'b88a20dcc2e34072fcf4159325bc6c34cd4b29a81a8b83d15d2f28ba561da296'}, {'path': '3rdparty/markupsafe', 'revision': '297fc8e356e6836a62087949245d09a28e9f1b13', 'repository': 'https://github.com/pallets/markupsafe', 'archive': 'https://github.com/pallets/markupsafe/archive/297fc8e356e6836a62087949245d09a28e9f1b13.tar.gz', 'filename': 'pallets-markupsafe-297fc8e356e6836a62087949245d09a28e9f1b13.tar.gz', 'bytes': 83817, 'sha256': 'da7c010c9c81a66ac73036558c1fcb6212b50482f43211cd1254035b94f82414'}, {'path': 'demos/3rdparty/nuklear', 'revision': '242f35efa067a46c595645eeda7b1771ea1f83b1', 'repository': 'https://github.com/Immediate-Mode-UI/Nuklear', 'archive': 'https://github.com/Immediate-Mode-UI/Nuklear/archive/242f35efa067a46c595645eeda7b1771ea1f83b1.tar.gz', 'filename': 'Immediate-Mode-UI-Nuklear-242f35efa067a46c595645eeda7b1771ea1f83b1.tar.gz', 'bytes': 2339403, 'sha256': 'ac567995f917c10a722409e0141d226e737d06488b0a31166f6e4925da8e58f0'}]
import os,json,hashlib,tarfile,subprocess
from pathlib import Path
r=Path(os.environ.get('CVE3_BUILD_ROOT','/Volumes/4M2/Dev/rushdeck/tmp/cve3/dyn5')).resolve();old=Path('/Volumes/4M2/Dev/rushdeck/mpvkit-dyn2/cve1-dyn3');src=r/'upstream/libplacebo-7.387.0';art=old/'verified-inputs'
assert ' on /Volumes/4M2 ' in subprocess.check_output(['/sbin/mount'],text=True)
import sys
sys.path.insert(0,str(r/'source/tools'))
from verify_cve3 import verify_sources
verify_sources(r)
assert Path('/tmp/rd-gate-lock/owner').read_text().startswith('cve3 ')
for s in SUBMODULES:
 a=Path('/Volumes/4M2/Dev/rushdeck/tmp/cve3/sources')/s['filename'];assert hashlib.sha256(a.read_bytes()).hexdigest()==s['sha256']
 target=src/s['path'];target.mkdir(parents=True,exist_ok=True)
 with tarfile.open(a) as t:
  for m in t:
   parts=Path(m.name).parts[1:]
   if not parts:continue
   path=target.joinpath(*parts);assert path.resolve().is_relative_to(target.resolve())
   if m.isdir():path.mkdir(parents=True,exist_ok=True)
   elif m.isfile():
    data=t.extractfile(m).read()
    if path.exists():assert path.read_bytes()==data
    else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
   else:raise RuntimeError('unsupported submodule member '+m.name)
 print('VERIFIED SUBMODULE',s['path'],s['sha256'],flush=True)
sdk=subprocess.check_output(['/usr/bin/xcrun','--sdk','macosx','--show-sdk-path'],text=True).strip()
def framework(n):
 paths=list((art/n).glob('*.xcframework/macos-*/'+n+'.framework'));assert len(paths)==1;return paths[0]
manifest=json.loads((r/'source/tools/dynamic-inputs.json').read_text())
for name in ['Libshaderc_combined','lcms2','Libdovi']:
 assert hashlib.sha256((framework(name)/name).read_bytes()).hexdigest()==manifest[name],name
header_root=r/'placebo-headers';header_root.mkdir(exist_ok=True)
if not (header_root/'libdovi').exists():(header_root/'libdovi').symlink_to(framework('Libdovi')/'Headers')
for arch in ['arm64','x86_64']:
 flags=['-arch',arch,'-isysroot',sdk,'-target',arch+'-apple-macos11.0','-mmacosx-version-min=11.0']
 cross=r/('placebo-'+arch+'.ini');cross.write_text((r/('harfbuzz-'+arch+'.ini')).read_text().replace('[binaries]\n', '[binaries]\npython = \'/usr/bin/python3\'\n'))
 pc=r/'placebo-pc'/arch;pc.mkdir(parents=True,exist_ok=True)
 def pkg(name,ver,libs,inc):
  (pc/(name+'.pc')).write_text('Name: '+name+'\nDescription: pinned CVE3 input\nVersion: '+ver+'\nLibs: '+libs+'\nCflags: -I'+str(inc)+'\n')
 pkg('shaderc','2025.5.0',str(framework('Libshaderc_combined')/'Libshaderc_combined')+' -lc++',framework('Libshaderc_combined')/'Headers')
 pkg('lcms2','2.17.0',str(framework('lcms2')/'lcms2'),framework('lcms2')/'Headers')
 pkg('dovi','3.3.2',str(framework('Libdovi')/'Libdovi')+' -framework Security -framework CoreFoundation -liconv',header_root)
 pkg('vulkan','1.4.334','-F'+str(r/'framework-stage'/arch)+' -framework MoltenVK',src/'3rdparty/Vulkan-Headers/include')
 env=dict(os.environ,PATH=str(r/'toolchain/bin')+':/usr/bin:/bin:/usr/sbin:/sbin',PKG_CONFIG_PATH='',PKG_CONFIG_LIBDIR=str(pc),PYTHONNOUSERSITE='1')
 build=r/'placebo-build'/arch;meson=str(r/'toolchain/bin/meson')
 options=['--wrap-mode=nodownload','--buildtype=release','-Ddefault_library=shared','-Ddemos=false','-Dtests=false','-Dbench=false','-Dfuzz=false']
 for n in ['vulkan','vk-proc-addr','opengl','gl-proc-addr','shaderc','lcms','dovi','libdovi']:options+=['-D'+n+'=enabled']
 for n in ['d3d11','glslang','unwind','xxhash']:options+=['-D'+n+'=disabled']
 for command in [[meson,'setup',str(build),str(src),'--prefix='+str(r/'placebo-prefix'/arch),'--cross-file='+str(cross)]+options,[meson,'compile','-C',str(build),'-j4'],[meson,'install','-C',str(build)]]:
  print('RUN',command,flush=True);subprocess.run(['/usr/bin/nice','-n','10']+command,env=env,check=True)
 print('PASS libplacebo source build',arch,flush=True)
