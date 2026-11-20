#!/bin/sh
# Rootless, standalone downloaded-IPA decryption feasibility lab.
# Not a general-purpose privileged service. Source IPA is read-only.
set -u
umask 077
ENGINE="/var/jb/usr/libexec/iparanger-rawipa/unfair"
INPUT="\${1:-}"
OUTDIR="\${2:-/var/mobile/Documents/IPARanger-RawIPA-Lab}"
STAMP="$(date -u '+%Y%m%dT%H%M%SZ')-$$"
if [ -z "$INPUT" ] || [ ! -f "$INPUT" ]; then
    echo "RAW-001: Hãy cung cấp đường dẫn IPA nguồn." >&2
    exit 1
fi
case "$INPUT" in *.ipa|*.IPA) ;; *) echo "RAW-001: Tệp phải có đuôi .ipa." >&2; exit 1;; esac
WORKDIR="$(mktemp -d /var/tmp/iparanger-rawipa.XXXXXXXX)" || exit 1
LIST="$WORKDIR/zipentries"
LOG="$WORKDIR/process.log"
ENGINELOG="$WORKDIR/engine.log"
STAGED="$WORKDIR/output.ipa"
LOGDIR="$OUTDIR/logs"
if ! mkdir -p "$LOGDIR"; then
    echo "RAW-014: Không tạo được thư mục báo lỗi." >&2
    rm -rf "$WORKDIR"
    exit 1
fi
chown mobile:mobile "$OUTDIR" "$LOGDIR" 2>/dev/null || true
chmod 755 "$OUTDIR" "$LOGDIR" 2>/dev/null || true
report() { printf '%s\n' "$*" | tee -a "$LOG"; }
finish() {
    for source in "$LOG" "$ENGINELOG"; do
        if [ -f "$source" ]; then
            case "$source" in "$LOG") destination="$LOGDIR/$STAMP.log";; *)
                destination="$LOGDIR/$STAMP.engine.log";;
            esac
            if ln "$source" "$destination" 2>/dev/null; then
                chmod 644 "$destination" || true
                chown mobile:mobile "$destination" 2>/dev/null || true
            fi
        fi
    done
    rm -rf "$WORKDIR"
}
trap finish EXIT
trap 'exit 130' INT TERM
abort() { report "RESULT: FAIL $1 - $2"; exit 1; }

report "IPARanger VN experimental RAW IPA test / $STAMP"
report "INPUT_NAME=$(basename "$INPUT")"
report "STAGE: PRECHECK"
[ "$(id -u)" -eq 0 ] || abort RAW-005 "Cần terminal root; không dùng --force để bỏ kiểm tra quyền."
[ -x "$ENGINE" ] || abort RAW-004 "Không tìm thấy helper hợp lệ."
if [ ! -e /var/jb/basebin/libjailbreak.dylib ] && [ ! -e /var/jb/usr/lib/libjailbreak.dylib ]; then
    abort RAW-006 "Thiếu libjailbreak; không tương thích môi trường rootless hiện tại."
fi
command -v unzip >/dev/null 2>&1 || abort RAW-004 "Thiếu unzip."
unzip -Z -1 "$INPUT" > "$LIST" 2>/dev/null || abort RAW-001 "Tệp ZIP bị lỗi."
if grep -Eq '(^/|(^|/)\.\.(/|$)|\\)' "$LIST"; then
    abort RAW-001 "Đường dẫn ZIP có nguy cơ thoát ra ngoài thư mục giải nén."
fi
grep -Eq '^Payload/[^/]+[.]app/Info[.]plist$' "$LIST" || abort RAW-002 "Sai cấu trúc Payload hoặc không tìm thấy Info.plist."
grep -Eq '^Payload/[^/]+[.]app/SC_Info/[^/]+[.]sinf$' "$LIST" || abort RAW-003 "Không có SC_Info/*.sinf cho IPA này."
FILE_KB="$(du -k "$INPUT" | awk '{print $1}')"
FREE_KB="$(df -Pk "$OUTDIR" | awk 'END {print $4}')"
if [ -n "$FILE_KB" ] && [ -n "$FREE_KB" ] && [ "$FREE_KB" -lt "$((FILE_KB * 4))" ]; then
    abort RAW-007 "Dung lượng trống không đủ để tạo staging và IPA mới."
fi
BASE="$(basename "$INPUT" | sed -E 's/[.][iI][pP][aA]$//' | tr -cd 'A-Za-z0-9._-' | cut -c1-80)"
[ -n "$BASE" ] || BASE=application
FINAL="$OUTDIR/\${BASE}_decrypted_\${STAMP}.ipa"
[ ! -e "$FINAL" ] || abort RAW-014 "Tệp đầu ra đã tồn tại."
report "STAGE: DECRYPT"
if ! "$ENGINE" package -i "$INPUT" -o "$STAGED" -v > "$ENGINELOG" 2>&1; then
    report "ENGINE_LOG=$LOGDIR/$STAMP.engine.log"
    if grep -Eqi 'SC_Info|sinf|license metadata|missingRootSinf' "$ENGINELOG"; then
        abort RAW-003 "Thiếu hoặc sai metadata cấp phép FairPlay."
    elif grep -Eqi 'libjailbreak|jbclient|proc_csflags_set|permission setup' "$ENGINELOG"; then
        abort RAW-006 "Quyền jailbreak chưa được khởi tạo đúng."
    elif grep -Eqi 'permission denied|mkdir staging|chown failed|staged app' "$ENGINELOG"; then
        abort RAW-008 "Không tạo hoặc truy cập được vùng staging."
    elif grep -Eqi 'mremap_encrypted|fairplay|authorization|EPERM' "$ENGINELOG"; then
        abort RAW-009 "Hệ thống từ chối xử lý vùng FairPlay."
    fi
    abort RAW-010 "Engine lỗi không xác định; xem nhật ký để phân tích."
fi
report "STAGE: VERIFY_ARCHIVE"
[ -s "$STAGED" ] || abort RAW-011 "Engine không tạo được IPA."
unzip -t -qq "$STAGED" >/dev/null 2>&1 || abort RAW-011 "ZIP đầu ra lỗi."
if unzip -Z -1 "$STAGED" | grep -Eq '(^|/)SC_Info/'; then
    abort RAW-015 "IPA đầu ra còn chứa SC_Info; từ chối xuất tệp."
fi
ln "$STAGED" "$FINAL" || abort RAW-014 "Không thể lưu IPA mới an toàn."
chmod 644 "$FINAL" || true
chown mobile:mobile "$FINAL" 2>/dev/null || true
report "OUTPUT=$FINAL"
report "RESULT: RAW-013 Đã tạo IPA thử nghiệm. Chưa xác nhận mọi Mach-O hay khả năng cài TrollStore. Hãy nhập IPA vào IPARanger để kiểm tra lại."
