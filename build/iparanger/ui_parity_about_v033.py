#!/usr/bin/env python3
"""UI parity hotfix for the tested 0.3.2 branch.
Run after polish_v032.py, retain original backend, all auth and download operations.
"""
from pathlib import Path
import json,sys

root=Path(sys.argv[1])
def once(s,a,b,where):
    n=s.count(a)
    assert n==1, f"{where}: expected 1 match, found {n} for {a[:100]!r}"
    return s.replace(a,b,1)
def translate(items):
    for code,pos in (("en",0),("vi",1)):
        p=root/"Resources"/(code+".lproj")/"Localizable.strings"
        content=p.read_text("utf-8")
        for key,vi in items.items():
            k=json.dumps(key,ensure_ascii=False)
            if f"{k} =" not in content:
                content += f"{k} = {json.dumps((key,vi)[pos],ensure_ascii=False)};\n"
        p.write_text(content,"utf-8")

# UISearchController can reset UISearchTextField.rightView on layout or activation.
# A *real subview* of the text field stays visible and is constrained to its trailing edge.
p=root/"Controllers/IPARSearchViewController.m"
s=p.read_text("utf-8")
s=once(s,'@property (nonatomic, strong) UILabel *storeCodeLabel;',
'''@property (nonatomic, strong) UILabel *storeCodeLabel;
@property (nonatomic, strong) UIView *countryOverlay;''',"overlay property")
start=s.index("- (void)installCountrySearchAccessory {")
end=s.index("- (void)updateCountrySearchAccessory {",start)
assert start < end
new=r'''- (void)installCountrySearchAccessory {
    UISearchTextField *field = self.searchController.searchBar.searchTextField;
    if (!field) return;
    if (self.countryOverlay.superview == field) {
        [self updateCountrySearchAccessory];
        return;
    }
    [self.countryOverlay removeFromSuperview];
    UIView *overlay = [[UIView alloc] initWithFrame:CGRectZero];
    overlay.translatesAutoresizingMaskIntoConstraints = NO;
    overlay.backgroundColor = UIColor.clearColor;
    [field addSubview:overlay];
    [NSLayoutConstraint activateConstraints:@[
        [overlay.trailingAnchor constraintEqualToAnchor:field.trailingAnchor constant:-7],
        [overlay.centerYAnchor constraintEqualToAnchor:field.centerYAnchor],
        [overlay.widthAnchor constraintEqualToConstant:80],
        [overlay.heightAnchor constraintEqualToConstant:32]
    ]];
    UIButton *clear = [UIButton buttonWithType:UIButtonTypeSystem];
    clear.frame = CGRectMake(0,0,28,32);
    [clear setImage:[UIImage systemImageNamed:@"xmark.circle.fill"] forState:UIControlStateNormal];
    clear.tintColor = UIColor.tertiaryLabelColor;
    [clear addTarget:self action:@selector(clearSearchText) forControlEvents:UIControlEventTouchUpInside];
    [overlay addSubview:clear];
    self.clearSearchButton = clear;
    UILabel *label = [[UILabel alloc] initWithFrame:CGRectMake(30,0,50,32)];
    label.textAlignment = NSTextAlignmentCenter;
    label.font = [UIFont systemFontOfSize:15 weight:UIFontWeightSemibold];
    label.adjustsFontSizeToFitWidth = YES;
    label.minimumScaleFactor = 0.85;
    label.isAccessibilityElement = YES;
    [overlay addSubview:label];
    self.storeCodeLabel = label;
    self.countryOverlay = overlay;
    // Reserve text space separately; the label is NOT inside rightView because
    // UISearchTextField may replace rightView with its internal accessory.
    field.clearButtonMode = UITextFieldViewModeNever;
    field.rightView = [[UIView alloc] initWithFrame:CGRectMake(0,0,89,1)];
    field.rightViewMode = UITextFieldViewModeAlways;
    [self updateCountrySearchAccessory];
}
- (void)viewDidAppear:(BOOL)animated {
    [super viewDidAppear:animated];
    [self installCountrySearchAccessory];
}
- (void)viewDidLayoutSubviews {
    [super viewDidLayoutSubviews];
    UISearchTextField *field=self.searchController.searchBar.searchTextField;
    if (field && self.countryOverlay.superview != field) {
        [self installCountrySearchAccessory];
    }
}
'''
s=s[:start]+new+s[end:]
s=once(s,'self.storeCodeLabel.textColor = (code.length == 2) ? UIColor.systemBlueColor : UIColor.secondaryLabelColor;',
'''self.storeCodeLabel.textColor = (code.length == 2) ? UIColor.systemBlueColor : UIColor.secondaryLabelColor;
    self.storeCodeLabel.accessibilityLabel = [NSString stringWithFormat:@"%@: %@",
        IPARL(@"Account Storefront"), self.storeCodeLabel.text ?: @"—"];''',"accessibility for storefront")
