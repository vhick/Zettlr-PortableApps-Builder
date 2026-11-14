# Using and updating Zettlr Portable

This independently packaged Zettlr is a **community build**, not an official PortableApps.com application.

1. Extract the ZIP to a writable folder, such as `D:\PortableApps\ZettlrPortable`. Or use the separately produced `.paf.exe` installer **after validating its provenance**.
2. Start `ZettlrPortable.exe` in that folder. Do **not** start `App\Zettlr\Zettlr.exe` directly: it would bypass the portable launcher.
3. After first launch, configuration, logs, caches, session state and dictionaries should be under `Data\Profile`. Zettlr's built-in tutorial, when resolved using Electron's Documents path, should be under `Data\Profile\PortableDocuments`.
4. Write or open your own `.md` documents from folders you choose. Documents that you explicitly save elsewhere are not automatically copied into the portable folder. Back them up separately.
5. If the app is minimized to the tray, use Zettlr's **Quit** or **Exit** command before removing your USB drive. Closing a window may not stop Zettlr.
6. To upgrade, **exit Zettlr completely**. Back up the entire portable directory, including every empty directory. Copy the new ZIP's binaries and `App` into the existing package while **preserving the existing Data folder**. A safer manual approach is extract the new package to an empty folder, exit old app, then copy the old Data folder into the new folder; verify before deleting the old copy.
7. For rollback, stop the app, restore the prior known-good `App` and launcher, and restore the matching `Data` backup. Newer data schema changes may make an earlier Zettlr version incompatible.
8. If `Data\TraceGuard\audit.log` exists, inspect it. The only recovered host entry the launcher handles is a newly created **empty** `%APPDATA%\Zettlr\Dictionaries`, under `Data\TraceGuard\Recovered\Roaming\Zettlr\Dictionaries`.

## Avoid these unsafe shortcuts

- Do not execute Zettlr's ordinary in-app Windows installer update as if it were a portable update.
- Do not delete installed Zettlr's `%APPDATA%\Zettlr` profile or Windows registrations.
- Do not merge a normal installed profile into `Data\Profile` without backups and conscious testing.
- Do not open two portable copies from different drives with the same application profile at once.
- Do not turn on automatic Windows startup or file associations unless you explicitly want a permanent host integration. This builder never performs these actions automatically.

## Manual Windows acceptance checklist

On a real Windows 10/11 desktop and a non-admin account, test a fresh ZIP in a path with spaces and non-ASCII characters. Test creating a Markdown workspace, preferences, writing statistics, custom dictionary, snippets, searches, opening an existing file by passing its path to the launcher, Pandoc import/export, restart, Quit vs tray, first-run tutorial, and relocations. Repeat with installed Zettlr already running. Record a ProcMon before/after trace for user profile, LocalAppData, ProgramData, Documents, Desktop, Start Menu, and registry. Check Windows toast notification display and click activation. Test the separate installer with an existing Data folder and confirmed rollback backup; CI does not simulate GUI installs.

If notification click-to-open fails, retain the app's notifications and report the limitation. Do not insert broad registry/shortcut deletion rules. All such tests are **NOT YET VERIFIED** until explicitly carried out.
