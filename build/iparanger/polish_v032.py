#!/usr/bin/env python3
"""IPARanger VN v0.3.2: polished account, search region accessory and post-install icon refresh.

Apply AFTER localize.py, patch_catalog_v03.py, add_languages.py and polish_v031.py.
No changes to ipatool executable, account credentials, App Store country resolution, IPA files, or downloads.
Every anchor must match exactly once: fail closed on upstream source changes.
"""
from pathlib import Path
import json
import sys

root=Path(sys.argv[1])

def replace_once(code, before, after, location):
    count=code.count(before)
    assert count == 1, f"{location}: expected 1 anchor, found {count}: {before[:110]!r}"
    return code.replace(before,after,1)

def strings_literal(s):
    return json.dumps(s,ensure_ascii=False)

# 1) Keep the country code inside the same search field (native UISearchTextField accessory).
search=root/"Controllers/IPARSearchViewController.m"
s=search.read_text("utf-8")
s=replace_once(s,'@property (nonatomic, strong) UISearchController *searchController;',
'''@property (nonatomic, strong) UISearchController *searchController;
@property (nonatomic, strong) UILabel *storeCodeLabel;
@property (nonatomic, strong) UIButton *clearSearchButton;''',"Search accessory properties")
s=replace_once(s,'self.navigationItem.searchController = self.searchController;',
'''self.navigationItem.searchController = self.searchController;
    [self installCountrySearchAccessory];''',"Search accessory initialization")
s=replace_once(s,'- (void)dealloc {',
r'''// Right-side accessory retains the Apple-ID storefront code while editing.
// A dedicated clear control replaces UITextField's overlapping built-in clear button.
- (void)installCountrySearchAccessory {
    UISearchTextField *field = self.searchController.searchBar.searchTextField;
    UIView *container = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 80, 36)];
    UIButton *clear = [UIButton buttonWithType:UIButtonTypeSystem];
    clear.frame = CGRectMake(0, 0, 30, 36);
    [clear setImage:[UIImage systemImageNamed:@"xmark.circle.fill"] forState:UIControlStateNormal];
    clear.tintColor = [UIColor tertiaryLabelColor];
    [clear addTarget:self action:@selector(clearSearchText) forControlEvents:UIControlEventTouchUpInside];
    [container addSubview:clear];
    self.clearSearchButton = clear;
    UILabel *badge = [[UILabel alloc] initWithFrame:CGRectMake(32, 0, 48, 36)];
    badge.textAlignment = NSTextAlignmentCenter;
    badge.font = [UIFont systemFontOfSize:15 weight:UIFontWeightSemibold];
    badge.adjustsFontSizeToFitWidth = YES;
    badge.minimumScaleFactor = 0.8;
    badge.accessibilityLabel = IPARL(@"Account Storefront");
    [container addSubview:badge];
    self.storeCodeLabel = badge;
    field.clearButtonMode = UITextFieldViewModeNever;
    field.rightView = container;
    field.rightViewMode = UITextFieldViewModeAlways;
    [self updateCountrySearchAccessory];
}
- (void)updateCountrySearchAccessory {
    if (!self.storeCodeLabel) return;
    NSString *code = self.activeCountry;
    self.storeCodeLabel.text = (code.length == 2) ? code : @"—";
    self.storeCodeLabel.textColor = (code.length == 2) ? UIColor.systemBlueColor : UIColor.secondaryLabelColor;
    self.clearSearchButton.hidden = (self.searchController.searchBar.text.length == 0);
}
- (void)clearSearchText {
    self.searchController.searchBar.text = @"";
    [self.debounceTimer invalidate];
    [self requestSearch:@""];
    [self updateCountrySearchAccessory];
}
- (void)dealloc {''',"Search accessory methods")
s=replace_once(s,'self.activeCountry = nil;\n    self.requestGeneration++;',
'''self.activeCountry = nil;
    [self updateCountrySearchAccessory];
    self.requestGeneration++;''',"Clear account region badge on refresh")
