#!/usr/bin/env python3
"""v0.4.3 Control Center style 1x4 IPA toolbars; separate original/decrypted sources."""
from pathlib import Path
import json,sys
root=Path(sys.argv[1])
p=root/"Controllers/IPARIPADetailViewController.h"
h=p.read_text("utf-8")
a='@property (nonatomic, copy) void (^onDelete)(void);'
assert h.count(a)==1
h=h.replace(a,a+'''
@property (nonatomic, copy) void (^onTrollStore)(void);
@property (nonatomic, copy) NSString *absoluteIPAPath;
@property (nonatomic) BOOL isDecryptedSource;
- (instancetype)initWithName:(NSString *)name fileName:(NSString *)fileName
                        size:(NSString *)size icon:(UIImage *)icon
                    fullPath:(NSString *)path decrypted:(BOOL)decrypted;
''')
p.write_text(h,"utf-8")
p=root/"Controllers/IPARIPADetailViewController.m"
s=p.read_text("utf-8")
a='''    self.fileName=[fileName copy] ?: @"";'''
assert s.count(a)==1
s=s.replace(a,a+'''
    self.absoluteIPAPath=[kIPARangerDocumentsPath stringByAppendingPathComponent:self.fileName];''',1)
anchor='''- (void)viewDidLoad {'''
assert s.count(anchor)==1
s=s.replace(anchor,'''- (instancetype)initWithName:(NSString *)name fileName:(NSString *)fileName
                        size:(NSString *)size icon:(UIImage *)icon
                    fullPath:(NSString *)path decrypted:(BOOL)decrypted {
    self=[self initWithName:name fileName:fileName size:size icon:icon];
    if (self) {
        self.absoluteIPAPath=[path copy];
        self.isDecryptedSource=decrypted;
    }
    return self;
}
- (void)viewDidLoad {''',1)
a='''    NSString *path=[kIPARangerDocumentsPath stringByAppendingPathComponent:self.fileName];'''
assert s.count(a)==2
s=s.replace(a,'''    NSString *path=self.absoluteIPAPath;''')
# Table action layout: 1 row of 4 tiles; preserve explicit red Delete row.
x=s.index('''    if (index.row==0) {
        UIStackView *column = [[UIStackView alloc] init];''')
