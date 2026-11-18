#!/usr/bin/env python3
"""Replace legacy IPA action sheet with a native details page, preserving exact actions."""
from pathlib import Path
import json,sys
root=Path(sys.argv[1])
p=root/"Controllers/IPARDownloadViewController.m"
s=p.read_text("utf-8")
def once(before,after,name):
    global s
    n=s.count(before)
    assert n==1,f"{name}: expected 1 match, got {n}"
    s=s.replace(before,after,1)
once('#import "IPARVersionPickerViewController.h"',
     '#import "IPARVersionPickerViewController.h"\n#import "IPARIPADetailViewController.h"', "detail controller import")
start=s.index("- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath {")
end=s.index("- (BOOL)refreshSpringBoardIconsAfterInstall {",start)
assert end>start and s.count("- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:")==1
new=r'''- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath {
    [tableView deselectRowAtIndexPath:indexPath animated:YES];
    if (indexPath.row >= self.existingApps.count) return;
    NSDictionary *item = [self.existingApps[indexPath.row] copy];
    NSString *fileName = [item[kFilenameIndex] copy];
    if (![fileName isKindOfClass:[NSString class]] || !fileName.length) return;
    NSString *displayName = [item[kAppnameIndex] isKindOfClass:[NSString class]] ?
                          item[kAppnameIndex] : fileName;
    NSString *size = [item[kSizeIndex] isKindOfClass:[NSString class]] ?
                     item[kSizeIndex] : @"—";
    UIImage *image = [item[kAppimageIndex] isKindOfClass:[UIImage class]] ?
                     item[kAppimageIndex] : [UIImage systemImageNamed:@"square.stack.3d.up"];
    IPARIPADetailViewController *detail =
        [[IPARIPADetailViewController alloc] initWithName:displayName
                                                  fileName:fileName size:size icon:image];
    __weak typeof(self) weakSelf = self;
    __weak typeof(detail) weakDetail = detail;
    detail.onInstall = ^{
        [weakSelf installApplication:fileName appName:displayName];
    };
    detail.onOpenInFilza = ^{
        [weakSelf openInFilza:[kIPARangerDocumentsPath stringByAppendingString:fileName]];
    };
    detail.onShare = ^{
        [weakSelf shareFile:fileName];
    };
    detail.onRename = ^{
        [weakSelf renameFileAtPath:fileName];
    };
    detail.onDelete = ^{
        NSInteger currentIndex = NSNotFound;
        for (NSUInteger i=0; i<weakSelf.existingApps.count; ++i) {
            if ([weakSelf.existingApps[i][kFilenameIndex] isEqualToString:fileName]) {
                currentIndex=(NSInteger)i;
                break;
            }
        }
        if (currentIndex == NSNotFound) return;
        // Pop first so the existing confirmation appears in the library, not
        // behind the details controller; preserve the existing delete logic.
        [weakDetail.navigationController popViewControllerAnimated:YES];
        [weakSelf deleteFile:fileName
                      index:[NSIndexPath indexPathForRow:currentIndex inSection:0]];
    };
    [self.navigationController pushViewController:detail animated:YES];
}

'''
s=s[:start]+new+s[end:]
# No change to download commands or IPA directory. Keep delete, rename and install routines.
assert 'kDownloadCommandBundleVersionOutputpathCountry' in s
assert '[self startDownloadForBundleID:bundleID' in s
assert 'refreshSpringBoardIconsAfterInstall' in s
p.write_text(s,"utf-8")

