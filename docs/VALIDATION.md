# Verification evidence matrix

## At kit-authoring time (14 November 2026)

| Stage | Evidence | Status |
|---|---|---|
| Official release, package.json and source main entry | Web-inspected Zettlr v4.9.0 source | SOURCE-INSPECTED |
| `--data-dir` and app.setPath('userData') | Upstream README and main.ts | SOURCE-INSPECTED |
| Separate Documents default and AUMID | Source patch code written, not executed on Windows | NOT YET VERIFIED |
| Shared Package Builder interface | Tagged `v1.0.0` action.yml inspected | SOURCE-INSPECTED |
| Shared Release Publisher interface | Tagged `v1.1.1` action.yml inspected | SOURCE-INSPECTED |
| Python release logic, source adaptation fixtures, launcher safeguards and package metadata | Six local unit tests and Python syntax checks passed | STATIC-VALIDATED only |
| MSVC launcher compilation | Requires Windows runner | NOT YET VERIFIED |
| Actual source-built Zettlr | Requires Windows runner and dependencies | NOT YET VERIFIED |
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

## b1r1 GitHub Windows run and b1r2 repair (14 November 2026)

- **WINDOWS-COMPILED (b1r1):** GitHub Actions logs confirm Zettlr 4.10.0 source build completed with `yarn package:win-x64`, after a successful startup source patch and Pandoc preparation.
- **FAILED/BLOCKED (b1r1):** Launcher build did not reach MSVC. The inline `vswhere -latest ... | Select-Object -First 1` query triggered `VS C++ toolchain missing` on `windows-2022`. A compiler invocation was not recorded.
- **STATIC-VALIDATED (b1r2):** Added `scripts/build_launcher.ps1`, using an all-installation `vswhere` query, a path fallback for runner layouts, existence checks for `VsDevCmd.bat` and `Hostx64/x64/cl.exe`, immediate capture of native exit codes and a stand-alone self-test. Python fixture checks inspect this regression path.
- **NOT YET VERIFIED (b1r2):** The revised MSVC launcher compilation and PortableApps ZIP/installer/publisher still require a fresh Windows CI run.
