#!/usr/bin/env python3
"""Bind upstream SHA, builder SHA, lock SHA to a noncolliding publication identity."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,urllib.request,urllib.error
up=Path('upstream')
sha=subprocess.check_output(['git','-C',str(up),'rev-parse','HEAD'],text=True).strip()
if not re.fullmatch('[a-f0-9]{40}',sha):raise RuntimeError('Invalid upstream commit')
version=os.environ['UPSTREAM_VERSION'];tag=os.environ['UPSTREAM_TAG']
pack=json.loads((up/'package.json').read_text(encoding='utf-8'))
if str(pack['version'])!=version or pack['name']!='zettlr':raise RuntimeError('Release does not match version in package.json')
lock=up/'yarn.lock'; lock_sha=hashlib.sha256(lock.read_bytes()).hexdigest()
builder=os.environ['GITHUB_SHA'];revision='b1r2'
if not re.fullmatch('[0-9a-f]{40}',builder):raise RuntimeError('Invalid builder revision')
release=f'portable-v{version}-{sha[:9]}-{revision}-{builder[:9]}'
# Need check EXACT builder-owned tag; 404 only means absent; other errors fail.
repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GH_TOKEN']
req=urllib.request.Request(f'https://api.github.com/repos/{repo}/releases/tags/{release}',headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+token,'User-Agent':'Zettlr-PortableApps-Builder'})
try:
    with urllib.request.urlopen(req,timeout=40) as f:
        payload=json.load(f)
        if payload.get('tag_name')!=release:raise RuntimeError('Unexpected existing-release identity')
        names={a.get('name','') for a in payload.get('assets',[])}
        expected_zip=f'ZettlrPortable_{version}_x64_{revision}_{sha[:9]}.zip'
        if expected_zip not in names or not any(n.lower().endswith('.paf.exe') for n in names):
            raise RuntimeError('Exact tag exists but its validated ZIP/PAF artifacts are incomplete; refusing accidental overwrite or false skip')
        skip='true'
except urllib.error.HTTPError as e:
    if e.code==404:skip='false'
    else:raise RuntimeError(f'Existing-release lookup HTTP {e.code}: {e.read().decode("utf8","replace")[:300]}')
source={'upstream_repository':'https://github.com/Zettlr/Zettlr','upstream_tag':tag,'upstream_commit':sha,'yarn_lock_sha256':lock_sha,'builder_commit':builder,'package_revision':revision,'release_tag':release,'python_version':sys.version.split()[0]}
Path('build-identity.json').write_text(json.dumps(source,indent=2)+'\n',encoding='utf-8')
with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:
    for k,v in {'upstream_sha':sha,'release_tag':release,'skip':skip}.items():f.write(f'{k}={v}\n')
print(json.dumps({'identity':source,'release_already_exists':skip=='true'},indent=2))
