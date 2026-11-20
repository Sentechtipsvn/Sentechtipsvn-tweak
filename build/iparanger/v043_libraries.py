#!/usr/bin/env python3
"""v0.4.3 Separate on-device libraries: original Apple ID IPA and imported unencrypted IPA.

Keep the original library/controller untouched except for a 2-way selector.
Decrypted subfolder uses a separate metadata sidecar, never overwrites originals.
Manual import is explicitly labeled as 'unencrypted / source not proven decrypted'.
Only validated ZIP+Payload+clear Mach-O binaries can enter the secondary library.
No automatic decryption, private API injection or unverifiable TrollStore success.
"""
from pathlib import Path
import json,sys
root=Path(sys.argv[1])
p=root/"Controllers/IPARDownloadViewController.m"
s=p.read_text("utf-8")
assert s.count('#import "IPARIPADetailViewController.h"')==1
s=s.replace('#import "IPARIPADetailViewController.h"',
            '#import "IPARIPADetailViewController.h"\n#import "IPARVerifiedLibraryViewController.h"',1)
anchor='@implementation IPARDownloadViewController\n'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'''- (void)viewDidLoad {
    [super viewDidLoad];
    UISegmentedControl *switcher=[[UISegmentedControl alloc]
         initWithItems:@[IPARL(@"Apple ID IPAs"),IPARL(@"Unencrypted IPAs")]];
    switcher.selectedSegmentIndex=0;
    switcher.translatesAutoresizingMaskIntoConstraints=NO;
    [switcher addTarget:self action:@selector(showVerifiedIPALibrary:)
          forControlEvents:UIControlEventValueChanged];
    UIView *header=[[UIView alloc] initWithFrame:CGRectMake(0,0,self.tableView.bounds.size.width,68)];
    header.autoresizingMask=UIViewAutoresizingFlexibleWidth;
    [header addSubview:switcher];
    [NSLayoutConstraint activateConstraints:@[
       [switcher.leadingAnchor constraintEqualToAnchor:header.leadingAnchor constant:15],
       [switcher.trailingAnchor constraintEqualToAnchor:header.trailingAnchor constant:-15],
       [switcher.topAnchor constraintEqualToAnchor:header.topAnchor constant:13],
       [switcher.heightAnchor constraintEqualToConstant:36]
    ]];
    self.tableView.tableHeaderView=header;
}
- (void)showVerifiedIPALibrary:(UISegmentedControl *)sender {
    if (sender.selectedSegmentIndex!=1) return;
    IPARVerifiedLibraryViewController *controller=[[IPARVerifiedLibraryViewController alloc] init];
    [self.navigationController pushViewController:controller animated:YES];
    sender.selectedSegmentIndex=0;
}
''',1)
p.write_text(s,"utf-8")

