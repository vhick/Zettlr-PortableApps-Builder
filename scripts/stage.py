#!/usr/bin/env python3
"""Make app-specific PortableApps stage from source-built Zettlr win32 x64 package."""
import os,json,shutil,sys,hashlib
from pathlib import Path
root=Path.cwd();up=root/'upstream';out=up/'out'/'Zettlr-win32-x64';stage=root/'staging'/'ZettlrPortable'
if not (out/'Zettlr.exe').is_file():raise RuntimeError('Missing source-compiled Zettlr.exe')
if not (out/'resources'/'app.asar').is_file():raise RuntimeError('Missing Electron app.asar')
if not (out/'resources'/'pandoc.exe').is_file():raise RuntimeError('Missing bundled Pandoc; cannot publish broken import/export')
if not (root/'bin'/'ZettlrPortable.exe').is_file():raise RuntimeError('Missing compiled root launcher')
if stage.exists(): shutil.rmtree(stage)
(stage/'App').mkdir(parents=True)
shutil.copytree(out,stage/'App'/'Zettlr',symlinks=False)
appinfo=stage/'App'/'AppInfo';appinfo.mkdir()
for original,dest in [('icon.ico','appicon.ico'),('icon_16.png','appicon_16.png'),('icon_32.png','appicon_32.png')]:
    shutil.copy2(root/'assets-build'/original,appinfo/dest)
meta=json.loads((root/'build-identity.json').read_text(encoding='utf-8'))
version=(up/'package.json').read_text(encoding='utf-8')
import re
v=re.search(r'"version"\s*:\s*"(\d+)\.(\d+)\.(\d+)"',version)
if not v:raise RuntimeError('Unexpected upstream version')
package_version='.'.join(v.groups())+'.1'
ini=f'''[Format]
Type=PortableApps.comFormat
Version=3.9

[Details]
Name=Zettlr Portable (Community Build)
AppID=ZettlrPortable-CommunityBuild
Publisher=Independent Community Builder (Zettlr by Hendrik Erz)
Homepage=https://www.zettlr.com/
Category=Office
Description=Portable community packaging of the Zettlr publication workbench.
Language=Multilingual

[License]
Shareable=true
OpenSource=true
Freeware=true
CommercialUse=true

[Version]
PackageVersion={package_version}
DisplayVersion={'.'.join(v.groups())} Community b1r5

[Control]
Icons=1
Start=ZettlrPortable.exe
'''
(appinfo/'appinfo.ini').write_text(ini,encoding='utf-8',newline='\r\n')
shutil.copy2(root/'bin'/'ZettlrPortable.exe',stage/'ZettlrPortable.exe')
for d in ('Data/Profile/PortableDocuments','Data/TraceGuard','Other/Source','Other/Help'):(stage/d).mkdir(parents=True,exist_ok=True)
for name in ('launcher/ZettlrPortable.cpp','scripts/patch_source.py','scripts/get_pandoc.py','scripts/prepare_icons.py','scripts/stage.py','scripts/build_launcher.ps1'):
    shutil.copy2(root/name,stage/'Other'/'Source'/Path(name).name)
shutil.copy2(root/'build-identity.json',stage/'Other'/'Source'/'build-identity.json')
shutil.copy2(root/'assets-build'/'ICON-PROVENANCE.json',stage/'Other'/'Source'/'ICON-PROVENANCE.json')
shutil.copy2(root/'docs/PORTABILITY-AUDIT.md',stage/'Other'/'Source'/'PORTABILITY-AUDIT.md')
if (root/'source-adaptation.diff').is_file():shutil.copy2(root/'source-adaptation.diff',stage/'Other'/'Source'/'source-adaptation.diff')
shutil.copy2(up/'LICENSE',stage/'Other'/'Source'/'UPSTREAM-LICENSE.txt')
shutil.copy2(up/'resources'/'PandocCopyright.txt',stage/'Other'/'Source'/'PANDOC-COPYRIGHT.txt')
shutil.copy2(root/'docs/PORTABLE-USAGE.md',stage/'Other'/'Help'/'README.md')
(stage/'Other'/'Source'/'SOURCE-AVAILABILITY.txt').write_text(f'''Source build of Zettlr at {meta['upstream_commit']} ({meta['upstream_tag']}).\nFull corresponding upstream source: https://github.com/Zettlr/Zettlr/tree/{meta['upstream_commit']}\nSource archive: https://github.com/Zettlr/Zettlr/archive/{meta['upstream_commit']}.zip\nCommunity launcher and patch source enclosed in this directory.\nLock SHA-256: {meta['yarn_lock_sha256']}\nZettlr name and graphics are separately trademarked and not owned by this community builder.\n''',encoding='utf-8')
print('Staged:',stage,'app files:',len(list((stage/'App'/'Zettlr').rglob('*'))))