p.write_text(s,"utf-8")

# Compact authors. URLs in the dictionaries remain unchanged.
p=root/"Controllers/IPARDeveloperLinksViewController.m"
s=p.read_text("utf-8")
s=once(s,'@"Sentechtipsvn · @Sentechtipsvn1"','@"Sentechtipsvn"',"X author name")
s=once(s,'@"Sentechtipsvn · Buy Me a Coffee"','@"Sentechtipsvn"',"Donation author name")
s=s.replace('@"subtitle":IPARL(@"Vietnamese fork developer")','@"subtitle":@""')
s=once(s,'cell.detailTextLabel.text=entry[@"subtitle"];',
'''NSString *subtitle=entry[@"subtitle"];
    cell.detailTextLabel.text=subtitle.length ? subtitle : nil;''',"empty credits subtitle")
p.write_text(s,"utf-8")

# About is a proper native page after Source code, with original MIT license retained.
p=root/"Controllers/IPARAccountAndCreditsController.m"
s=p.read_text("utf-8")
s=once(s,'#import "IPARDeveloperLinksViewController.h"',
        '#import "IPARDeveloperLinksViewController.h"\n#import "IPARAboutViewController.h"',"about import")
s=once(s,'[self linkRowWithImageNamed:kGithubIcon title:IPARL(@"Source code")\n                            action:@selector(openGithub)],',
'''[self linkRowWithImageNamed:kGithubIcon title:IPARL(@"Source code")
                            action:@selector(openGithub)],
        [self linkRowWithImageNamed:@"info.circle" title:IPARL(@"About")
                            action:@selector(showAppAbout)],''',"About beneath source")
s=once(s,'- (void)showDeveloperX {',
'''- (void)showAppAbout {
    [self.navigationController pushViewController:[[IPARAboutViewController alloc] init] animated:YES];
}
- (void)showDeveloperX {''',"About navigation")
s=once(s,'IPARL(@"Vietnamese fork by Sentechtipsvn")','@"Sentechtipsvn"',"compact footer name")
p.write_text(s,"utf-8")

