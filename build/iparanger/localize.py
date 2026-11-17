#!/usr/bin/env python3
"""IPARanger VN v0.2: translate *display-only* Objective-C string literals.
Do not touch Apple responses, JSON keys, preference keys, command templates or state sentinels.
The source is the pinned upstream commit plus the tested v0.1 search fix.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1])
replacements={
"Controllers/IPARSearchViewController.m": {
    "Search in Appstore: %@": "Tìm trong App Store: %@",
    "App Name cannot be empty": "Vui lòng nhập tên ứng dụng",
    "OK": "Đồng ý",
    "e.g - Netflix": "Ví dụ: Zalo",
    "Enter App Name": "Nhập tên ứng dụng",
    "Sign in required": "Cần đăng nhập",
    "Searching the App Store needs an Apple ID. Sign in to search and download apps.": "Đăng nhập Apple ID để tìm kiếm và tải ứng dụng từ App Store.",
    "Sign In": "Đăng nhập",
    "Not now": "Để sau",
    "Sign in to search the App Store.\nTap the search icon to sign in.": "Đăng nhập để tìm trên App Store.\nChạm biểu tượng tìm kiếm để đăng nhập.",
    "Nothing to show here.\nStart by clicking the search icon!": "Chưa có kết quả.\nChạm biểu tượng kính lúp để tìm ứng dụng.",
    "App Selected %@": "Ứng dụng: %@",
    "Bundle ID: %@": "Mã gói (Bundle ID): %@",
    "Copy Bundle": "Sao chép Bundle ID",
    "Fetching more results for %@...": "Đang tải thêm kết quả cho %@...",
    "Searching the App Store for %@...": "Đang tìm %@ trên App Store...",
    "Search failed. Try again.": "Tìm kiếm thất bại. Vui lòng thử lại.",
    "Invalid search response. Try again.": "Phản hồi tìm kiếm không hợp lệ. Vui lòng thử lại.",
    "No results for %@": "Không tìm thấy ứng dụng: %@",
    "Invalid search data. Please retry.": "Dữ liệu tìm kiếm không hợp lệ. Vui lòng thử lại.",
},
"Controllers/IPARDownloadViewController.m": {
    "Download Appstore: %@": "Tải từ App Store: %@",
    "Loading downloaded apps…": "Đang tải danh sách IPA…",
    "OK": "Đồng ý",
    "YES": "Có",
    "Delete All": "Xóa tất cả",
    "Open Download Folder in Filza": "Mở thư mục tải trong Filza",
    "Delete Cache Folder": "Xóa bộ nhớ đệm",
    "The cache folder contains cached information about your previously downloaded apps.\nYour downloaded app will still exists.\n\nCache folder size: %@\n\nAre you sure?": "Bộ nhớ đệm lưu thông tin các ứng dụng đã tải.\nCác tệp IPA của Sếp sẽ không bị xóa.\n\nDung lượng bộ nhớ đệm: %@\n\nSếp có chắc muốn xóa?",
    "No": "Không",
    "Yes": "Có",
    "You are about to delete all downloaded IPAs\n\nThis operation cannot be undone\nAre you sure?": "Sắp xóa toàn bộ IPA đã tải.\n\nKhông thể hoàn tác thao tác này.\nSếp có chắc muốn tiếp tục?",
    "Cancel": "Hủy",
    "Bundle ID cannot be empty": "Vui lòng nhập Bundle ID",
    "e.g com.facebook.Facebook": "Ví dụ: com.facebook.Facebook",
    "Enter App Bundle ID": "Nhập Bundle ID ứng dụng",
    "Continue": "Tiếp tục",
    "Fetching available versions…": "Đang lấy danh sách phiên bản…",
    "Invalid bundle identifier.": "Bundle ID không hợp lệ.",
    "Could not reach the App Store.": "Không thể kết nối App Store.",
    "No App Store app was found for this bundle ID.": "Không tìm thấy ứng dụng với Bundle ID này trên App Store.",
    "Could not resolve the app's ID.": "Không xác định được mã ứng dụng.",
    "Version history is unavailable.": "Không thể lấy lịch sử phiên bản.",
    "No version history was found for this app.": "Ứng dụng này không có lịch sử phiên bản khả dụng.",
    "%@\n\nYou can still download the latest version.": "%@\n\nSếp vẫn có thể tải phiên bản mới nhất.",
    "Download Latest": "Tải phiên bản mới nhất",
    "App with same name already exists in %@": "Đã có ứng dụng trùng tên tại %@",
    "Logout": "Đăng xuất",
    "The download finished successfully!": "Tải IPA thành công!",
    "Nothing to show here.\nStart by clicking the download icon!": "Chưa có IPA đã tải.\nChạm biểu tượng tải xuống để bắt đầu.",
    "Open in Filza": "Mở bằng Filza",
    "Share": "Chia sẻ",
    "Rename File": "Đổi tên tệp",
    "Install Application": "Cài đặt ứng dụng",
    "Delete": "Xóa",
    "Installing “%@”…": "Đang cài đặt “%@”…",
    "Successfully installed '%@'!": "Đã cài đặt “%@” thành công!",
    "Error occurred while trying to install '%@'": "Không thể cài đặt “%@”.",
    "You are about to install App: %@\n\nAre you sure?": "Sắp cài ứng dụng: %@\n\nSếp có muốn tiếp tục?",
    "IPARanger\nInstall Application": "IPARanger\nCài ứng dụng",
    "Yes, Continue": "Có, tiếp tục",
    "You are about to delete file: %@\n\nAre you sure?": "Sắp xóa tệp: %@\n\nSếp có chắc muốn xóa?",
    "There was an error trying to rename your file\nCheck your filename and try again": "Không thể đổi tên tệp.\nHãy kiểm tra tên tệp và thử lại.",
    "Your IPA file does not end with '.ipa' extension.\nDo you wish to continue?": "Tên tệp không có đuôi '.ipa'.\nSếp vẫn muốn tiếp tục?",
    "%@\n\nDont forget to add '.ipa' at the end of your file": "%@\n\nHãy thêm đuôi '.ipa' vào tên tệp",
    "Rename": "Đổi tên",
    "Downloading": "Đang tải",
},
"Controllers/IPARVersionPickerViewController.m": {
    "Select Version": "Chọn phiên bản",
    "Search versions": "Tìm phiên bản",
    "Latest version": "Phiên bản mới nhất",
    "The current App Store release": "Bản đang phát hành trên App Store",
    "Unknown version": "Không rõ phiên bản",
},
"Controllers/IPARAccountAndCreditsController.m": {
    "Not signed in": "Chưa đăng nhập",
    "Sign in to search and download apps": "Đăng nhập để tìm kiếm và tải ứng dụng",
    "Sign In": "Đăng nhập",
    "Last login": "Đăng nhập gần nhất",
    "Follow me on Twitter": "Theo dõi tác giả trên Twitter",
    "Buy me a coffee": "Ủng hộ tác giả",
    "Source code": "Mã nguồn",
    "Created by 0xkuj": "Phát triển bởi 0xkuj",
    "SPECIAL THANKS": "CẢM ƠN ĐẶC BIỆT",
    "Log out?": "Đăng xuất?",
    "You’ll need to sign in with your Apple ID again to search and download apps.": "Sếp cần đăng nhập lại bằng Apple ID để tìm kiếm và tải ứng dụng.",
    "Cancel": "Hủy",
    "Log Out": "Đăng xuất",
    "Continue anyway": "Vẫn tiếp tục",
},
"Controllers/IPARLoginScreenViewController.m": {
    "Apple ID email": "Email Apple ID",
    "OK": "Đồng ý",
    "Password": "Mật khẩu",
    "Browse downloaded apps": "Xem IPA đã tải (không đăng nhập)",
    "Need help?": "Trợ giúp",
    "Source code": "Mã nguồn",
    "Created by 0xkuj": "Phát triển bởi 0xkuj",
    "Welcome to IPA Ranger!": "Chào mừng đến IPA Ranger!",
    "This is an open source project I worked hard to maintain. Your Apple ID and password are sent directly to Apple’s servers and are never saved on your device.\n\nIf you have any concerns, check out the source code below (and maybe drop a star ;) ).\n\nEnjoy!": "Đây là dự án mã nguồn mở do 0xkuj phát triển và duy trì. Theo mô tả của tác giả, Apple ID và mật khẩu được gửi đến máy chủ Apple và không được lưu trong ứng dụng.\n\nSếp có thể xem mã nguồn để tự kiểm tra cách hoạt động và ủng hộ tác giả.\n\nChúc trải nghiệm thuận lợi!",
    "Check out the code": "Xem mã nguồn",
    "Logging in…\nFirst-time setup: downloading Apple components (~75 MB). This can take 5 minutes or more — keep the app open.": "Đang đăng nhập…\nThiết lập lần đầu: tải thành phần Apple (~75 MB). Hãy giữ ứng dụng mở trong quá trình này.",
    "Logging in…": "Đang đăng nhập…",
    "Try Again": "Thử lại",
    "Login failed: unexpected response": "Đăng nhập thất bại: phản hồi không hợp lệ",
    "Continue with 2FA": "Xác minh hai yếu tố (2FA)",
    "Please enter the 2FA you got from Apple": "Nhập mã xác minh 2FA Apple vừa gửi",
    "Cancel": "Hủy",
    "Verifying your 2FA code…": "Đang xác minh mã 2FA…",
    "2FA login failed: unexpected response": "Xác minh 2FA thất bại: phản hồi không hợp lệ",
},
"Controllers/IPARCountryTableViewController_deprecated.m": {
    "Select The Country Of Your Account": "Chọn quốc gia của tài khoản",
},
"Extensions/IPARConstants.h": {
    "IPARanger\nCopy Bundle": "IPARanger\nSao chép Bundle ID",
    "IPARanger\nError": "IPARanger\nLỗi",
    "IPARanger\nWarning": "IPARanger\nCảnh báo",
    "IPARanger\nDelete File": "IPARanger\nXóa tệp",
    "IPARanger\nDelete Files": "IPARanger\nXóa tệp",
    "IPARanger\nRename File": "IPARanger\nĐổi tên tệp",
    "IPARanger\nLogout": "IPARanger\nĐăng xuất",
    "IPARanger - Download": "IPARanger - Tải IPA",
    "IPARanger - Search": "IPARanger - Tìm kiếm",
    "IPARanger\nDownloading..": "IPARanger\nĐang tải…",
    "IPARanger\nSuccess!": "IPARanger\nThành công!",
    "IPARanger\nInstallation\n": "IPARanger\nCài đặt\n",
    "Show More Results": "Hiển thị thêm kết quả",
    "The first GUI-based app for ipatool\n<made by 0xkuj>": "Giao diện quản lý ipatool trên iOS\n<phát triển bởi 0xkuj>",
},
}
total=0
for relative,mapping in replacements.items():
    file=root/relative
    source=file.read_text("utf-8")
    for english, vietnamese in mapping.items():
        orig='@"'+english.replace("\n",r"\n")+'"'
        target='@"'+vietnamese.replace("\n",r"\n")+'"'
        occurrences=source.count(orig)
        if occurrences==0:
            raise RuntimeError(f"Missing source string in {relative}: {english!r}")
        if english==vietnamese:
            continue
        source=source.replace(orig,target)
        total+=occurrences
    file.write_text(source,"utf-8")
    print(relative, "localized", len(mapping), "keys")
# UI-only labels: identifiers like kSearchTitle are also used for control flow; do not change them.
for relative, original, replacement in [
    ("Controllers/IPARSearchViewController.m", "self.title = kSearchTitle;", 'self.title = @"Tìm kiếm";'),
    ("Controllers/IPARSearchViewController.m", "self.tabBarItem.title = kSearchTitle;", 'self.tabBarItem.title = @"Tìm kiếm";'),
    ("Controllers/IPARDownloadViewController.m", "self.title = kDownloadTitle;", 'self.title = @"IPA đã tải";'),
    ("Controllers/IPARDownloadViewController.m", "self.tabBarItem.title = kDownloadTitle;", 'self.tabBarItem.title = @"IPA đã tải";'),
    ("Controllers/IPARAccountAndCreditsController.m", "self.title = kAccountTitle;", 'self.title = @"Tài khoản";'),
    ("Controllers/IPARAccountAndCreditsController.m", "self.tabBarItem.title = kAccountTitle;", 'self.tabBarItem.title = @"Tài khoản";'),
    ("Controllers/IPARLoginScreenViewController.m","[button setTitle:kLoginTitle forState:UIControlStateNormal];", '[button setTitle:@"Đăng nhập" forState:UIControlStateNormal];'),
    ("Controllers/IPARAccountAndCreditsController.m","[button setTitle:kLogoutTitle forState:UIControlStateNormal];", '[button setTitle:@"Đăng xuất" forState:UIControlStateNormal];'),
]:
    file=root/relative
    code=file.read_text("utf-8")
    assert code.count(original)==1,(relative,original)
    file.write_text(code.replace(original,replacement),"utf-8")
# Version history includes plural English 's'. Replace full formatting expression.
version=root/"Controllers/IPARVersionPickerViewController.m"
code=version.read_text("utf-8")
original='return [NSString stringWithFormat:@"%lu version%@ available",\n                (unsigned long)count, count == 1 ? @"" : @"s"];'
assert code.count(original)==1,"Version count UI formatting changed"
code=code.replace(original,'return [NSString stringWithFormat:@"Có %lu phiên bản", (unsigned long)count];')
version.write_text(code,"utf-8")
# Welcome timer label and button:
login=root/"Controllers/IPARLoginScreenViewController.m"
code=login.read_text("utf-8")
for old,new in [
    ('@"OK (10…)"','@"Đồng ý (10…)"'),
    ('@"OK (%d…)"','@"Đồng ý (%d…)"'),
]:
    assert old in code,old
    code=code.replace(old,new)
login.write_text(code,"utf-8")
# Display-only version and SpringBoard label; keep internal identifiers unchanged.
constants_file=root/"Extensions/IPARConstants.h"
text_v=constants_file.read_text("utf-8")
old='@"IPA Ranger version: 2.8.2 (rootless)"'
assert text_v.count(old)==1
constants_file.write_text(text_v.replace(old,'@"IPA Ranger VN: 2.8.2+vn0.2 (rootless)"'),"utf-8")
info=root/"Resources/Info.plist"
text_info=info.read_text("utf-8")
key='<key>CFBundleIdentifier</key>\n\t<string>com.0xkuj.iparanger</string>'
assert text_info.count(key)==1
info.write_text(text_info.replace(key,key+'\n\t<key>CFBundleDisplayName</key>\n\t<string>IPA Ranger VN</string>'),"utf-8")
# Avoid translating back-end error sentinels, preference flags, 'search'/'download' commands.
constants=(root/"Extensions/IPARConstants.h").read_text("utf-8")
assert 'kSearchTitle = @"Search"' in constants
assert 'kDownloadTitle = @"Download"' in constants
assert 'kJsonLevelError = @"error"' in constants
assert 'kAuthenticatedKeyFromFile = @"Authenticated"' in constants
assert 'kLoginCommandPathAccountPassword =' in constants
print("Translation successful:",total,"literal occurrences + 8 UI labels; internal keys preserved.")
