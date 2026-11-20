#!/bin/sh
# IPARanger VN laboratory-only standalone raw IPA decryption diagnostic.
# Run as root on a personal jailbreak device. No services/hooks; no app changes.
set -u
umask 077
ENGINE="/var/jb/usr/libexec/iparanger-rawipa/unfair"
DEFAULT_OUT="/var/mobile/Documents/IPARanger-RawIPA-Lab"
INPUT="${1:-}"
OUTDIR="${2:-$DEFAULT_OUT}"
STAMP="$(date -u '+%Y%m%dT%H%M%SZ')-$$"
LOGDIR="$OUTDIR/logs"
LOG="$LOGDIR/$STAMP.log"
log() { printf '%s\n' "$*" | tee -a "$LOG"; }
abort() { log "RESULT: FAIL $1 - $2"; exit "${3:-1}"; }
if [ -z "$INPUT" ] || [ ! -f "$INPUT" ]; then
  echo "RAW-001: Cần đường dẫn tệp IPA hợp lệ. Cú pháp: iparanger-rawipa-test INPUT.ipa [OUTPUT_DIRECTORY]" >&2
  exit 1
fi
case "$INPUT" in *.ipa|*.IPA) ;; *) echo "RAW-001: Tệp phải có phần mở rộng .ipa" >&2; exit 1;; esac
mkdir -p "$LOGDIR" || exit 1
# Allow the mobile user to browse the result in Files/Filza after a root terminal run.
chown mobile:mobile "$OUTDIR" "$LOGDIR" 2>/dev/null || true
chmod 755 "$OUTDIR" "$LOGDIR" 2>/dev/null || true
log "IPARanger VN Raw IPA Lab / $STAMP"
log "INPUT_NAME=$(basename "$INPUT")"
log "STAGE: PRECHECK"
[ "$(id -u)" -eq 0 ] || abort RAW-005 "Phải chạy từ terminal root; không sửa chmod hoặc cưỡng ép kiến trúc gói."
[ -x "$ENGINE" ] || abort RAW-004 "Thiếu helper: $ENGINE"
if [ ! -e /var/jb/basebin/libjailbreak.dylib ] && [ ! -e /var/jb/usr/lib/libjailbreak.dylib ]; then
   abort RAW-006 "Không tìm thấy libjailbreak yêu cầu."
fi
command -v unzip >/dev/null 2>&1 || abort RAW-004 "Thiếu unzip để kiểm tra IPA."
LIST="$LOGDIR/$STAMP.zipentries"
trap 'rm -f "$LIST"' EXIT HUP INT TERM
unzip -Z -1 "$INPUT" > "$LIST" 2>/dev/null || abort RAW-001 "Không đọc được danh sách ZIP."
grep -Eq '^Payload/[^/]+[.]app/Info[.]plist$' "$LIST" || abort RAW-002 "Thiếu thư mục Payload/*.app/Info.plist."
grep -Eq '^Payload/[^/]+[.]app/SC_Info/[^/]+[.]sinf$' "$LIST" || abort RAW-003 "Thiếu tệp cấp phép FairPlay SC_Info/*.sinf."
if grep -Eq '(^/|(^|/)\.\.(/|$)|\\)' "$LIST"; then
    abort RAW-001 "Phát hiện đường dẫn ZIP không an toàn."
fi
FILE_KB=$(du -k "$INPUT" | awk '{print $1}')
FREE_KB=$(df -Pk "$OUTDIR" | awk 'END {print $4}')
if [ -n "$FILE_KB" ] && [ -n "$FREE_KB" ] && [ "$FREE_KB" -lt "$((FILE_KB * 4))" ]; then
    abort RAW-007 "Không đủ dung lượng trống cho staging và bản xuất."
fi
BASE=$(basename "$INPUT" .ipa | tr -cd 'A-Za-z0-9._-' | cut -c1-80)
[ -n "$BASE" ] || BASE="application"
OUTPUT="$OUTDIR/${BASE}_decrypted_${STAMP}.ipa"
[ ! -e "$OUTPUT" ] || abort RAW-014 "Đầu ra đã tồn tại; không ghi đè."
log "STAGE: DECRYPT"
ENGINELOG="$LOGDIR/$STAMP.engine.log"
if ! "$ENGINE" package -i "$INPUT" -o "$OUTPUT" -v > "$ENGINELOG" 2>&1; then
    log "ENGINE_LOG=$ENGINELOG"
    if grep -Eqi 'SC_Info|sinf|license metadata|missingRootSinf' "$ENGINELOG"; then
        abort RAW-003 "Thiếu hoặc sai metadata cấp phép FairPlay (không ghi nội dung SC_Info)."
    elif grep -Eqi 'libjailbreak|jbclient|proc_csflags_set|permission setup' "$ENGINELOG"; then
        abort RAW-006 "Không khởi tạo được quyền jailbreak; xem nhật ký."
    elif grep -Eqi 'permission denied|mkdir staging|chown failed|staged app' "$ENGINELOG"; then
        abort RAW-008 "Không tạo được môi trường staging an toàn."
    elif grep -Eqi 'mremap_encrypted|fairplay|authorization|EPERM' "$ENGINELOG"; then
        abort RAW-009 "Không được hệ thống xác thực giải mã FairPlay cho IPA này."
    fi
    abort RAW-010 "Helper thất bại; chưa đủ dữ liệu xác định lỗi, xem engine log."
fi
log "STAGE: VERIFY_ARCHIVE"
[ -s "$OUTPUT" ] || abort RAW-011 "Không tìm thấy IPA đầu ra."
unzip -t -qq "$OUTPUT" >/dev/null 2>&1 || abort RAW-011 "ZIP đầu ra không hợp lệ."
if unzip -Z -1 "$OUTPUT" | grep -Eq '(^|/)SC_Info/'; then
    abort RAW-015 "IPA đầu ra còn chứa SC_Info; không sử dụng."
fi
chmod 644 "$OUTPUT" "$LOG" "$ENGINELOG" || true
chown mobile:mobile "$OUTPUT" "$LOG" "$ENGINELOG" 2>/dev/null || true
log "OUTPUT=$OUTPUT"
log "RESULT: RAW-013 IPA đã được tạo. PHẢI nhập vào IPARanger và xác minh mọi Mach-O (frameworks/extensions) trước khi thử TrollStore."
exit 0
