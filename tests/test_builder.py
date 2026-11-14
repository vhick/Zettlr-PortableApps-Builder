"""Cross-platform fixture tests for fail-closed release parsing and source patch."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import resolve_release

class BuildTests(unittest.TestCase):
    def test_semver_not_lexicographic(self):
        def rel(tag):return {'tag_name':tag,'draft':False,'prerelease':False,'published_at':'2026-01-01'}
        chosen=resolve_release.select([rel('v4.9.0'),rel('v4.10.0'),rel('v4.8.0')],'')
        self.assertEqual(chosen['tag_name'],'v4.10.0')
    def test_no_prereleases_or_branch(self):
        items=[{'tag_name':'v4.11.0-beta','draft':False,'prerelease':False,'published_at':'2026-01-01'},
        {'tag_name':'develop','draft':False,'prerelease':False,'published_at':'2026-01-01'}]
        with self.assertRaises(RuntimeError):resolve_release.select(items,'')
    def test_fail_closed_source_patch_and_portable_order(self):
        body='''import { app } from 'electron'\nimport path from 'path'\nhandleExitArguments()\nif (!app.requestSingleInstanceLock()) {}\nif (process.platform === 'win32') {\n  app.setAppUserModelId('com.zettlr.app')\n}\n// Setting custom data dir for user configuration files.\nlet dataDir = getCLIArgument(DATA_DIR)\nif (typeof dataDir === 'string') {\n  app.setPath('userData', dataDir)\n  app.setAppLogsPath(path.join(dataDir, 'logs'))\n}\n// On systems with virtual GPUs (i.e. VMs), it might be necessary to disable\n'''
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'main.ts';p.write_text(body,encoding='utf-8')
            script=Path(__file__).resolve().parents[1]/'scripts'/'patch_source.py'
            subprocess.run([sys.executable,str(script),str(p)],check=True,capture_output=True)
            modified=p.read_text()
            self.assertLess(modified.index("app.setPath('userData'"),modified.index('app.requestSingleInstanceLock'))
            self.assertIn("app.setPath('documents', portableDocs)",modified)
            self.assertIn('com.zettlr.portable.community',modified)
            result=subprocess.run([sys.executable,str(script),str(p)],capture_output=True)
            self.assertNotEqual(result.returncode,0,'Patching twice must fail closed')
    def test_launcher_self_test_before_assembly(self):
        source=(Path(__file__).resolve().parents[1]/'launcher'/'ZettlrPortable.cpp').read_text(encoding='utf-8')
        self.assertLess(source.index('wcscmp(argv[1],L"--self-test")'), source.index('!fs::exists(target)'))
    def test_portableapps_format_identity(self):
        stage=(Path(__file__).resolve().parents[1]/'scripts'/'stage.py').read_text(encoding='utf-8')
        self.assertIn('Version=3.9',stage)
        self.assertIn('AppID=ZettlrPortable-CommunityBuild',stage)
        self.assertIn("package_version='.'.join(v.groups())+'.1'",stage)
    def test_launcher_source_host_protection(self):
        source=(Path(__file__).resolve().parents[1]/'launcher'/'ZettlrPortable.cpp').read_text(encoding='utf-8')
        self.assertIn('!existedDict',source)
        self.assertIn('isEmptyRealDirectory(hostDict)',source)
        self.assertIn('!anyZettlrActive()',source)
        self.assertIn('ZETTLR_PORTABLE_MODE',source)
        self.assertIn('if(!SetEnvironmentVariableW(',source)
        self.assertNotIn('RegDeleteTree',source)
if __name__=='__main__':unittest.main(verbosity=2)
