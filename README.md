# Zettlr PortableApps Community Builder

This independent, open-source Windows build kit compiles **Zettlr** from an official stable release tag, applies narrowly scoped PortableApps adaptations, compiles a real C++ Windows launcher, validates a ready-to-extract ZIP, creates a separate PortableApps-style installer, and publishes both files to **this builder repository's** GitHub Releases.

This is **not an official Zettlr or PortableApps.com distribution**, certification, endorsement or signature. Zettlr is authored by Hendrik Erz and contributors. The community launcher icon is original and distinct from Zettlr's trademarked icon.

## What it builds

| Output | Details |
|---|---|
| `ZettlrPortable_...zip` | Full portable Windows x64 folder, `ZettlrPortable.exe`, app binaries, bundled Pandoc, metadata and Data folders |
| `*.paf.exe` | PortableApps-style custom-NSIS installer made only by `vhick/Portable-Package-Builder@v1.0.0` |
| Release | Both files published only by `vhick/portable-release-publisher@v1.1.1` after checksum and structure validation |

The packaged application is compiled on Windows from the resolved **official Zettlr source tag** with Yarn's locked dependencies. The builder does not download or repackage the ordinary Zettlr Windows installer. The ZIP can be used without the .paf.exe.

## Running a build

1. Place this repository's files into a GitHub repository you control, preserving `.github/workflows/build-portable.yml`.
2. In GitHub **Actions**, select **Build and publish Zettlr PortableApps** and choose **Run workflow**.
3. Leave *upstream_version* blank for the latest published stable release, or specify a full stable version, e.g. `4.10.0`.
4. For a **public** builder repository, first obtain the appropriate rights to redistribute the Zettlr-branded application and confirm them with the checkbox. The checkbox is a user attestation, not legal verification. In private repositories you may build without it.
5. After the job passes, download the `.zip` and `.paf.exe` from **Releases** and verify their SHA-256 checksums from the Actions log.

The builder source repository can be public by default, but public GitHub Releases containing modified Zettlr-branded binaries are separately subject to trademark and redistribution rights. The default is manual dispatch, without scheduled jobs or paid runners. A stable source is chosen numerically (not by release date or string sorting). The exact upstream commit, SHA-256 of its `yarn.lock`, builder commit, and package revision determine the release identity. An identical release tag is skipped.

## Portable data handling

Run **`ZettlrPortable.exe` at the portable folder root**. It starts `App/Zettlr/Zettlr.exe` with Zettlr's documented `--data-dir`, Chromium's `--user-data-dir`, and a private, application-only mode flag. Zettlr's own source is adapted to apply its data directory before requesting a single-instance lock. A separate portable Windows notification identity is set, and the Documents path is set to `Data/Profile/PortableDocuments` so Zettlr's first-run tutorial cannot pollute the user's Documents folder.

Settings, logs, caches and sessions are expected under `Data/Profile/`. First-run tutorial and documents resolved through Electron's Documents API go under `Data/Profile/PortableDocuments/`. Markdown workspaces in other locations remain where the user explicitly saved them. The launcher does not create system-wide shell integrations or redirect global APPDATA or TEMP.

See [portable usage and upgrade notes](docs/PORTABLE-USAGE.md), [source audit and limitations](docs/PORTABILITY-AUDIT.md), [validation matrix](docs/VALIDATION.md), and [security/redistribution](docs/SECURITY-AND-LICENSES.md).

## Supported environment

GitHub-hosted **Windows 2022 x64**, Visual Studio C++ tools, Python 3.12, Node.js 22 with Corepack/Yarn as specified by Zettlr. No local development tools are needed to run the GitHub Actions workflow. GUI interactivity, Explorer notification activation and actual installer upgrade are **not** proven by the hosted headless runner; those require real Windows acceptance tests.

## Source code and license

- Upstream: https://github.com/Zettlr/Zettlr (GPL-3.0)
- Zettlr's official portable guide: https://docs.zettlr.com/en/guides/portable.html
- Original launcher implementation: `launcher/ZettlrPortable.cpp`
- Auditable main-process patch: `scripts/patch_source.py`
- Shared installer: https://github.com/vhick/Portable-Package-Builder/tree/v1.0.0
- Shared publisher: https://github.com/vhick/portable-release-publisher/tree/v1.1.1

Zettlr's **name, logos and corporate identity are subject to separate restrictions**. See https://www.zettlr.com/press and secure permission before public distribution. This repository supplies generic launcher artwork, but the separately copyrighted upstream Zettlr executable is built from source using its original branding. Upstream license and source availability are retained within portable `Other/Source`.

## Security and limitations

- No registry-wide sweeps, file-association installation, shell extension registration, global AppData changes, or silent uninstall of host files.
- TraceGuard only considers one explicitly documented legacy leak: an **empty**, newly created `%APPDATA%\Zettlr\Dictionaries` directory. It never removes any existing or non-empty folder and saves an empty recovered counterpart first.
- Windows Jump Lists/notification caches or external editors, export tools and reference managers can create normal host activity. They are not captured.
- Upstream in-app **installer updates should not be used** for this portable package. Download a new builder-produced archive and preserve Data. The upstream update-checking capability remains enabled rather than circumventing Zettlr's redistribution conditions.
- User data may contain machine-bound secrets or absolute workspace links. Moving drives or PCs is not guaranteed to repair those references.
- A successful Actions run proves source compilation and static package integrity, **not** interactive portability or official distribution approval.

## Contributing

Changes to the release discovery, source patch or shared action baselines must be reviewed against the actual upstream code and tagged action interfaces. Pull requests should include verification evidence, not claims of completed GUI tests without a Windows session.

## Launcher build diagnostics (b1r3)

The Windows launcher uses `scripts/build_launcher.ps1` to discover installed Visual Studio C++ tools with `vswhere.exe` and standard installation locations. After validating the x64 compiler, it initializes **Microsoft Developer PowerShell** using `Launch-VsDevShell.ps1` and separately invokes the Windows resource compiler and C++ compiler using .NET's structured argument passing. No nested `cmd.exe` quoting or unverified temporary batch command is used. This corrects a command-quoting failure in b1r2 that occurred *after* Visual Studio Enterprise 2022 was found, while retaining the working source build and source-based profile isolation.

The b1r2 run proved Zettlr's upstream Windows source compilation and Visual Studio discovery, but the new b1r3 launcher compilation and real PortableApps packages still require GitHub-hosted Windows validation. See `docs/VALIDATION.md` for precise evidence stages.
