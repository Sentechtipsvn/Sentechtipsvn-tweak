# Raw IPA Lab — thao tác trên iPhone jailbreak (CHỈ KIỂM THỬ)

**Đây không phải bản IPARanger VN v0.4.4 hoàn chỉnh.** Bản lab là tiện ích dòng lệnh độc lập nhằm chứng minh có thể xử lý IPA còn mã hóa do IPARanger tải, ngay cả khi ứng dụng **chưa được cài trên máy**.

## Điều kiện an toàn
- iPhone jailbreak Dopamine Rootless, terminal chạy root.
- Có `ldid`, `unzip`, `libjailbreak.dylib`; tệp IPA là ứng dụng người dùng được quyền tải và sử dụng theo Apple ID của mình.
- Còn dung lượng tối thiểu gấp 4 lần IPA nguồn; thử trên ứng dụng không chứa dữ liệu quan trọng.
- **Không cài chồng ứng dụng** để hoàn tất bước giải mã thử nghiệm. Đây chỉ là phép kiểm tra raw IPA.
- Trước khi cài gói lab, lưu lại gói IPARanger v0.4.3 ổn định. Không cần gỡ IPARanger; helper có Package ID riêng, không thay đổi SpringBoard hoặc jailbreak.

## Khi DEB được build thành công
Cài gói `com.sentechtipsvn.iparanger.rawipa-lab_0.1.0~exp1_iphoneos-arm64.deb` bằng Sileo.

Tại terminal root trên iPhone, sau khi sao chép một IPA từ IPARanger vào `/var/mobile/Documents/test-app.ipa`, chạy:

```sh
/var/jb/usr/bin/ldid -S/var/jb/usr/share/doc/iparanger-rawipa-lab/global.xml /var/jb/usr/libexec/iparanger-rawipa/unfair
/var/jb/usr/bin/iparanger-rawipa-test '/var/mobile/Documents/test-app.ipa'
```

Đường dẫn IPA có thể khác; hãy nhập đúng đường dẫn trong Filza. **Không đưa mật khẩu Apple ID vào lệnh hoặc nhật ký.**

Kết quả:
- `RAW-001`.. `RAW-016`: lỗi kiểm tra, xem nhật ký ở `/var/mobile/Documents/IPARanger-RawIPA-Lab/logs/`.
- `RAW-013`: công cụ đã tạo IPA, **chưa chứng minh đã giải mã toàn bộ hay cài được**. Nhập IPA đầu ra vào thư viện `IPA đã giải mã` trong IPARanger v0.4.3, kiểm tra `FairPlay`, `ZIP`, `Payload`, sau đó mới thử TrollStore với app không quan trọng.
- Ở lần kiểm chứng đầu tiên, chọn **IPA chưa cài** để không vô tình dùng đường chạy đã cài đặt.

**Nếu có lỗi root, entitlement, quyền staging hoặc crash, dừng; không dùng dpkg --force, không sửa MobileGestalt, không can thiệp SpringBoard.** Gửi phần nhật ký mã lỗi, loại bỏ đường dẫn riêng tư nếu cần.

## Tuyên bố
Engine Unfair chỉ được dự kiến dùng trong gói thử nghiệm riêng, giữ bản quyền gốc MIT © 2026 Lakr233. Trạng thái tương thích iOS 15.8.8 chưa được kiểm chứng trên thiết bị. Một bản build thành công trong CI không phải là chứng nhận khả năng giải mã thực tế.
