#!/usr/bin/env python3
"""Independent pre-installer checks: files, PE machine, ZIP integrity, manifest and empty dirs."""
from pathlib import Path
import hashlib,zipfile,struct,os,json,sys
root=Path.cwd();stage=root/'staging'/'ZettlrPortable';dist=root/'dist';dist.mkdir(exist_ok=True)
identity=json.loads((root/'build-identity.json').read_text(encoding='utf-8'))
version=identity['upstream_tag'].lstrip('v');short=identity['upstream_commit'][:9]
revision=identity['package_revision']
name=f'ZettlrPortable_{version}_x64_{revision}_{short}.zip'
required=['ZettlrPortable.exe','App/Zettlr/Zettlr.exe','App/Zettlr/resources/app.asar','App/Zettlr/resources/pandoc.exe','App/AppInfo/appinfo.ini','App/AppInfo/appicon.ico','App/AppInfo/appicon_16.png','App/AppInfo/appicon_32.png','Other/Source/ZettlrPortable.cpp','Other/Source/UPSTREAM-LICENSE.txt']
for namepart in required:
    if not (stage/namepart).is_file():raise RuntimeError('Missing '+namepart)
# The launcher and PortableApps menu must use the authentic icon set from
# THIS exact source checkout, not a generated/unrelated icon.
icon_provenance_path = stage / 'Other/Source/ICON-PROVENANCE.json'
if not icon_provenance_path.is_file():
    raise RuntimeError('Missing official icon provenance')
icon_provenance = json.loads(icon_provenance_path.read_text(encoding='utf-8'))
icon_names = {'icon.ico': 'appicon.ico', 'icon_16.png': 'appicon_16.png', 'icon_32.png': 'appicon_32.png'}
for name, packaged_name in icon_names.items():
    data = icon_provenance['files'][name]
    original = root/'upstream'/data['upstream_path']
    staged = stage/'App'/'AppInfo'/packaged_name
    source_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    packaged_hash = hashlib.sha256(staged.read_bytes()).hexdigest()
    if source_hash != data['sha256'] or packaged_hash != source_hash:
        raise RuntimeError(f'Official icon mismatch: {packaged_name}')
print('SOURCE-MATCHED ICONS PASSED: appinfo ICO and both PNGs')
for path in ('Data/Profile/PortableDocuments','Data/TraceGuard','Other/Source'):
    if not (stage/path).is_dir():raise RuntimeError('Missing required directory '+path)
for item in stage.rglob('*'):
    if item.is_symlink() or (hasattr(os.path,'isjunction') and os.path.isjunction(item)):raise RuntimeError('No symlinks or junctions allowed in package: '+str(item))

def machine(path):
    with path.open('rb') as f:
        if f.read(2)!=b'MZ':raise RuntimeError(f'Not PE: {path}')
        f.seek(0x3c);off=struct.unpack('<I',f.read(4))[0];f.seek(off)
        if f.read(4)!=b'PE\0\0':raise RuntimeError(f'Not PE signature: {path}')
        return struct.unpack('<H',f.read(2))[0]
for exe in ('ZettlrPortable.exe','App/Zettlr/Zettlr.exe','App/Zettlr/resources/pandoc.exe'):
    if machine(stage/exe)!=0x8664:raise RuntimeError('Not x64 PE: '+exe)
meta=(stage/'App/AppInfo/appinfo.ini').read_text(encoding='utf-8')
for token in ('AppID=ZettlrPortable-CommunityBuild',f'PackageVersion={version}.1','Start=ZettlrPortable.exe','Type=PortableApps.comFormat'):
    if token not in meta:raise RuntimeError('Metadata mismatch: '+token)
manifest={}
for p in sorted(stage.rglob('*')):
    if p.is_file():manifest[p.relative_to(stage).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(stage/'Other'/'Source'/'SHA256-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
zip_path=dist/name
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
    z.write(stage,'ZettlrPortable/')
    for p in sorted(stage.rglob('*')):z.write(p,'ZettlrPortable/'+p.relative_to(stage).as_posix()+('/' if p.is_dir() else ''))
with zipfile.ZipFile(zip_path) as z:
    failure=z.testzip()
    if failure:raise RuntimeError('ZIP CRC failure: '+failure)
    for member in required:
        if 'ZettlrPortable/'+member not in z.namelist():raise RuntimeError('ZIP missing '+member)
    for member in ('Data/Profile/PortableDocuments/','Data/TraceGuard/'):
        if 'ZettlrPortable/'+member not in z.namelist():raise RuntimeError('ZIP missing empty directory '+member)
sha_obj=hashlib.sha256()
with zip_path.open('rb') as src:
    for block in iter(lambda:src.read(1024*1024),b''):sha_obj.update(block)
sha=sha_obj.hexdigest()
(dist/(zip_path.name+'.sha256')).write_text(sha+'  '+zip_path.name+'\n',encoding='ascii')
print('INDEPENDENT ZIP VALIDATION PASSED:',zip_path,'SHA256',sha)
with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:f.write('zip_file='+str(zip_path.resolve())+'\n')
