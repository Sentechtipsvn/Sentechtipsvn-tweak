#!/usr/bin/env python3
"""IPA Manager Pro v0.4: searchable/sortable library, history log,
Files/iCloud export, non-destructive multiple versions.
Applied AFTER v0.3.3 and v04_audit.py.
"""
from pathlib import Path
import json,sys
root=Path(sys.argv[1])
def once(s,a,b,name):
    count=s.count(a)
    assert count==1,f"{name}: expected one anchor, found {count}"
    return s.replace(a,b,1)
(root/"Utils/IPARDiagnostics.h").write_text(r'''#import <Foundation/Foundation.h>
@interface IPARDiagnostics : NSObject
+ (void)recordEvent:(NSString *)event bundle:(NSString *)bundle;
+ (NSURL *)exportURL;
@end
''',"utf-8")
(root/"Utils/IPARDiagnostics.m").write_text(r'''#import "IPARDiagnostics.h"
#import "../Extensions/IPARConstants.h"
@implementation IPARDiagnostics
+ (NSURL *)exportURL {
    NSString *folder=[kIPARangerDocumentsPath stringByAppendingPathComponent:@"diagnostics"];
    return [NSURL fileURLWithPath:[folder stringByAppendingPathComponent:@"events.jsonl"]];
}
+ (void)recordEvent:(NSString *)event bundle:(NSString *)bundle {
    // Never record Apple ID, password, purchase token, raw ipatool stderr, or IPA bytes.
    static dispatch_queue_t queue;
    static dispatch_once_t once;
    dispatch_once(&once,^{queue=dispatch_queue_create("vn.sentechtips.iparanger.diagnostics",DISPATCH_QUEUE_SERIAL);});
    NSSet *allowed=[NSSet setWithArray:@[@"download_started",@"download_succeeded",@"download_failed",
        @"install_started",@"install_succeeded",@"install_failed",@"icons_refreshed",@"icons_refresh_failed"]];
    if (![allowed containsObject:event]) return;
    NSString *safeBundle=@"";
    if ([bundle isKindOfClass:NSString.class] && bundle.length<=200) {
        NSCharacterSet *valid=[NSCharacterSet characterSetWithCharactersInString:
                              @"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"];
        if ([bundle rangeOfCharacterFromSet:valid.invertedSet].location==NSNotFound) safeBundle=bundle;
    }
    dispatch_async(queue,^{
        NSURL *url=[self exportURL];
        NSFileManager *fm=NSFileManager.defaultManager;
        [fm createDirectoryAtURL:[url URLByDeletingLastPathComponent]
                 withIntermediateDirectories:YES attributes:nil error:nil];
        NSDictionary *obj=@{@"time":@([NSDate date].timeIntervalSince1970),
                             @"event":event,@"bundle":safeBundle};
        NSData *serialized=[NSJSONSerialization dataWithJSONObject:obj options:0 error:nil];
        if (!serialized) return;
        NSMutableData *line=[serialized mutableCopy];
        [line appendBytes:"\n" length:1];
        if (![fm fileExistsAtPath:url.path]) [fm createFileAtPath:url.path contents:nil attributes:nil];
        NSFileHandle *f=[NSFileHandle fileHandleForWritingAtPath:url.path];
        if (!f) return;
        @try {
            [f seekToEndOfFile];
            [f writeData:line];
        } @catch (NSException *error) {}
        [f closeFile];
    });
}
@end
''',"utf-8")

p=root/"Controllers/IPARDownloadViewController.m"
s=p.read_text("utf-8")
s=once(s,'#import "IPARIPADetailViewController.h"',
       '#import "IPARIPADetailViewController.h"\n#import "../Utils/IPARDiagnostics.h"',"diag import")
