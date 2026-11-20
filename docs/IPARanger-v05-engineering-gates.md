# IPARanger VN — next-stage engineering gates (v0.4.2 → v0.5)

## Fixed baseline
- Known-good reference from iPhone 7 Plus (iOS 15.8.8 / Dopamine): **v0.4.1.1 Recovery**; user confirmed app runs smoothly after the reverted ID change.
- All test builds retain Debian Package and iOS Bundle ID `com.0xkuj.iparanger`.
- Do not change `/var/jb/Library/IPARanger/`, existing language/settings storage or `ipatool` login and region resolution.
- A future public release may use `com.sentechtipsvn.iparanger` only after a separately reviewed identity migration and a verified rollback route.
- No public Sileo repo update until device test approval.

## v0.4.2 test focus
1. Ordinary App Store IPA: CRC-valid ZIP, `Payload/App.app` detected and existing install flow unaffected.
2. Repacked ZIP with `Folder/Payload/App.app`: show **Payload nested**; when trying to install through the app, show remediation rather than invoking appinst.
3. ZIP without Payload: show **Payload missing**.
4. ZIP with Payload but corrupted Info.plist: show invalid metadata.
5. ZIP with bad CRC: show invalid ZIP; do not claim FairPlay decrypted or TrollStore-compatible.
6. Test multilingual alerts, navigation, copy Bundle ID, app download, install, File export and no unexpected Respring.
7. Check SpringBoard after package installation, app startup and uninstall; if Safe Mode occurs, capture SpringBoard crash log before changing package identifiers.

## v0.5 research — keep separate from stable features

### Compatibility analysis
- Continue reporting ZIP, SHA-256, minimum iOS and Mach-O encryption state without modifying downloaded IPA.
- Lack of FairPlay encryption is **not** proof that TrollStore can install a given app.
- For an app installed and obtained legitimately, investigate whether an on-device extraction tool can provide a compatible archive. This is exploratory, not a promised universal decryption or signature bypass. Test extensions and embedded frameworks and respect licensing.
- Only implement an extraction workflow after a controlled lab test on a properly authorized sample and after documenting data preservation / rollback.

### Multiple Apple IDs
- Design a clearly user-initiated account switch; never infer storefront from VPN country.
- Never persist plain-text passwords or tokens; keep authentication entrusted to the existing backend / secure storage.
- Isolate cached storefront and catalog results per selected account if multiple sessions are supported. Maintain existing single-account path as the fallback.

### Download queue and resume
- Confirm whether the current `ipatool` download backend can provide resumable partial downloads and reliable cancellation.
- No synthetic 99% progress, retry loops or fake resume claims. Queue/resume remains research-only until supported.

### New Sentechtipsvn identity — release gate
- Investigate package manager removal order, shared application path collisions and persistent preference/keychain migration.
- Make a dedicated migration build with different install paths if necessary, verified Debian scripts and rollback tests.
- Do **not** combine this identity migration with feature refactors; only attempt after v0.4.x test acceptance.

## Release acceptance checklist
- Original iOS app and Debian IDs remain constant in test DEB.
- Native Objective-C code compiles with Theos rootless SDK for arm64.
- `ipatool` backend checksum matches verified binary.
- UI copy and dialogs work in Vietnamese and English.
- No deletion of old IPA archives or account files.
- Device tests documented for install, no Safe Mode, search, download, audit and IPA export.
