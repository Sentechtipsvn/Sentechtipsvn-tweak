#!/usr/bin/env python3
"""IPARanger VN v0.4.1.1 SAFE MODE RECOVERY build.

This is deliberately an in-place update of the previously verified
v0.4.0 package. DO NOT change the Package ID OR CFBundleIdentifier while
investigating the v0.4.1 SpringBoard Safe Mode report.
No Conflicts/Breaks/Replaces. The previously tested app path and shared IPA
storage remain unchanged. No manual deletion, respring, or jbinjection changes.

The new com.sentechtipsvn.iparanger identity migration is postponed until
we can verify a distinct payload path and Sileo package transaction.
"""
from pathlib import Path
import plistlib,sys
root=Path(sys.argv[1])
old="com.0xkuj.iparanger"
new="com.sentechtipsvn.iparanger"
control=root/"layout/DEBIAN/control"
t=control.read_text("utf-8")
assert t.count(f"Package: {old}")==1, t
for flag in ("Replaces:","Conflicts:","Breaks:"):
    assert flag not in t, f"Unsafe package transition: {flag}"
assert new not in t, "Unexpected new package identifier"
t=t.replace("Maintainer: 0xkuj","Maintainer: Sentechtipsvn",1)
t=t.replace("Author: 0xkuj","Author: 0xkuj; Sentechtipsvn",1)
control.write_text(t,"utf-8")

plist=root/"Resources/Info.plist"
data=plistlib.loads(plist.read_bytes())
assert data.get("CFBundleIdentifier")==old, "Unexpected identity change"
assert data.get("CFBundleExecutable")=="IPARanger"
data["CFBundleDisplayName"]="IPA Ranger VN"
data["CFBundleShortVersionString"]="0.4.1"
data["CFBundleVersion"]="411"
data["IPARVNPackageVersion"]="2.8.2+vn0.4.1.1"
plist.write_bytes(plistlib.dumps(data,fmt=plistlib.FMT_XML,sort_keys=False))

constants=(root/"Extensions/IPARConstants.h").read_text("utf-8")
assert '@"/var/jb/Library/IPARanger/"' in constants
assert '@"/var/jb/User/Library/Preferences/com.0xkuj.iparangersettings.plist"' in constants
assert '--keychain-passphrase IPARanger' in constants
assert "@\"/var/jb/Applications/IPARanger.app/" in constants
postinst=(root/"layout/DEBIAN/postinst").read_text("utf-8")
assert '/var/jb/Applications/IPARanger.app/ipatool' in postinst
assert "rm -rf" not in postinst
assert "uicache" not in postinst.lower(), "Postinstall must not force icon cache operations"
assert "sbreload" not in postinst.lower(), "Postinstall must not restart SpringBoard"
print("SAFE recovery: original package/bundle ID, original app path, original data/auth and unchanged install script")
