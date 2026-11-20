#!/usr/bin/env python3
"""IPARanger VN 0.4.2: IPA layout preflight without changing working download/install backend.

The v0.4 inspector conflated ZIP CRC integrity with iOS IPA layout validity.
This patch reports them separately, distinguishing nested Payload and missing
Payload, displays a precise localized diagnosis, and blocks installation only
when a completed preflight *positively* identifies malformed IPA layout.
Unknown/unfinished verification preserves prior installation behavior.

DO NOT modify package identifier, App ID, ipatool, account country, credentials,
IPA storage path, or existing FairPlay inspection. This is NOT DRM decryption.
"""
from pathlib import Path
import json,sys

root=Path(sys.argv[1])
def once(text, old, new, label):
    count=text.count(old)
    assert count == 1, f"{label}: expected single anchor, got {count}"
    return text.replace(old,new,1)

audit=root/"Utils/IPARIPAAudit.m"
s=audit.read_text("utf-8")
s=once(s,'@"zip":@"unknown",','@"zip":@"unknown",\n                                @"structure":@"unknown",',
       "audit schema")
a='''    NSString *mainPlist=nil;
    for (NSString *name in names) {
        if ([name hasPrefix:@"Payload/"] && [name hasSuffix:@".app/Info.plist"]
            && [[name componentsSeparatedByString:@"/"] count]==3) {mainPlist=name;break;}
    }
    if (!mainPlist) {
        out[@"zip"]=@"invalid";return out;
    }
    // Verify all ZIP entries' CRC; on large archives this can be expensive, so
    // always run from a background queue (caller responsibility).
    NSString *test=IPARFindTempPath();
    BOOL zipValid=IPARRunUnzip(@[@"-tqq",path],test);
    [[NSFileManager defaultManager] removeItemAtPath:test error:nil];
    out[@"zip"]=zipValid?@"valid":@"invalid";
    if (!zipValid) return out;'''
b='''    // ZIP integrity and iOS IPA layout are independent properties.
    // A ZIP may pass all CRC tests while Payload is nested in a folder,
    // which makes MobileInstallation reject it.
    NSString *test=IPARFindTempPath();
    BOOL zipValid=IPARRunUnzip(@[@"-tqq",path],test);
    [[NSFileManager defaultManager] removeItemAtPath:test error:nil];
    out[@"zip"]=zipValid?@"valid":@"invalid";
    if (!zipValid) return out;

    NSString *mainPlist=nil;
    BOOL nestedPayload=NO;
    for (NSString *name in names) {
        NSArray<NSString *> *parts=[name componentsSeparatedByString:@"/"];
        BOOL appPlist=[name hasSuffix:@".app/Info.plist"];
        if (appPlist && [name hasPrefix:@"Payload/"] && parts.count==3) {
            mainPlist=name;
            break;
        }
        if (appPlist && [name containsString:@"/Payload/"] && parts.count>=4) {
            nestedPayload=YES;
        }
    }
    if (!mainPlist) {
        out[@"structure"]=nestedPayload?@"nested":@"missing";
        return out;
    }
    out[@"structure"]=@"valid";'''
s=once(s,a,b,"split CRC validity from IPA Payload layout")
s=once(s,'''    NSDictionary *main=IPARPlistForEntry(path,mainPlist);
    if (!main) return out;''',
'''    NSDictionary *main=IPARPlistForEntry(path,mainPlist);
    if (!main) {
        out[@"structure"]=@"bad-plist";
        return out;
    }''',"verify main Info.plist")
audit.write_text(s,"utf-8")

detail=root/"Controllers/IPARIPADetailViewController.m"
s=detail.read_text("utf-8")
s=once(s,
'''return section == 0 ? 1 : section == 1 ? 4 : section == 2 ? 2 : 5;''',
'''return section == 0 ? 1 : section == 1 ? 4 : section == 2 ? 2 : 6;''',
"additional diagnostics row")
s=once(s,
'''                       IPARL(@"TrollStore installability")];''',
'''                       IPARL(@"TrollStore installability"),
                       IPARL(@"IPA Payload layout")];''',"diagnostics label")
a='''            } else {
                NSString *state=self.audit[@"troll"];
                value=[state isEqualToString:@"blocked"]?IPARL(@"Blocked: encrypted binary"):
                      [state isEqualToString:@"unverified"]?IPARL(@"Needs signing/entitlement check"):
                      IPARL(@"Not verified");
            }
        }
        cell.detailTextLabel.text=value;'''
