#!/usr/bin/env python3
"""Fail closed on public trademark/redistribution without user attestation."""
import os,json,urllib.request
req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY'],headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+os.environ['GH_TOKEN'],'User-Agent':'Zettlr-PortableApps-Builder'})
with urllib.request.urlopen(req,timeout=30) as r: repo=json.load(r)
public=not repo.get('private',True)
attested=os.environ.get('BRAND_PERMISSION','false').lower()=='true'
if public and not attested:raise RuntimeError('PUBLIC builder repository: publication blocked without confirm_brand_rights=true. Zettlr brand/logo redistribution requires permission from rights holder, see https://www.zettlr.com/press . Use private repo or obtain rights.')
print('Publication gate passed; public=',public,'user attestation=',attested,'(not independent legal verification).')
