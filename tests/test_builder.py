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
    def test_msvc_detection_b1r2_regression(self):
        root=Path(__file__).resolve().parents[1]
        workflow=(root/'.github/workflows/build-portable.yml').read_text(encoding='utf-8')
        ps1=(root/'scripts/build_launcher.ps1').read_text(encoding='utf-8')
        self.assertIn('run: ./scripts/build_launcher.ps1',workflow)
        self.assertNotIn('Select-Object -First 1',workflow)
        self.assertIn('-all -products',ps1)
        self.assertIn('VsDevCmd.bat',ps1)
        self.assertIn('bin\\Hostx64\\x64\\cl.exe',ps1)
        self.assertIn('vswhere required-component exit code:',ps1)
        self.assertIn('Compiling ZettlrPortable.exe with initialized x64 MSVC',ps1)
        self.assertIn('--self-test',ps1)

    def test_msvc_quoting_b1r3_regression(self):
        """Reject the b1r2 nested cmd.exe invocation that split Program Files."""
        root=Path(__file__).resolve().parents[1]
        ps1=(root/'scripts/build_launcher.ps1').read_text(encoding='utf-8')
        self.assertIn('Launch-VsDevShell.ps1',ps1)
        self.assertIn('& ($selected.Shell) -Arch amd64 -HostArch amd64 -SkipAutomaticLocation',ps1)
        self.assertIn('$env:VSCMD_VER',ps1)
        self.assertIn('[System.Diagnostics.ProcessStartInfo]::new()',ps1)
        self.assertIn('$startInfo.ArgumentList.Add($arg)',ps1)
        self.assertIn('UseShellExecute = $false',ps1)
        self.assertIn("('/Fe:' + $exe)",ps1)
        self.assertNotIn('cmd.exe /d /c',ps1)
        self.assertNotIn('compile-zettlr-launcher.cmd',ps1)
        self.assertNotIn('$batch',ps1)
        self.assertIn("Write-Host 'Compiling launcher resource with rc.exe'",ps1)
        self.assertIn("& $exe --self-test",ps1)

    def test_revision_consistency_b1r4(self):
        root=Path(__file__).resolve().parents[1]
        for relative in ('scripts/identity.py','scripts/validate_package.py','scripts/stage.py','.github/workflows/build-portable.yml'):
            source=(root/relative).read_text(encoding='utf-8')
            self.assertNotIn('b1r1',source,relative)
        self.assertIn("revision=identity['package_revision']",(root/'scripts/validate_package.py').read_text(encoding='utf-8'))
        self.assertIn('package-revision: b1r4',(root/'.github/workflows/build-portable.yml').read_text(encoding='utf-8'))

    def test_official_icons_are_used_everywhere(self):
        root = Path(__file__).resolve().parents[1]
        build = (root/'scripts/build_launcher.ps1').read_text(encoding='utf-8')
        stage = (root/'scripts/stage.py').read_text(encoding='utf-8')
        wf = (root/'.github/workflows/build-portable.yml').read_text(encoding='utf-8')
        validate = (root/'scripts/validate_package.py').read_text(encoding='utf-8')
        self.assertIn('assets-build\\icon.ico', build)
        self.assertIn("root/'assets-build'/original",stage)
        self.assertIn("'ICON-PROVENANCE.json'",stage)
        self.assertIn('scripts/prepare_icons.py --upstream upstream --output assets-build',wf)
        self.assertLess(wf.index('Verify authentic Zettlr icons'), wf.index('Compile genuine C++64 PortableApps launcher'))
        self.assertIn('SOURCE-MATCHED ICONS PASSED',validate)
        self.assertFalse((root/'assets'/'portable.ico').exists(), 'No generic art remains in the kit')
        self.assertFalse((root/'scripts'/'create_assets.py').exists())

    def test_official_icon_source_validation_and_exact_copy(self):
        import struct, zlib
        from importlib import import_module
        icons = import_module('prepare_icons')
        def png(sz):
            def chunk(name, data):
                blob = name + data
                return struct.pack('>I',len(data))+blob+struct.pack('>I',zlib.crc32(blob)&0xffffffff)
            row = bytes([0]) + b'\x00\x80\x00\xff' * sz
            return (icons.PNG_SIGNATURE
                    + chunk(b'IHDR',struct.pack('>IIBBBBB',sz,sz,8,6,0,0,0))
                    + chunk(b'IDAT',zlib.compress(row * sz))
                    + chunk(b'IEND',b''))
        def ico():
            contents=[png(16),png(32)]
            directory=struct.pack('<HHH',0,1,2)
            offset=6+16*2
            for size, blob in zip((16,32),contents):
                directory += struct.pack('<BBBBHHII',size,size,0,0,1,32,len(blob),offset)
                offset += len(blob)
            return directory + b''.join(contents)
        with tempfile.TemporaryDirectory() as tmp:
            up=Path(tmp)/'upstream'; target=Path(tmp)/'assets-build'
            d=up/'resources/icons/png';d.mkdir(parents=True)
            (up/'resources/icons/icon.ico').write_bytes(ico())
            (d/'16x16.png').write_bytes(png(16))
            (d/'32x32.png').write_bytes(png(32))
            icons.prepare(up,target)
            self.assertEqual((target/'icon.ico').read_bytes(),(up/'resources/icons/icon.ico').read_bytes())
            self.assertEqual((target/'icon_16.png').read_bytes(),(d/'16x16.png').read_bytes())
            self.assertEqual((target/'icon_32.png').read_bytes(),(d/'32x32.png').read_bytes())
            info=json.loads((target/'ICON-PROVENANCE.json').read_text(encoding='utf-8'))
            self.assertEqual(info['files']['icon_32.png']['upstream_path'],'resources/icons/png/32x32.png')
            (d/'32x32.png').write_bytes(png(16))
            with self.assertRaises(RuntimeError):icons.prepare(up,target)
            (d/'32x32.png').unlink()
            with self.assertRaises(RuntimeError):icons.prepare(up,target)

    def test_launcher_source_host_protection(self):
        source=(Path(__file__).resolve().parents[1]/'launcher'/'ZettlrPortable.cpp').read_text(encoding='utf-8')
        self.assertIn('!existedDict',source)
        self.assertIn('isEmptyRealDirectory(hostDict)',source)
        self.assertIn('!anyZettlrActive()',source)
        self.assertIn('ZETTLR_PORTABLE_MODE',source)
        self.assertIn('if(!SetEnvironmentVariableW(',source)
        self.assertNotIn('RegDeleteTree',source)
if __name__=='__main__':unittest.main(verbosity=2)
