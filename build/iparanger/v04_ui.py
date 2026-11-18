#!/usr/bin/env python3
"""v0.4 UI: metadata copy action and stable About footer.
Applied AFTER 0.3.3 patches. Touches only UI; never changes app credentials or IPA bytes.
"""
from pathlib import Path
import json
import sys
root=Path(sys.argv[1])
def repl(s,a,b,name):
    n=s.count(a)
    assert n==1,f"{name}: found {n} matching anchors"
    return s.replace(a,b,1)

p=root/"Controllers/IPARIPADetailViewController.m"
s=p.read_text("utf-8")
# UITableView accessory: a small copy icon beside Bundle ID, not a whole new row.
a='''        cell.selectionStyle=UITableViewCellSelectionStyleNone;
        return cell;
    }
    if (index.row==0) {'''
b='''        if (index.row==2 && self.bundleIdentifier.length && ![self.bundleIdentifier isEqualToString:@"—"]) {
            UIButton *copy = [UIButton buttonWithType:UIButtonTypeSystem];
            copy.frame=CGRectMake(0,0,46,44);
            [copy setImage:[UIImage systemImageNamed:@"doc.on.doc"] forState:UIControlStateNormal];
            copy.tintColor=UIColor.systemBlueColor;
            copy.accessibilityLabel=IPARL(@"Copy Bundle ID");
            [copy addTarget:self action:@selector(copyBundleIdentifier:) forControlEvents:UIControlEventTouchUpInside];
            cell.accessoryView=copy;
        }
        cell.selectionStyle=UITableViewCellSelectionStyleNone;
        return cell;
    }
    if (index.row==0) {'''
s=repl(s,a,b,"Bundle ID copy accessory")
a='''- (void)handleGridAction:(UIButton *)button {'''
b='''- (void)copyBundleIdentifier:(UIButton *)button {
    if (!self.bundleIdentifier.length || [self.bundleIdentifier isEqualToString:@"—"]) return;
    [UIPasteboard generalPasteboard].string=self.bundleIdentifier;
    [button setImage:[UIImage systemImageNamed:@"checkmark"] forState:UIControlStateNormal];
    button.accessibilityLabel=IPARL(@"Copied");
    [self announceCopiedBundleIdentifier];
}
- (void)announceCopiedBundleIdentifier {
    UILabel *toast=[[UILabel alloc] initWithFrame:CGRectZero];
    toast.text=IPARL(@"Copied");
    toast.textColor=UIColor.whiteColor;
    toast.backgroundColor=[UIColor colorWithWhite:0.1 alpha:0.86];
    toast.font=[UIFont systemFontOfSize:13 weight:UIFontWeightMedium];
    toast.textAlignment=NSTextAlignmentCenter;
    toast.layer.cornerRadius=9;
    toast.layer.masksToBounds=YES;
    toast.translatesAutoresizingMaskIntoConstraints=NO;
    [self.view addSubview:toast];
    [NSLayoutConstraint activateConstraints:@[
       [toast.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],
       [toast.bottomAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.bottomAnchor constant:-15],
       [toast.widthAnchor constraintGreaterThanOrEqualToConstant:126],
       [toast.heightAnchor constraintEqualToConstant:36]
    ]];
    [UIView animateWithDuration:0.2 animations:^{toast.alpha=1.0;} completion:^(BOOL finished){
        [UIView animateWithDuration:0.3 delay:1.0 options:0 animations:^{toast.alpha=0.0;}
                        completion:^(BOOL done){[toast removeFromSuperview];}];
    }];
}
- (void)handleGridAction:(UIButton *)button {'''
s=repl(s,a,b,"copy action")
p.write_text(s,"utf-8")

# Make About four sections: app/terms/License, and ONLY THEN the creator/version footer.
p=root/"Controllers/IPARAboutViewController.m"
s=p.read_text("utf-8")
s=repl(s,'''- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView { return 4; }''',
         '''- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView { return 4; }''',"about section count")
a='''    return section == 0 ? 2 : section == 1 ? 3 : section == 2 ? 3 : 1;'''
b='''    return section == 0 ? 1 : section == 1 ? 3 : section == 2 ? 1 : 4;'''
s=repl(s,a,b,"about rows")
a='''        case 1:return IPARL(@"Developers and acknowledgments");
        case 2:return IPARL(@"Terms of use");
        default:return IPARL(@"MIT License (original)");'''
b='''        case 1:return IPARL(@"Terms of use");
        case 2:return IPARL(@"MIT License (original)");
        default:return IPARL(@"About application");'''
s=repl(s,a,b,"about sections")
start=s.index("    switch(index.section) {",s.index("- (NSString *)detailForIndex:"))
end=s.index("\n}",start)
s=s[:start]+r'''    switch(index.section) {
        case 0: return IPARL(@"About app description");
        case 1:
            if (index.row==0) return IPARL(@"About terms license");
            if (index.row==1) return IPARL(@"About terms responsibility");
            return IPARL(@"About terms disclaimer");
        case 2: return IPAROriginalMITLicense();
        case 3:
            if (index.row==0) return @"IPARanger VN";
            if (index.row==1) return @"© 2023 0xkuj";
            if (index.row==2) return @"© 2026 Sentechtipsvn";
            return kIPARangerVersion;
        default: return @"";
    }'''+s[end:]
# Avoid showing credits in the middle and use compact gray centered footer
a='''    cell.textLabel.font=[UIFont systemFontOfSize:(index.section==3 ? 12.5 : 14.5)];
    cell.textLabel.textColor=(index.section==0 && index.row==1) ?
       UIColor.secondaryLabelColor : UIColor.labelColor;'''
b='''    cell.textLabel.font=[UIFont systemFontOfSize:(index.section==2 ? 12.5 : 14.5)];
    cell.textLabel.textColor=(index.section==3) ? UIColor.secondaryLabelColor : UIColor.labelColor;
    if (index.section==3) cell.textLabel.textAlignment=NSTextAlignmentCenter;'''
s=repl(s,a,b,"about compact footer styling")
p.write_text(s,"utf-8")

for code,n in (("en",0),("vi",1)):
    p=root/"Resources"/(code+".lproj")/"Localizable.strings"
    s=p.read_text("utf-8")
    for k,values in {
        "Copy Bundle ID":("Copy Bundle ID","Sao chép Bundle ID"),
        "Copied":("Copied","Đã sao chép"),
        "About application":("Application and credits","Ứng dụng và bản quyền")
    }.items():
        key=json.dumps(k,ensure_ascii=False)
        if key+" =" not in s: s+=f"{key} = {json.dumps(values[n],ensure_ascii=False)};\n"
    p.write_text(s,"utf-8")
print("v0.4 UI: Copy Bundle ID and About footer moved to the bottom")