y=s.index('''    cell.imageView.image=[UIImage systemImageNamed:@"trash"];''',x)
s=s[:x]+r'''    if (index.row==0) {
        UIStackView *line=[[UIStackView alloc] init];
        line.axis=UILayoutConstraintAxisHorizontal;
        line.distribution=UIStackViewDistributionFillEqually;
        line.spacing=8;
        line.translatesAutoresizingMaskIntoConstraints=NO;
        [cell.contentView addSubview:line];
        for (NSInteger action=0; action<4; action++) {
            [line addArrangedSubview:[self gridActionButton:action]];
        }
        [NSLayoutConstraint activateConstraints:@[
            [line.topAnchor constraintEqualToAnchor:cell.contentView.topAnchor constant:10],
            [line.bottomAnchor constraintEqualToAnchor:cell.contentView.bottomAnchor constant:-10],
            [line.leadingAnchor constraintEqualToAnchor:cell.contentView.leadingAnchor constant:10],
            [line.trailingAnchor constraintEqualToAnchor:cell.contentView.trailingAnchor constant:-10]
        ]];
        cell.selectionStyle=UITableViewCellSelectionStyleNone;
        return cell;
    }
'''+s[y:]
# Rebuild tail. Contains old gridActionButton and handleGridAction, keep safe preflight.
x=s.index('''- (UIButton *)gridActionButton:(NSInteger)action {''')
y=s.index('''- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:''',x)
# Preserve copy Bundle ID, its animation, and Files export from the stable v0.4.x.
savedStart=s.index("- (void)saveToFiles {",x)
savedEnd=s.index("- (void)handleGridAction:",savedStart)
retained=s[savedStart:savedEnd]
assert "initForExportingURLs" in retained and "copyBundleIdentifier" in retained
s=s[:x]+r'''- (UIButton *)gridActionButton:(NSInteger)action {
    NSArray<NSString *> *original=@[IPARL(@"Install Application"),IPARL(@"Inspect IPA"),
                                    IPARL(@"Open in Filza"),IPARL(@"More IPA actions")];
    NSArray<NSString *> *decrypted=@[IPARL(@"Open in TrollStore"),IPARL(@"Install Application"),
                                     IPARL(@"Export IPA"),IPARL(@"More IPA actions")];
    NSArray<NSString *> *originalIcons=@[@"square.and.arrow.down",@"checkmark.shield",
                                         @"folder",@"ellipsis"];
    NSArray<NSString *> *decryptedIcons=@[@"iphone",@"square.and.arrow.down",
                                          @"square.and.arrow.up",@"ellipsis"];
    NSArray<NSString *> *titles=self.isDecryptedSource?decrypted:original;
    NSArray<NSString *> *icons=self.isDecryptedSource?decryptedIcons:originalIcons;
    UIButton *button=[UIButton buttonWithType:UIButtonTypeSystem];
    button.tag=action;
    button.backgroundColor=UIColor.tertiarySystemGroupedBackgroundColor;
    button.layer.cornerRadius=17;
    button.layer.cornerCurve=kCACornerCurveContinuous;
    button.accessibilityLabel=titles[action];
    UIImageView *glyph=[[UIImageView alloc] initWithImage:[UIImage systemImageNamed:icons[action]]];
    glyph.tintColor=UIColor.systemBlueColor;
    glyph.contentMode=UIViewContentModeScaleAspectFit;
    glyph.translatesAutoresizingMaskIntoConstraints=NO;
    [button addSubview:glyph];
    UILabel *title=[[UILabel alloc] init];
    title.text=titles[action];
    title.textColor=UIColor.labelColor;
    title.textAlignment=NSTextAlignmentCenter;
    title.numberOfLines=2;
    title.minimumScaleFactor=0.76;
    title.adjustsFontSizeToFitWidth=YES;
    title.font=[UIFont systemFontOfSize:11 weight:UIFontWeightMedium];
    title.translatesAutoresizingMaskIntoConstraints=NO;
    [button addSubview:title];
    [NSLayoutConstraint activateConstraints:@[
        [button.heightAnchor constraintEqualToConstant:92],
        [glyph.centerXAnchor constraintEqualToAnchor:button.centerXAnchor],
        [glyph.topAnchor constraintEqualToAnchor:button.topAnchor constant:13],
        [glyph.widthAnchor constraintEqualToConstant:25],
        [glyph.heightAnchor constraintEqualToConstant:25],
        [title.leadingAnchor constraintEqualToAnchor:button.leadingAnchor constant:4],
        [title.trailingAnchor constraintEqualToAnchor:button.trailingAnchor constant:-4],
        [title.topAnchor constraintEqualToAnchor:glyph.bottomAnchor constant:9],
        [title.bottomAnchor constraintLessThanOrEqualToAnchor:button.bottomAnchor constant:-6]
    ]];
    [button addTarget:self action:@selector(handleGridAction:) forControlEvents:UIControlEventTouchUpInside];
    return button;
}
- (void)showMoreIPAActions:(UIView *)sender {
    UIAlertController *sheet=[UIAlertController alertControllerWithTitle:IPARL(@"More IPA actions")
                              message:nil preferredStyle:UIAlertControllerStyleActionSheet];
    if (self.onShare) [sheet addAction:[UIAlertAction actionWithTitle:IPARL(@"Share")
        style:UIAlertActionStyleDefault handler:^(UIAlertAction *a){self.onShare();}]];
    if (self.onOpenInFilza && self.isDecryptedSource)
        [sheet addAction:[UIAlertAction actionWithTitle:IPARL(@"Open in Filza")
        style:UIAlertActionStyleDefault handler:^(UIAlertAction *a){self.onOpenInFilza();}]];
    if (self.onRename) [sheet addAction:[UIAlertAction actionWithTitle:IPARL(@"Rename File")
        style:UIAlertActionStyleDefault handler:^(UIAlertAction *a){self.onRename();}]];
    [sheet addAction:[UIAlertAction actionWithTitle:IPARL(@"Export IPA")
        style:UIAlertActionStyleDefault handler:^(UIAlertAction *a){[self saveToFiles];}]];
    [sheet addAction:[UIAlertAction actionWithTitle:IPARL(@"Copy file path")
        style:UIAlertActionStyleDefault handler:^(UIAlertAction *a){
           [UIPasteboard generalPasteboard].string=self.absoluteIPAPath;
        }]];
    [sheet addAction:[UIAlertAction actionWithTitle:IPARL(@"Cancel")
        style:UIAlertActionStyleCancel handler:nil]];
    UIPopoverPresentationController *popover=sheet.popoverPresentationController;
    if (popover) {popover.sourceView=sender;popover.sourceRect=sender.bounds;}
    [self presentViewController:sheet animated:YES completion:nil];
}
- (void)showPreflightWarning:(NSString *)reason {
    NSString *message=[NSString stringWithFormat:@"%@\n\n%@",reason,IPARL(@"IPA repack instructions")];
    UIAlertController *a=[UIAlertController alertControllerWithTitle:IPARL(@"IPA package layout error")
            message:message preferredStyle:UIAlertControllerStyleAlert];
    [a addAction:[UIAlertAction actionWithTitle:IPARL(@"OK") style:UIAlertActionStyleDefault handler:nil]];
    [self presentViewController:a animated:YES completion:nil];
}
- (BOOL)checkIPAForOpening {
    if (!self.audit) {
        [self showPreflightWarning:IPARL(@"IPA audit still running")];
        return NO;
    }
    NSString *structure=self.audit[@"structure"];
    NSString *zip=self.audit[@"zip"];
    if (![zip isEqualToString:@"valid"] || ![structure isEqualToString:@"valid"]) {
        NSString *reason=[structure isEqualToString:@"nested"]?
           IPARL(@"Payload is inside an extra folder"):
           ([structure isEqualToString:@"missing"]?
              IPARL(@"Missing top-level Payload folder"):IPARL(@"IPA structure was not verified"));
        [self showPreflightWarning:reason];
        return NO;
    }
    return YES;
}
- (void)handleGridAction:(UIButton *)button {
    NSInteger selected=button.tag;
    if (self.isDecryptedSource) {
        if (selected==0) {
            if (![self checkIPAForOpening]) return;
            NSString *drm=self.audit[@"drm"];
            if (![drm isEqualToString:@"clear"]) {
                UIAlertController *warning=[UIAlertController alertControllerWithTitle:IPARL(@"TrollStore preflight")
                    message:([drm isEqualToString:@"encrypted"]?
                        IPARL(@"Cannot pass encrypted IPA to TrollStore"):
                        IPARL(@"IPA encryption status is unknown"))
                    preferredStyle:UIAlertControllerStyleAlert];
                [warning addAction:[UIAlertAction actionWithTitle:IPARL(@"OK") style:UIAlertActionStyleDefault handler:nil]];
                [self presentViewController:warning animated:YES completion:nil];
                return;
            }
            if (self.onTrollStore) self.onTrollStore();
        } else if (selected==1) {
            if ([self checkIPAForOpening] && self.onInstall) self.onInstall();
        } else if (selected==2) [self saveToFiles];
        else [self showMoreIPAActions:button];
        return;
    }
    if (selected==0) {
        if ([self checkIPAForOpening] && self.onInstall) self.onInstall();
    } else if (selected==1) {
        [self.tableView scrollToRowAtIndexPath:[NSIndexPath indexPathForRow:0 inSection:3]
                              atScrollPosition:UITableViewScrollPositionTop animated:YES];
    } else if (selected==2) {
        if (self.onOpenInFilza) self.onOpenInFilza();
    } else [self showMoreIPAActions:button];
}
'''+retained+s[y:]
p.write_text(s,"utf-8")
trs={
"Inspect IPA":"Kiểm tra",
"Open in TrollStore":"TrollStore",
"Export IPA":"Xuất IPA",
"More IPA actions":"Thêm",
"Copy file path":"Sao chép đường dẫn",
"IPA audit still running":"Đang kiểm tra IPA, hãy thử lại",
"IPA structure was not verified":"Cấu trúc IPA chưa được xác minh",
"TrollStore preflight":"Kiểm tra TrollStore",
"Cannot pass encrypted IPA to TrollStore":"IPA vẫn được mã hóa FairPlay, TrollStore không thể cài trực tiếp. Chưa có chức năng giải mã tự động.",
"IPA encryption status is unknown":"Không xác định được trạng thái mã hóa; chưa thể xác nhận khả năng chuyển sang TrollStore."
}
for lang in ("en","vi"):
    p=root/"Resources"/(lang+".lproj")/"Localizable.strings"
    s=p.read_text("utf-8")
    for en,vi in trs.items():
        key=json.dumps(en,ensure_ascii=False)
        if key+" =" not in s:
            s+=f"{key} = {json.dumps(vi if lang=='vi' else en,ensure_ascii=False)};\n"
    p.write_text(s,"utf-8")
# App metadata must agree with test DEB; ID remains the v0.4.x baseline.
import plistlib
info=root/"Resources"/"Info.plist"
meta=plistlib.loads(info.read_bytes())
assert meta.get("CFBundleIdentifier")=="com.0xkuj.iparanger"
assert meta.get("IPARVNPackageVersion")=="2.8.2+vn0.4.2"
meta["IPARVNPackageVersion"]="2.8.2+vn0.4.3"
meta["CFBundleShortVersionString"]="0.4.3"
meta["CFBundleVersion"]="430"
info.write_bytes(plistlib.dumps(meta,fmt=plistlib.FMT_XML,sort_keys=False))
print("v0.4.3: CC 4-action toolbar; distinct original/unencrypted paths; version synchronized")