(root/"Controllers/IPARIPADetailViewController.h").write_text(r'''#import <UIKit/UIKit.h>
@interface IPARIPADetailViewController : UITableViewController
@property (nonatomic, copy) void (^onInstall)(void);
@property (nonatomic, copy) void (^onOpenInFilza)(void);
@property (nonatomic, copy) void (^onShare)(void);
@property (nonatomic, copy) void (^onRename)(void);
@property (nonatomic, copy) void (^onDelete)(void);
- (instancetype)initWithName:(NSString *)name fileName:(NSString *)fileName
                        size:(NSString *)size icon:(UIImage *)icon;
@end
''',"utf-8")
(root/"Controllers/IPARIPADetailViewController.m").write_text(r'''#import "IPARIPADetailViewController.h"
#import "../Utils/IPARLanguageManager.h"

@interface IPARIPADetailViewController ()
@property (nonatomic, copy) NSString *appName;
@property (nonatomic, copy) NSString *fileName;
@property (nonatomic, copy) NSString *humanSize;
@property (nonatomic, strong) UIImage *appIcon;
@property (nonatomic, copy) NSString *appVersion;
@property (nonatomic, copy) NSString *bundleIdentifier;
@end

@implementation IPARIPADetailViewController
- (instancetype)initWithName:(NSString *)name fileName:(NSString *)fileName
                        size:(NSString *)size icon:(UIImage *)icon {
    self=[super initWithStyle:UITableViewStyleInsetGrouped];
    if (!self) return nil;
    self.title=IPARL(@"IPA details");
    self.appName=[name copy] ?: @"IPA";
    self.fileName=[fileName copy] ?: @"";
    self.humanSize=[size copy] ?: @"—";
    self.appIcon=icon;
    NSString *base=[self.fileName stringByDeletingPathExtension];
    NSArray<NSString *> *tokens=[base componentsSeparatedByString:@"_"];
    self.appVersion=@"—";
    self.bundleIdentifier=@"—";
    if (tokens.count>=3) {
        NSString *candidateVersion=tokens.lastObject;
        NSString *numericID=tokens[tokens.count-2];
        NSCharacterSet *digits=[NSCharacterSet decimalDigitCharacterSet];
        NSCharacterSet *versionChars=[NSCharacterSet characterSetWithCharactersInString:@"0123456789."];
        NSString *bundle=[[tokens subarrayWithRange:NSMakeRange(0,tokens.count-2)] componentsJoinedByString:@"_"];
        if (numericID.length && [numericID rangeOfCharacterFromSet:digits.invertedSet].location==NSNotFound
            && candidateVersion.length
            && [candidateVersion rangeOfCharacterFromSet:versionChars.invertedSet].location==NSNotFound
            && [bundle containsString:@"."]) {
            self.appVersion=candidateVersion;
            self.bundleIdentifier=bundle;
        }
    }
    return self;
}
- (void)viewDidLoad {
    [super viewDidLoad];
    self.tableView.backgroundColor=UIColor.systemGroupedBackgroundColor;
    self.tableView.rowHeight=UITableViewAutomaticDimension;
    self.tableView.estimatedRowHeight=64;
}
- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView { return 3; }
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return section == 0 ? 1 : section == 1 ? 4 : 5;
}
- (NSString *)tableView:(UITableView *)tableView titleForHeaderInSection:(NSInteger)section {
    if (section==1) return IPARL(@"File information");
    if (section==2) return IPARL(@"Actions");
    return nil;
}
- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)index {
    UITableViewCell *cell=[[UITableViewCell alloc] initWithStyle:UITableViewCellStyleSubtitle reuseIdentifier:nil];
    cell.backgroundColor=UIColor.secondarySystemGroupedBackgroundColor;
    cell.textLabel.numberOfLines=2;
    cell.detailTextLabel.numberOfLines=(index.section==1 && index.row==3) ? 3 : 2;
    cell.detailTextLabel.textColor=UIColor.secondaryLabelColor;
    if (index.section==0) {
        cell.imageView.image=self.appIcon;
        cell.imageView.layer.cornerRadius=11;
        cell.imageView.layer.masksToBounds=YES;
        cell.textLabel.text=self.appName;
        cell.textLabel.font=[UIFont systemFontOfSize:18 weight:UIFontWeightSemibold];
        cell.detailTextLabel.text=[NSString stringWithFormat:@"%@ · %@",self.appVersion,self.humanSize];
        cell.selectionStyle=UITableViewCellSelectionStyleNone;
        return cell;
    }
    if (index.section==1) {
        NSString *keys[]={IPARL(@"Version"),IPARL(@"File size"),IPARL(@"Bundle ID"),IPARL(@"File name")};
        NSString *values[]={self.appVersion,self.humanSize,self.bundleIdentifier,self.fileName};
        cell.textLabel.text=keys[index.row];
        cell.detailTextLabel.text=values[index.row];
        cell.selectionStyle=UITableViewCellSelectionStyleNone;
        return cell;
    }
    NSString *actions[]={IPARL(@"Install Application"),IPARL(@"Open in Filza"),
                         IPARL(@"Share"),IPARL(@"Rename File"),IPARL(@"Delete")};
    NSString *icons[]={@"square.and.arrow.down",@"folder",@"square.and.arrow.up",
                       @"pencil",@"trash"};
    cell.textLabel.text=actions[index.row];
    cell.imageView.image=[UIImage systemImageNamed:icons[index.row]];
    cell.imageView.tintColor=(index.row==4)?UIColor.systemRedColor:UIColor.systemBlueColor;
    if (index.row==4) cell.textLabel.textColor=UIColor.systemRedColor;
    cell.accessoryType=UITableViewCellAccessoryDisclosureIndicator;
    return cell;
}
- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)index {
    [tableView deselectRowAtIndexPath:index animated:YES];
    if (index.section!=2) return;
    switch(index.row) {
        case 0:if(self.onInstall)self.onInstall();break;
        case 1:if(self.onOpenInFilza)self.onOpenInFilza();break;
        case 2:if(self.onShare)self.onShare();break;
        case 3:if(self.onRename)self.onRename();break;
        case 4:if(self.onDelete)self.onDelete();break;
        default:break;
    }
}
@end
''',"utf-8")
for code,index in (("en",0),("vi",1)):
    file=root/"Resources"/(code+".lproj")/"Localizable.strings"
    s=file.read_text("utf-8")
    tr={"IPA details":"Chi tiết IPA","File information":"Thông tin tệp","Actions":"Thao tác",
        "File size":"Dung lượng","File name":"Tên tệp","Bundle ID":"Bundle ID"}
    for key,vi in tr.items():
        k=json.dumps(key,ensure_ascii=False)
        if k+" =" not in s: s+=f"{k} = {json.dumps((key,vi)[index],ensure_ascii=False)};\n"
    file.write_text(s,"utf-8")
print("Replaced old download action sheet with detail page: install, Filza, share, rename and delete")
