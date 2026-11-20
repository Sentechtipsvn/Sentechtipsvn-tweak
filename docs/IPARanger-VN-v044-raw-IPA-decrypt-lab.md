# IPARanger VN · Native IPA decryption feasibility lab (v0.4.4)
Date: 2026-11-20
Status: **EXPERIMENTAL. Not integrated into the stable app.**

## Verified source-code findings
- The installed-app workflow in `donato-fiore/TrollDecrypt` uses `LSApplicationProxy`, launches a process, and reads decrypted memory. It does **not** expose a raw IPA file entrypoint and cannot process an IPA just by passing its filename.
- `lbr77/unfair`, revision `a754437649b1428e07918c0315a678ed7fc57dec`, documents a different **jailbroken iOS raw IPA** workflow: staging a temporary application-bundle directory under `/var/containers/Bundle/Application`, consuming an existing `SC_Info` license, and mapping encrypted segments through iOS FairPlay mechanisms. MIT license, copyright © 2026 Lakr233, must be retained.
- The `unfair` iOS implementation explicitly requires **EUID 0** and its jailbreak-primitives library (`/var/jb/usr/lib/libjailbreak.dylib` or `/var/jb/basebin/libjailbreak.dylib`). It is not safe to call it from an unprivileged IPARanger UI and assume success.
- No compatibility test for iPhone 7 Plus / iOS 15.8.8 / Dopamine has yet been run.

## Approved test isolation
1. **No change** to the working IPARanger v0.4.3 app or existing DEB.
2. Build a **separate rootless CLI helper package**, using the pinned MIT-licensed engine. No SpringBoard injection, no post-install respring, no root background service, no existing package ID replacement.
3. Run it manually once with an IPA legitimately downloaded using the same Apple account, an IPA that is **not installed** on the test phone.
4. Save diagnostics and output in a dedicated, non-system directory. Never overwrite the input IPA. Clean temporary state on errors.
5. Verify with IPARanger IPA audit: valid ZIP/Payload, **all** binary `cryptid == 0` including frameworks and app extensions; output does not contain sensitive `SC_Info`, SHA-256 recorded. Attempt TrollStore installation on a disposable app only. A success message from the helper alone is not sufficient.
6. **Only after that** integrate a tightly restricted, auditable root-helper interface into IPARanger under a separate beta toggle. No generic arbitrary command execution endpoint.

## Proposed in-app UI (not yet shipped)
Original Apple-ID library -> IPA Details -> More -> **Decrypt original IPA (Beta)**:
- Shows app name, version, selected version ID, region, Apple-ID ownership warning, ZIP/SC_Info and free-space preflight.
- Runs a single selected IPA through the verified native helper, not TrollDecrypt installed-app code.
- Step tracker: `PRECHECK / STAGE / AUTH / DECRYPT / VERIFY / IMPORT / DONE`.
- On any failure, show stable error ID + plain-language Vietnamese/English guidance + `Export diagnostic log` action; original file remains untouched.
- Only verified successful outputs enter the Unencrypted IPA library.
- A separate **Decrypt installed app** link may launch the existing TrollDecrypt app (no undocumented URL actions).

## Error codes
| Code | Action / explanation |
|---|---|
| RAW-001 | Not a valid IPA or damaged ZIP |
| RAW-002 | Missing or wrongly nested Payload/App |
| RAW-003 | Missing usable SC_Info/FairPlay license metadata |
| RAW-004 | Helper missing or wrong CPU/package architecture |
| RAW-005 | Root/Jailbreak permissions missing; do **not** force-install or silently elevate |
| RAW-006 | Required libjailbreak methods missing |
| RAW-007 | Insufficient temporary disk space |
| RAW-008 | Staging failed (permissions, path or collision) |
| RAW-009 | FairPlay authorization failed for this device/account |
| RAW-010 | Engine failed / timed out / unsupported binary |
| RAW-011 | Output ZIP or Payload invalid |
| RAW-012 | At least one executable/framework/extension still encrypted |
| RAW-013 | Installability unknown: code-signing or entitlements not verified |
| RAW-014 | Import failed; preserve original and include recovery path |
| RAW-015 | License/SC_Info removal check failed; do not publish output |
| RAW-016 | iOS minimum exceeds installed iOS; decryption and runtime compatibility are separate |

## Privacy and license
Do not log Apple ID email, password, tokens, SC_Info contents, keychain, device identifiers or application private data. Ensure metadata is user-visible; logs include only stage, code, generic error, SHA-256, app/version metadata and timestamp. The original source and license of `unfair` remain credited.

References:
- https://github.com/donato-fiore/TrollDecrypt/tree/main/Decryption
- https://github.com/lbr77/unfair/blob/a754437649b1428e07918c0315a678ed7fc57dec/README.txt
- https://github.com/lbr77/unfair/blob/a754437649b1428e07918c0315a678ed7fc57dec/LICENSE