s=once(s,'@property (nonatomic) BOOL isRefreshing;',
       '''@property (nonatomic) BOOL isRefreshing;
@property (nonatomic, strong) UISearchController *ipaLibrarySearch;
@property (nonatomic, copy) NSString *ipaLibraryQuery;
@property (nonatomic) NSInteger ipaSortMode;''',"library props")
# Search via delegate. Preserve the rest of the UIViewController setup.
s=once(s,'    [self setupDownloadsMenu];',
'''    [self setupDownloadsMenu];
    self.ipaSortMode=0;
    self.ipaLibrarySearch=[[UISearchController alloc] initWithSearchResultsController:nil];
    self.ipaLibrarySearch.obscuresBackgroundDuringPresentation=NO;
    self.ipaLibrarySearch.searchResultsUpdater=(id<UISearchResultsUpdating>)self;
    self.ipaLibrarySearch.searchBar.placeholder=IPARL(@"Search downloaded IPAs");
    self.navigationItem.searchController=self.ipaLibrarySearch;
    self.navigationItem.hidesSearchBarWhenScrolling=YES;''',"search configuration")
# filter results without altering underlying array (important for delete/cache).
anchor='- (void)setupDownloadsMenu {'
s=once(s,anchor,r'''- (NSArray<NSDictionary *> *)displayedIPAItems {
    NSArray *original=[self.existingApps copy] ?: @[];
    NSString *query=[self.ipaLibraryQuery stringByTrimmingCharactersInSet:
                              NSCharacterSet.whitespaceAndNewlineCharacterSet];
    if (query.length) {
        original=[original filteredArrayUsingPredicate:[NSPredicate predicateWithBlock:
            ^BOOL(NSDictionary *row, NSDictionary *bindings) {
              NSString *name=[row[kAppnameIndex] isKindOfClass:NSString.class]?row[kAppnameIndex]:@"";
              NSString *file=[row[kFilenameIndex] isKindOfClass:NSString.class]?row[kFilenameIndex]:@"";
              return [name localizedCaseInsensitiveContainsString:query]
                  || [file localizedCaseInsensitiveContainsString:query];
            }]];
    }
    NSInteger sort=self.ipaSortMode;
    return [original sortedArrayUsingComparator:^NSComparisonResult(NSDictionary *a,NSDictionary *b) {
        NSString *fileA=a[kFilenameIndex]?:@"";
        NSString *fileB=b[kFilenameIndex]?:@"";
        if (sort==1 || sort==2) {
            NSString *pathA=[kIPARangerDocumentsPath stringByAppendingPathComponent:fileA];
            NSString *pathB=[kIPARangerDocumentsPath stringByAppendingPathComponent:fileB];
            NSDictionary *attrA=[NSFileManager.defaultManager attributesOfItemAtPath:pathA error:nil];
            NSDictionary *attrB=[NSFileManager.defaultManager attributesOfItemAtPath:pathB error:nil];
            if (sort==1) {
                NSDate *dateA=attrA[NSFileModificationDate]?:[NSDate distantPast];
                NSDate *dateB=attrB[NSFileModificationDate]?:[NSDate distantPast];
                NSComparisonResult result=[dateB compare:dateA];
                if (result!=NSOrderedSame) return result;
            } else {
                unsigned long long sizeA=[attrA[NSFileSize] unsignedLongLongValue];
                unsigned long long sizeB=[attrB[NSFileSize] unsignedLongLongValue];
                if (sizeA!=sizeB) return sizeA>sizeB?NSOrderedAscending:NSOrderedDescending;
            }
        }
        NSString *nameA=a[kAppnameIndex]?:fileA;
        NSString *nameB=b[kAppnameIndex]?:fileB;
        NSComparisonResult result=[nameA localizedStandardCompare:nameB];
        return result==NSOrderedSame?[fileA localizedStandardCompare:fileB]:result;
    }];
}
- (void)updateSearchResultsForSearchController:(UISearchController *)searchController {
    self.ipaLibraryQuery=searchController.searchBar.text;
    [self.tableView reloadData];
}
- (void)setIPASortMode:(NSInteger)sort {
    self.ipaSortMode=sort;
    [self.tableView reloadData];
}
- (void)exportIPADiagnostics {
    NSURL *url=[IPARDiagnostics exportURL];
    if (![[NSFileManager defaultManager] fileExistsAtPath:url.path]) {
        UIAlertController *a=[UIAlertController alertControllerWithTitle:IPARL(@"Diagnostics")
            message:IPARL(@"No diagnostic events yet") preferredStyle:UIAlertControllerStyleAlert];
        [a addAction:[UIAlertAction actionWithTitle:IPARL(@"OK") style:UIAlertActionStyleDefault handler:nil]];
        [self presentViewController:a animated:YES completion:nil];
        return;
    }
    UIActivityViewController *share=[[UIActivityViewController alloc] initWithActivityItems:@[url] applicationActivities:nil];
    share.popoverPresentationController.barButtonItem=self.navigationItem.leftBarButtonItem;
    [self presentViewController:share animated:YES completion:nil];
}
- (void)setupDownloadsMenu {''',"library filtering and diagnostics")
# Add sort menu and diagnostic export to existing menu.
anchor='''    UIMenu *menu = [UIMenu menuWithTitle:@""'''
replacement=r'''    __weak typeof(self) weakSelf=self;
    UIAction *nameSort=[UIAction actionWithTitle:IPARL(@"Sort by name") image:nil identifier:nil
        handler:^(__kindof UIAction *action){[weakSelf setIPASortMode:0];}];
    UIAction *dateSort=[UIAction actionWithTitle:IPARL(@"Sort by recent") image:nil identifier:nil
        handler:^(__kindof UIAction *action){[weakSelf setIPASortMode:1];}];
    UIAction *sizeSort=[UIAction actionWithTitle:IPARL(@"Sort by size") image:nil identifier:nil
        handler:^(__kindof UIAction *action){[weakSelf setIPASortMode:2];}];
    UIMenu *sortMenu=[UIMenu menuWithTitle:IPARL(@"Sort IPA library")
        image:[UIImage systemImageNamed:@"arrow.up.arrow.down"] identifier:nil
        options:0 children:@[nameSort,dateSort,sizeSort]];
    UIAction *diagnostics=[UIAction actionWithTitle:IPARL(@"Export diagnostics")
        image:[UIImage systemImageNamed:@"doc.text"] identifier:nil
        handler:^(__kindof UIAction *action){[weakSelf exportIPADiagnostics];}];

    UIMenu *menu = [UIMenu menuWithTitle:@""'''