s=replace_once(s,'self.navigationItem.prompt = [NSString stringWithFormat:@"App Store: %@", country];',
'''self.navigationItem.prompt = nil;
                [self updateCountrySearchAccessory];''',"Move active region from navigation prompt")
# In v0.3 the translated version of this string is IPARL(...) in add_languages.py.
bad_prompt='self.navigationItem.prompt = IPARL(@"App Store region could not be determined");'
assert bad_prompt in s, "Missing localized storefront failure prompt"
s=replace_once(s,bad_prompt,'''self.navigationItem.prompt = nil;
                [self updateCountrySearchAccessory];''',"Move failure prompt into accessory")
s=replace_once(s,'- (void)updateSearchResultsForSearchController:(UISearchController *)searchController {\n    [self scheduleSearch:searchController.searchBar.text];',
'''- (void)updateSearchResultsForSearchController:(UISearchController *)searchController {
    [self updateCountrySearchAccessory];
    [self scheduleSearch:searchController.searchBar.text];''',"Update built-in clear button")
search.write_text(s,"utf-8")

# 2) Move Language directly below Log Out, organize two-author menus.
account=root/"Controllers/IPARAccountAndCreditsController.m"
s=account.read_text("utf-8")
s=replace_once(s,'[stack addArrangedSubview:[self makeLanguageCard]];\n    [stack addArrangedSubview:[self makeLogoutButton]];',
'''[stack addArrangedSubview:[self makeLogoutButton]];
    [stack addArrangedSubview:[self makeLanguageCard]];''',"Move language card under Log Out")
anchor='#import "IPARLanguagePickerViewController.h"'
s=replace_once(s,anchor,anchor+'\n#import "IPARDeveloperLinksViewController.h"',"New author links controller import")
start=s.index("- (UIView *)makeLinksCard {")
end=s.index("#pragma mark - Credits footer",start)
assert s.count("- (UIView *)makeLinksCard {")==1 and end>start
s=s[:start]+r'''- (UIView *)makeLinksCard {
    NSArray<UIView *> *rows = @[
        [self linkRowWithImageNamed:kTwitterIcon title:IPARL(@"Follow on X")
                            action:@selector(showDeveloperX)],
        [self linkRowWithImageNamed:kPaypalIcon title:IPARL(@"Support Developers")
                            action:@selector(showDeveloperSupport)],
        [self linkRowWithImageNamed:kGithubIcon title:IPARL(@"Source code")
                            action:@selector(openGithub)],
    ];
    return [self cardWithRows:rows separatorInset:56];
}

'''+s[end:]
anchor='- (void)openTwitter { [IPARUtils openTW]; }\n- (void)openPaypal { [IPARUtils openPP]; }'
s=replace_once(s,anchor,r'''- (void)showDeveloperX {
    [self.navigationController pushViewController:
        [[IPARDeveloperLinksViewController alloc] initWithKind:IPARDeveloperLinksKindX]
                                     animated:YES];
}
- (void)showDeveloperSupport {
    [self.navigationController pushViewController:
        [[IPARDeveloperLinksViewController alloc] initWithKind:IPARDeveloperLinksKindSupport]
                                     animated:YES];
}''',"Author links navigation")
old='''    [stack addArrangedSubview:createdBy];'''
new='''    UILabel *vnFork = [self labelWithText:IPARL(@"Vietnamese fork by Sentechtipsvn")
                                     font:[UIFont systemFontOfSize:13 weight:UIFontWeightMedium]
                                    color:[UIColor secondaryLabelColor]];
    vnFork.textAlignment = NSTextAlignmentCenter;
    [stack addArrangedSubview:createdBy];
    [stack addArrangedSubview:vnFork];'''
s=replace_once(s,old,new,"Vietnamese fork attribution")
s=replace_once(s,'[stack setCustomSpacing:18 afterView:createdBy];',
'''[stack setCustomSpacing:18 afterView:vnFork];''',"Credits spacing")
# Normalize the last login locale to the selected in-app language, not the phone's locale.
anchor='[formatter setDateFormat:kDateFormatter];'
s=replace_once(s,anchor,'''formatter.locale = [NSLocale localeWithLocaleIdentifier:
      [[IPARLanguageManager languageCode] isEqualToString:@"en"] ? @"en_US" : @"vi_VN"];
    [formatter setDateFormat:kDateFormatter];''',"Last login language")
