#!/usr/bin/env python3
"""Installer artifact identity and PE structure. Interactive installs need real user testing."""
import os,hashlib,struct,sys,subprocess,shutil
from pathlib import Path
path=Path(os.environ['INSTALLER_FILE'])
if not path.is_file() or path.stat().st_size<200000:raise RuntimeError('Installer missing or suspiciously small')
if not path.name.lower().endswith('.paf.exe'):raise RuntimeError('Expected real PortableApps-style .paf.exe')
with path.open('rb') as f:
    if f.read(2)!=b'MZ':raise RuntimeError('Installer not PE')
    f.seek(0x3c);off=struct.unpack('<I',f.read(4))[0];f.seek(off)
    if f.read(4)!=b'PE\0\0':raise RuntimeError('Installer lacks PE signature')
    arch=struct.unpack('<H',f.read(2))[0]
    if arch not in (0x14c,0x8664):raise RuntimeError(f'Unexpected installer architecture {arch:04x}')
sha=hashlib.sha256(path.read_bytes()).hexdigest()
if sha.lower()!=os.environ['INSTALLER_SHA256'].lower():raise RuntimeError('Shared builder hash disagrees with actual installer')
(Path('dist')/(path.name+'.sha256')).write_text(sha+'  '+path.name+'\n',encoding='ascii')
seven=shutil.which('7z.exe') or os.environ.get('SEVEN_ZIP','')
if not seven or not Path(seven).exists():raise RuntimeError('7-Zip needed to independently inventory NSIS installer contents')
listing=subprocess.run([seven,'l','-slt',str(path.resolve())],capture_output=True,text=True,errors='replace')
if listing.returncode!=0:raise RuntimeError('Cannot open generated NSIS installer as an archive: '+listing.stderr[-600:])
entries=listing.stdout.lower()
for item in ('zettlrportable.exe','zettlr.exe','appinfo.ini'):
    if item not in entries:raise RuntimeError('Missing embedded installer payload: '+item)
print('Independent 7-Zip NSIS payload inventory includes launcher, Zettlr and PortableApps metadata.')
print('INSTALLER STATIC VALIDATION PASSED',path,'architecture',hex(arch),'SHA256',sha)
print('LIMITATION: Cannot prove silent install/reinstall or embedded extraction in headless runner.')