s=once(s,anchor,replacement,"IPA sorting action")
s=once(s,'children:@[openInFilzaAction, deleteCacheAction]];',
          'children:@[sortMenu, diagnostics, openInFilzaAction, deleteCacheAction]];',"library menu")
# Keep original IPA array for deletes, use sorted and filtered copy for rendering.
s=once(s,'''    if (self.existingApps.count > 0) {
        self.noDataLabel.text = @" \\n  ";
        return self.existingApps.count;
    }''',
'''    NSArray *visible=[self displayedIPAItems];
    if (visible.count>0) {
        self.noDataLabel.text=@" ";
        return visible.count;
    }''',"table rows")
s=once(s,'self.noDataLabel.text = @"Nothing to show here.\\nStart by clicking the download icon!";',
'''self.noDataLabel.text=self.existingApps.count ? IPARL(@"No matches in IPA library"):
                            IPARL(@"No downloaded IPAs yet");''',"table empty state")
# Replace cell display only. The filename expression is used elsewhere
# for deletion and must NOT be globally replaced.
cellStart=s.index("- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:")
cellEnd=s.index("#pragma mark - Table View Delegate",cellStart)
cell=s[cellStart:cellEnd]
for k in ["kAppnameIndex","kFilenameIndex","kSizeIndex","kAppimageIndex"]:
    cell=once(cell,f"self.existingApps[indexPath.row][{k}]",f"[self displayedIPAItems][indexPath.row][{k}]",
              "library cell "+k)
s=s[:cellStart]+cell+s[cellEnd:]
s=once(s,'if (indexPath.row < self.existingApps.count) {',
       'if (indexPath.row < [self displayedIPAItems].count) {',"library cell bound")
# Detail source should use filtered list; deleting maps to original unfiltered list.
s=once(s,'if (indexPath.row >= self.existingApps.count) return;',
       'if (indexPath.row >= [self displayedIPAItems].count) return;',"library detail bound")
