#!/usr/bin/env python3
"""Install runtime switchable en/vi localization in IPARanger (UIKit/Theos).
No Apple ID data, keychain, IPA or runtime country preference is touched.
Add a new language by appending the translations and making a .lproj table.
"""
from pathlib import Path
import ast
import json
import sys

root=Path(sys.argv[1])
src=Path("build/iparanger/localize.py").read_text(encoding="utf-8")
tree=ast.parse(src)
mapping={}
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="replacements" for t in node.targets):
        mapping=ast.literal_eval(node.value)
assert mapping

# Original English text -> Vietnamese display text. v0.2 already replaced all these.
translations={}
for path,section in mapping.items():
    for en,vi in section.items():
        if en!=vi:
            translations[en]=vi
# v0.3 introduced new strings: add entries once, without editing translation engine.
translations.update({
  "Discover":"Khám phá",
  "Downloads":"IPA đã tải",
  "Account":"Tài khoản",
  "Language":"Ngôn ngữ",
  "App language":"Ngôn ngữ ứng dụng",
  "Language preference is saved on this iPhone.":"Lựa chọn ngôn ngữ được lưu trên iPhone này.",
  "Vietnamese":"Tiếng Việt",
  "English":"Tiếng Anh",
  "Search apps or Bundle ID":"Tìm ứng dụng hoặc Bundle ID",
  "Enter an app name to begin searching.":"Nhập tên ứng dụng để bắt đầu tìm kiếm.",
  "Sign in with Apple ID to browse the App Store.":"Đăng nhập Apple ID để khám phá App Store.",
  "Checking your Apple ID App Store region…":"Đang kiểm tra vùng App Store của Apple ID…",
  "App Store: %@":"App Store: %@",
  "App Store region could not be determined":"Chưa xác định được vùng App Store",
  "Could not read Apple ID region. Tap refresh to retry.":"Không đọc được vùng Apple ID. Chạm làm mới để thử lại.",
  "Please sign in with Apple ID to search.":"Vui lòng đăng nhập Apple ID để tìm kiếm.",
  "Searching App Store %@…":"Đang tìm trên App Store %@…",
  "Unable to load App Store catalog. Check your connection.":"Không thể tải danh mục App Store. Kiểm tra kết nối rồi thử lại.",
  "No apps found in your account's App Store region.":"Không tìm thấy ứng dụng trong vùng App Store của tài khoản.",
  "Paid app":"Ứng dụng có phí",
  "Displayed price: %@. Downloading may require an existing license or payment. Continue?":"Giá hiển thị: %@. Việc tải có thể yêu cầu giấy phép hoặc phát sinh thanh toán. Sếp có muốn tiếp tục?",
  "Continue":"Tiếp tục",
  "Select version":"Chọn phiên bản",
  "Copy Bundle ID":"Sao chép Bundle ID",
  "Cancel":"Hủy",
  "Fetching version history…":"Đang lấy lịch sử phiên bản…",
  "Apple ID country could not be determined. Sign in again or refresh.":"Không xác định được quốc gia của Apple ID. Vui lòng đăng nhập lại hoặc thử làm mới.",
  "No version history found in your account's App Store region.":"Không tìm thấy lịch sử phiên bản trong vùng App Store của tài khoản.",
  "No version history available.":"Không có lịch sử phiên bản khả dụng.",
  "Version":"Phiên bản",
  "Latest version":"Phiên bản mới nhất",
  "iOS requirement":"Yêu cầu iOS",
  "iOS requirement unavailable":"Chưa có dữ liệu iOS",
  "Unknown":"Không rõ",
  "Buy this app in App Store first.":"Hãy mua ứng dụng qua App Store trước.",
  "IPARanger\nError":"IPARanger\nLỗi",
  "IPARanger\nWarning":"IPARanger\nCảnh báo",
  "IPARanger\nCopy Bundle":"IPARanger\nSao chép Bundle ID",
  "IPARanger\nDownloading..":"IPARanger\nĐang tải…",
  "IPARanger\nSuccess!":"IPARanger\nThành công!",
  "IPARanger\nDelete File":"IPARanger\nXóa tệp",
  "IPARanger\nDelete Files":"IPARanger\nXóa tệp",
  "IPARanger\nRename File":"IPARanger\nĐổi tên tệp",
  "IPARanger\nLogout":"IPARanger\nĐăng xuất",
  "Install Application":"Cài đặt ứng dụng",
  "Open in Filza":"Mở bằng Filza",
  "Share":"Chia sẻ",
  "Delete":"Xóa",
  "Rename File":"Đổi tên tệp",
  "Account Storefront":"Vùng App Store của tài khoản",
  "iOS %@+":"iOS %@+",
  "%lu versions available":"Có %lu phiên bản",
})
# Existing v0.2 title / label direct replacements that aren't part of the mapping literal dictionary.
translations.update({
    "Search":"Tìm kiếm",
    "Download":"IPA đã tải",
    "Account":"Tài khoản",
    "Last login":"Đăng nhập gần nhất",
    "Sign In":"Đăng nhập",
    "Log Out":"Đăng xuất",
    "Login":"Đăng nhập",
    "Select Version":"Chọn phiên bản",
    "Search versions":"Tìm phiên bản",
    "Show More Results":"Hiển thị thêm kết quả",
    "The current App Store release":"Bản đang phát hành trên App Store",
    "Unknown version":"Không rõ phiên bản",
    "You can still download the latest version.":"Sếp vẫn có thể tải phiên bản mới nhất.",
    "The download finished successfully!":"Tải IPA thành công!",
})
# Use legacy Vietnamese strings as aliases, so even existing constant display strings
# and generic IPARDialog wrappers can translate them without modifying command constants.
both={}
for english,viet in translations.items():
    both[english]=(english,viet)
    both[viet]=(english,viet)

