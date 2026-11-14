# Zettlr Windows portability audit — SOURCE-INSPECTED at v4.9.0

All paths and behaviors below are separated by **source-inspected**, **upstream-documented**, or **inferred/unverified**. No Windows interactive execution was performed while authoring this kit.

| Finding | Evidence | File/registry path | Responsible component | NATIVE remedy (not built) | PORTABLEAPPS remedy | Data safety | Functionality tradeoff | Test | Limitation |
|---|---|---|---|---|---|---|---|---|---|
| Electron configuration and logs | `source/main.ts` lines 48–67, SOURCE-INSPECTED | `%APPDATA%\Zettlr` by default | Zettlr/Electron | In-process source patch | Root EXE passes `--data-dir` and `--user-data-dir`; move setPath before lock | No host profile overwrite | None expected | First-run profile comparison | Chromium children untested |
| Single-instance ownership | `source/main.ts` lines 28–39, SOURCE-INSPECTED | Electron userData lock | Zettlr/Electron | Configure before lock | Move data-dir configuration above requestSingleInstanceLock | Installed app should stay separate | Zettlr still supports one process per profile | Concurrent installed vs portable desktop test | Runtime unverified |
| Windows notifications | `source/main.ts` lines 42–46, SOURCE-INSPECTED | AUMID `com.zettlr.app` | Zettlr/Windows shell | Distinct app identity | `com.zettlr.portable.community` only for portable | Never alter installed CLSID/shortcuts | Windows click-to-open may require owned shortcut | Desktop toast and activation test | Shell registration unverified |
| Empty default dictionary | Upstream README `--data-dir` note, UPSTREAM-DOCUMENTED | `%APPDATA%\Zettlr\Dictionaries` | Electron framework | Avoid in-process | TraceGuard preserves newly created empty folder in `Data/TraceGuard` then removes only empty owned path | Never touch preexisting or nonempty data; skip cleanup if another Zettlr process exists | No useful dictionary content moved | Nonempty/empty/pre-existing fixture tests | Host write not runtime-observed |
| Tutorial may write to Documents | Zettlr FAQ & PortableApps developer discussion, UPSTREAM-DOCUMENTED | Current user's Documents | Zettlr first-run logic | Source redirect | `app.setPath('documents', Data/Profile/PortableDocuments)` when portable; pre-created by launcher | Never move user Documents | Default Documents dialogs may open portable path | First-run tutorials, default file dialogs | Actual call site not independently located, runtime unverified |
| Default storage subdirectories | `source/app/util/environment-check.ts` lines 42–49 and 124–131, SOURCE-INSPECTED | userData/dict, lang, logs, defaults, snippets, lua-filter | Zettlr | same userData | Redirect userData to `Data/Profile` before boot | Retain empty dirs | None expected | First run and ZIP inventory | Provider-level paths not exhaustively inspected |
| Bundled document converter | `forge.config.js` lines 93–115, SOURCE-INSPECTED | `resources/pandoc.exe` | Zettlr build/ Pandoc | Bundle | Pin exactly upstream-specified official Pandoc release and verify asset digest | No host writes by packaging | Full import/export available | PE and package presence; manual export | Actual export unverified |
| Windows installation associations | `electron-builder.yml` Windows NSIS/fileAssociations, SOURCE-INSPECTED | Explorer file associations and uninstall registry | Upstream Windows installer, not Zettlr runtime | None | Do NOT run upstream installer; shared standalone package builder | No automatic association registration | Explorer Open With not registered | Before/after installer snapshot | Shared installer behavior untested |
| Protocol `safe-file` | `source/app/util/custom-protocols.ts`, SOURCE-INSPECTED | Electron process-local scheme | Zettlr | None | Preserve upstream handler | No host registry cleanup | Local files remain readable | Image/file preview | No evidence of OS protocol registration |
| Tray and background | Upstream README `--launch-minimized`, UPSTREAM-DOCUMENTED | Zettlr child processes | Zettlr | Lifecycle integration | Launcher waits for source app process and checks exact app executable before bounded cleanup | Avoid deleting while app alive | Tray close delays launcher completion | Real tray Quit + relaunch | Child tracking partial, manual test needed |
| Windows Jump Lists and shell caches | INFERRED | Windows-managed shell profile caches | Windows | Not app-owned | Document as outside safe scoped recovery | Never delete shared caches | May retain usage history | Real OS trace | No verified owner-specific cleanup |
| Credentials and external services | INFERRED | OS credential store, Zotero/reference managers, selected workspaces | Dependencies/user | Preserve OS behavior | Do not globally redirect external tools | Installed app and other programs protected | Some mobility restrictions | Different Windows account | Not verified |

## Source identity and adaptation

- Stable upstream source tag: inspected **v4.9.0**; workflow independently resolves latest published stable or requested stable version at execution time.
- Build: Node 22, Corepack/Yarn 4 according to packageManager, official `yarn.lock`, `yarn package:win-x64` (Forge, Electron, Webpack). `scripts/get_pandoc.py` obtains official upstream-selected Pandoc and checks its GitHub asset SHA-256 digest.
- `scripts/patch_source.py`: fails closed when source main entry anchors or expected methods change. Only changes `source/main.ts` before build. The exact `git diff` is retained during CI.
- App-specific compiled launcher: `launcher/ZettlrPortable.cpp`.
- The public README is general; nontechnical GitHub Desktop instructions are in a separate document.

## Why no aggressive ShellGuard

There is no source evidence in the files inspected that Zettlr **at runtime** installs file associations, writes COM registrations, or creates shortcuts. Upstream *NSIS installer* declares associations; this builder does not run that installer. Its own custom NSIS installer must still be verified in a real Windows installation. Unconditionally sweeping Start Menu, HKCU or Jump Lists would endanger other installed apps. For now ShellGuard is **document-and-test only** for notifications and Windows-managed shell caches. Do not claim zero host traces.

## Latest upstream confirmed by CI (14 November 2026)

The user-provided b1r1 run selected official upstream v4.10.0 (`d6286e4be59f19bdd9a6299dcbe147e24f6c2112`). The source adaptation and Windows x64 `package:win-x64` build succeeded in both b1r1 and b1r2 logs. b1r1 then failed Visual Studio discovery; b1r2 discovered Visual Studio Enterprise and two x64 compilers, but the nested cmd.exe command split a quoted Program Files path and failed before invocation. b1r4 replaces the nested batch invocation with Developer PowerShell and structured argument passing; its Windows result is not yet verified. The older v4.9.0 source-inspection evidence remains correctly labeled above.

### Icon source and scope (b1r4)

The builder previously used a visually distinct generated portable icon, although the Zettlr application binary used upstream branding. The b1r4 builder instead consumes official `resources/icons/icon.ico` (root launcher PE resource and PortableApps appicon.ico), `resources/icons/png/16x16.png` and `resources/icons/png/32x32.png` (PortableApps menu), from the exact checked-out release. Source bytes, dimensions, SHA-256 and package provenance are checked. No icon binaries are redistributed inside the builder source kit. Zettlr branding remains restricted; independent public distribution must respect the Zettlr corporate-identity policy.

### Legacy generic icons and checkout upgrades (b1r5)

A ZIP overlay does not delete old files. The b1r4 CI log showed that old `assets/portable.ico` was still tracked, causing an overstrict test failure even though official icon preparation passed. This residual file is not a source for b1r5 packaging. Source-icon provenance checking, launcher resource injection, and AppInfo exact copy are enforced. Manual cleanup through GitHub Desktop is recommended but not a build prerequisite.
