#!/usr/bin/env python3
"""v0.4.1 migration preparation and explicit new identity.

Old: com.0xkuj.iparanger
New: com.sentechtipsvn.iparanger
Keep executable path, IPA/document/cache path, application-owned settings plist,
and ipatool auth/keychain passphrase unchanged. Nothing deletes user files.
The new Debian package conflicts with and replaces the old package: an apt-based
installer must resolve that transaction; raw dpkg -i may require removing old package.
"""
from pathlib import Path
import plistlib
import sys
root=Path(sys.argv[1])
old="com.0xkuj.iparanger"
new="com.sentechtipsvn.iparanger"
control=root/"layout/DEBIAN/control"
t=control.read_text("utf-8")
assert t.count("Package: "+old)==1
assert "Replaces:" not in t and "Conflicts:" not in t
t=t.replace("Package: "+old,"Package: "+new,1)
t=t.replace("Maintainer: 0xkuj","Maintainer: Sentechtipsvn",1)
t=t.replace("Author: 0xkuj","Author: 0xkuj; Sentechtipsvn",1)
t += "Replaces: "+old+"\nBreaks: "+old+"\nConflicts: "+old+"\n"
control.write_text(t,"utf-8")

plist=root/"Resources/Info.plist"
payload=plistlib.loads(plist.read_bytes())
assert payload["CFBundleIdentifier"]==old
payload["CFBundleIdentifier"]=new
payload["CFBundleDisplayName"]="IPA Ranger VN"
payload["CFBundleShortVersionString"]="0.4.1"
payload["CFBundleVersion"]="41"
payload["IPARVNPackageVersion"]="2.8.2+vn0.4.1"
plist.write_bytes(plistlib.dumps(payload,fmt=plistlib.FMT_XML,sort_keys=False))

# Language preference: best-effort import from former default domain, without
# altering Apple ID credentials, ipatool keychain, or on-disk downloaded IPA files.
lang=root/"Utils/IPARLanguageManager.m"
s=lang.read_text("utf-8")
oldcode='''    if ([stored isEqualToString:@"en"] || [stored isEqualToString:@"vi"]) return stored;
    // Preserve Vietnamese as the default on upgrade from earlier IPARanger VN.'''
newcode='''    if ([stored isEqualToString:@"en"] || [stored isEqualToString:@"vi"]) return stored;
    CFPropertyListRef legacy=CFPreferencesCopyAppValue(CFSTR("Sentechtips.IPARanger.Language"),
                                                        CFSTR("com.0xkuj.iparanger"));
    if (legacy) {
        id former=CFBridgingRelease(legacy);
        if ([former isKindOfClass:NSString.class] &&
           ([former isEqualToString:@"vi"] || [former isEqualToString:@"en"])) {
            [[NSUserDefaults standardUserDefaults] setObject:former forKey:kIPARLanguagePreference];
            return former;
        }
    }
    // Preserve Vietnamese as the default on upgrade from earlier IPARanger VN.'''
assert s.count(oldcode)==1
lang.write_text(s.replace(oldcode,newcode,1),"utf-8")
# A common data path deliberately remains stable across package identity changes.
constants=(root/"Extensions/IPARConstants.h").read_text("utf-8")
for key in ('@"/var/jb/Library/IPARanger/"',
            '@"/var/jb/User/Library/Preferences/com.0xkuj.iparangersettings.plist"',
            '--keychain-passphrase IPARanger'):
    assert key in constants, f"Shared data/auth contract changed: {key}"
assert new not in constants, "Do not rename shared data directories blindly"
postinst=(root/"layout/DEBIAN/postinst").read_text("utf-8")
assert 'FILES_DIR="/var/jb/Library/IPARanger/"' in postinst
assert "rm -rf" not in postinst
print("v0.4.1 identity transition: new bundle/package ID, original data paths retained.")
