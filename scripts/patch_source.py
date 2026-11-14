#!/usr/bin/env python3
"""Fail-closed, narrow patch of the exact audited Zettlr main entry sequence.

Changes: (1) before single-instance lock, resolve source-supported data-dir;
(2) for the compiled community portable app only, make Documents defaults portable;
(3) distinct AUMID for portable and installed Zettlr. No broad APPDATA override.
"""
from pathlib import Path
import os,sys

path=Path(sys.argv[1] if len(sys.argv)>1 else 'upstream/source/main.ts')
src=path.read_text(encoding='utf-8')
start='// Setting custom data dir for user configuration files.\n'
end='// On systems with virtual GPUs (i.e. VMs), it might be necessary to disable\n'
anchor='handleExitArguments()\n'
assert src.count(start)==1 and src.count(end)==1 and src.count(anchor)==1, 'main.ts anchors changed upstream; stop and re-audit'
pre,rest=src.split(start,1)
original,post=rest.split(end,1)
assert "app.setPath('userData', dataDir)" in original and "app.setAppLogsPath(path.join(dataDir, 'logs'))" in original
assert src.count("app.setAppUserModelId('com.zettlr.app')")==1
# Require original block to be after the pre-lock code, preventing duplicate execution.
assert pre.index('app.requestSingleInstanceLock()') > pre.index(anchor), 'Unexpected singleton structure'
# Early dataDir change needed to give portable copy its own singleton profile.
additional='''// Community PortableApps adaptation: source-specific portable data and Documents.\n// The launcher pre-creates Data/Profile/PortableDocuments; never touch host Documents.\n  if (process.env.ZETTLR_PORTABLE_MODE === '1') {\n    const portableDocs = path.join(dataDir, 'PortableDocuments')\n    app.setPath('documents', portableDocs)\n  }\n'''
# The additional source goes inside the dataDir conditional after setAppLogsPath.
original=original.replace("  app.setAppLogsPath(path.join(dataDir, 'logs'))\n", "  app.setAppLogsPath(path.join(dataDir, 'logs'))\n"+additional)
assert original.count('ZETTLR_PORTABLE_MODE')==1
out=pre.replace(anchor,anchor+start+original+'\n',1)+end+post
old="app.setAppUserModelId('com.zettlr.app')"
new="app.setAppUserModelId(process.env.ZETTLR_PORTABLE_MODE === '1' ? 'com.zettlr.portable.community' : 'com.zettlr.app')"
out=out.replace(old,new,1)
assert out.index("app.setPath('userData', dataDir)") < out.index('app.requestSingleInstanceLock()')
assert out.count('app.setPath(\'userData\', dataDir)')==1
assert out.count('com.zettlr.portable.community')==1
# Fail closed on drifting upstream: ensure no further modifications from unrecognized variant.
path.write_text(out,encoding='utf-8',newline='\n')
print('Source adapted; userData/logs and portable Documents before first-instance lock; distinct portable AUMID.')