(root/"Controllers/IPARVerifiedLibraryViewController.h").write_text(r'''#import <UIKit/UIKit.h>
@interface IPARVerifiedLibraryViewController : UITableViewController
   <UIDocumentPickerDelegate, UIDocumentInteractionControllerDelegate, UISearchResultsUpdating>
@end
''',"utf-8")
(root/"Controllers/IPARVerifiedLibraryViewController.m").write_text(r'''#import "IPARVerifiedLibraryViewController.h"
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>
#import "IPARIPADetailViewController.h"
#import "../Utils/IPARIPAAudit.h"
#import "../Utils/IPARLanguageManager.h"
#import "../Utils/IPARUtils.h"
#import "../Extensions/IPARConstants.h"

@interface IPARVerifiedLibraryViewController ()
@property (nonatomic,strong) NSMutableArray<NSString *> *entries;
@property (nonatomic,strong) UISearchController *librarySearch;
@property (nonatomic,strong) UIDocumentInteractionController *documentInteraction;
@end
@implementation IPARVerifiedLibraryViewController

- (NSString *)verifiedDirectory {
    return [kIPARangerDocumentsPath stringByAppendingPathComponent:@"Decrypted"];
}
- (void)viewDidLoad {
    [super viewDidLoad];
    self.title=IPARL(@"Unencrypted IPAs");
    self.entries=[NSMutableArray array];
    self.tableView.backgroundColor=UIColor.systemGroupedBackgroundColor;
    self.tableView.rowHeight=82;
    self.navigationItem.rightBarButtonItem=[[UIBarButtonItem alloc] initWithBarButtonSystemItem:
         UIBarButtonSystemItemAdd target:self action:@selector(importIPA)];
    UISegmentedControl *tabs=[[UISegmentedControl alloc] initWithItems:
         @[IPARL(@"Apple ID IPAs"), IPARL(@"Unencrypted IPAs")]];
    tabs.selectedSegmentIndex=1;
    tabs.translatesAutoresizingMaskIntoConstraints=NO;
    [tabs addTarget:self action:@selector(libraryChanged:) forControlEvents:UIControlEventValueChanged];
    UIView *header=[[UIView alloc] initWithFrame:CGRectMake(0,0,self.tableView.bounds.size.width,68)];
    header.autoresizingMask=UIViewAutoresizingFlexibleWidth;
    [header addSubview:tabs];
    [NSLayoutConstraint activateConstraints:@[
      [tabs.leadingAnchor constraintEqualToAnchor:header.leadingAnchor constant:15],
      [tabs.trailingAnchor constraintEqualToAnchor:header.trailingAnchor constant:-15],
      [tabs.topAnchor constraintEqualToAnchor:header.topAnchor constant:13],
      [tabs.heightAnchor constraintEqualToConstant:36]
    ]];
    self.tableView.tableHeaderView=header;
    self.librarySearch=[[UISearchController alloc] initWithSearchResultsController:nil];
    self.librarySearch.obscuresBackgroundDuringPresentation=NO;
    self.librarySearch.searchResultsUpdater=self;
    self.librarySearch.searchBar.placeholder=IPARL(@"Search imported IPA files");
    self.navigationItem.searchController=self.librarySearch;
    self.navigationItem.hidesSearchBarWhenScrolling=YES;
    [self reloadLocalIPAs];
}
- (void)viewWillAppear:(BOOL)animated {
    [super viewWillAppear:animated];
    [self reloadLocalIPAs];
}
- (void)libraryChanged:(UISegmentedControl *)sender {
    if (sender.selectedSegmentIndex==0) [self.navigationController popViewControllerAnimated:YES];
}
- (void)showNotice:(NSString *)message title:(NSString *)title {
    UIAlertController *alert=[UIAlertController alertControllerWithTitle:title message:message
                             preferredStyle:UIAlertControllerStyleAlert];
    [alert addAction:[UIAlertAction actionWithTitle:IPARL(@"OK")
                                style:UIAlertActionStyleDefault handler:nil]];
    [self presentViewController:alert animated:YES completion:nil];
}
- (void)reloadLocalIPAs {
    NSFileManager *fm=NSFileManager.defaultManager;
    NSString *dir=self.verifiedDirectory;
    [fm createDirectoryAtPath:dir withIntermediateDirectories:YES attributes:nil error:nil];
    NSArray *contents=[fm contentsOfDirectoryAtPath:dir error:nil] ?: @[];
    NSMutableArray *entries=[NSMutableArray array];
    for (NSString *name in contents) {
        if (![name.pathExtension.lowercaseString isEqualToString:@"ipa"]) continue;
        NSString *path=[dir stringByAppendingPathComponent:name];
        NSDictionary *attributes=[fm attributesOfItemAtPath:path error:nil];
        if (![attributes[NSFileType] isEqualToString:NSFileTypeRegular]) continue;
        [entries addObject:name];
    }
    [entries sortUsingSelector:@selector(localizedStandardCompare:)];
    self.entries=entries;
    [self.tableView reloadData];
}
- (NSArray<NSString *> *)visibleEntries {
    NSString *query=[self.librarySearch.searchBar.text
        stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet];
    if (!query.length) return self.entries;
    NSPredicate *predicate=[NSPredicate predicateWithBlock:^BOOL(NSString *name,NSDictionary *bindings) {
        NSDictionary *info=[self metadataForName:name];
        return [name localizedCaseInsensitiveContainsString:query] ||
               [info[@"bundle"] localizedCaseInsensitiveContainsString:query] ||
               [info[@"original"] localizedCaseInsensitiveContainsString:query];
    }];
    return [self.entries filteredArrayUsingPredicate:predicate];
}
- (void)updateSearchResultsForSearchController:(UISearchController *)searchController {
    [self.tableView reloadData];
}
- (NSString *)pathForName:(NSString *)name {
    return [self.verifiedDirectory stringByAppendingPathComponent:name];
}
- (NSDictionary *)metadataForName:(NSString *)name {
    NSString *path=[[self pathForName:name] stringByDeletingPathExtension];
    NSDictionary *meta=[NSDictionary dictionaryWithContentsOfFile:
                           [path stringByAppendingPathExtension:@"plist"]];
    return [meta isKindOfClass:NSDictionary.class]?meta:@{};
}
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return [self visibleEntries].count;
}
- (NSString *)tableView:(UITableView *)tableView titleForHeaderInSection:(NSInteger)section {
    return IPARL(@"Manually imported, checked as unencrypted — not proof of decryption");
}
- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)index {
    UITableViewCell *cell=[[UITableViewCell alloc] initWithStyle:UITableViewCellStyleSubtitle reuseIdentifier:nil];
    NSArray *visible=[self visibleEntries];
    if (index.row>=visible.count) return cell;
    NSString *name=visible[index.row];
    NSDictionary *meta=[self metadataForName:name];
    cell.textLabel.text=meta[@"original"] ?: name;
    cell.textLabel.font=[UIFont systemFontOfSize:16 weight:UIFontWeightSemibold];
    NSDictionary *attrs=[NSFileManager.defaultManager attributesOfItemAtPath:
                          [self pathForName:name] error:nil];
    unsigned long long bytes=[attrs[NSFileSize] unsignedLongLongValue];
    cell.detailTextLabel.text=[NSString stringWithFormat:@"%@ · %@ · %.1f MB",
      meta[@"bundle"]?:@"IPA",IPARL(@"No Mach-O encryption found"),
      (double)bytes/1048576.0];
    cell.detailTextLabel.numberOfLines=2;
    cell.imageView.image=[UIImage systemImageNamed:@"lock.open"];
    cell.imageView.tintColor=UIColor.systemBlueColor;
    cell.accessoryType=UITableViewCellAccessoryDisclosureIndicator;
    return cell;
}
- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)index {
    [tableView deselectRowAtIndexPath:index animated:YES];
    NSArray *list=[self visibleEntries];
    if (index.row>=list.count) return;
    NSString *file=list[index.row];
    NSDictionary *meta=[self metadataForName:file];
    NSString *name=meta[@"original"] ?: file;
    NSString *full=[self pathForName:file];
    NSDictionary *attrs=[NSFileManager.defaultManager attributesOfItemAtPath:full error:nil];
    NSString *size=[NSString stringWithFormat:@"%.1f MB",[attrs[NSFileSize] doubleValue]/1048576.0];
    IPARIPADetailViewController *detail=[[IPARIPADetailViewController alloc]
           initWithName:name fileName:file size:size
                  icon:[UIImage systemImageNamed:@"lock.open"]
              fullPath:full decrypted:YES];
    __weak typeof(self) weakSelf=self;
    __weak typeof(detail) weakDetail=detail;
    detail.onTrollStore=^{[weakSelf handoffToTrollStore:full];};
    detail.onInstall=^{
        [weakSelf.navigationController popViewControllerAnimated:NO];
        [weakSelf installVerifiedIPAAtPath:full];
    };
    detail.onShare=^{
        [weakSelf.navigationController popViewControllerAnimated:NO];
        [weakSelf shareURL:[NSURL fileURLWithPath:full]];
    };
    detail.onOpenInFilza=^{[weakSelf openPathInFilza:full];};
    detail.onRename=^{
        [weakSelf.navigationController popViewControllerAnimated:NO];
        [weakSelf renameFile:file];
    };
    detail.onDelete=^{
        [weakDetail.navigationController popViewControllerAnimated:NO];
        [weakSelf confirmDeleteFile:file];
    };
    [self.navigationController pushViewController:detail animated:YES];
}
- (void)importIPA {
    UIDocumentPickerViewController *picker=[[UIDocumentPickerViewController alloc]
        initForOpeningContentTypes:@[UTTypeData] asCopy:YES];
    picker.delegate=self;
    picker.allowsMultipleSelection=NO;
    [self presentViewController:picker animated:YES completion:nil];
}
- (void)documentPicker:(UIDocumentPickerViewController *)controller didPickDocumentsAtURLs:(NSArray<NSURL *> *)urls {
    NSURL *url=urls.firstObject;
    if (!url) return;
    if (![url.pathExtension.lowercaseString isEqualToString:@"ipa"]) {
        [self showNotice:IPARL(@"Select a .ipa file") title:IPARL(@"Import IPA")];
        return;
    }
    NSString *temp=[NSTemporaryDirectory() stringByAppendingPathComponent:
          [NSString stringWithFormat:@"ipar-import-%@.ipa",NSUUID.UUID.UUIDString]];
    UIActivityIndicatorView *spinner=[[UIActivityIndicatorView alloc] initWithActivityIndicatorStyle:UIActivityIndicatorViewStyleLarge];
    spinner.center=self.view.center;
    spinner.autoresizingMask=UIViewAutoresizingFlexibleTopMargin|UIViewAutoresizingFlexibleBottomMargin|
                              UIViewAutoresizingFlexibleLeftMargin|UIViewAutoresizingFlexibleRightMargin;
    [self.view addSubview:spinner];
    [spinner startAnimating];
    self.view.userInteractionEnabled=NO;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY,0),^{
        BOOL scoped=[url startAccessingSecurityScopedResource];
        NSError *error=nil;
        BOOL copied=[NSFileManager.defaultManager copyItemAtURL:url toURL:[NSURL fileURLWithPath:temp] error:&error];
        if (scoped) [url stopAccessingSecurityScopedResource];
        NSDictionary *audit=copied?[IPARIPAAudit inspectFileAtPath:temp]:nil;
        BOOL valid=[audit[@"zip"] isEqualToString:@"valid"] &&
          [audit[@"structure"] isEqualToString:@"valid"] &&
          [audit[@"drm"] isEqualToString:@"clear"] &&
          [audit[@"bundle"] isKindOfClass:NSString.class] &&
          [audit[@"bundle"] length]>0 && [audit[@"executables"] integerValue]>0;
        NSError *moveError=nil;
        if (valid) {
            NSString *destination=[self.verifiedDirectory stringByAppendingPathComponent:
                 [NSString stringWithFormat:@"%@.ipa",NSUUID.UUID.UUIDString]];
            BOOL stored=[NSFileManager.defaultManager moveItemAtPath:temp toPath:destination error:&moveError];
            valid=stored;
            if (stored) {
                NSDictionary *meta=@{@"original":url.lastPathComponent ?: @"Imported.ipa",
                        @"bundle":audit[@"bundle"],@"version":audit[@"version"]?:@"",
                        @"sha":audit[@"sha"]?:@"", @"source":@"manual-import",
                        @"verified":@"no-macho-encryption-detected",
                        @"importedAt":@([NSDate date].timeIntervalSince1970)};
                NSString *plist=[[destination stringByDeletingPathExtension] stringByAppendingPathExtension:@"plist"];
                if (![meta writeToFile:plist atomically:YES]) {
                    [NSFileManager.defaultManager removeItemAtPath:destination error:nil];
                    valid=NO;
                }
            }
        }
        [NSFileManager.defaultManager removeItemAtPath:temp error:nil];
        dispatch_async(dispatch_get_main_queue(),^{
            [spinner stopAnimating];[spinner removeFromSuperview];
            self.view.userInteractionEnabled=YES;
            [self reloadLocalIPAs];
            if(valid) {
                [self showNotice:IPARL(@"Imported unencrypted IPA; signature and installability still unverified")
                           title:IPARL(@"Import completed")];
            } else {
                NSString *reason=IPARL(@"Unknown IPA validation failure");
                if(error || moveError) reason=(error?:moveError).localizedDescription;
                else if ([audit[@"zip"] isEqualToString:@"invalid"]) reason=IPARL(@"Invalid ZIP");
                else if (![audit[@"structure"] isEqualToString:@"valid"]) reason=IPARL(@"Missing or misplaced Payload");
                else if ([audit[@"drm"] isEqualToString:@"encrypted"]) reason=IPARL(@"FairPlay encrypted IPA cannot be imported to unencrypted library");
                else if (![audit[@"drm"] isEqualToString:@"clear"]) reason=IPARL(@"Mach-O encryption could not be verified");
                [self showNotice:reason title:IPARL(@"Import failed")];
            }
        });
    });
}
- (void)shareURL:(NSURL *)url {
    UIActivityViewController *share=[[UIActivityViewController alloc]
                  initWithActivityItems:@[url] applicationActivities:nil];
    share.popoverPresentationController.barButtonItem=self.navigationItem.rightBarButtonItem;
    [self presentViewController:share animated:YES completion:nil];
}
- (void)handoffToTrollStore:(NSString *)path {
    if (![NSFileManager.defaultManager fileExistsAtPath:path]) {
        [self showNotice:IPARL(@"IPA file not found") title:IPARL(@"TrollStore preflight")];
        return;
    }
    UIAlertController *prompt=[UIAlertController alertControllerWithTitle:IPARL(@"Open in TrollStore")
      message:IPARL(@"Choose TrollStore from the iOS Open In menu. This only transfers the IPA; installation is not confirmed and may fail due to signing or entitlements.")
      preferredStyle:UIAlertControllerStyleAlert];
    [prompt addAction:[UIAlertAction actionWithTitle:IPARL(@"Cancel") style:UIAlertActionStyleCancel handler:nil]];
    [prompt addAction:[UIAlertAction actionWithTitle:IPARL(@"Continue")
        style:UIAlertActionStyleDefault handler:^(UIAlertAction *a){
        NSURL *url=[NSURL fileURLWithPath:path];
        self.documentInteraction=[UIDocumentInteractionController interactionControllerWithURL:url];
        self.documentInteraction.delegate=self;
        if (![self.documentInteraction presentOpenInMenuFromRect:CGRectMake(self.view.bounds.size.width/2,0,1,1)
                                                           inView:self.view animated:YES]) {
            [self shareURL:url];
        }
    }]];
    [self presentViewController:prompt animated:YES completion:nil];
}
- (void)openPathInFilza:(NSString *)path {
    NSString *uri=[NSString stringWithFormat:@"%@%@",kFilzaScheme,path];
    NSURL *url=[NSURL URLWithString:[uri stringByAddingPercentEncodingWithAllowedCharacters:
                                     NSCharacterSet.URLFragmentAllowedCharacterSet]];
    if (!url) return;
    [UIApplication.sharedApplication openURL:url options:@{} completionHandler:^(BOOL ok) {
      if (!ok) [self showNotice:IPARL(@"Filza could not open this file")
                         title:IPARL(@"Error")];
    }];
}
- (void)installVerifiedIPAAtPath:(NSString *)path {
    // A validated unencrypted IPA can still fail signing/entitlement validation.
    NSString *name=path.lastPathComponent;
    UIAlertController *ask=[UIAlertController alertControllerWithTitle:IPARL(@"Install Application")
      message:IPARL(@"Run the existing appinst installer? This does not guarantee code-signing compatibility.")
      preferredStyle:UIAlertControllerStyleAlert];
    [ask addAction:[UIAlertAction actionWithTitle:IPARL(@"Cancel") style:UIAlertActionStyleCancel handler:nil]];
    [ask addAction:[UIAlertAction actionWithTitle:IPARL(@"Install Application") style:UIAlertActionStyleDefault
      handler:^(UIAlertAction *a){
        dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{
            // All imported IPA paths are UUID-based and contain only safe characters.
            NSCharacterSet *allowed=[NSCharacterSet characterSetWithCharactersInString:
                                      @"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./_-"];
            BOOL safe=([path rangeOfCharacterFromSet:allowed.invertedSet].location==NSNotFound);
            NSDictionary *out=safe?[IPARUtils setupTaskAndPipesWithCommand:
                         [NSString stringWithFormat:@"%@ %@",kAppinstScriptPath,path]]:nil;
            BOOL success=NO;
            for (id line in out[kstdOutput]) {
                if ([line isKindOfClass:NSString.class] && [line containsString:@"Successfully installed"]) {
                    success=YES;break;
                }
            }
            dispatch_async(dispatch_get_main_queue(),^{
                [self showNotice:success?
                   IPARL(@"appinst reported installation success. Confirm the app appears and opens normally."):
                   IPARL(@"appinst failed. IPA signature, entitlements, DRM or iOS compatibility may be the cause.")
                    title:success?IPARL(@"Install completed"):IPARL(@"Install failed")];
            });
        });
    }]];
    [self presentViewController:ask animated:YES completion:nil];
}
- (void)confirmDeleteFile:(NSString *)name {
    UIAlertController *ask=[UIAlertController alertControllerWithTitle:IPARL(@"Delete")
        message:IPARL(@"Delete this imported IPA and its metadata? The original Apple ID IPA library will not be changed.")
        preferredStyle:UIAlertControllerStyleAlert];
    [ask addAction:[UIAlertAction actionWithTitle:IPARL(@"Cancel") style:UIAlertActionStyleCancel handler:nil]];
    [ask addAction:[UIAlertAction actionWithTitle:IPARL(@"Delete") style:UIAlertActionStyleDestructive
        handler:^(UIAlertAction *a){
          NSString *file=[self pathForName:name];
          [NSFileManager.defaultManager removeItemAtPath:file error:nil];
          [NSFileManager.defaultManager removeItemAtPath:
             [[file stringByDeletingPathExtension] stringByAppendingPathExtension:@"plist"] error:nil];
          [self reloadLocalIPAs];
        }]];
    [self presentViewController:ask animated:YES completion:nil];
}
- (void)renameFile:(NSString *)name {
    UIAlertController *alert=[UIAlertController alertControllerWithTitle:IPARL(@"Rename File")
        message:IPARL(@"Enter a new IPA filename") preferredStyle:UIAlertControllerStyleAlert];
    [alert addTextFieldWithConfigurationHandler:^(UITextField *f){f.text=name;}];
    [alert addAction:[UIAlertAction actionWithTitle:IPARL(@"Cancel") style:UIAlertActionStyleCancel handler:nil]];
    [alert addAction:[UIAlertAction actionWithTitle:IPARL(@"Rename File")
      style:UIAlertActionStyleDefault handler:^(UIAlertAction *a) {
       NSString *target=alert.textFields.firstObject.text ?: @"";
       NSCharacterSet *safe=[NSCharacterSet characterSetWithCharactersInString:
                            @"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"];
       if (![target.pathExtension.lowercaseString isEqualToString:@"ipa"] ||
           [target rangeOfCharacterFromSet:safe.invertedSet].location!=NSNotFound ||
           target.length<5 || [target isEqualToString:@".."]) {
           [self showNotice:IPARL(@"Invalid IPA filename") title:IPARL(@"Error")];
           return;
       }
       NSString *old=[self pathForName:name], *new=[self pathForName:target];
       if ([NSFileManager.defaultManager fileExistsAtPath:new]) {
           [self showNotice:IPARL(@"A file with this name already exists") title:IPARL(@"Error")];
           return;
       }
       NSError *err=nil;
       if (![NSFileManager.defaultManager moveItemAtPath:old toPath:new error:&err]) {
           [self showNotice:err.localizedDescription title:IPARL(@"Error")];return;
       }
       NSString *former=[[old stringByDeletingPathExtension] stringByAppendingPathExtension:@"plist"];
       NSString *future=[[new stringByDeletingPathExtension] stringByAppendingPathExtension:@"plist"];
       if (![NSFileManager.defaultManager moveItemAtPath:former toPath:future error:&err]) {
           // Restore the source name rather than leave a metadata-less record.
           [NSFileManager.defaultManager moveItemAtPath:new toPath:old error:nil];
           [self showNotice:err.localizedDescription title:IPARL(@"Error")];return;
       }
       [self reloadLocalIPAs];
    }]];
    [self presentViewController:alert animated:YES completion:nil];
}
@end
''',"utf-8")
translations={
"Apple ID IPAs":"IPA từ Apple ID",
"Unencrypted IPAs":"IPA đã giải mã",
"Search imported IPA files":"Tìm IPA đã nhập",
"Manually imported, checked as unencrypted — not proof of decryption":"IPA nhập thủ công · không phát hiện mã hóa; chưa xác minh nguồn giải mã",
"No Mach-O encryption found":"Không phát hiện mã hóa Mach-O",
"Select a .ipa file":"Hãy chọn tệp .ipa",
"Import IPA":"Nhập IPA",
"Imported unencrypted IPA; signature and installability still unverified":"Đã nhập IPA không mã hóa. Chữ ký và khả năng cài đặt chưa được xác minh.",
"Import completed":"Nhập IPA thành công",
"Unknown IPA validation failure":"Không xác minh được IPA",
"Invalid ZIP":"Tệp ZIP không hợp lệ",
"Missing or misplaced Payload":"Thiếu hoặc sai cấp thư mục Payload",
"FairPlay encrypted IPA cannot be imported to unencrypted library":"IPA còn mã hóa FairPlay, không thể đưa vào thư viện IPA không mã hóa",
"Mach-O encryption could not be verified":"Không xác minh được trạng thái mã hóa Mach-O",
"Import failed":"Nhập IPA thất bại",
"IPA file not found":"Không tìm thấy tệp IPA",
"Open in TrollStore":"Mở bằng TrollStore",
"Choose TrollStore from the iOS Open In menu. This only transfers the IPA; installation is not confirmed and may fail due to signing or entitlements.":"Chọn TrollStore trong menu Mở bằng của iOS nếu có. Đây chỉ là chuyển tệp, không xác nhận cài thành công; chữ ký hoặc entitlement có thể gây lỗi.",
"Continue":"Tiếp tục",
"Filza could not open this file":"Filza không thể mở tệp này",
"Error":"Lỗi",
"Run the existing appinst installer? This does not guarantee code-signing compatibility.":"Cài bằng appinst hiện có? Tệp vẫn có thể không tương thích chữ ký hoặc quyền ứng dụng.",
"appinst reported installation success. Confirm the app appears and opens normally.":"appinst báo cài thành công. Vui lòng xác nhận ứng dụng xuất hiện và mở bình thường.",
"appinst failed. IPA signature, entitlements, DRM or iOS compatibility may be the cause.":"appinst không cài được. Có thể do chữ ký, entitlement, DRM hoặc iOS không tương thích.",
"Install completed":"Cài đặt hoàn tất",
"Install failed":"Cài đặt thất bại",
"Delete this imported IPA and its metadata? The original Apple ID IPA library will not be changed.":"Xóa IPA đã nhập cùng metadata? Không ảnh hưởng IPA trong thư viện Apple ID.",
"Enter a new IPA filename":"Nhập tên tệp IPA mới",
"Invalid IPA filename":"Tên tệp IPA không hợp lệ",
"A file with this name already exists":"Tệp cùng tên đã tồn tại"
}
for lang in ("en","vi"):
    file=root/"Resources"/(lang+".lproj")/"Localizable.strings"
    s=file.read_text("utf-8")
    for en,vi in translations.items():
        key=json.dumps(en,ensure_ascii=False)
        if key+" =" not in s:s+=f"{key} = {json.dumps(vi if lang=='vi' else en,ensure_ascii=False)};\n"
    file.write_text(s,"utf-8")
# Link UniformTypeIdentifiers used by the non-deprecated iOS 14+ picker.
makefile=root/"Makefile"
make=makefile.read_text("utf-8")
assert make.count("IPARanger_FRAMEWORKS = UIKit CoreGraphics")==1
make=make.replace("IPARanger_FRAMEWORKS = UIKit CoreGraphics",
                  "IPARanger_FRAMEWORKS = UIKit CoreGraphics UniformTypeIdentifiers",1)
makefile.write_text(make,"utf-8")
print("v0.4.3: separate Apple ID and manually imported clear-IPA folders; import/audit/install/Files/TrollStore handoff")
