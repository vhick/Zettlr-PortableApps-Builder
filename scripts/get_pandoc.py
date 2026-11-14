#!/usr/bin/env python3
"""Download the exact Pandoc required by pinned upstream source; verify GitHub asset SHA-256."""
from pathlib import Path
from urllib.request import urlopen,Request
import hashlib,json,os,re,sys,zipfile
root=Path(sys.argv[1] if len(sys.argv)>1 else 'upstream')
s=(root/'scripts/get-pandoc.sh').read_text(encoding='utf-8')
m=re.search(r'^VERSION="([0-9]+\.[0-9]+(?:\.[0-9]+)*)"$',s,re.M)
if not m: raise RuntimeError('Unexpected Pandoc version upstream - re-audit before changing')
version=m.group(1);name=f'pandoc-{version}-windows-x86_64.zip'
api=f'https://api.github.com/repos/jgm/pandoc/releases/tags/{version}'
h={'Accept':'application/vnd.github+json','User-Agent':'Zettlr-PortableApps-Builder','Authorization':'Bearer '+os.environ['GH_TOKEN']}
with urlopen(Request(api,headers=h),timeout=60) as f: obj=json.load(f)
if obj.get('draft') or obj.get('prerelease'): raise RuntimeError('Pandoc prerelease excluded')
assets=[a for a in obj.get('assets',[]) if a.get('name')==name]
if len(assets)!=1: raise RuntimeError('Exact official Pandoc Windows ZIP not found')
a=assets[0];expected=a.get('digest','')
if not re.fullmatch('sha256:[a-fA-F0-9]{64}',expected): raise RuntimeError('Missing official asset digest; refusing unverified dependency')
url=a.get('browser_download_url','')
if not url.startswith(f'https://github.com/jgm/pandoc/releases/download/{version}/'):raise RuntimeError('Untrusted asset URL')
print(f'Downloading verified Pandoc {name}; official SHA256 {expected}')
archive=root/'resources'/name
with urlopen(Request(url,headers={'User-Agent':'Zettlr-PortableApps-Builder'}),timeout=240) as f, archive.open('wb') as dest:
    sha=hashlib.sha256()
    while True:
        chunk=f.read(1024*1024)
        if not chunk:break
        dest.write(chunk);sha.update(chunk)
if sha.hexdigest().lower()!=expected.split(':',1)[1].lower():
    archive.unlink(missing_ok=True);raise RuntimeError('Pandoc checksum mismatch; refusing build')
with zipfile.ZipFile(archive) as z:
    names=[n for n in z.namelist() if n.endswith('/pandoc.exe') or n=='pandoc.exe']
    if len(names)!=1:raise RuntimeError('Official ZIP has unexpected binary layout')
    copyright_entries=[n for n in z.namelist() if n.endswith('/COPYRIGHT.txt') or n=='COPYRIGHT.txt']
    if not copyright_entries:raise RuntimeError('Official Pandoc archive missing COPYRIGHT.txt')
    (root/'resources'/'PandocCopyright.txt').write_bytes(z.read(copyright_entries[0]))
    with z.open(names[0]) as inp,(root/'resources'/'pandoc-win32-x64.exe').open('wb') as out:
        while True:
            b=inp.read(1024*1024)
            if not b:break
            out.write(b)
archive.unlink()
print('Pandoc official ZIP digest VERIFIED; extracted to Forge-probed resource name.')
