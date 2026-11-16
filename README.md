# Sentechtipsvn Tweak

Kho APT cho Sileo và nơi lưu mã nguồn tweak do **© Sentechtipsvn** phát triển.

## Thêm nguồn vào Sileo

Nguồn dùng trực tiếp từ GitHub:

```text
https://raw.githubusercontent.com/sentechtipsvn/sentechtipsvn-tweak/master/repo/
```

Mở **Sileo → Nguồn → dấu + → dán địa chỉ → Thêm nguồn**, sau đó làm mới nguồn.

Các gói hiện dành riêng **iPhone 7 Plus · iOS 15.8.8 · Dopamine rootless (`iphoneos-arm64`)**. Không dành cho iPhone 11 chưa jailbreak. Respring sau khi cài/nâng cấp. Phụ thuộc CCSupport lấy từ [nguồn chính thức opa334](https://opa334.github.io/) khi cần; kho không đóng gói lại phụ thuộc bên thứ ba.

## Ba tweak hiện có

| Tweak | Bản hiện tại | Chức năng | Trạng thái |
| --- | --- | --- | --- |
| [SenSwipe](projects/SenSwipe/README.md) | `0.1.0~beta1` | Cử chỉ Home kiểu iPhone X, tùy chọn Control Center/Home bar | Đã có phản hồi cử chỉ chạy mượt; vẫn là beta |
| [ShareWifi](projects/ShareWifi/README.md) | `0.2.0~beta1` | Bật chia sẻ mạng một chạm, ba chế độ dừng, máy khách và Control Center | 0.1.1 đã chạy được; nút CC 0.2.0 đã hiển thị; chế độ mới cần thử thêm |
| [QuickControl](projects/QuickControl/README.md) | `0.1.0~beta1` | Khay tiện ích nổi, ứng dụng/URL/phím tắt và QR offline | Chưa chạy trên iPhone thật |

Các gói cài gốc được giữ nguyên byte, ID, version, phụ thuộc và phạm vi firmware. Chỉ thêm metadata hiển thị vào chỉ mục APT; không sửa/repack .deb.

## Cấu trúc

- `repo/`: nguồn APT tĩnh có Packages, bản nén gzip/bzip2/xz, Release, icon, native depictions và trang giới thiệu.
- `repo/debs/`: **chỉ các bản đang phân phối**. Thêm .deb mới ở đây rồi cập nhật `catalog.json`.
- `projects/`: mã nguồn từng tweak, hướng dẫn, script build và các bài kiểm tra sẵn có. Bản tài liệu gốc có thể ghi trạng thái tại thời điểm bàn giao; bảng trên và `catalog.json` ghi nhận phản hồi mới hơn.
- `sources/`: ZIP nguồn của ba bản hiện tại để tải riêng.
- `archive/`: bản ShareWifi 0.1.0 và 0.1.1 cùng ZIP nguồn để lưu lịch sử; không đưa vào chỉ mục cài mặc định.
- `scripts/build_repo.py`: tạo chỉ mục, checksum, native depictions và giao diện web từ metadata thực của .deb.
- `scripts/verify_repo.py`: kiểm tra ID/version/architecture/dependency, từng byte .deb theo hash, icon/depiction, các bản nén và checksum Release.
- `scripts/verify_sileo.py`: chạy parser C của Sileo 2.5.1 trên host, đối chiếu điều kiện chấp nhận Release và hash; có kiểm tra hồi quy trường Components. Cần clang.
- `scripts/verify_apt.sh`: dùng APT đọc chỉ mục local trong thư mục tạm, không cài gói hoặc sửa cấu hình APT của máy.
- `.github/workflows/publish.yml`: tự kiểm tra sau mỗi lần push lên master; xuất bản Pages nếu Pages đã bật ở chế độ GitHub Actions.

## Cập nhật sau này

1. Build tweak có **version mới**. Không thay byte của một .deb đã phát hành mà vẫn giữ cùng version.
2. Lưu .deb/source ZIP cũ vào `archive/` nếu cần. Chỉ giữ .deb mới nhất trong `repo/debs/` cho mỗi tweak.
3. Cập nhật mã nguồn trong `projects/`, ZIP hiện tại trong `sources/` và metadata trong `catalog.json` (file, version, mô tả, changelog, trạng thái thử máy).
4. Tạo lại và kiểm tra chỉ mục:

```sh
python3 scripts/build_repo.py
python3 scripts/verify_repo.py
python3 scripts/verify_sileo.py
bash scripts/verify_apt.sh
```

5. Commit cả .deb mới lẫn các file chỉ mục sinh ra, rồi push. **Nguồn raw phục vụ trực tiếp các file đã commit**, vì vậy phải cập nhật Packages/Release cùng .deb. Quy trình CI sẽ báo nếu chỉ mục sai; không tự commit ngược vào nhánh.

Công cụ tạo nguồn cần Python 3 và `dpkg-scanpackages` (gói `dpkg-dev` trên Debian/Ubuntu). Thử đọc APT cần `apt-get`/`apt-cache`; chạy parser C cần clang hỗ trợ Blocks. Các tweak có môi trường build riêng ghi trong README của từng dự án.

## Bật địa chỉ GitHub Pages ngắn hơn (một lần)

Địa chỉ Pages dự kiến:

```text
https://sentechtipsvn.github.io/Sentechtipsvn-tweak/
```

Trong repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**. Sau đó vào **Actions → Publish Sileo repository → Run workflow**. Chờ workflow xuất bản thành công rồi mở địa chỉ Pages bằng trình duyệt để bấm **Thêm vào Sileo** (nút tự dùng nguồn raw chữ thường).

Trang Pages dùng để xem danh sách và tải gói. **Nút Thêm vào Sileo và Sao chép nguồn luôn dùng địa chỉ raw GitHub chữ thường ở đầu README**, kể cả khi trang đang được xuất bản bằng Pages.

Trong ảnh lỗi từ thiết bị thử, Sileo truy cập đường dẫn nguồn chữ thường. `/Sentechtipsvn-tweak/Release` trên Pages trả 200 nhưng `/sentechtipsvn-tweak/Release` trả 404. Địa chỉ raw chữ thường được kiểm tra trả 200. Không thêm địa chỉ Pages này trực tiếp vào Sileo; nếu đã thêm và gặp 404, xóa đúng nguồn Pages lỗi rồi thêm địa chỉ raw. Không cần gỡ tweak đã cài.

Workflow bỏ qua deploy nếu Pages chưa bật và vẫn kiểm tra APT bình thường. Không cần đưa PAT hoặc khóa riêng vào repo.

## Sửa lỗi Sileo không đọc được Release

Sileo 2.5.1 yêu cầu Release có `Architectures` phù hợp và trường `Components`, kể cả nguồn flat. Bản tạo kho trước đây thiếu `Components`, nên APT vẫn đọc được nhưng Sileo báo `Could not parse release file.` và nguồn có 0 gói. Bộ tạo hiện thêm `Components: main` và CI chạy parser C thật từ tag Sileo 2.5.1 cùng các điều kiện kiểm tra trong RepoManager.

Nếu đã thêm nguồn raw, chỉ cần làm mới nguồn sau cập nhật. Nguồn Pages chữ thường cũ vẫn là địa chỉ khác bị 404; xóa riêng nguồn Pages lỗi để nó không báo đỏ trong mỗi lần làm mới. Không cần gỡ tweak hoặc respring chỉ để cập nhật metadata nguồn.

### Mã kiểm thử bên thứ ba

`tests/vendor/sileo-2.5.1/` giữ parser C và giấy phép gốc. Driver và header tương thích Linux chỉ dùng cho kiểm thử, không đưa vào các tweak. This product includes software developed by the Sileo Team. Xem `tests/vendor/sileo-2.5.1/LICENSE` và [mã nguồn tag 2.5.1](https://github.com/Sileo/Sileo/tree/2.5.1). Đây không phải chứng nhận của Sileo; kiểm thử host không chạy app iOS, cache hay giao diện trên thiết bị.

## Kiểm chứng và giới hạn

Kho có native depictions theo định dạng của [Sileo Developer](https://developer.getsileo.app/native-depictions). Chỉ mục và các checksum không thay thế kiểm thử cài đặt trên máy thật. Chưa xác nhận việc thêm nguồn bằng Sileo trong môi trường build; các test dùng APT và kiểm tra HTTP/chỉ mục.

Kho hiện không có chữ ký GPG Release. Chữ ký ad-hoc trong binary tweak và checksum .deb là các phần kiểm tra khác nhau, không phải chứng chỉ Apple hay bảo đảm tương thích mọi máy. Không tự công bố bản beta là bản ổn định chỉ vì CI xanh.

© Sentechtipsvn · Mã nguồn theo MIT, xem LICENSE trong từng dự án.
