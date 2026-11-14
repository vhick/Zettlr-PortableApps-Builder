# Beginner setup with GitHub Desktop

These instructions are intentionally separate from the public project `README.md`.

1. Sign into GitHub at https://github.com. In the top-right **+** menu choose **New repository**. Name it `Zettlr-Portable-Builder` (or any available name). Choose **Public** for the builder source by default (standard GitHub Actions hosted runners are free). A public repository also makes its GitHub Releases public, so do not publish modified Zettlr-branded binaries unless you have the necessary trademark/redistribution rights. Choose **Private** when you need private releases or are handling confidential files; a private repository does not by itself grant redistribution rights. Leave **Add a README** unchecked if possible, then create the repository. Do **not** fork `Zettlr/Zettlr`.
2. On the repository's main page select **Code → Open with GitHub Desktop**. Choose a local clone folder. You do not need to run `git init` or install compilers.
3. Extract the downloaded builder kit ZIP into the newly cloned folder. Make sure hidden `.github` and its `workflows` subfolder are present at the repository root. The root should have `README.md`, `.github/`, `scripts/`, `launcher/`, `assets/`, `tests/` and `docs/`.
4. Open GitHub Desktop. You should see the new project files under **Changes**. Enter this exact example commit message:

   **Summary:** `Add Zettlr PortableApps builder kit b1r2`

   **Description:** `Fix Windows MSVC discovery after successful Zettlr source build using multi-install Visual Studio detection, validated x64 compiler paths and explicit diagnostics; update builder revision to b1r2 and retain all portable-data protections.`

   Click **Commit to main** (or your default branch), then click **Push origin**. This is the **commit summary** needed for these instructions.
5. Open your new builder repository in GitHub and choose **Actions**. If GitHub asks whether to enable workflows, enable them for this repo. Select **Build and publish Zettlr PortableApps** on the left and click **Run workflow**.
6. Leave `upstream_version` blank to build the newest published stable release. Optionally type a stable version such as `4.10.0`. If your repository is **public**, you must first obtain suitable rights to distribute Zettlr's brand and only then tick **confirm_brand_rights**. In private repos leave it unchecked.
7. Click **Run workflow**. Open the newly created run to read the steps. Green means that the code compiled and static validations passed; it does not prove that the app's GUI works on your computer. Red means a failure; open the first failed step, copy the error text and save it for troubleshooting.
8. When the workflow succeeds, open your own repository's **Releases** page. Download both the `ZettlrPortable_...zip` file and the `.paf.exe` installer. Confirm the ZIP and installer SHA-256 values against the Action logs (and matching `.sha256` records when shown in the log).
9. To use the ZIP, extract the complete `ZettlrPortable` folder to your chosen USB or computer folder and start **`ZettlrPortable.exe`**. If using the installer, select a writable PortableApps directory and test it carefully. In the PortableApps Platform, refresh the app list or restart the menu if the new item is missing.
10. Your settings and profile should be saved at **`ZettlrPortable\Data\Profile`**. Bounded recovered empty directory state, when encountered, is at **`ZettlrPortable\Data\TraceGuard\Recovered`**. Keep this entire `Data` tree intact, including empty directories, during upgrades.
11. When Zettlr releases a new stable version, revisit **Actions → Build and publish... → Run workflow**, leave version blank, and create a new package. Never delete `Data` as part of an update. Quit from the tray first, back up the old folder, extract the new ZIP, and copy your old Data into it. Avoid upstream in-app installer updates.
12. To roll back, fully exit Zettlr, restore your saved earlier program files **and their matching Data backup**, then run `ZettlrPortable.exe`. New versions may have migrated settings in a way an old version cannot read.

**If installer generation fails:** inspect the Package Builder step. A validated ZIP may be available as a fallback Action artifact for troubleshooting; do not label the installer a success. **If desktop notifications or tutorials do not work:** record a Windows desktop runtime test rather than treating successful build logs as proof.
