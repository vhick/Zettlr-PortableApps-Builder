# Security, licensing, provenance and publication

Zettlr's source code is GPL-3.0, but Zettlr's registered trademark and corporate identity are separately protected. The bundled app will still display Zettlr's original application name/icon. The launcher and PortableApps metadata use the unmodified official icon files checked out from Zettlr source at the exact selected release; the kit does not contain branded icon binaries. **Get suitable permission before publicly redistributing Zettlr-branded binaries.** The Actions workflow blocks public publication until a user explicitly attests rights; a checkbox is not a substitute for legal permission.

The kit is independent and unaffiliated with Zettlr, PortableApps.com, and the shared action authors. Its source is GPL-3.0-or-later (files under `launcher/` and `scripts/`), with upstream attribution in each generated package. Zettlr upstream icons are separately protected and not licensed as generic reusable art by this kit. Full corresponding source of Zettlr can be retrieved at the exact upstream commit recorded in `Other/Source`, with our patch source alongside it. Check third-party licenses within upstream modules before public release.

Official upstream build flags `BUNDLE_PANDOC=0` and `ZETTLR_DISABLE_UPDATE_CHECK` are **not used**. Zettlr's normal update notification still exists, but installing the upstream regular NSIS update inside a portable package is unsafe. Apply packaged updates manually or through a separately verified workflow. This is a documented functionality conflict requiring real Windows testing.

The build excludes unofficial mirrors and no hidden binary blobs are committed. The packaged Pandoc comes directly from GitHub releases; the requested specific release and asset digest are read from GitHub's authenticated API and checked against downloaded bytes. The exact upstream tag and `yarn.lock` identify the source dependency set. Yarn installation requires TLS and trustworthy registries; an immutable lockfile is not a security attestation.

The shared action tags `vhick/Portable-Package-Builder@v1.0.0` and `vhick/portable-release-publisher@v1.1.1` were inspected at their tagged `action.yml` interfaces. They remain tag references per the user's pinned baseline. Before operating a security-critical production build, independently pin trusted immutable commit SHAs and re-inspect code at those SHAs.

Portable folders must not be protected Windows directories or symlink/junction paths. The launcher does not seek elevation, create Windows services, alter system default apps, or remove preexisting host data.

## Official icon provenance

`prepare_icons.py` validates `resources/icons/icon.ico`, `resources/icons/png/16x16.png` and `resources/icons/png/32x32.png` in the source checkout, copies bytes unchanged, and records their source paths and SHA-256 values in the generated package. This does not imply trademark permission or official endorsement. The Windows launcher icon resource is compiled using the same source `icon.ico`.