account.write_text(s,"utf-8")

# 3) New small native list: original developer + Sentechtipsvn.
(root/"Controllers/IPARDeveloperLinksViewController.h").write_text(r'''#import <UIKit/UIKit.h>
typedef NS_ENUM(NSInteger, IPARDeveloperLinksKind) {
    IPARDeveloperLinksKindX,
    IPARDeveloperLinksKindSupport
};
@interface IPARDeveloperLinksViewController : UITableViewController
- (instancetype)initWithKind:(IPARDeveloperLinksKind)kind;
@end
''',"utf-8")
(root/"Controllers/IPARDeveloperLinksViewController.m").write_text(r'''#import "IPARDeveloperLinksViewController.h"
#import "../Utils/IPARLanguageManager.h"

@interface IPARDeveloperLinksViewController ()
@property (nonatomic, assign) IPARDeveloperLinksKind kind;
@property (nonatomic, strong) NSArray<NSDictionary<NSString *, NSString *> *> *entries;
@end
@implementation IPARDeveloperLinksViewController
- (instancetype)initWithKind:(IPARDeveloperLinksKind)kind {
    self=[super initWithStyle:UITableViewStyleInsetGrouped];
    if (!self) return nil;
    self.kind=kind;
    self.title=IPARL(kind==IPARDeveloperLinksKindX ? @"Follow on X" : @"Support Developers");
    if (kind==IPARDeveloperLinksKindX) {
        self.entries=@[
           @{@"title":@"0xkuj",
             @"subtitle":IPARL(@"Original developer"),
             @"url":@"https://x.com/0xkuj"},
           @{@"title":@"Sentechtipsvn · @Sentechtipsvn1",
             @"subtitle":IPARL(@"Vietnamese fork developer"),
             @"url":@"https://x.com/Sentechtipsvn1"}
        ];
    } else {
        self.entries=@[
           @{@"title":@"0xkuj · PayPal",
             @"subtitle":IPARL(@"Original developer"),
             @"url":@"https://paypal.me/0xkuj"},
           @{@"title":@"Sentechtipsvn · Buy Me a Coffee",
             @"subtitle":IPARL(@"Vietnamese fork developer"),
             @"url":@"https://buymeacoffee.com/Sentechtipsvn"}
        ];
    }
    return self;
}
- (void)viewDidLoad {
    [super viewDidLoad];
    self.tableView.rowHeight=UITableViewAutomaticDimension;
    self.tableView.estimatedRowHeight=62;
    self.tableView.backgroundColor=UIColor.systemGroupedBackgroundColor;
}
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return self.entries.count;
}
- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath {
    UITableViewCell *cell=[tableView dequeueReusableCellWithIdentifier:@"DeveloperLink"];
    if (!cell) cell=[[UITableViewCell alloc] initWithStyle:UITableViewCellStyleSubtitle reuseIdentifier:@"DeveloperLink"];
    NSDictionary *entry=self.entries[indexPath.row];
    cell.textLabel.text=entry[@"title"];
    cell.textLabel.font=[UIFont systemFontOfSize:16 weight:UIFontWeightMedium];
    cell.detailTextLabel.text=entry[@"subtitle"];
    cell.detailTextLabel.textColor=UIColor.secondaryLabelColor;
    cell.accessoryType=UITableViewCellAccessoryDisclosureIndicator;
    return cell;
}
- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath {
    [tableView deselectRowAtIndexPath:indexPath animated:YES];
    NSString *address=self.entries[indexPath.row][@"url"];
    NSURL *url=[NSURL URLWithString:address];
    if (!url || ![url.scheme isEqualToString:@"https"]) return;
    [[UIApplication sharedApplication] openURL:url options:@{} completionHandler:nil];
}
@end
''',"utf-8")