b='''            } else if (index.row==4) {
                NSString *state=self.audit[@"troll"];
                value=[state isEqualToString:@"blocked"]?IPARL(@"Blocked: encrypted binary"):
                      [state isEqualToString:@"unverified"]?IPARL(@"Needs signing/entitlement check"):
                      IPARL(@"Not verified");
            } else {
                NSString *state=self.audit[@"structure"];
                value=[state isEqualToString:@"valid"]?IPARL(@"Payload is correctly placed"):
                      [state isEqualToString:@"nested"]?IPARL(@"Payload is inside an extra folder"):
                      [state isEqualToString:@"missing"]?IPARL(@"Missing top-level Payload folder"):
                      [state isEqualToString:@"bad-plist"]?IPARL(@"Info.plist cannot be read"):
                      IPARL(@"Not verified");
            }
        }
        cell.detailTextLabel.text=value;'''
s=once(s,a,b,"show Payload diagnosis")
a='''- (void)handleGridAction:(UIButton *)button {
    switch(button.tag) {'''
b='''- (void)handleGridAction:(UIButton *)button {
    // Refuse only definitively malformed IPA packaging. Do not change the
    // established ipatool/App Store install flow or reject encrypted binaries
    // that the legitimate device installer may support.
    if (button.tag==0 && self.audit) {
        NSString *state=self.audit[@"structure"];
        if ([state isEqualToString:@"nested"] ||
            [state isEqualToString:@"missing"] ||
            [state isEqualToString:@"bad-plist"]) {
            NSString *reason=[state isEqualToString:@"nested"]?
                IPARL(@"Payload is inside an extra folder"):
                ([state isEqualToString:@"missing"]?
                  IPARL(@"Missing top-level Payload folder"):
                  IPARL(@"Info.plist cannot be read"));
            NSString *detailText=[NSString stringWithFormat:@"%@\\n\\n%@",
                            reason,IPARL(@"IPA repack instructions")];
            UIAlertController *warning=[UIAlertController
                alertControllerWithTitle:IPARL(@"IPA package layout error")
                message:detailText
                preferredStyle:UIAlertControllerStyleAlert];
            [warning addAction:[UIAlertAction actionWithTitle:IPARL(@"OK")
                style:UIAlertActionStyleDefault handler:nil]];
            [self presentViewController:warning animated:YES completion:nil];
            return;
        }
    }
    switch(button.tag) {'''
s=once(s,a,b,"preflight installation validation")
detail.write_text(s,"utf-8")

localized={
"IPA Payload layout":"Cấu trúc Payload",
"Payload is correctly placed":"Payload nằm đúng cấp trong IPA",
"Payload is inside an extra folder":"Payload bị lồng trong thư mục khác",
"Missing top-level Payload folder":"Không tìm thấy Payload ở cấp gốc",
"Info.plist cannot be read":"Không đọc được Info.plist",
"IPA package layout error":"Cấu trúc IPA không hợp lệ",
"IPA repack instructions":"Open the archive and repackage it so that Payload/YourApp.app is directly at the root of the IPA ZIP. Changing the extension alone does not repair its structure. A correctly packaged file may still need a valid signature."
}
localized["IPA repack instructions"]="Mở tệp nén và đóng gói lại để Payload/TênỨngDụng.app nằm ngay ở cấp gốc của IPA. Đổi đuôi tệp không sửa được cấu trúc. Gói đúng cấu trúc vẫn có thể cần chữ ký hợp lệ."
for lang in ("en","vi"):
    p=root/"Resources"/f"{lang}.lproj"/"Localizable.strings"
    data=p.read_text("utf-8")
    for en,vi in localized.items():
        key=json.dumps(en,ensure_ascii=False)
        if key+" =" in data:continue
        val=vi if lang=="vi" else en
        if en=="IPA repack instructions" and lang=="en":
            val="Repackage the archive so Payload/YourApp.app is directly at the ZIP root. Changing the extension alone will not fix its structure. A valid IPA layout does not guarantee a valid code signature."
        data+=f"{key} = {json.dumps(val,ensure_ascii=False)};\n"
    p.write_text(data,"utf-8")
print("v0.4.2: IPA package layout preflight and localized repack guidance installed")