def quote_objc(v):
    return '@'+json.dumps(v,ensure_ascii=False)

def escape_strings(v):
    return json.dumps(v,ensure_ascii=False)

# Collect every translation entry into both target-language tables.
for code,index in (("en",0),("vi",1)):
    dest=root/"Resources"/(code+".lproj")
    dest.mkdir(parents=True,exist_ok=True)
    table=dest/"Localizable.strings"
    table.write_text("/* IPARanger VN - UTF-8. Keys are stable display strings; do not use in backend commands. */\n"+
                     "\n".join(f"{escape_strings(k)} = {escape_strings(pair[index])};" for k,pair in sorted(both.items()))+"\n",encoding="utf-8")

# Language manager is a first-party Utils class; Makefile already includes IPAR*.m automatically.
(root/"Utils/IPARLanguageManager.h").write_text(r'''#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>

FOUNDATION_EXPORT NSString *IPARL(NSString *key);

@interface IPARLanguageManager : NSObject
+ (NSString *)languageCode;
+ (void)setLanguageCode:(NSString *)code;
+ (NSString *)displayNameForCode:(NSString *)code;
+ (void)rebuildMainTabsFromController:(UIViewController *)controller;
@end
''',encoding="utf-8")

(root/"Utils/IPARLanguageManager.m").write_text(r'''#import "IPARLanguageManager.h"
#import "../Controllers/IPARSearchViewController.h"
#import "../Controllers/IPARDownloadViewController.h"
#import "../Controllers/IPARAccountAndCreditsController.h"

static NSString *const kIPARLanguagePreference = @"Sentechtips.IPARanger.Language";

@implementation IPARLanguageManager
+ (NSString *)languageCode {
    NSString *stored = [[NSUserDefaults standardUserDefaults] stringForKey:kIPARLanguagePreference];
    if ([stored isEqualToString:@"en"] || [stored isEqualToString:@"vi"]) return stored;
    NSString *locale = NSLocale.preferredLanguages.firstObject ?: @"vi";
    return [[locale lowercaseString] hasPrefix:@"vi"] ? @"vi" : @"en";
}
+ (void)setLanguageCode:(NSString *)code {
    if (![code isEqualToString:@"vi"] && ![code isEqualToString:@"en"]) return;
    [[NSUserDefaults standardUserDefaults] setObject:code forKey:kIPARLanguagePreference];
}
+ (NSString *)displayNameForCode:(NSString *)code {
    return [code isEqualToString:@"vi"] ? @"Tiếng Việt" : @"English";
}
+ (void)rebuildMainTabsFromController:(UIViewController *)controller {
    UITabBarController *tabs = controller.tabBarController;
    if (!tabs) return;
    IPARSearchViewController *search = [[IPARSearchViewController alloc] init];
    IPARDownloadViewController *downloads = [[IPARDownloadViewController alloc] init];
    IPARAccountAndCredits *account = [[IPARAccountAndCredits alloc] init];
    tabs.viewControllers = @[
       [[UINavigationController alloc] initWithRootViewController:search],
       [[UINavigationController alloc] initWithRootViewController:downloads],
       [[UINavigationController alloc] initWithRootViewController:account]
    ];
    tabs.selectedIndex = 2;
}
@end

NSString *IPARL(NSString *key) {
    if (![key isKindOfClass:[NSString class]] || key.length == 0) return key;
    NSString *code = [IPARLanguageManager languageCode];
    NSString *path = [[NSBundle mainBundle] pathForResource:code ofType:@"lproj"];
    NSBundle *bundle = path ? [NSBundle bundleWithPath:path] : nil;
    if (!bundle) return key;
    return [bundle localizedStringForKey:key value:key table:@"Localizable"];
}
''',encoding="utf-8")

