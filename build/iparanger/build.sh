#!/usr/bin/env bash
set -euo pipefail
git clone --depth 1 --branch main https://github.com/0xkuj/IPARanger.git upstream
python3 - <<'PY'
from pathlib import Path
p=Path("upstream/Controllers/IPARSearchViewController.m")
src=p.read_text(encoding="utf-8")
start="- (void)runSearchCommand {"
stop="- (void)populateTableWithSearchResults {"
assert src.count(start)==1 and src.count(stop)==1, "Upstream layout changed"
assert src.count("@property (nonatomic) NSInteger limitSearch;")==1
src=src.replace("@property (nonatomic) NSInteger limitSearch;", "@property (nonatomic) NSInteger limitSearch;\n@property (nonatomic, assign) BOOL searchInProgress;",1)
new_run=r'''- (void)runSearchCommand {
    if (self.searchInProgress) { return; }
    NSString *term = [[self.latestSearchTerm stringByTrimmingCharactersInSet:
                      [NSCharacterSet whitespaceAndNewlineCharacterSet]] copy];
    if (term.length == 0) { return; }
    self.searchInProgress = YES;
    NSInteger limit = self.limitSearch;
    NSString *loadingMessage = (limit > APPS_SEARCH_INITIAL_LIMIT)
       ? [NSString stringWithFormat:@"Fetching more results for %@...", term]
       : [NSString stringWithFormat:@"Searching the App Store for %@...", term];
    [IPARUtils presentLoadingDialogWithMessage:loadingMessage on:self];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSString *safeTerm = [term stringByReplacingOccurrencesOfString:@"'"
                                                              withString:@"'\\''"];
        NSString *command = [NSString stringWithFormat:kSearchCommandPathTermLimitCountry,
                             kIpatoolScriptPath, safeTerm, (long)limit];
        NSDictionary *raw = [IPARUtils executeCommandAndGetJSON:kLaunchPathBash
                                                           arg1:kBashCommandKey arg2:command arg3:nil];
        dispatch_async(dispatch_get_main_queue(), ^{
            self.searchInProgress = NO;
            NSDictionary *response = [raw isKindOfClass:[NSDictionary class]] ? raw : nil;
            id rawApps = response[@"apps"];
            NSArray *apps = [rawApps isKindOfClass:[NSArray class]] ? rawApps : nil;
            id rawLevel = response[kJsonLevel];
            NSString *level = [rawLevel isKindOfClass:[NSString class]] ? rawLevel : nil;
            id rawError = response[kJsonLevelError];
            NSString *errorValue = [rawError isKindOfClass:[NSString class]] ? rawError : nil;
            NSString *message = nil;
            if ([level isEqualToString:kJsonLevelError]) {
                message = errorValue.length ? errorValue : @"Search failed. Try again.";
                NSLog(@"[IPARangerVN] Search returned error");
            } else if (!apps) {
                message = @"Invalid search response. Try again.";
                NSLog(@"[IPARangerVN] Search JSON schema invalid");
            } else if (apps.count == 0) {
                message = [NSString stringWithFormat:@"No results for %@", term];
            }
            [self dismissViewControllerAnimated:YES completion:^{
                if (message) {
                    [IPARUtils presentDialogWithTitle:kIPARangerErrorHeadline
                                             message:message hasTextfield:NO
                                  withTextfieldBlock:nil alertConfirmationBlock:nil
                                      withConfirmText:@"OK" alertCancelBlock:nil withCancelText:nil
                                       presentOn:self];
                } else {
                    self.lastCommandResult = response;
                    [self populateTableWithSearchResults];
                }
            }];
        });
    });
}

'''
new_populate=r'''- (void)populateTableWithSearchResults {
    [self.searchResults removeAllObjects];
    id raw = self.lastCommandResult[@"apps"];
    NSArray *apps = [raw isKindOfClass:[NSArray class]] ? raw : @[];
    UIImage *placeholder = [UIImage systemImageNamed:kUnknownSystemImage] ?: [UIImage new];
    NSMutableArray<NSDictionary *> *validApps = [NSMutableArray array];
    for (id candidate in apps) {
        if (![candidate isKindOfClass:[NSDictionary class]]) { continue; }
        NSMutableDictionary *item = [candidate mutableCopy];
        if (![item[kAppBundleIndex] isKindOfClass:[NSString class]] ||
             [item[kAppBundleIndex] length] == 0) { continue; }
        if (![item[kAppnameIndex] isKindOfClass:[NSString class]]) {
            item[kAppnameIndex] = item[kAppBundleIndex];
        }
        id version = item[kAppVersionIndex];
        if (![version isKindOfClass:[NSString class]]) {
            item[kAppVersionIndex] = [version respondsToSelector:@selector(stringValue)]
                ? [version stringValue] : @"—";
        }
        item[kAppimageIndex] = placeholder;
        [self.searchResults addObject:item];
        [validApps addObject:item];
    }
    [self.tableView reloadData];
    if (validApps.count == 0) {
        [IPARUtils presentDialogWithTitle:kIPARangerErrorHeadline
                                 message:@"Invalid search data. Please retry."
                            hasTextfield:NO withTextfieldBlock:nil alertConfirmationBlock:nil
                          withConfirmText:@"OK" alertCancelBlock:nil withCancelText:nil presentOn:self];
        return;
    }
    [IPARUtils getAppIconsFromApple:validApps country:self.lastCommandResult[@"country"]
                       completion:^(NSDictionary<NSString *, UIImage *> *icons) {
        for (NSMutableDictionary *item in self.searchResults) {
            UIImage *icon = icons[item[kAppBundleIndex]];
            if (icon) { item[kAppimageIndex] = icon; }
        }
        [self.tableView reloadData];
    }];
}

'''
a=src.index(start)
b=src.index(stop,a+len(start))
src=src[:a]+new_run+new_populate+src[b:]
x=src.index(stop,a+len(new_run)+len(new_populate))
y=src.index("#pragma mark - Table View Data Source",x)
src=src[:x]+src[y:]
assert src.count("- (void)populateTableWithSearchResults {")==1
assert src.count("- (void)runSearchCommand {")==1
p.write_text(src,encoding="utf-8")
ctrl=Path("upstream/layout/DEBIAN/control")
control=ctrl.read_text(encoding="utf-8")
assert "Version: 2.8.2" in control
ctrl.write_text(control.replace("Version: 2.8.2", "Version: 2.8.2+vn0.1").replace("Name: IPA Ranger", "Name: IPA Ranger VN (Search Fix)"), encoding="utf-8")
print("PATCH OK: UI thread, JSON validation, search concurrency, safe shell term")
PY
cd upstream
# Use an installed SDK; preserve min deployment target iOS 14.
sed -i 's/iphone:clang:14.5:14.0/iphone:clang:latest:14.0/' Makefile
# iPhone 7 Plus is arm64; no arm64e slice is required in this test build.
sed -i 's/ARCHS = arm64 arm64e/ARCHS = arm64/' Makefile
THEOS_PACKAGE_SCHEME=rootless make clean package FINALPACKAGE=1
find packages -type f -name '*iphoneos-arm64.deb' -print
test -n "$(find packages -type f -name '*iphoneos-arm64.deb' -print -quit)"
for deb in packages/*iphoneos-arm64.deb; do
  dpkg-deb --info "$deb" | head -30
  test "$(stat -c %s "$deb")" -gt 100000
done
