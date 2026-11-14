#!/usr/bin/env python3
"""Resolve official stable Zettlr GitHub releases, never arbitrary branch HEAD."""
import json, os, re, sys, urllib.request, urllib.error
from pathlib import Path

API='https://api.github.com/repos/Zettlr/Zettlr'
STABLE=re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$')

def api(path):
    req=urllib.request.Request(API+path, headers={'Accept':'application/vnd.github+json','User-Agent':'Zettlr-PortableApps-Builder','X-GitHub-Api-Version':'2022-11-28','Authorization':'Bearer '+os.environ['GH_TOKEN']})
    try:
        with urllib.request.urlopen(req,timeout=35) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        msg=e.read().decode('utf-8','replace')[:400]
        raise RuntimeError(f'GitHub API HTTP {e.code} {path}: {msg}') from e

def select(releases, version):
    valid=[]
    for rel in releases:
        tag=rel.get('tag_name','')
        m=STABLE.fullmatch(tag)
        if (not m or rel.get('draft') or rel.get('prerelease') or
            not rel.get('published_at')): continue
        num=tuple(map(int,m.groups()))
        if version and tag not in (version,'v'+version.lstrip('v')): continue
        valid.append((num,rel))
    if not valid: raise RuntimeError('No matching published stable Zettlr release found')
    valid.sort(key=lambda row:row[0],reverse=True)
    return valid[0][1]

def main():
    version=os.getenv('UPSTREAM_VERSION','').strip()
    if version and not STABLE.fullmatch(version): raise RuntimeError('Explicit version must be stable X.Y.Z or vX.Y.Z')
    releases=[]
    for page in range(1,6):
        batch=api(f'/releases?per_page=100&page={page}')
        if not isinstance(batch,list): raise RuntimeError('Unexpected GitHub response')
        releases.extend(batch)
        if version and any(r.get('tag_name','') in (version,'v'+version.lstrip('v')) for r in batch): break
        if len(batch)<100: break
    rel=select(releases, version)
    tag=rel['tag_name']; resolved=tag.lstrip('v')
    values={'upstream_tag':tag, 'upstream_version':resolved}
    print(json.dumps({'selected_release':tag,'published_at':rel['published_at'],'html_url':rel['html_url']},ensure_ascii=False))
    output=os.getenv('GITHUB_OUTPUT')
    if output:
        with open(output,'a',encoding='utf-8') as f:
            for k,v in values.items(): f.write(f'{k}={v}\n')
    else:
        for k,v in values.items(): print(f'{k}={v}')
if __name__=='__main__':
    try: main()
    except Exception as e: print(f'RELEASE RESOLUTION FAILED: {e}',file=sys.stderr);sys.exit(1)
