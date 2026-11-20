#!/usr/bin/env bash
set -euo pipefail
git clone --depth 1 --branch main https://github.com/0xkuj/IPARanger.git upstream
git -C upstream fetch --depth 1 origin ea3b0f721481dc9b192b213f16169afdb7615fc2
git -C upstream checkout --detach ea3b0f721481dc9b192b213f16169afdb7615fc2
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
ctrl.write_text(control.replace("Version: 2.8.2", "Version: 2.8.2+vn0.4.3").replace("Name: IPA Ranger", "Name: IPA Ranger VN"), encoding="utf-8")
print("PATCH OK: UI thread, JSON validation, search concurrency, safe shell term")
PY
python3 build/iparanger/localize.py upstream
python3 build/iparanger/patch_catalog_v03.py upstream
python3 build/iparanger/add_languages.py upstream
python3 build/iparanger/polish_v031.py upstream
python3 build/iparanger/polish_v032.py upstream
python3 build/iparanger/ui_parity_about_v033.py upstream
python3 build/iparanger/ipa_details_v033.py upstream
python3 build/iparanger/v04_ui.py upstream
python3 build/iparanger/v04_audit.py upstream
python3 build/iparanger/v04_library.py upstream
python3 build/iparanger/v041_about.py upstream
python3 build/iparanger/v041_safe_recovery.py upstream
python3 build/iparanger/v042_preflight.py upstream
python3 build/iparanger/v043_libraries.py upstream
python3 build/iparanger/v043_toolbar.py upstream

set -x
# Enforce all approved UI views before building, not only successful compilation.
grep -q 'countryOverlay' upstream/Controllers/IPARSearchViewController.m
grep -q 'gridActionButton' upstream/Controllers/IPARIPADetailViewController.m
grep -q 'IPARAboutViewController' upstream/Controllers/IPARAccountAndCreditsController.m
grep -q 'MIT License' upstream/Controllers/IPARAboutViewController.m
grep -q 'Sentechtipsvn' upstream/Controllers/IPARDeveloperLinksViewController.m
grep -q 'IPARIPAAudit' upstream/Controllers/IPARIPADetailViewController.m
grep -q 'copyBundleIdentifier' upstream/Controllers/IPARIPADetailViewController.m
grep -q 'displayedIPAItems' upstream/Controllers/IPARDownloadViewController.m
grep -q 'initForExportingURLs' upstream/Controllers/IPARIPADetailViewController.m
grep -q -- '- (void)copyBundleIdentifier:' upstream/Controllers/IPARIPADetailViewController.m
grep -q -- '- (void)saveToFiles' upstream/Controllers/IPARIPADetailViewController.m
grep -q 'IPARDiagnostics' upstream/Controllers/IPARDownloadViewController.m
grep -q 'IPARAboutTextViewController' upstream/Controllers/IPARAboutViewController.m
grep -q 'IPARVNPackageVersion' upstream/Resources/Info.plist
grep -q 'IPA Payload layout' upstream/Controllers/IPARIPADetailViewController.m
grep -q 'nestedPayload' upstream/Utils/IPARIPAAudit.m
grep -q 'IPA package layout error' upstream/Controllers/IPARIPADetailViewController.m
grep -q 'IPARVerifiedLibraryViewController' upstream/Controllers/IPARDownloadViewController.m
grep -q 'IPA từ Apple ID' upstream/Resources/vi.lproj/Localizable.strings
grep -q 'IPA đã giải mã' upstream/Resources/vi.lproj/Localizable.strings
grep -q 'self.isDecryptedSource' upstream/Controllers/IPARIPADetailViewController.m
grep -q 'Manually imported, checked as unencrypted' upstream/Controllers/IPARVerifiedLibraryViewController.m
grep -q 'com.0xkuj.iparanger' upstream/layout/DEBIAN/control
! grep -Eq '^(Conflicts|Replaces|Breaks):' upstream/layout/DEBIAN/control
grep -q 'Package: com.0xkuj.iparanger' upstream/layout/DEBIAN/control
! grep -Eq '^(Conflicts|Replaces|Breaks):' upstream/layout/DEBIAN/control
grep -q '<string>com.0xkuj.iparanger</string>' upstream/Resources/Info.plist
sed -i 's/IPA Ranger VN: 2.8.2+vn0.2/IPA Ranger VN: 2.8.2+vn0.4.3/' upstream/Extensions/IPARConstants.h
# Build pipeline supplies patched ipatool from macOS native iOS build.
test -s backend/ipatool-ios-arm64
cp backend/ipatool-ios-arm64 upstream/Resources/ipatool/ipatool
chmod +x upstream/Resources/ipatool/ipatool
cd upstream
# Use an installed SDK; preserve min deployment target iOS 14.
sed -i 's/iphone:clang:14.5:14.0/iphone:clang:latest:14.0/' Makefile
# iPhone 7 Plus is arm64; no arm64e slice is required in this test build.
sed -i 's/ARCHS = arm64 arm64e/ARCHS = arm64/' Makefile
# Remove upstream prebuilt packages so only OUR rebuilt package can be uploaded.
find packages -maxdepth 1 -type f -name '*.deb' -delete
THEOS_PACKAGE_SCHEME=rootless make clean package FINALPACKAGE=1
find packages -type f -name '*iphoneos-arm64.deb' -print
test -n "$(find packages -type f -name '*iphoneos-arm64.deb' -print -quit)"
for deb in packages/*iphoneos-arm64.deb; do
  dpkg-deb --info "$deb" | head -30
  test "$(stat -c %s "$deb")" -gt 100000
  test "$(dpkg-deb -f "$deb" Version)" = "2.8.2+vn0.4.3"
done