# 4) Only after appinst confirms installation, refresh SpringBoard application icons.
downloads=root/"Controllers/IPARDownloadViewController.m"
s=downloads.read_text("utf-8")
install_anchor="- (void)installApplication:(NSString *)ipaFilePath appName:(NSString *)appName {"
method=r'''// uicache is shipped by jailbreak toolchains; it does not force a Respring.
// Run in the existing background install queue and retain truthful UI feedback.
- (BOOL)refreshSpringBoardIconsAfterInstall {
    NSFileManager *fm=[NSFileManager defaultManager];
    NSString *binary=nil;
    for (NSString *candidate in @[@"/var/jb/usr/bin/uicache", @"/usr/bin/uicache"]) {
        if ([fm isExecutableFileAtPath:candidate]) { binary=candidate; break; }
    }
    if (!binary) return NO;
    NSTask *task=[[NSTask alloc] init];
    task.launchPath=binary;
    task.arguments=@[@"-a"];
    task.standardOutput=[NSFileHandle fileHandleWithNullDevice];
    task.standardError=[NSFileHandle fileHandleWithNullDevice];
    @try {
        [task launch];
        [task waitUntilExit];
        return task.terminationStatus == 0;
    } @catch (NSException *exception) {
        NSLog(@"[IPARangerVN] uicache launch failed");
        return NO;
    }
}

'''
s=replace_once(s,install_anchor,method+install_anchor,"Refresh icon method")
success_anchor='''if ([obj containsString:@"Successfully installed"]) {
                    dispatch_async(dispatch_get_main_queue(), ^{'''
s=replace_once(s,success_anchor,'''if ([obj containsString:@"Successfully installed"]) {
                    BOOL iconsRefreshed=[self refreshSpringBoardIconsAfterInstall];
                    dispatch_async(dispatch_get_main_queue(), ^{''',"Refresh after appinst successful")
# v0.3.1 already localizes success string at runtime. Add explicit warning when the refresh fails.
msg='''message:[NSString stringWithFormat:IPARL(@"Successfully installed '%@'!"), appName]'''
if s.count(msg)!=1:
    raise AssertionError(f"Expected localized installed success literal exactly once; got {s.count(msg)}")
s=s.replace(msg,'''message:(iconsRefreshed
   ? [NSString stringWithFormat:IPARL(@"Successfully installed '%@'!"), appName]
   : [NSString stringWithFormat:IPARL(@"Installed '%@', but icons could not be refreshed. If the app is missing, try Respring."), appName])''')
downloads.write_text(s,"utf-8")

# 5) Add each display string to both localizations; no backend keys are localized.
new_strings={
    "Account Storefront":"Vùng App Store của tài khoản",
    "Follow on X":"Theo dõi trên X",
    "Support Developers":"Ủng hộ nhà phát triển",
    "Original developer":"Tác giả gốc",
    "Vietnamese fork developer":"Phát triển bản Việt hóa",
    "Vietnamese fork by Sentechtipsvn":"Bản Việt hóa và phát triển: Sentechtipsvn",
    "Installed '%@', but icons could not be refreshed. If the app is missing, try Respring.":
      "Đã cài “%@” nhưng không làm mới được biểu tượng. Nếu chưa thấy ứng dụng, hãy thử Respring."
}
for lang,index in (("en",0),("vi",1)):
    p=root/"Resources"/(lang+".lproj")/"Localizable.strings"
    data=p.read_text("utf-8")
    for english,vietnamese in new_strings.items():
        assert strings_literal(english)+" =" not in data, "Duplicate localization key: "+english
        data+=f"{strings_literal(english)} = {strings_literal((english,vietnamese)[index])};\n"
    p.write_text(data,"utf-8")

# Preserve vital behavior (no change to keys, auth, download, process and Apple-ID region).
constants=(root/"Extensions/IPARConstants.h").read_text("utf-8")
assert "kDownloadCommandBundleVersionOutputpathCountry" in constants
assert "kIpatoolScriptPath" in constants
assert "kAppVersionHistoryURL" in constants
print("v0.3.2 patched: search region in field, language order, two-author links, locale and uicache fallback")
