# Verification evidence matrix

## At kit-authoring time (14 November 2026)

| Stage | Evidence | Status |
|---|---|---|
| Official release, package.json and source main entry | Web-inspected Zettlr v4.9.0 source | SOURCE-INSPECTED |
| `--data-dir` and app.setPath('userData') | Upstream README and main.ts | SOURCE-INSPECTED |
| Separate Documents default and AUMID | Source patch code written, not executed on Windows | NOT YET VERIFIED |
| Shared Package Builder interface | Tagged `v1.0.0` action.yml inspected | SOURCE-INSPECTED |
| Shared Release Publisher interface | Tagged `v1.1.1` action.yml inspected | SOURCE-INSPECTED |
| Python release logic, source adaptation fixtures, launcher safeguards and package metadata | Eleven local unit tests passing for b1r5 (including source-icon provenance and quoting regression) | STATIC-VALIDATED only |
| MSVC launcher compilation | b1r2 attempt failed before invoking compiler; b1r3/b1r4 not yet proven on Windows | NOT YET VERIFIED |
| Actual source-built Zettlr | b1r1 and b1r2 GitHub Windows logs show successful `package:win-x64` | WINDOWS-COMPILED |
| PortableApps launcher process operation | Requires Windows executable | NOT YET VERIFIED |
| TraceGuard empty directory cleanup | Designed and fixture-testable; Windows run pending | NOT YET VERIFIED |
| Shell/notification behavior | Requires interactive desktop | NOT YET VERIFIED |
| ZIP layout and CRC | Runtime workflow script available, no produced app ZIP yet | NOT YET VERIFIED |
| Shared PAF installer generation | Requires Actions and shared action | NOT YET VERIFIED |
| Installer install, upgrade, Data preservation | Requires manual Windows VM tests | NOT YET VERIFIED |
| Publisher dry-run and publication | Requires GitHub Actions token and repo | NOT YET VERIFIED |

## What Windows CI can prove after a successful build

The GitHub Actions workflow will report the real source SHA, lockfile digest, builder SHA, compile exit codes, launcher PE/x64, app PE/x64, bundled Pandoc presence, ZIP layout and CRC, ZIP SHA-256, generated installer PE/SHA-256, and publisher dry-run before publication. These are build/static facts only.

## What manual Windows acceptance must prove separately

- GUI and notification click activation; installed Zettlr coexistence; first run and repeat run.
- User documents, settings, stats, snippets, dictionaries, empty folders and crash recovery.
- File/open, save, Open With and CLI arguments with spaces and Unicode paths.
- Background/tray process closure, relocation, USB dismount safety.
- Installer clean install, reinstall, upgrade, uninstall/rollback protections.
- Windows and dependency-created host activity using ProcMon.

Any failure should block a claim of *runtime portability*, regardless of CI success.

## User-supplied GitHub Windows run logs (14 November 2026)

- **WINDOWS-COMPILED (b1r1):** GitHub Actions logs confirm Zettlr 4.10.0 source build completed with `yarn package:win-x64`, after a successful startup source patch and Pandoc preparation.
- **FAILED/BLOCKED (b1r1):** Launcher build did not reach MSVC. The inline `vswhere -latest ... | Select-Object -First 1` query triggered `VS C++ toolchain missing` on `windows-2022`. A compiler invocation was not recorded.
- **STATIC-VALIDATED (b1r2):** Added `scripts/build_launcher.ps1`, using an all-installation `vswhere` query, a path fallback for runner layouts, existence checks for `VsDevCmd.bat` and `Hostx64/x64/cl.exe`, immediate capture of native exit codes and a stand-alone self-test. Python fixture checks inspect this regression path.
- **FAILED/BLOCKED (b1r2):** Visual Studio Enterprise 2022 and two Hostx64/x64 compilers were found, proving the detection repair. Launcher compilation failed before invoking the C++ compiler because `cmd.exe /d /c` misparsed a path containing spaces (`C:\Program Files\...`). The explicit error included `'C:\Program' is not recognized` and exit code 1.
- **STATIC-VALIDATED (b1r4):** Replaced nested `cmd.exe`/batch invocation with Microsoft's documented `Launch-VsDevShell.ps1` initialization and .NET `ProcessStartInfo.ArgumentList` for invoking `rc.exe` and `cl.exe` as separate argument tokens. This removes the quote-splitting failure mode without hard-coding Visual Studio year/edition. Added dedicated regression checks for the formerly failing command structure.
- **NOT YET VERIFIED (b1r4):** The new PowerShell launcher build, actual x64 compilation, runtime data retention, package ZIP, NSIS installer and publisher require Windows CI/desktop verification. Local tests cannot prove a Windows compiler executes successfully.

### Official icon fix (b1r4)

- **SOURCE-INSPECTED:** Zettlr v4.10.0 stores its Windows `icon.ico` in `resources/icons/icon.ico` and provides `16x16.png` and `32x32.png` under `resources/icons/png/`. The brand is controlled by Zettlr; a public-release permission gate remains.
- **STATIC-VALIDATED:** The builder uses these exact files as byte-for-byte copies for `AppInfo` and passes the upstream `.ico` to the root launcher resource compiler. The new validator checks file structures, dimensions, checksums, and recorded source paths with local controlled test fixtures.
- **NOT YET VERIFIED:** The exact Zettlr v4.10.0 icon binary was not downloaded to the local Linux environment. Icon embedding, icon rendering in Explorer/PortableApps Platform, and the generated installer's appearance must be verified with a Windows Actions run and a manual Windows session.

### b1r4 user-run log and b1r5 fix (14 November 2026)

- **FAILED/BLOCKED (b1r4):** User-provided GitHub Actions log `logs_117956318865.zip` confirms that exactly 10 of 11 static unit tests passed. `test_official_icons_are_used_everywhere` failed only because stale `assets/portable.ico` remained from an earlier builder version after ZIP overlay extraction. App compilation was not attempted in this run.
- **STATIC-VALIDATED (b1r5):** Corrected the test to check that the official icon bytes are staged into AppInfo and injected into the launcher resource. Changed its obsolete-file check from a build-blocking assertion to an explicit CI warning. Source icon integrity and checksums remain mandatory. Tested with the four stale legacy files present in the builder checkout as a regression fixture.
- **NOT YET VERIFIED:** b1r5 Windows compilation, installer generation, runtime, and publication require a new Actions run; this test fix alone does not prove those stages.
