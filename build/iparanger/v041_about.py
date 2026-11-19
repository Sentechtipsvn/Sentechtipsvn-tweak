#!/usr/bin/env python3
"""v0.4.1 native About/Legal redesign based on approved IPARanger VN design.
Preserves verbatim original 0xkuj MIT license and moves it into its own readable page.
Applied last, after v0.4 UI patches. No network, download or auth changes.
"""
from pathlib import Path
import json,sys
root=Path(sys.argv[1])
about=root/"Controllers/IPARAboutViewController.m"
source=about.read_text("utf-8")
begin=source.index("static NSString *IPAROriginalMITLicense(void) {")
end=source.index("\n}\n",begin)+2
mit=source[begin:end]
assert "Copyright (c) 2023 0xkuj" in mit and "THE SOFTWARE IS PROVIDED" in mit

new = r'''#import "IPARAboutViewController.h"
#import "../Utils/IPARLanguageManager.h"
#import "../Extensions/IPARConstants.h"

'''+mit+r'''

@interface IPARAboutTextViewController : UIViewController
@property (nonatomic, copy) NSString *articleText;
- (instancetype)initWithTitle:(NSString *)title article:(NSString *)article;
@end

@implementation IPARAboutTextViewController
- (instancetype)initWithTitle:(NSString *)title article:(NSString *)article {
    if ((self=[super init])) {
        self.title=title;
        self.articleText=[article copy];
    }
    return self;
}
- (void)viewDidLoad {
    [super viewDidLoad];
    self.view.backgroundColor=UIColor.systemGroupedBackgroundColor;
    UITextView *document=[[UITextView alloc] initWithFrame:CGRectZero];
    document.translatesAutoresizingMaskIntoConstraints=NO;
    document.editable=NO;
    document.selectable=YES;
    document.scrollEnabled=YES;
    document.backgroundColor=UIColor.clearColor;
    document.textColor=UIColor.labelColor;
    document.font=[UIFont preferredFontForTextStyle:UIFontTextStyleBody];
    document.adjustsFontForContentSizeCategory=YES;
    document.textContainerInset=UIEdgeInsetsMake(22,18,30,18);
    document.text=self.articleText ?: @"";
    [self.view addSubview:document];
    [NSLayoutConstraint activateConstraints:@[
       [document.topAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.topAnchor],
       [document.bottomAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.bottomAnchor],
       [document.leadingAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.leadingAnchor],
       [document.trailingAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.trailingAnchor]
    ]];
}
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
    self.tableView.estimatedRowHeight=84;
    self.tableView.separatorInset=UIEdgeInsetsMake(0,16,0,16);
}
- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView { return 4; }
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    switch(section) {
        case 0: return 1;
        case 1: return 1;
        case 2: return 3;
        default: return 4;
    }
}
- (NSString *)tableView:(UITableView *)tableView titleForHeaderInSection:(NSInteger)section {
    if (section==2) return IPARL(@"Information and legal");
    if (section==3) return IPARL(@"Developers");
    return nil;
}
- (UITableViewCell *)heroCell {
    UITableViewCell *cell=[[UITableViewCell alloc] initWithStyle:UITableViewCellStyleDefault reuseIdentifier:nil];
    cell.selectionStyle=UITableViewCellSelectionStyleNone;
    cell.backgroundColor=UIColor.secondarySystemGroupedBackgroundColor;
    UIStackView *stack=[[UIStackView alloc] initWithFrame:CGRectZero];
    stack.translatesAutoresizingMaskIntoConstraints=NO;
    stack.axis=UILayoutConstraintAxisVertical;
    stack.alignment=UIStackViewAlignmentCenter;
    stack.spacing=7;
    UIImage *logo=[UIImage imageNamed:@"AppIcon60x60"];
    if (!logo) logo=[UIImage systemImageNamed:@"shippingbox.fill"];
    UIImageView *icon=[[UIImageView alloc] initWithImage:logo];
    icon.translatesAutoresizingMaskIntoConstraints=NO;
    icon.contentMode=UIViewContentModeScaleAspectFit;
    icon.layer.cornerRadius=16;
    icon.layer.masksToBounds=YES;
    [NSLayoutConstraint activateConstraints:@[
       [icon.widthAnchor constraintEqualToConstant:74],
       [icon.heightAnchor constraintEqualToConstant:74]
    ]];
    UILabel *name=[[UILabel alloc] init];
    name.text=@"IPARanger VN";
    name.font=[UIFont preferredFontForTextStyle:UIFontTextStyleTitle2];
    name.adjustsFontForContentSizeCategory=YES;
    name.textAlignment=NSTextAlignmentCenter;
    name.textColor=UIColor.labelColor;
    UILabel *tagline=[[UILabel alloc] init];
    tagline.text=IPARL(@"About tagline");
    tagline.numberOfLines=0;
    tagline.textAlignment=NSTextAlignmentCenter;
    tagline.font=[UIFont preferredFontForTextStyle:UIFontTextStyleSubheadline];
    tagline.adjustsFontForContentSizeCategory=YES;
    tagline.textColor=UIColor.secondaryLabelColor;
    [stack addArrangedSubview:icon];
    [stack addArrangedSubview:name];
    [stack addArrangedSubview:tagline];
    [cell.contentView addSubview:stack];
    [NSLayoutConstraint activateConstraints:@[
       [stack.topAnchor constraintEqualToAnchor:cell.contentView.topAnchor constant:22],
       [stack.bottomAnchor constraintEqualToAnchor:cell.contentView.bottomAnchor constant:-22],
       [stack.leadingAnchor constraintEqualToAnchor:cell.contentView.leadingAnchor constant:18],
       [stack.trailingAnchor constraintEqualToAnchor:cell.contentView.trailingAnchor constant:-18]
    ]];
    return cell;
}
- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)index {
    if(index.section==0) return [self heroCell];
    UITableViewCell *cell=[[UITableViewCell alloc] initWithStyle:UITableViewCellStyleSubtitle reuseIdentifier:nil];
    cell.backgroundColor=UIColor.secondarySystemGroupedBackgroundColor;
    cell.textLabel.adjustsFontForContentSizeCategory=YES;
    cell.detailTextLabel.adjustsFontForContentSizeCategory=YES;
    cell.detailTextLabel.textColor=UIColor.secondaryLabelColor;
    if(index.section==1) {
        cell.textLabel.text=IPARL(@"Overview");
        cell.textLabel.font=[UIFont preferredFontForTextStyle:UIFontTextStyleHeadline];
        cell.detailTextLabel.text=IPARL(@"About app description");
        cell.detailTextLabel.numberOfLines=0;
        cell.detailTextLabel.font=[UIFont preferredFontForTextStyle:UIFontTextStyleSubheadline];
        cell.selectionStyle=UITableViewCellSelectionStyleNone;
        return cell;
    }
    if(index.section==2) {
        NSArray<NSString *> *keys=@[@"User guide",@"Terms and notices",@"Open-source licenses"];
        NSArray<NSString *> *subs=@[@"Guide summary",@"Terms summary",@"Licenses summary"];
        NSArray<NSString *> *icons=@[@"book.closed",@"shield.checkered",@"scale.3d"];
        cell.textLabel.text=IPARL(keys[index.row]);
        cell.textLabel.font=[UIFont preferredFontForTextStyle:UIFontTextStyleBody];
        cell.detailTextLabel.text=IPARL(subs[index.row]);
        cell.detailTextLabel.font=[UIFont preferredFontForTextStyle:UIFontTextStyleCaption1];
        cell.imageView.image=[UIImage systemImageNamed:icons[index.row]];
        cell.imageView.tintColor=UIColor.secondaryLabelColor;
        cell.accessoryType=UITableViewCellAccessoryDisclosureIndicator;
        return cell;
    }
    NSString *packageVersion=[[NSBundle mainBundle] objectForInfoDictionaryKey:@"IPARVNPackageVersion"];
    if (![packageVersion isKindOfClass:NSString.class] || !packageVersion.length)
        packageVersion=kIPARangerVersion;
    NSArray<NSString *> *labels=@[@"IPARanger VN",@"© 2023 0xkuj",@"© 2026 Sentechtipsvn",
                                 [NSString stringWithFormat:@"%@: %@",IPARL(@"Version"),packageVersion]];
    cell.textLabel.text=labels[index.row];
    cell.textLabel.font=[UIFont preferredFontForTextStyle:UIFontTextStyleFootnote];
    cell.textLabel.textColor=UIColor.secondaryLabelColor;
    cell.textLabel.textAlignment=NSTextAlignmentCenter;
    cell.selectionStyle=UITableViewCellSelectionStyleNone;
    return cell;
}
- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)index {
    [tableView deselectRowAtIndexPath:index animated:YES];
    if (index.section!=2) return;
    NSString *title=nil;
    NSString *body=nil;
    if(index.row==0) {
        title=IPARL(@"User guide");
        body=IPARL(@"Guide article");
    } else if(index.row==1) {
        title=IPARL(@"Terms and notices");
        body=IPARL(@"About terms license");
        body=[@[body,IPARL(@"About terms responsibility"),IPARL(@"About terms disclaimer")]
               componentsJoinedByString:@"\n\n"];
    } else {
        title=IPARL(@"Open-source licenses");
        body=[NSString stringWithFormat:@"%@\n\n%@",
              IPAROriginalMITLicense(),IPARL(@"Third-party attribution")];
    }
    IPARAboutTextViewController *page=[[IPARAboutTextViewController alloc]
                                          initWithTitle:title article:body];
    [self.navigationController pushViewController:page animated:YES];
}
@end
'''
about.write_text(new,"utf-8")
translations={
 "About tagline":"Find, download and manage IPA on compatible iOS devices",
 "Overview":"Overview",
 "Information and legal":"INFORMATION & LEGAL",
 "Developers":"DEVELOPERS",
 "User guide":"User Guide",
 "Terms and notices":"Terms and Notices",
 "Open-source licenses":"Open-source Licenses",
 "Guide summary":"Discover, download and manage IPA files",
 "Terms summary":"Usage rights and responsibilities",
 "Licenses summary":"MIT license and third-party attribution",
 "Guide article":("1. Sign in with the Apple ID entitled to the app. The Store region follows that account.\n\n"
                  "2. Use Discover to search by name or Bundle ID.\n\n"
                  "3. Select a version and download. Older versions are not guaranteed to run on every iOS release.\n\n"
                  "4. Open Downloaded IPAs for file details, copy Bundle ID, install, rename, share or export to Files.\n\n"
                  "5. Integrity inspection reports ZIP status, SHA-256 and encryption indicators. An unencrypted IPA is not necessarily installable using TrollStore."),
 "Third-party attribution":("Additional components: ipatool (Majd Alfhaily) and appinst (angelXwind). "
                             "Refer to the respective upstream projects for their license terms. "
                             "This software is independent and is not affiliated with Apple."),
}
vi={
 "About tagline":"Tìm kiếm, tải và quản lý IPA trên iOS tương thích",
 "Overview":"Tổng quan",
 "Information and legal":"THÔNG TIN VÀ PHÁP LÝ",
 "Developers":"NHÀ PHÁT TRIỂN",
 "User guide":"Hướng dẫn sử dụng",
 "Terms and notices":"Điều khoản và lưu ý",
 "Open-source licenses":"Giấy phép mã nguồn mở",
 "Guide summary":"Các chức năng chính của ứng dụng",
 "Terms summary":"Quyền sử dụng và trách nhiệm",
 "Licenses summary":"MIT và thông tin các thành phần liên quan",
 "Guide article":("1. Đăng nhập Apple ID có quyền tải ứng dụng. Vùng App Store được nhận theo tài khoản.\n\n"
                  "2. Vào Khám phá, tìm bằng tên hoặc Bundle ID.\n\n"
                  "3. Chọn phiên bản và tải IPA. Phiên bản cũ không được bảo đảm tương thích với mọi iOS.\n\n"
                  "4. Mở IPA đã tải để xem chi tiết, sao chép Bundle ID, cài đặt, đổi tên, chia sẻ hoặc xuất sang Files.\n\n"
                  "5. Công cụ kiểm tra báo cấu trúc ZIP, SHA-256 và dấu hiệu mã hóa. IPA không mã hóa vẫn chưa chắc cài được bằng TrollStore."),
 "Third-party attribution":("Thành phần liên quan: ipatool (Majd Alfhaily) và appinst (angelXwind). "
                             "Tham khảo dự án gốc để biết điều khoản giấy phép tương ứng. "
                             "Ứng dụng độc lập, không liên kết hoặc được Apple bảo trợ."),
}
for code,vals in (("en",translations),("vi",vi)):
    table=root/"Resources"/(code+".lproj")/"Localizable.strings"
    content=table.read_text("utf-8")
    for k,v in vals.items():
        key=json.dumps(k,ensure_ascii=False)
        if key+" =" in content: continue
        content += f"{key} = {json.dumps(v,ensure_ascii=False)};\n"
    table.write_text(content,"utf-8")
print("v0.4.1: Native iOS About overview + three subpages + bottom credits and package version")