(root/"Controllers/IPARAboutViewController.h").write_text(r'''#import <UIKit/UIKit.h>
@interface IPARAboutViewController : UITableViewController
@end
''',"utf-8")
(root/"Controllers/IPARAboutViewController.m").write_text(r'''#import "IPARAboutViewController.h"
#import "../Utils/IPARLanguageManager.h"
#import "../Extensions/IPARConstants.h"

static NSString *IPAROriginalMITLicense(void) {
    return @"MIT License\n\n"
    @"Copyright (c) 2023 0xkuj\n\n"
    @"Permission is hereby granted, free of charge, to any person obtaining a copy "
    @"of this software and associated documentation files (the \"Software\"), to deal "
    @"in the Software without restriction, including without limitation the rights "
    @"to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
    @"copies of the Software, and to permit persons to whom the Software is "
    @"furnished to do so, subject to the following conditions:\n\n"
    @"The above copyright notice and this permission notice shall be included in "
    @"all copies or substantial portions of the Software.\n\n"
    @"THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR "
    @"IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
    @"FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE "
    @"AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER "
    @"LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, "
    @"OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.";
}

@interface IPARAboutViewController ()
@end
@implementation IPARAboutViewController
- (instancetype)init {
    self=[super initWithStyle:UITableViewStyleInsetGrouped];
    if (self) self.title=IPARL(@"About");
    return self;
}
- (void)viewDidLoad {
    [super viewDidLoad];
    self.tableView.backgroundColor=UIColor.systemGroupedBackgroundColor;
    self.tableView.rowHeight=UITableViewAutomaticDimension;
    self.tableView.estimatedRowHeight=105;
}
- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView { return 4; }
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return section == 0 ? 2 : section == 1 ? 3 : section == 2 ? 3 : 1;
}
- (NSString *)tableView:(UITableView *)tableView titleForHeaderInSection:(NSInteger)section {
    switch(section) {
        case 0:return IPARL(@"Software");
        case 1:return IPARL(@"Developers and acknowledgments");
        case 2:return IPARL(@"Terms of use");
        default:return IPARL(@"MIT License (original)");
    }
}
- (NSString *)detailForIndex:(NSIndexPath *)index {
    switch(index.section) {
        case 0:
            return index.row == 0 ?
               IPARL(@"About app description") : kIPARangerVersion;
        case 1:
            if (index.row == 0) return @"© 2023 0xkuj — IPARanger";
            if (index.row == 1) return @"© 2026 Sentechtipsvn — IPARanger VN";
            return @"Majd Alfhaily — ipatool\nangelXwind — appinst";
        case 2:
            if (index.row == 0) return IPARL(@"About terms license");
            if (index.row == 1) return IPARL(@"About terms responsibility");
            return IPARL(@"About terms disclaimer");
        default:
            return IPAROriginalMITLicense();
    }
}
- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)index {
    UITableViewCell *cell=[tableView dequeueReusableCellWithIdentifier:@"AboutTextCell"];
    if (!cell) cell=[[UITableViewCell alloc] initWithStyle:UITableViewCellStyleDefault reuseIdentifier:@"AboutTextCell"];
    cell.selectionStyle=UITableViewCellSelectionStyleNone;
    cell.textLabel.numberOfLines=0;
    cell.textLabel.font=[UIFont systemFontOfSize:(index.section==3 ? 12.5 : 14.5)];
    cell.textLabel.textColor=(index.section==0 && index.row==1) ?
       UIColor.secondaryLabelColor : UIColor.labelColor;
    cell.textLabel.text=[self detailForIndex:index];
    return cell;
}
@end
''',"utf-8")
translate({
    "About":"Giới thiệu",
    "Software":"Phần mềm",
    "Developers and acknowledgments":"Tác giả và ghi công",
    "Terms of use":"Điều khoản sử dụng",
    "MIT License (original)":"Giấy phép MIT (nguyên bản)",
    "About app description":"IPARanger VN hỗ trợ tìm ứng dụng theo vùng App Store của Apple ID đang đăng nhập, chọn phiên bản khả dụng, tải và quản lý IPA trên thiết bị jailbreak tương thích.",
    "About terms license":"Chỉ tải và sử dụng ứng dụng mà bạn có quyền sử dụng hợp pháp. Việc mua, tải và sử dụng ứng dụng còn phụ thuộc điều khoản của Apple và nhà phát hành.",
    "About terms responsibility":"Việc cài đặt IPA, sử dụng jailbreak và thay đổi phần mềm hệ thống có rủi ro. Hãy sao lưu dữ liệu và tự đánh giá khả năng tương thích trước khi cài.",
    "About terms disclaimer":"Phần mềm cung cấp theo giấy phép MIT, không có bảo hành. Đây là dự án độc lập, không thuộc hoặc được Apple bảo trợ."
})
print("UI v0.3.3: persistent Store badge and native About / Terms / original MIT license")