s=once(s,'NSDictionary *item = [self.existingApps[indexPath.row] copy];',
       'NSDictionary *item = [[self displayedIPAItems][indexPath.row] copy];',"library detail item")
# Swipe with filtered mapping and original source indices.
anchor='''    UIContextualAction *deleteAction = [UIContextualAction contextualActionWithStyle:UIContextualActionStyleDestructive'''
s=once(s,anchor,'''    NSArray *visible=[self displayedIPAItems];
    if (indexPath.row >= visible.count) return nil;
    NSDictionary *item=visible[indexPath.row];
    NSString *target=item[kFilenameIndex];
    NSUInteger originalIndex=[self.existingApps indexOfObjectPassingTest:^BOOL(id object,NSUInteger idx,BOOL *stop){
         return [object[kFilenameIndex] isEqualToString:target];
    }];
    if (originalIndex==NSNotFound) return nil;
    NSIndexPath *sourceIndex=[NSIndexPath indexPathForRow:originalIndex inSection:0];
    UIContextualAction *deleteAction = [UIContextualAction contextualActionWithStyle:UIContextualActionStyleDestructive''',"swipe mapped")
# Prior source used self.existingApps[indexPath.row] on swipe
s=once(s,'[self deleteFile:self.existingApps[indexPath.row][kFilenameIndex] index:indexPath];',
          '[self deleteFile:target index:sourceIndex];',"swipe delete safe mapping")
s=once(s,'[self shareFile:self.existingApps[indexPath.row][kFilenameIndex]];',
          '[self shareFile:target];',"swipe share safe mapping")
# After removing unfiltered source item, reload displayed list rather than an incompatible row animation.
s=once(s,'''        [self.existingApps removeObjectAtIndex:indexPath.row];
        [self.tableView deleteRowsAtIndexPaths:@[indexPath] withRowAnimation:UITableViewRowAnimationAutomatic];''',
'''        [self.existingApps removeObjectAtIndex:indexPath.row];
        [self.tableView reloadData];''',"single delete filtered source")
# bulk deletion: clear source then reload once
s=once(s,'''            [self.existingApps removeObjectAtIndex:indexPath.row];
            [self.tableView deleteRowsAtIndexPaths:@[indexPath] withRowAnimation:UITableViewRowAnimationAutomatic];''',
'''            [self.existingApps removeObjectAtIndex:indexPath.row];
            [self.tableView reloadData];''',"bulk delete filtered source")

# Existing stable backend unchanged apart from event recording at known points.
s=once(s,'''    self.lastBundleDownload = bundleID;
    [self showDownloadDialog];''',
'''    self.lastBundleDownload = bundleID;
    [IPARDiagnostics recordEvent:@"download_started" bundle:bundleID];
    [self showDownloadDialog];''',"download starts")
s=once(s,'''    if ([lastCommandResult[kJsonLevel] isEqualToString:kJsonLevelError]) {
       [self dismissViewControllerAnimated:YES completion:^{''',
'''    if ([lastCommandResult[kJsonLevel] isEqualToString:kJsonLevelError]) {
       [IPARDiagnostics recordEvent:@"download_failed" bundle:bundleID];
       [self dismissViewControllerAnimated:YES completion:^{''',"download early failure")
s=once(s,'''                if ([level isEqualToString:kJsonLevelError]) {
                    if ([jsonDict''',
'''                if ([level isEqualToString:kJsonLevelError]) {
                    [IPARDiagnostics recordEvent:@"download_failed" bundle:self.lastBundleDownload];
                    if ([jsonDict''',"download progress failure")
s=once(s,'''                } else if ([level isEqualToString:@"info"] && success) {
                    [self dismissViewControllerAnimated:YES completion:^{''',
'''                } else if ([level isEqualToString:@"info"] && success) {
                    [IPARDiagnostics recordEvent:@"download_succeeded" bundle:self.lastBundleDownload];
                    [self dismissViewControllerAnimated:YES completion:^{''',"download success")
