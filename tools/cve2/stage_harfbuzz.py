from pathlib import Path
import shutil,plistlib,subprocess,re,hashlib,os
r=Path(os.environ.get('CVE2_BUILD_ROOT','/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4-final')).resolve();fork=r/'source'
assert ' on /Volumes/4M2 ' in subprocess.check_output(['/sbin/mount'],text=True)
assert r in {Path('/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4'),Path('/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4-final')}
assert Path('/tmp/rd-gate-lock/owner').read_text().startswith('mpvlgpl ')
original=r/'verified-inputs/Libharfbuzz/Libharfbuzz.xcframework/macos-arm64_x86_64/Libharfbuzz.framework'
target=r/'static-stage/Libharfbuzz.framework';target.parent.mkdir();shutil.copytree(original,target,symlinks=True)
(target/'Headers').rename(r/'static-stage/original-harfbuzz-Headers')
(target/'Modules').rename(r/'static-stage/original-harfbuzz-Modules')
version=target/'Versions/A';(version/'Headers').mkdir();shutil.copytree(r/'harfbuzz-prefix/arm64/include/harfbuzz',version/'Headers/harfbuzz')
for header in (r/'harfbuzz-prefix/arm64/include/harfbuzz').glob('*.h'):
 assert header.read_bytes()==(r/'harfbuzz-prefix/x86_64/include/harfbuzz'/header.name).read_bytes(),header.name
(target/'Headers').symlink_to('Versions/Current/Headers')
(version/'Modules').mkdir();(version/'Modules/module.modulemap').write_text('framework module Libharfbuzz [system] {\n umbrella "../Headers"\n export *\n}\n')
(target/'Modules').symlink_to('Versions/Current/Modules')
info=version/'Resources/Info.plist';meta=plistlib.loads(info.read_bytes());meta.update(CFBundleShortVersionString='15.0.0',CFBundleVersion='15.0.0',MinimumOSVersion='11.0',LSMinimumSystemVersion='11.0');info.write_bytes(plistlib.dumps(meta))
binary=(target/'Libharfbuzz').resolve()
subprocess.run(['/usr/bin/lipo','-create',str(r/'harfbuzz-prefix/arm64/lib/libharfbuzz.a'),str(r/'harfbuzz-prefix/x86_64/lib/libharfbuzz.a'),'-output',str(binary)],check=True)
subprocess.run(['/usr/bin/lipo',str(binary),'-verify_arch','arm64','x86_64'],check=True)
(fork/'Static').mkdir(exist_ok=True)
subprocess.run(['/usr/bin/xcodebuild','-create-xcframework','-framework',str(target),'-output',str(fork/'Static/Libharfbuzz.xcframework')],check=True)
assert 'path: "Static/Libharfbuzz.xcframework"' in (fork/'Package.swift').read_text()
print('PASS new static HarfBuzz 15.0.0 target, both architectures, equal headers; archive SHA256',hashlib.sha256(binary.read_bytes()).hexdigest())
