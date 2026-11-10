import os,json,subprocess,sys,re,hashlib
from pathlib import Path
r=Path(os.environ.get('CVE2_BUILD_ROOT','/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4-final')).resolve();sys.path.insert(0,str(r/'source/tools'))
from verify_cve2 import verify_sources
from build_frameworks import framework,input_binary
verify_sources(r)
assert ' on /Volumes/4M2 ' in subprocess.check_output(['/sbin/mount'],text=True)
assert Path('/tmp/rd-gate-lock/owner').read_text().startswith('mpvlgpl ')
sdk=subprocess.check_output(['/usr/bin/xcrun','--sdk','macosx','--show-sdk-path'],text=True).strip()
art=r/'verified-inputs';manifest=json.loads((r/'source/tools/dynamic-inputs.json').read_text())
assert hashlib.sha256(input_binary(art,'Libluajit').read_bytes()).hexdigest()==manifest['Libluajit']
for arch in ['arm64','x86_64']:
 prefix=r/'prefix'/arch;stage=r/'framework-stage'/arch;pc=prefix/'lib/pkgconfig';inc=prefix/'include'
 for dirname,headers in [('libbluray',framework(art,'Libbluray')/'Headers'),('uchardet',framework(art,'Libuchardet')/'Headers/uchardet')]:
  target=inc/dirname
  if not target.exists():target.symlink_to(headers,target_is_directory=True)
 def pkg(name,version,libs,includes):
  (pc/(name+'.pc')).write_text('prefix='+str(prefix)+'\nincludedir='+str(inc)+'\nName: '+name+'\nDescription: pinned CVE2 input\nVersion: '+version+'\nLibs: '+libs+'\nCflags: -I'+str(includes)+'\n')
 pkg('libbluray','1.4.0','-F'+str(stage)+' -framework Libbluray',inc)
 pkg('uchardet','0.0.8','-F'+str(stage)+' -framework Libuchardet',inc/'uchardet')
 pkg('luajit','2.1.0',str(input_binary(art,'Libluajit')),framework(art,'Libluajit')/'Headers/luajit-2.1')
 for name in ['freetype2','harfbuzz','libass','shaderc']:
  file=pc/(name+'.pc');text=file.read_text();lines=text.splitlines();private=next((v.split(':',1)[1].strip() for v in lines if v.startswith('Libs.private:')),'');lines=[v+' '+private if v.startswith('Libs:') else v.replace('Requires.private:','Requires:') for v in lines if not v.startswith('Libs.private:')];file.write_text('\n'.join(lines)+'\n')
 (pc/'dovi.pc').write_bytes((r/'placebo-pc'/arch/'dovi.pc').read_bytes())
 generated=(r/'placebo-prefix'/arch/'lib/pkgconfig/libplacebo.pc').read_text()
 generated=re.sub(r'^Libs:.*$', 'Libs: -F'+str(stage)+' -framework Libplacebo',generated,flags=re.M)
 (pc/'libplacebo.pc').write_text(generated)
 cross=r/('mpv-'+arch+'.ini');s=(r/('placebo-'+arch+'.ini')).read_text()
 s=s.replace('[binaries]\n',"[binaries]\npython3 = '/usr/bin/python3'\n")
 s=s.replace("[binaries]\n", "[binaries]\nobjc = '/usr/bin/clang'\n")
 s+='objc_args = '+next(line.split(' = ',1)[1] for line in s.splitlines() if line.startswith('c_args = '))+'\n'
 s+='objc_link_args = '+next(line.split(' = ',1)[1] for line in s.splitlines() if line.startswith('c_link_args = '))+'\n'
 cross.write_text(s)
 options=['--wrap-mode=nodownload','--buildtype=release','-Ddefault_library=shared','-Db_lundef=true','-Dprefer_static=false','-Dauto_features=disabled','-Dlibmpv=true','-Dcplayer=false','-Dgpl=false','-Dbuild-date=true','-Dlua=luajit','-Dswift-flags=-sdk '+sdk+' -target '+arch+'-apple-macos11.0']
 enabled=['gl','plain-gl','iconv','uchardet','vulkan','moltenvk','libbluray','cocoa','coreaudio','avfoundation','gl-cocoa','videotoolbox-gl','videotoolbox-pl','lcms2','libavdevice','zlib','cplugins','vector','swift-build','macos-10-15-4-features','macos-11-features','macos-11-3-features','macos-12-features','macos-cocoa-cb','macos-media-player','macos-touchbar']
 options+=['-D'+n+'=enabled' for n in enabled]
 options+=['-D'+n+'=disabled' for n in ['libcurl','dvda','dvdnav','cdda','subrandr','javascript','zimg','jpeg','vapoursynth','rubberband']]
 env=dict(os.environ,PATH=str(r/'toolchain/bin')+':/usr/bin:/bin:/usr/sbin:/sbin',PKG_CONFIG_LIBDIR=str(pc),PKG_CONFIG_PATH='',PYTHONNOUSERSITE='1')
 meson=str(r/'toolchain/bin/meson');build=r/'mpv-build'/arch
 for command in [[meson,'setup',str(build),str(r/'upstream/mpv-0.42.0'),'--prefix='+str(r/'mpv-prefix'/arch),'--cross-file='+str(cross)]+options,[meson,'compile','-C',str(build),'-j4'],[meson,'install','-C',str(build)]]:
  print('RUN',command,flush=True);subprocess.run(['/usr/bin/nice','-n','10']+command,env=env,check=True)
 print('PASS mpv 0.42.0 with both retained fork patches',arch,flush=True)
