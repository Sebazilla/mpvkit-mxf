from pathlib import Path
import os,shutil,hashlib,subprocess
r=Path(os.environ['CVE3_BUILD_ROOT']);old=Path('/Volumes/4M2/Dev/rushdeck/mpvkit-dyn4')
assert Path('/tmp/rd-gate-lock/owner').read_text().startswith('cve3 ')
for arch in ['arm64','x86_64']:
 shutil.copytree(old/'harfbuzz-prefix'/arch,r/'harfbuzz-prefix'/arch,symlinks=True)
 cross=r/('harfbuzz-'+arch+'.ini');cross.write_text((old/cross.name).read_text().replace('/Volumes/4M2/Dev/rushdeck/tmp/cve2/dyn4-final',str(r)))
binary=r/'retained-harfbuzz-universal.a'
subprocess.run(['/usr/bin/lipo','-create',str(r/'harfbuzz-prefix/arm64/lib/libharfbuzz.a'),str(r/'harfbuzz-prefix/x86_64/lib/libharfbuzz.a'),'-output',str(binary)],check=True)
tag=r/'source/Static/Libharfbuzz.xcframework/macos-arm64_x86_64/Libharfbuzz.framework/Libharfbuzz'
assert hashlib.sha256(binary.read_bytes()).hexdigest()==hashlib.sha256(tag.read_bytes()).hexdigest()
print('RETAINED HB15 matches dyn4 tag universal SHA256',hashlib.sha256(binary.read_bytes()).hexdigest(),flush=True)
