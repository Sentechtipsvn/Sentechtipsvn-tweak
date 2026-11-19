# IPARanger VN v0.4.1 — Migration test (rootless)

## What's new
- Redesigned compact About page: overview, user guide, terms, **complete original MIT license**, and credits/version at the bottom.
- New **Debian Package ID** and **CFBundleIdentifier**: `com.sentechtipsvn.iparanger`.
- Exact app/version automatically displayed from bundled metadata.
- Vietnamese and English localization retained.
- IPA search/download, FairPlay checks, hash, Filza, Files export and install backend unchanged.

## Data preserved in application logic
- Shared rootless IPA folder: `/var/jb/Library/IPARanger/`.
- Existing settings file: `/var/jb/User/Library/Preferences/com.0xkuj.iparangersettings.plist`.
- Existing ipatool command passphrase: `IPARanger`.
- Existing app binary's install location: `/var/jb/Applications/IPARanger.app`.
- Language preference attempts one-time migration from the old app preference domain.

The package does **not delete** downloaded IPA or settings. However, **changing the bundle identifier is an iOS app identity change**. Login state and container-based preferences may need to be set up again. Do not promise seamless migration before on-device testing.

## Test installation — iPhone 7 Plus, iOS 15.8.8, Dopamine
1. Back up any critical IPA files to Files/iCloud via the existing v0.4.0 app. Note the selected language and Apple ID Store region.
2. Prefer an **APT-capable installer** (e.g. Sileo) because the new Debian package `Conflicts` and `Replaces` the previous package `com.0xkuj.iparanger`.
3. A raw `dpkg -i` may refuse to install while the old package is installed. If needed, carefully remove **only the old package** first. Do not erase `/var/jb/Library/IPARanger/` or the shared settings file.
4. Install the v0.4.1 DEB, open IPARanger VN, verify stored IPAs and Storefront region. If Apple authentication is not restored automatically, sign in again using your own account.
5. Verify About: three subpages, full original MIT, footer at the end, dynamic version, Vietnamese/English.
6. Verify downloads/search, copy Bundle ID, IPA integrity and Filza/Files export.
7. Report any data/locale migration issue before public Sileo release.

## Release safety
- This is a **pre-release test**. Keep the previously verified v0.4.0 DEB available.
- Rollback across a Bundle ID change may require removing the new package and reinstalling the old package. Back up files first.
- Do not distribute DRM-protected IPA content without rights.