(root/"Controllers/IPARLanguagePickerViewController.h").write_text(r'''#import <UIKit/UIKit.h>
@interface IPARLanguagePickerViewController : UITableViewController
@end
''',encoding="utf-8")
(root/"Controllers/IPARLanguagePickerViewController.m").write_text(r'''#import "IPARLanguagePickerViewController.h"
#import "../Utils/IPARLanguageManager.h"

@implementation IPARLanguagePickerViewController
- (instancetype)init {
    self=[super initWithStyle:UITableViewStyleInsetGrouped];
    if (self) self.title=IPARL(@"Language");
    return self;
}
- (void)viewDidLoad {
    [super viewDidLoad];
    self.tableView.backgroundColor=UIColor.systemGroupedBackgroundColor;
    UILabel *footer=[[UILabel alloc] initWithFrame:CGRectMake(0,0,self.tableView.bounds.size.width,75)];
    footer.numberOfLines=0;
    footer.textAlignment=NSTextAlignmentCenter;
    footer.textColor=UIColor.secondaryLabelColor;
    footer.font=[UIFont systemFontOfSize:13];
    footer.text=IPARL(@"Language preference is saved on this iPhone.");
    self.tableView.tableFooterView=footer;
}
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section { return 2; }
- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath {
    UITableViewCell *cell=[tableView dequeueReusableCellWithIdentifier:@"LanguageRow"];
    if (!cell) cell=[[UITableViewCell alloc] initWithStyle:UITableViewCellStyleDefault reuseIdentifier:@"LanguageRow"];
    NSString *code=indexPath.row == 0 ? @"vi" : @"en";
    cell.textLabel.text=[IPARLanguageManager displayNameForCode:code];
    cell.accessoryType=[[IPARLanguageManager languageCode] isEqualToString:code] ?
        UITableViewCellAccessoryCheckmark : UITableViewCellAccessoryNone;
    cell.tintColor=UIColor.systemGreenColor;
    return cell;
}
- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath {
    [tableView deselectRowAtIndexPath:indexPath animated:YES];
    NSString *code=indexPath.row == 0 ? @"vi" : @"en";
    if ([[IPARLanguageManager languageCode] isEqualToString:code]) return;
    [IPARLanguageManager setLanguageCode:code];
    [IPARLanguageManager rebuildMainTabsFromController:self];
}
@end
''',encoding="utf-8")

# Account language card is shown in the account tab above the logout action.
account=root/"Controllers/IPARAccountAndCreditsController.m"
s=account.read_text("utf-8")
anchor='#import "../Views/IPARDialog.h"'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'\n#import "../Utils/IPARLanguageManager.h"\n#import "IPARLanguagePickerViewController.h"')
anchor='[stack addArrangedSubview:[self makeLogoutButton]];'
assert s.count(anchor)==1
s=s.replace(anchor,'[stack addArrangedSubview:[self makeLanguageCard]];\n    '+anchor)
anchor='#pragma mark - Logout button'
assert s.count(anchor)==1
s=s.replace(anchor,r'''- (UIView *)makeLanguageCard {
    NSString *current=[IPARLanguageManager displayNameForCode:[IPARLanguageManager languageCode]];
    return [self cardWithRows:@[
        [self linkRowWithImageNamed:@"globe" title:[NSString stringWithFormat:@"%@ · %@",
            IPARL(@"Language"),current] action:@selector(showLanguagePicker)]
    ] separatorInset:56];
}
- (void)showLanguagePicker {
    IPARLanguagePickerViewController *picker=[[IPARLanguagePickerViewController alloc] init];
    [self.navigationController pushViewController:picker animated:YES];
}

'''+anchor)
# Existing link-row builder supports named bitmaps; allow SF Symbols fallback for new globe row.
s=s.replace('[[UIImageView alloc] initWithImage:[UIImage imageNamed:imageName]]',
            '[[UIImageView alloc] initWithImage:([UIImage imageNamed:imageName] ?: [UIImage systemImageNamed:imageName])]')
