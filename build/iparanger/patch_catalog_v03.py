#!/usr/bin/env python3
"""Apply approved v0.3 catalog and direct version-selection navigation to the v0.2 tree."""
from pathlib import Path
import re
import sys

root=Path(sys.argv[1])
search=root/"Controllers/IPARSearchViewController.m"
search.write_text(r'''#import "IPARSearchViewController.h"
#import "IPARDownloadViewController.h"
#import "../Utils/IPARUtils.h"
#import "../Cells/IPARAppCell.h"
#import "../Extensions/IPARConstants.h"

@interface IPARSearchViewController () <UISearchResultsUpdating, UISearchBarDelegate>
@property (nonatomic, strong) UISearchController *searchController;
@property (nonatomic, strong) NSMutableArray<NSMutableDictionary *> *searchResults;
@property (nonatomic, strong) NSCache *iconCache;
@property (nonatomic, strong) UILabel *noDataLabel;
@property (nonatomic, strong) NSTimer *debounceTimer;
@property (nonatomic, copy) NSString *activeCountry;
@property (nonatomic, copy) NSString *currentTerm;
@property (nonatomic) NSInteger requestGeneration;
@property (nonatomic) BOOL resolvingCountry;
@end

@implementation IPARSearchViewController

- (instancetype)init {
    self = [super initWithStyle:UITableViewStylePlain];
    if (self) {
        self.title = @"Khám phá";
        self.tabBarItem.title = @"Khám phá";
        self.tabBarItem.image = [UIImage systemImageNamed:@"magnifyingglass"];
    }
    return self;
}

- (void)viewDidLoad {
    [super viewDidLoad];
    self.searchResults = [NSMutableArray array];
    self.iconCache = [[NSCache alloc] init];
    self.tableView.rowHeight = 86.0;
    self.tableView.backgroundColor = UIColor.systemBackgroundColor;
    self.tableView.separatorStyle = UITableViewCellSeparatorStyleNone;
    self.tableView.keyboardDismissMode = UIScrollViewKeyboardDismissModeOnDrag;
    self.noDataLabel = [[UILabel alloc] initWithFrame:self.tableView.bounds];
    self.noDataLabel.numberOfLines = 0;
    self.noDataLabel.textAlignment = NSTextAlignmentCenter;
    self.noDataLabel.textColor = UIColor.secondaryLabelColor;
    self.noDataLabel.text = @"Nhập tên ứng dụng để bắt đầu tìm kiếm.";
    self.tableView.backgroundView = self.noDataLabel;
    self.searchController = [[UISearchController alloc] initWithSearchResultsController:nil];
    self.searchController.searchResultsUpdater = self;
    self.searchController.searchBar.delegate = self;
    self.searchController.searchBar.placeholder = @"Tìm ứng dụng hoặc Bundle ID";
    self.searchController.obscuresBackgroundDuringPresentation = NO;
    self.navigationItem.searchController = self.searchController;
    self.navigationItem.hidesSearchBarWhenScrolling = NO;
    self.definesPresentationContext = YES;
    self.navigationItem.rightBarButtonItem = [[UIBarButtonItem alloc]
        initWithImage:[UIImage systemImageNamed:@"arrow.clockwise"]
        style:UIBarButtonItemStylePlain target:self action:@selector(refreshStorefront:)];
    [self resolveStorefront];
}

- (void)dealloc {
    [self.debounceTimer invalidate];
}

- (void)refreshStorefront:(id)sender {
    self.activeCountry = nil;
    [self.iconCache removeAllObjects];
    [self resolveStorefront];
}

- (void)resolveStorefront {
    if (self.resolvingCountry || [IPARUtils isGuestMode]) {
        if ([IPARUtils isGuestMode]) {
            self.noDataLabel.text = @"Đăng nhập Apple ID để khám phá App Store.";
        }
        return;
    }
    self.resolvingCountry = YES;
    self.noDataLabel.text = @"Đang kiểm tra vùng App Store của Apple ID…";
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSString *command = [NSString stringWithFormat:@"%@ auth info --keychain-passphrase IPARanger --format json",
                             kIpatoolScriptPath];
        NSDictionary *result = [IPARUtils executeCommandAndGetJSON:kLaunchPathBash
            arg1:kBashCommandKey arg2:command arg3:nil];
        id countryRaw = result[@"country"];
        NSString *country = [countryRaw isKindOfClass:[NSString class]] ? [countryRaw uppercaseString] : nil;
        NSCharacterSet *bad = [[NSCharacterSet characterSetWithCharactersInString:@"ABCDEFGHIJKLMNOPQRSTUVWXYZ"] invertedSet];
        if (country.length != 2 || [country rangeOfCharacterFromSet:bad].location != NSNotFound) country = nil;
        dispatch_async(dispatch_get_main_queue(), ^{
            self.resolvingCountry = NO;
            self.activeCountry = country;
            if (country) {
                self.navigationItem.prompt = [NSString stringWithFormat:@"App Store: %@", country];
                self.noDataLabel.text = @"Nhập tên ứng dụng để bắt đầu tìm kiếm.";
                if (self.searchController.searchBar.text.length) {
                    [self scheduleSearch:self.searchController.searchBar.text];
                }
            } else {
                self.navigationItem.prompt = @"Chưa xác định được vùng App Store";
                self.noDataLabel.text = @"Không đọc được vùng Apple ID. Chạm làm mới để thử lại.";
                [self.tableView reloadData];
            }
        });
    });
}

- (void)updateSearchResultsForSearchController:(UISearchController *)searchController {
    [self scheduleSearch:searchController.searchBar.text];
}

- (void)searchBarSearchButtonClicked:(UISearchBar *)searchBar {
    [self.debounceTimer invalidate];
    [self requestSearch:searchBar.text];
    [searchBar resignFirstResponder];
}

- (void)scheduleSearch:(NSString *)term {
    [self.debounceTimer invalidate];
    self.debounceTimer = [NSTimer scheduledTimerWithTimeInterval:0.45
        target:self selector:@selector(searchTimerFired:) userInfo:@{@"term":term ?: @""} repeats:NO];
}

- (void)searchTimerFired:(NSTimer *)timer {
    [self requestSearch:timer.userInfo[@"term"]];
}

- (void)requestSearch:(NSString *)query {
    NSString *term = [query stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet];
    self.currentTerm = term;
    NSInteger generation = ++self.requestGeneration;
    if (term.length == 0) {
        [self.searchResults removeAllObjects];
        self.noDataLabel.text = @"Nhập tên ứng dụng để bắt đầu tìm kiếm.";
        [self.tableView reloadData];
        return;
    }
    if ([IPARUtils isGuestMode]) {
        self.noDataLabel.text = @"Vui lòng đăng nhập Apple ID để tìm kiếm.";
        return;
    }
    if (self.activeCountry.length != 2) {
        if (!self.resolvingCountry) [self resolveStorefront];
        return;
    }
    self.noDataLabel.text = [NSString stringWithFormat:@"Đang tìm trên App Store %@…", self.activeCountry];
    NSURLComponents *parts = [NSURLComponents componentsWithString:
        ([term containsString:@"."] && [term rangeOfString:@" "].location == NSNotFound)
        ? @"https://itunes.apple.com/lookup" : @"https://itunes.apple.com/search"];
    BOOL byBundle = [parts.path isEqualToString:@"/lookup"];
    NSMutableArray *items = [NSMutableArray arrayWithObjects:
        [NSURLQueryItem queryItemWithName:@"country" value:self.activeCountry],
        [NSURLQueryItem queryItemWithName:@"media" value:@"software"],
        [NSURLQueryItem queryItemWithName:@"entity" value:@"software"], nil];
    if (byBundle) {
        [items addObject:[NSURLQueryItem queryItemWithName:@"bundleId" value:term]];
    } else {
        [items addObject:[NSURLQueryItem queryItemWithName:@"term" value:term]];
        [items addObject:[NSURLQueryItem queryItemWithName:@"limit" value:@"60"]];
    }
    parts.queryItems = items;
    NSURL *url = parts.URL;
    if (!url) return;
    NSURLSessionDataTask *task = [[NSURLSession sharedSession] dataTaskWithURL:url
        completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
        NSHTTPURLResponse *http = (NSHTTPURLResponse *)response;
        NSDictionary *payload = nil;
        if (!error && http.statusCode == 200 && data.length > 0) {
            id parsed = [NSJSONSerialization JSONObjectWithData:data options:0 error:nil];
            if ([parsed isKindOfClass:[NSDictionary class]]) payload = parsed;
        }
        NSArray *raw = [payload[@"results"] isKindOfClass:[NSArray class]] ? payload[@"results"] : nil;
        NSMutableArray *apps = [NSMutableArray array];
        for (id item in raw) {
            if (![item isKindOfClass:[NSDictionary class]]) continue;
            NSDictionary *app = (NSDictionary *)item;
            NSString *bundleID = [app[@"bundleId"] isKindOfClass:[NSString class]] ? app[@"bundleId"] : nil;
            NSString *name = [app[@"trackName"] isKindOfClass:[NSString class]] ? app[@"trackName"] : bundleID;
            if (bundleID.length == 0) continue;
            NSMutableDictionary *record = [NSMutableDictionary dictionary];
            record[kAppBundleIndex] = bundleID;
            record[kAppnameIndex] = name ?: bundleID;
            record[kAppVersionIndex] = [app[@"version"] isKindOfClass:[NSString class]] ? app[@"version"] : @"—";
            record[kAppimageIndex] = [UIImage systemImageNamed:kUnknownSystemImage] ?: [UIImage new];
            if ([app[@"trackId"] respondsToSelector:@selector(stringValue)]) record[@"trackId"] = app[@"trackId"];
            if ([app[@"artworkUrl100"] isKindOfClass:[NSString class]]) record[@"artworkURL"] = app[@"artworkUrl100"];
            if ([app[@"price"] respondsToSelector:@selector(doubleValue)]) record[@"price"] = app[@"price"];
            if ([app[@"formattedPrice"] isKindOfClass:[NSString class]]) record[@"formattedPrice"] = app[@"formattedPrice"];
            [apps addObject:record];
        }
        dispatch_async(dispatch_get_main_queue(), ^{
            if (self.requestGeneration != generation) return;
            self.searchResults = apps;
            if (!raw) {
                self.noDataLabel.text = @"Không thể tải danh mục App Store. Kiểm tra kết nối rồi thử lại.";
            } else {
                self.noDataLabel.text = apps.count ? @"" : @"Không tìm thấy ứng dụng trong vùng App Store của tài khoản.";
            }
            [self.tableView reloadData];
        });
    }];
    [task resume];
}

- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return self.searchResults.count;
}

- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath {
    IPARAppCell *cell = [tableView dequeueReusableCellWithIdentifier:kIPARCell];
    if (!cell) cell = [[IPARAppCell alloc] initWithStyle:UITableViewCellStyleDefault reuseIdentifier:kIPARCell];
    NSDictionary *item = self.searchResults[indexPath.row];
    cell.backgroundColor = UIColor.clearColor;
    cell.appName.text = item[kAppnameIndex];
    cell.appBundle.text = item[kAppBundleIndex];
    cell.appVersion.text = item[kAppVersionIndex];
    cell.appImage.image = item[kAppimageIndex];
    UIButton *button = [UIButton buttonWithType:UIButtonTypeSystem];
    button.frame = CGRectMake(0, 0, 48, 48);
    button.tag = indexPath.row;
    [button setImage:[UIImage systemImageNamed:@"arrow.down.circle.fill"] forState:UIControlStateNormal];
    button.tintColor = [UIColor systemGreenColor];
    button.contentHorizontalAlignment = UIControlContentHorizontalAlignmentCenter;
    button.contentVerticalAlignment = UIControlContentVerticalAlignmentCenter;
    [button addTarget:self action:@selector(downloadTapped:) forControlEvents:UIControlEventTouchUpInside];
    cell.accessoryView = button;
    NSString *bundleID = item[kAppBundleIndex];
    UIImage *cached = [self.iconCache objectForKey:bundleID];
    if (cached) {
        cell.appImage.image = cached;
    } else {
        [self loadArtwork:item bundleID:bundleID generation:self.requestGeneration];
    }
    return cell;
}

- (void)loadArtwork:(NSDictionary *)item bundleID:(NSString *)bundleID generation:(NSInteger)generation {
    NSString *urlText = item[@"artworkURL"];
    NSURL *url = [urlText isKindOfClass:[NSString class]] ? [NSURL URLWithString:urlText] : nil;
    if (!url || ![url.scheme isEqualToString:@"https"]) return;
    NSURLSessionDataTask *task = [[NSURLSession sharedSession] dataTaskWithURL:url
        completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
        UIImage *image = (!error && data.length) ? [UIImage imageWithData:data] : nil;
        if (!image) return;
        [self.iconCache setObject:image forKey:bundleID];
        dispatch_async(dispatch_get_main_queue(), ^{
            if (generation != self.requestGeneration) return;
            for (NSMutableDictionary *record in self.searchResults) {
                if ([record[kAppBundleIndex] isEqualToString:bundleID]) {
                    record[kAppimageIndex] = image;
                }
            }
            [self.tableView reloadData];
        });
    }];
    [task resume];
}

- (void)downloadTapped:(UIButton *)sender {
    NSInteger index = sender.tag;
    if (index < 0 || index >= self.searchResults.count) return;
    NSDictionary *item = self.searchResults[index];
    NSNumber *price = item[@"price"];
    if ([price respondsToSelector:@selector(doubleValue)] && [price doubleValue] > 0) {
        NSString *shown = item[@"formattedPrice"] ?: @"có phí";
        UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"Ứng dụng có phí"
            message:[NSString stringWithFormat:@"Giá hiển thị: %@. Việc tải có thể yêu cầu giấy phép hoặc phát sinh thanh toán. Sếp có muốn tiếp tục?",shown]
            preferredStyle:UIAlertControllerStyleAlert];
        [alert addAction:[UIAlertAction actionWithTitle:@"Hủy" style:UIAlertActionStyleCancel handler:nil]];
        [alert addAction:[UIAlertAction actionWithTitle:@"Tiếp tục" style:UIAlertActionStyleDefault
            handler:^(UIAlertAction *action) { [self openVersionsForItem:item]; }]];
        [self presentViewController:alert animated:YES completion:nil];
    } else {
        [self openVersionsForItem:item];
    }
}

- (void)openVersionsForItem:(NSDictionary *)item {
    if (self.tabBarController.viewControllers.count < 2) return;
    id target = self.tabBarController.viewControllers[1];
    if (![target isKindOfClass:[UINavigationController class]]) return;
    UINavigationController *navigation = target;
    IPARDownloadViewController *downloader = (IPARDownloadViewController *)navigation.viewControllers.firstObject;
    if (![downloader isKindOfClass:[IPARDownloadViewController class]]) return;
    [self.searchController setActive:NO];
    self.tabBarController.selectedIndex = 1;
    dispatch_async(dispatch_get_main_queue(), ^{
        [downloader beginVersionSelectionForBundleID:item[kAppBundleIndex]
            appID:item[@"trackId"] appName:item[kAppnameIndex]];
    });
}

- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath {
    [tableView deselectRowAtIndexPath:indexPath animated:YES];
    if (indexPath.row >= self.searchResults.count) return;
    NSDictionary *item = self.searchResults[indexPath.row];
    NSString *bundleID = item[kAppBundleIndex];
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:item[kAppnameIndex]
        message:bundleID preferredStyle:UIAlertControllerStyleActionSheet];
    [alert addAction:[UIAlertAction actionWithTitle:@"Chọn phiên bản" style:UIAlertActionStyleDefault
        handler:^(UIAlertAction *action) { [self openVersionsForItem:item]; }]];
    [alert addAction:[UIAlertAction actionWithTitle:@"Sao chép Bundle ID" style:UIAlertActionStyleDefault
        handler:^(UIAlertAction *action) { [UIPasteboard generalPasteboard].string = bundleID; }]];
    [alert addAction:[UIAlertAction actionWithTitle:@"Hủy" style:UIAlertActionStyleCancel handler:nil]];
    if (UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPad) {
        alert.popoverPresentationController.sourceView = self.view;
        alert.popoverPresentationController.sourceRect = [tableView rectForRowAtIndexPath:indexPath];
    }
    [self presentViewController:alert animated:YES completion:nil];
}
@end
''',encoding="utf-8")
header=root/"Controllers/IPARDownloadViewController.h"
s=header.read_text("utf-8")
assert s.count("@end")==1
s=s.replace("@end","- (void)beginVersionSelectionForBundleID:(NSString *)bundleID appID:(NSNumber *)appID appName:(NSString *)appName;\n@end")
header.write_text(s,"utf-8")
d=root/"Controllers/IPARDownloadViewController.m"
s=d.read_text("utf-8")
a=s.index("- (void)fetchVersionsForBundleID:(NSString *)bundleID {")
b=s.index("// Version history couldn't be loaded",a)
new=r'''- (void)fetchVersionsForBundleID:(NSString *)bundleID {
    [self beginVersionSelectionForBundleID:bundleID appID:nil appName:nil];
}

// The search tab already supplied a trustworthy App ID and bundle identifier.
// This skips an unnecessary iTunes lookup and never touches the clipboard.
- (void)beginVersionSelectionForBundleID:(NSString *)bundleID appID:(NSNumber *)appID appName:(NSString *)appName {
    if (bundleID.length == 0) return;
    [IPARUtils presentLoadingDialogWithMessage:@"Đang lấy lịch sử phiên bản…" on:self];
    if ([appID respondsToSelector:@selector(stringValue)] && [appID longLongValue] > 0) {
        [self loadVersionHistoryForBundleID:bundleID appID:appID name:appName ?: bundleID];
        return;
    }
    // Legacy manual Bundle ID entry. Resolve by the signed-in account's region.
    NSString *command = [NSString stringWithFormat:@"%@ auth info --keychain-passphrase IPARanger --format json",
                         kIpatoolScriptPath];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSDictionary *account = [IPARUtils executeCommandAndGetJSON:kLaunchPathBash
             arg1:kBashCommandKey arg2:command arg3:nil];
        NSString *country = [account[@"country"] isKindOfClass:[NSString class]] ? [account[@"country"] uppercaseString] : nil;
        if (country.length != 2) {
            [self dismissVersionFetchWithError:@"Không xác định được quốc gia của Apple ID. Vui lòng đăng nhập lại hoặc thử làm mới."];
            return;
        }
        NSURLComponents *parts = [NSURLComponents componentsWithString:@"https://itunes.apple.com/lookup"];
        parts.queryItems = @[
            [NSURLQueryItem queryItemWithName:@"bundleId" value:bundleID],
            [NSURLQueryItem queryItemWithName:@"country" value:country],
            [NSURLQueryItem queryItemWithName:@"media" value:@"software"],
            [NSURLQueryItem queryItemWithName:@"limit" value:@"1"]];
        NSURLSessionDataTask *task = [[NSURLSession sharedSession] dataTaskWithURL:parts.URL
        completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
            id payload = data.length ? [NSJSONSerialization JSONObjectWithData:data options:0 error:nil] : nil;
            NSArray *results = [payload isKindOfClass:[NSDictionary class]] && [payload[@"results"] isKindOfClass:[NSArray class]] ? payload[@"results"] : nil;
            NSDictionary *found = results.count && [results[0] isKindOfClass:[NSDictionary class]] ? results[0] : nil;
            NSNumber *resolved = [found[@"trackId"] respondsToSelector:@selector(longLongValue)] ? found[@"trackId"] : nil;
            if (!resolved || [resolved longLongValue] <= 0) {
                [self offerLatestVersionForBundleID:bundleID
                    message:@"Không tìm thấy lịch sử phiên bản trong vùng App Store của tài khoản."];
                return;
            }
            NSString *name = [found[@"trackName"] isKindOfClass:[NSString class]] ? found[@"trackName"] : bundleID;
            [self loadVersionHistoryForBundleID:bundleID appID:resolved name:name];
        }];
        [task resume];
    });
}

- (void)loadVersionHistoryForBundleID:(NSString *)bundleID appID:(NSNumber *)appID name:(NSString *)name {
    NSString *urlString = [NSString stringWithFormat:kAppVersionHistoryURL,appID];
    NSURL *url = [NSURL URLWithString:urlString];
    if (!url) {
        [self offerLatestVersionForBundleID:bundleID message:@"Không thể lấy lịch sử phiên bản."];
        return;
    }
    NSURLSessionDataTask *task = [[NSURLSession sharedSession] dataTaskWithURL:url
        completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
        id payload = data.length ? [NSJSONSerialization JSONObjectWithData:data options:0 error:nil] : nil;
        NSArray *versions = [payload isKindOfClass:[NSDictionary class]] && [payload[@"data"] isKindOfClass:[NSArray class]] ? payload[@"data"] : nil;
        if (versions.count == 0) {
            [self offerLatestVersionForBundleID:bundleID message:@"Không có lịch sử phiên bản khả dụng."];
            return;
        }
        dispatch_async(dispatch_get_main_queue(), ^{
            [self dismissViewControllerAnimated:YES completion:^{
                IPARVersionPickerViewController *picker =
                    [[IPARVersionPickerViewController alloc] initWithAppName:name versions:versions
                    completion:^(NSString *externalVersionID) {
                    [self startDownloadForBundleID:bundleID externalVersionID:externalVersionID];
                }];
                UINavigationController *nav = [[UINavigationController alloc] initWithRootViewController:picker];
                nav.modalPresentationStyle = UIModalPresentationFormSheet;
                [self presentViewController:nav animated:YES completion:nil];
            }];
        });
    }];
    [task resume];
}

'''
s=s[:a]+new+s[b:]
d.write_text(s,"utf-8")
print("Applied iTunes catalog, account-bound region, direct App ID to versions, and IPA manager integration.")