# Existing install method has confirmed appinst success and optional uicache. Logs only after confirmation.
s=once(s,'''    AlertActionBlockWithTextField alertBlockConfirm = ^(UITextField *textField) {
        __block NSDictionary *standardAndErrorOutputs''',
'''    AlertActionBlockWithTextField alertBlockConfirm = ^(UITextField *textField) {
        [IPARDiagnostics recordEvent:@"install_started" bundle:appName];
        __block NSDictionary *standardAndErrorOutputs''',"install started")
s=once(s,'''if ([obj containsString:@"Successfully installed"]) {
                    BOOL iconsRefreshed=[self refreshSpringBoardIconsAfterInstall];''',
'''if ([obj containsString:@"Successfully installed"]) {
                    [IPARDiagnostics recordEvent:@"install_succeeded" bundle:appName];
                    BOOL iconsRefreshed=[self refreshSpringBoardIconsAfterInstall];
                    [IPARDiagnostics recordEvent:(iconsRefreshed?@"icons_refreshed":@"icons_refresh_failed") bundle:appName];''',"install success")
# Failing path after the success loop; log once.
needle='''            dispatch_async(dispatch_get_main_queue(), ^{
                    [self dismissViewControllerAnimated:YES completion:^{
                        [IPARUtils presentDialogWithTitle:kIPARangerErrorHeadline message:[NSString stringWithFormat:'''
assert needle in s
s=s.replace(needle,'''            [IPARDiagnostics recordEvent:@"install_failed" bundle:appName];
'''+needle,1)
p.write_text(s,"utf-8")

# Export directly to Files / iCloud without copying into another folder or losing the library.
p=root/"Controllers/IPARIPADetailViewController.m"
s=p.read_text("utf-8")
s=once(s,'#import "../Extensions/IPARConstants.h"',
       '#import "../Extensions/IPARConstants.h"\n#import "../Utils/IPARDiagnostics.h"',"detail export imports")
s=once(s,'    self.tableView.estimatedRowHeight=64;',
'''    self.tableView.estimatedRowHeight=64;
    self.navigationItem.rightBarButtonItem=[[UIBarButtonItem alloc]
        initWithImage:[UIImage systemImageNamed:@"square.and.arrow.up"]
        style:UIBarButtonItemStylePlain target:self action:@selector(saveToFiles)];''',"detail Files action")
s=once(s,'- (void)copyBundleIdentifier:(UIButton *)button {',
'''- (void)saveToFiles {
    NSString *path=[kIPARangerDocumentsPath stringByAppendingPathComponent:self.fileName];
    NSURL *url=[NSURL fileURLWithPath:path];
    if (![[NSFileManager defaultManager] fileExistsAtPath:path]) return;
    UIDocumentPickerViewController *picker=[[UIDocumentPickerViewController alloc]
        initForExportingURLs:@[url] asCopy:YES];
    picker.modalPresentationStyle=UIModalPresentationFormSheet;
    [self presentViewController:picker animated:YES completion:nil];
}
- (void)copyBundleIdentifier:(UIButton *)button {''',"Files/iCloud picker")
p.write_text(s,"utf-8")

for lang,index in (("en",0),("vi",1)):
    file=root/"Resources"/(lang+".lproj")/"Localizable.strings"
    content=file.read_text("utf-8")
    data={
        "Search downloaded IPAs":"Tìm IPA đã tải",
        "No matches in IPA library":"Không tìm thấy IPA phù hợp",
        "No downloaded IPAs yet":"Chưa có IPA được tải",
        "Sort by name":"Theo tên ứng dụng",
        "Sort by recent":"Mới tải gần đây",
        "Sort by size":"Theo dung lượng",
        "Sort IPA library":"Sắp xếp thư viện",
        "Export diagnostics":"Xuất nhật ký chẩn đoán",
        "Diagnostics":"Nhật ký chẩn đoán",
        "No diagnostic events yet":"Chưa có sự kiện chẩn đoán",
        "OK":"Đồng ý"
    }
    for english,vi in data.items():
        k=json.dumps(english,ensure_ascii=False)
        if k+" =" not in content:content+=f"{k} = {json.dumps((english,vi)[index],ensure_ascii=False)};\n"
    file.write_text(content,"utf-8")
print("v0.4 library: search/sort, versions coexist, Files/iCloud export, privacy-safe events and export")