# Restore localized text on controller creation. Generic labels pass through the translation engine.
s=s.replace('self.title = @"Tài khoản";','self.title = IPARL(@"Account");')
s=s.replace('self.tabBarItem.title = @"Tài khoản";','self.tabBarItem.title = IPARL(@"Account");')
s=s.replace('label.text = text;','label.text = IPARL(text);')
# UI titles in buttons are localized using IPARL without changing their selectors.
s=s.replace('[button setTitle:@"Đăng nhập" forState:UIControlStateNormal]', '[button setTitle:IPARL(@"Sign In") forState:UIControlStateNormal]')
s=s.replace('[button setTitle:@"Đăng xuất" forState:UIControlStateNormal]', '[button setTitle:IPARL(@"Log Out") forState:UIControlStateNormal]')
account.write_text(s,encoding="utf-8")

# Convert already translated visible ObjC literals in controller implementations
# to runtime language function calls. Do not touch string constants in header files.
for path in mapping:
    if not path.endswith(".m"):continue
    file=root/path
    if not file.exists():continue
    s=file.read_text("utf-8")
    for en,vi in mapping[path].items():
        if en==vi:continue
        old=quote_objc(vi)
        new="IPARL("+quote_objc(en)+")"
        s=s.replace(old,new)
    if 'IPARL(' in s and "IPARLanguageManager.h" not in s:
        s='#import "../Utils/IPARLanguageManager.h"\n'+s
    file.write_text(s,"utf-8")

# Convert v0.3 catalog's main visible strings to live localized texts.
cat=root/"Controllers/IPARSearchViewController.m"
s=cat.read_text("utf-8")
for en,vi in translations.items():
    if en == vi: continue
    old=quote_objc(vi)
    if old in s:
        s=s.replace(old,"IPARL("+quote_objc(en)+")")
if "IPARLanguageManager.h" not in s:
    s='#import "../Utils/IPARLanguageManager.h"\n'+s
cat.write_text(s,"utf-8")

# Version picker uses a modern grouped list; localize its labels and date/count strings.
picker=root/"Controllers/IPARVersionPickerViewController.m"
s=picker.read_text("utf-8")
for en,vi in translations.items():
    if en==vi: continue
    old=quote_objc(vi)
    if old in s:s=s.replace(old,"IPARL("+quote_objc(en)+")")
if "IPARLanguageManager.h" not in s:
    s='#import "../Utils/IPARLanguageManager.h"\n'+s
# Explicit localized formatted count.
s=s.replace('@"Có %lu phiên bản"', 'IPARL(@"%lu versions available")')
picker.write_text(s,encoding="utf-8")

# Runtime dialog layer catches strings from constants as well as English alert buttons.
dialog=root/"Views/IPARDialog.m"
s=dialog.read_text("utf-8")
s='#import "../Utils/IPARLanguageManager.h"\n'+s
s=s.replace('[[self alloc] init]', '[[self alloc] init]')  # no-op
# dialogWithTitle sets title + message in setters; translate at construction time.
s=s.replace('dialog.titleText = title;', 'dialog.titleText = IPARL(title);')
s=s.replace('dialog.messageText = message;', 'dialog.messageText = IPARL(message);')
s=s.replace('[button setTitle:title forState:UIControlStateNormal];',
            '[button setTitle:IPARL(title) forState:UIControlStateNormal];')
dialog.write_text(s,"utf-8")
# If the original project uses different ivar names, fail loudly rather than silently.
assert 'IPARL(title)' in s and 'IPARL(message)' in s

# Apply localizable titles for other main screens that used hardcoded values in v0.2.
download=root/"Controllers/IPARDownloadViewController.m"
s=download.read_text("utf-8")
s=s.replace('self.title = @"IPA đã tải";','self.title = IPARL(@"Downloads");')
s=s.replace('self.tabBarItem.title = @"IPA đã tải";','self.tabBarItem.title = IPARL(@"Downloads");')
download.write_text(s,"utf-8")

# Account/Download constants can still pass untranslated in custom strings; the dialog
# adapter uses the translated aliases generated in both language tables.
print("Installed runtime localization with",len(translations),"English translation keys and 2 .lproj tables.")
