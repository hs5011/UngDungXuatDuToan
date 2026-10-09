# NHẬT KÝ CHỈNH SỬA

> Mỗi lần chỉnh sửa ứng dụng đều ghi lại ở đây, mới nhất ở trên cùng.
> Mỗi mục gồm: ngày, yêu cầu, nội dung đã sửa (theo file), kiểm tra đã chạy, việc còn treo.

---

## 2026-10-09 – Lượt 19: Chọn dự án như App_TestHieuNang (tự lưu, chọn lại, tạo, xoá)
**Yêu cầu:** Bổ sung chỗ "Dự án" cho phép chọn dự án như thiết kế ở App_TestHieuNang (PerfTool).

**Đã làm**
- `dutoan/storage.py` (mới): lưu mỗi dự án thành `workspace/projects/<thời gian>-<tên-không-dấu>.json` (ghi nguyên tử),
  liệt kê (mới nhất trước, báo file hỏng), tạo mới (rỗng hoặc từ file .json nhập vào), đọc, xoá.
- `app.py`
  - Thanh bên: ô chọn **Dự án** ("— Chọn dự án —", mỗi dòng "tên · dd/mm/yyyy"); mục **➕ Tạo dự án mới** (nhập tên →
    Tạo dự án; hoặc nhập từ file .json); mục **⚠️ Xoá dự án** ở cuối (bấm "Xoá dự án này" → "Xác nhận xoá"/"Huỷ").
  - Chưa chọn dự án: trang chào hướng dẫn quy trình 9 bước.
  - **Tự động lưu** dự án đang mở sau mỗi thay đổi; chọn lại dự án là nạp đúng dữ liệu đã lưu.
  - Bỏ ô "Dự án" chỉ đọc và mục "📂 Mở / tạo dự án" cũ; 9b đổi thành "Sao lưu dự án về máy tính" và hướng dẫn nhập lại.
- `.gitignore`: bỏ qua `workspace/` (dữ liệu dự án cá nhân, không đưa lên GitHub công khai).
- `tests/test_storage.py` (mới): 3 kiểm thử tạo/lưu/mở/xoá, nhập từ .json, file hỏng.
- `README.md`: thêm hướng dẫn chọn/tạo/xoá dự án.

**Kiểm tra**
- `python -m pytest`: 25/25 đạt.
- Trình duyệt: tạo "Thử nghiệm A" → sửa Gms 6 tỷ → file tự lưu (Gms 6 tỷ) → tải lại trang, chọn lại dự án → Gms 6 tỷ;
  xoá dự án (2 bước) → file bị xoá, về trang chào. Bước 9 không lỗi.

**Git:** đã duyệt – đẩy lên GitHub cùng lượt 14–18.

---

## 2026-10-09 – Lượt 18: Ghi rõ cách lưu và mở lại dự án (.json)
**Yêu cầu:** Mục 9b "Lưu dự án" chưa rõ – phải ghi rõ là tải file json về máy tính để lưu trữ và mở lại bằng mục nào.

**Đã sửa** – `app.py`
- 9b đổi tên "Lưu dự án về máy tính"; thêm giải thích: ứng dụng không tự lưu, đóng/tải lại trang là mất dữ liệu; file
  .json chứa toàn bộ thông tin, tham số, thiết bị, công việc đã sửa, ghi chú, phân bổ vốn.
- Nút đổi thành "💾 Tải file dự án về máy (<tên>.json)", nổi bật (màu chính).
- Hướng dẫn mở lại từng bước: thanh bên trái → 📂 Mở / tạo dự án → Browse files (hoặc kéo thả) → chọn file .json;
  ghi chú file nằm ở thư mục tải về của trình duyệt (thường là Downloads).
- Thanh bên: ô mở file đổi nhãn "Mở file dự án (.json) đã lưu trên máy", có chú thích trỏ về bước 9b.

**Kiểm tra:** trình duyệt – bước 9 hiển thị đủ hướng dẫn, không lỗi.

**Git:** đã đẩy lên GitHub (cùng lượt 19).

---

## 2026-10-09 – Lượt 17: Đồng nhất chuẩn bảng toàn hệ thống
**Yêu cầu:** Bảng 6b dòng vẫn quá cao; xem và đồng nhất tất cả bảng trong hệ thống theo chuẩn đã nói.

**Chuẩn áp dụng (đã ghi vào `CLAUDE.md`):** mọi dòng cao 35 px, chữ không xuống dòng (bảng rộng thì cuộn ngang);
cột rộng vừa nội dung; số tiền dấu chấm căn phải; dòng nhóm I–V và TỔNG CỘNG in đậm; bảng khoản mục chia nhóm I–V.

**Đã sửa** – `app.py`
- Bỏ hẳn dòng cao 66 px (`ROW_H`): 6a (sửa ghi chú) và 6b dùng dòng 35 px như mọi bảng; cột chữ cho rộng tới
  620/720 px để hiện đủ nội dung trên một dòng.
- Bảng HTML (`.tbl`: 3b, 4a, 6a, 7b, 8c) từ 38 px (có dòng 61 px do xuống dòng) về đúng 35 px, không xuống dòng, có khung
  cuộn ngang khi rộng.
- 6b: cột "Nhóm chi phí" rút gọn (bỏ chữ "Chi phí" đầu), ví dụ "E. Lập E-HSMT, đánh giá E-HSDT (tv4)".
- `ed_height()` mặc định dùng dòng chuẩn 35 px.
- `CLAUDE.md`: thêm mục "Chuẩn bảng" và "Chuẩn nhập liệu" để các lần sửa sau tuân theo.

**Kiểm tra:** đo trên trình duyệt – mọi bảng HTML ở bước 3, 4, 6, 7, 8 cao đúng 35 px/dòng; 9 bước không lỗi;
`python -m pytest` 22/22 đạt.

**Git:** đã đẩy lên GitHub (cùng lượt 19).

---

## 2026-10-09 – Lượt 16: Bảng 7a, 7b chia theo nhóm I–V
**Yêu cầu:** Bảng 7a, 7b phải có các mục I, II, III… để biết khoản chi phí thuộc nhóm nào.

**Đã sửa** – `app.py` (`step_phan_bo` viết lại)
- 7a: thêm dòng nhóm (I CHI PHÍ TRANG THIẾT BỊ, II QLDA, III TƯ VẤN, IV KHÁC, V DỰ PHÒNG) trước các khoản của nhóm; cột STT
  thay cho cột mã nội bộ (pm, thiet_bi…); dòng nhóm để trống %, sửa vào sẽ bị bỏ qua; nội dung khoản mục thụt lề.
- 7b: chuyển sang bảng HTML giống 6a – dòng nhóm in đậm nền xám kèm tổng của nhóm theo từng năm, dòng TỔNG CỘNG in đậm
  nền xanh, cột số căn phải; thêm chú thích cột "Còn lại".

**Kiểm tra:** trình duyệt – 7a, 7b hiện đủ nhóm I–V, số nhóm khớp tổng các khoản; không lỗi.

**Git:** đã đẩy lên GitHub (cùng lượt 19).

---

## 2026-10-09 – Lượt 15: Bảng 7a dòng cao chuẩn
**Yêu cầu:** Bảng 7a (tỷ lệ phân bổ) có dòng quá cao, không đồng nhất với các bảng khác.

**Đã sửa** – `app.py`: bảng 7a bỏ dòng cao 66 px, dùng dòng chuẩn 35 px; cột "Nội dung" cho phép rộng tới 620 px nên tên
khoản mục dài vẫn hiện đủ trên một dòng (không cần xuống dòng).

**Kiểm tra:** trình duyệt – 7a dòng thấp như các bảng khác, đủ 18 khoản mục, không lỗi.

**Git:** đã đẩy lên GitHub (cùng lượt 19).

---

## 2026-10-09 – Lượt 14: Độ rộng cột bảng vừa đủ nội dung
**Yêu cầu:** Rút ngắn chiều rộng các cột trong bảng cho vừa đủ (ví dụ cột "Công việc" ở 3a thừa nhiều khoảng trắng).

**Đã sửa** – `app.py`
- Hàm mới `editor()` thay cho mọi `st.data_editor`: tự tính độ rộng từng cột theo chữ dài nhất (tiêu đề, nội dung, lựa
  chọn của ô chọn), ~7,4 px/ký tự, tối đa 380 px; bảng co theo tổng độ rộng cột (`width="content"`) thay vì kéo giãn.
- Cột khai báo small/medium/large được hiểu là độ rộng tối thiểu 64/150/240 px (để bảng còn trống vẫn đủ chỗ gõ).
- Bảng nhập liệu bước 2, 5: cột tên khoản mục/vị trí rộng tối thiểu 240 px; phương pháp, nguồn giá, ghi chú 150 px.
- Áp dụng cho 8 bảng: bước 2, 3a, 4b, 5, 6a (sửa ghi chú), 6b, 7a, 8 (bảng NĐ 193, TT 28).

**Kiểm tra:** trình duyệt – 3a cột "Công việc" vừa khít dòng dài nhất; bước 2–8 không lỗi. Không đổi lõi tính toán.

**Git:** đã đẩy lên GitHub (cùng lượt 19).

---

## 2026-10-09 – Lượt 13: Đưa mã nguồn lên GitHub
**Yêu cầu:** Đẩy code lên `https://github.com/hs5011/UngDungXuatDuToan.git`; từ nay đẩy sau mỗi lần người dùng duyệt.

**Đã làm**
- `git init` nhánh `main`, thêm remote `origin`, commit toàn bộ mã nguồn, kiểm thử, tài liệu, cấu hình.
- `.gitignore` (mới): bỏ `__pycache__`, `.pytest_cache`, file dự án `.json` người dùng lưu ra; **tạm không đẩy** 2 template
  Excel và 2 file yêu cầu `.md` gốc vì repo đang ở chế độ công khai – chờ người dùng xác nhận.
- `CLAUDE.md`: thêm quy trình git (duyệt → ghi CHANGELOG → commit → push).

---

## 2026-10-09 – Lượt 12: Bỏ khoảng trống phía trên thanh bên trái
**Yêu cầu:** Thanh bên trái cũng còn khoảng trống phía trên – rút gọn.

**Nguyên nhân:** ô đầu thanh bên của Streamlit (chứa nút thu gọn «) cao 60px, cộng khoảng đệm 16px trước tiêu đề.

**Đã sửa** – `app.py` (CSS): `stSidebarHeader` cao 2rem; `stSidebarUserContent` bỏ đệm trên, kéo lên 0,5rem;
tiêu đề "Dự toán PM" bỏ lề trên.

**Kiểm tra:** trình duyệt – tiêu đề thanh bên cách mép trên 24px (trước 76px); nút « vẫn nằm góc phải trên.

---

## 2026-10-09 – Lượt 11: Bỏ vùng trống phía trên các trang
**Yêu cầu:** Ở mọi màn hình có một vùng trắng phía trên tiêu đề trang – rút gọn và bỏ đi.

**Nguyên nhân:** (1) Streamlit mặc định đệm ~6rem phía trên nội dung trang; (2) khung ẩn chứa script định dạng số
(`components.html(FMT_SCRIPT)`) nằm đầu trang chính nên chiếm thêm một dòng trống.

**Đã sửa** – `app.py`
- CSS: `.block-container` / `stMainBlockContainer` đệm trên còn 1,5rem.
- Dời khung script định dạng số vào cuối thanh bên, ẩn hẳn khung đó (cao 0) → không tạo khoảng trống ở trang chính.

**Kiểm tra:** trình duyệt – tiêu đề "1. Nhập thông tin dự án" cách mép trên 40px (trước ~150px); gõ 4200000000 vào ô Gms
vẫn tự hiện "4.200.000.000" (script vẫn chạy).

---

## 2026-10-09 – Lượt 10: Thu gọn tiếp khoảng trống thanh bên
**Yêu cầu:** Các khoảng trống quanh 2 đường kẻ ngang ở thanh bên (trên/dưới thẻ TMĐT, dưới dòng cảnh báo) vẫn còn cao.

**Nguyên nhân:** mỗi phần tử Streamlit có khoảng cách cố định ~1rem; thẻ `<hr>` trong markdown bị bỏ class nên vẫn
dùng lề mặc định 32px (và đường kẻ không hiện màu).

**Đã sửa** – `app.py`
- Gộp đường kẻ + thẻ TMĐT + dòng cảnh báo + đường kẻ + tiêu đề "CÁC BƯỚC THỰC HIỆN" thành **một khối HTML**
  (`.sb-block`) → không còn khoảng cách giữa các phần tử.
- Đường kẻ dùng `<div class='sb-hr'>` (lề 0,55rem), `kpi_cards(..., as_html=True)` trả về HTML để ghép khối.

**Kiểm tra (đo trên trình duyệt):** "Mở / tạo dự án" → đường kẻ 15px; đường kẻ → thẻ TMĐT 9px; cảnh báo → đường kẻ 9px;
đường kẻ → "CÁC BƯỚC THỰC HIỆN" 9px; tiêu đề → nút 1: 9px (trước đây 32–40px).

---

## 2026-10-09 – Lượt 9: Thanh ngang dưới "Mở / tạo dự án", thu gọn khoảng trống thanh bên
**Yêu cầu:** (1) thêm thanh ngang dưới mục "Mở / tạo dự án"; (2) rút ngắn khoảng trống dưới dòng cảnh báo.

**Đã sửa** – `app.py`
- Thêm đường kẻ ngang mảnh (`.sb-hr`) dưới mục "Mở / tạo dự án", trước thẻ Tổng mức đầu tư.
- Dòng "⚠️ … cảnh báo" đổi sang khối chữ gọn (`.sb-warn`); thay `st.divider()` (lề lớn) bằng đường kẻ mảnh lề nhỏ
  ngay trước "CÁC BƯỚC THỰC HIỆN" → khoảng trống giảm rõ.

**Kiểm tra:** trình duyệt – thanh bên hiện đường kẻ dưới "Mở / tạo dự án", khoảng cách cảnh báo → danh sách bước gọn.
Không đổi lõi tính toán.

---

## 2026-10-09 – Lượt 8: Đưa thẻ TMĐT lên đầu menu, dòng bảng 3a/5a/5b cao chuẩn
**Yêu cầu:** (1) Chuyển khối Tổng mức đầu tư (thanh bên) lên trước "Các bước thực hiện"; (2) dòng của bảng 3a, 5a, 5b
quá cao, không đồng nhất với các bảng khác.

**Đã sửa** – `app.py`
- Thanh bên: thẻ TMĐT (kèm Gms, dự phòng) và dòng cảnh báo nằm ngay dưới mục "Mở / tạo dự án", trước danh sách bước.
- Bảng 3a và các bảng nhập liệu bước 2, 5 (5a lương, 5b chi khác): bỏ dòng cao 66px, về dòng chuẩn 35px như các bảng
  khác; khung bảng vẫn cao theo số dòng (`ed_height(..., ROW_STD)`).
- Giữ dòng cao (tự xuống dòng) cho 6a sửa ghi chú, 6b so sánh văn bản, 7a tỷ lệ phân bổ – các bảng có chữ dài.

**Kiểm tra:** trình duyệt – thanh bên hiện thẻ TMĐT ở trên; 3a hiện đủ 7 dòng chuẩn; bước 2, 3, 5 không lỗi.
Không đổi lõi tính toán.

---

## 2026-10-09 – Lượt 7: Chữ trong bảng hiện đầy đủ, tự xuống dòng
**Yêu cầu:** Các ô chữ trong bảng (ví dụ "Nhóm chi phí", "Công việc" ở 6b) đang bị cắt; hiện đầy đủ và tự ngắt dòng
như bảng 6a.

**Đã sửa** – `app.py`
- `show_table()` (mọi bảng chỉ để xem) chuyển từ `st.dataframe` sang bảng HTML giống 6a: chữ tự xuống dòng, cao theo nội
  dung, cột số căn phải, số thập phân dạng 2,15. Áp dụng: 3b tổng hợp nhóm, 4a bảng nhân công, 7b số tiền theo năm,
  8c đơn giá kỹ sư. In đậm dòng cộng/tổng (3b: trước thuế, sau thuế; 4a: TỔNG; 7b: TỔNG CỘNG).
- Bảng sửa được (lưới Streamlit chỉ cho xuống dòng khi dòng cao > 64px): đặt `row_height = 66` và khung bảng cao
  theo số dòng (`ed_height()`), không phải cuộn trong bảng. Áp dụng: bảng nhập bước 2 và 5, 3a công việc,
  6a sửa ghi chú, 6b so sánh văn bản, 7a tỷ lệ phân bổ. Bảng 4b (vai trò ngắn) giữ dòng thấp.

**Kiểm tra**
- Trình duyệt: 6b chữ "Nhóm chi phí", "Công việc" xuống 2 dòng, đọc đủ; 3a hiện đủ 7 dòng + dòng thêm mới;
  4a bảng HTML có dòng TỔNG in đậm; các bước 2, 3, 4, 5, 6, 7, 8 không lỗi.
- Không đổi lõi tính toán (kiểm thử 22/22 giữ nguyên).

**Lưu ý:** cột cuối "Căn cứ văn bản" ở 6b vẫn cần kéo ngang khi màn hình hẹp (bảng có 9 cột).

---

## 2026-10-09 – Lượt 6: Định dạng số khi nhập, ngày dd/mm/yyyy, thêm việc ngay trên bảng 3a, làm rõ bảng 6a/6b
**Yêu cầu (8 mục):** (1) nhập Gms phải thấy TMĐT tương ứng; (2) ô nhập số có dấu phân cách ngay khi gõ;
(3) ô ngày dạng dd/mm/yyyy + chọn lịch; (4) thêm việc mới ngay trên bảng 3a, không tách mục riêng;
(5) 6a in đậm các dòng I–V, tổng cộng; (6) 6a ẩn dòng = 0 ở mục I; (7) 6a có ghi chú cho mọi dòng, sửa được;
(8) 6b khó hiểu (E1, E2… là gì).

**Đã sửa**
- `app.py`
  - (1) Bước 1b: nhập Gms → thẻ "→ Tổng mức đầu tư tính ra"; nhập TMĐT → thẻ "→ Gms tương ứng".
  - (2) Ô tiền đổi sang ô chữ có định dạng: script `FMT_SCRIPT` chèn dấu chấm hàng nghìn **ngay khi gõ**
    (giữ vị trí con trỏ), áp dụng cho mọi ô có nhãn chứa "(đồng)"; hàm `money_input()`/`parse_money()`.
    Áp dụng: bước 1, 3c (Ck, ghi đè tổng nhóm), 5, 8 (lương, ngưỡng, mốc neo, NĐ 214…).
    Ô trong bảng nhập liệu (đơn giá…) hiển thị dạng có phân cách (`localized`).
  - (3) Thời điểm lập: `st.date_input` định dạng DD/MM/YYYY, gõ tay hoặc chọn lịch; lưu yyyy-mm-dd.
  - (4) Bước 3: bỏ mục "Công việc bổ sung"; bảng 3a cho thêm dòng (➕ / dòng trống cuối bảng), xoá dòng (🗑 hoặc
    tick Xoá), sửa tên việc. Việc tự thêm mã A+1…, hiện "nhập tay" ở cột Tự động. Mục đổi số: 3b tổng hợp,
    3c điều chỉnh, 3d QĐ 1688.
  - (5)(6)(7) Bước 6a: bảng HTML – dòng I…V in đậm nền xám, TỔNG CỘNG in đậm nền xanh; số căn phải; ẩn dòng = 0
    ở mục I (công tắc "Hiện cả các dòng bằng 0"); cột Ghi chú có nội dung cho mọi dòng; mục
    "✏️ Sửa cột Ghi chú" để sửa, có nút khôi phục mặc định.
  - (8) Bước 6b: đoạn giải thích (văn bản nào quy định, Mã việc = mã dòng ở bước 3, A = QLDA … E = tv4 lập
    E-HSMT, F = tv5 thẩm định); bảng có cột Mã việc, Nhóm chi phí, Công việc, Theo chuyên gia, Theo văn bản,
    Chênh lệch, **Dùng VB** (tick ngay tại đây), Căn cứ văn bản. Liệt kê mọi việc có số văn bản, không chỉ lệch > 50%.
- `dutoan/calc.py`: ghi chú mặc định `DEFAULT_NOTES`, `SEC_NOTES`; `res.compare` thành danh sách có cấu trúc;
  cho phép đổi tên việc mặc định (`ghi_de[...]["ten"]`).
- `dutoan/defaults.py`: thêm `ghi_chu` (ghi chú người dùng sửa).
- `dutoan/excel_export.py`: cột Ghi chú BẢNG TMĐT dùng ghi chú đã sửa, có ghi chú cho dòng I–V;
  thời điểm lập ghi dạng dd/mm/yyyy.
- `tests/test_calc.py`: +2 kiểm thử (đổi tên việc, ghi chú mặc định, so sánh văn bản).

**Kiểm tra**
- `python -m pytest`: 22/22 đạt. Excel 16 tính lại 6 kịch bản: khớp Python đến từng đồng.
- Trình duyệt: gõ 5250000000 → ô hiện "5.250.000.000" ngay khi gõ; thẻ TMĐT tính ra cập nhật; thêm việc
  "Hop khoi dong" trên bảng 3a (A+1, tổng nhóm 159,7 → 162,4 triệu) rồi xoá bằng 🗑 (về 159,7); 9 bước không lỗi.

---

## 2026-10-09 – Lượt 5: Thêm/xoá công việc, bố cục bước 3 theo hàng, bảng 6a cao hơn
**Yêu cầu:** (1) Thêm hoặc xoá bớt công việc trong bảng 3a; (2) 3b, 3c, 3d để 3 cột khó đọc → mỗi phần một hàng,
giải thích rõ là gì; (3) bảng 6a tăng chiều cao để thấy nhiều dòng hơn.

**Đã sửa**
- `dutoan/defaults.py`: thêm khoá `viec_them` (công việc người dùng tự thêm theo từng nhóm).
- `dutoan/calc.py`: `compute_group()` cộng các công việc bổ sung (mã `A+1`, `B+1`…): số CG × số ngày × hệ số × đơn giá
  ngày theo bậc; không co giãn theo Gms; đi qua Cql/TN/VAT như việc thường.
- `dutoan/excel_export.py`: việc bổ sung xuất vào sheet nhóm, hệ số là ô nhập (nền vàng), ghi chú "Công việc bổ sung".
- `app.py` – bước 3 sắp xếp lại, mỗi phần một hàng ngang toàn trang:
  - 3a Bảng công việc: cột "Bỏ" đổi thành **Xoá** (tick = loại khỏi dự toán, bỏ tick = khôi phục); thêm chú thích
    từng cột; cột "Công việc" rộng hơn.
  - 3b **Công việc bổ sung (mới)**: bảng thêm/xoá dòng tự do (Công việc, Bậc, Số CG, Số ngày, Hệ số).
  - 3c Tổng hợp chi phí của nhóm: bảng có thêm cột **Cách tính** (Ccg → Cql → Ck → TN → VAT), bên phải là thẻ
    TỔNG NHÓM và trước thuế (số đầy đủ).
  - 3d Điều chỉnh thủ công: Ck · ghi đè tổng nhóm · nút "Khôi phục mặc định của nhóm" nằm cùng một hàng.
  - 3e Tham chiếu QĐ 1688: công thức đầy đủ + thẻ số tiền + nút dùng số định mức.
  - `show_table(height="all")`: bảng cao đủ hiện mọi dòng; áp dụng cho bảng 6a và 3c.
- `tests/test_calc.py`: thêm kiểm thử thêm việc + xoá việc.

**Kiểm tra**
- `python -m pytest`: 20/20 đạt.
- Excel 16 tính lại 6 kịch bản (có thêm việc bổ sung ở nhóm B): khớp Python đến từng đồng.
- Trình duyệt: thêm việc "Hop thu nghiem" vào nhóm A → tổng nhóm 159,7 → 162,4 triệu, TMĐT tự tính lại;
  bảng 6a hiện toàn bộ dòng không cần cuộn; bước 3, 6 không lỗi. Sau đó đã tạo lại dự án mặc định để xoá dữ liệu thử.

---

## 2026-10-09 – Lượt 4: Thiết kế lại thẻ số liệu (không còn bị cắt "…")
**Yêu cầu:** Các thẻ số liệu (Gms, Nhân công, TMĐT, Dự phòng, Thuế GTGT…) bị cắt thành "3.000.0…", không đọc được tổng tiền.

**Đã sửa** – `app.py`
- Bỏ `st.metric` (Streamlit tự cắt số dài). Thêm hàm `kpi_cards()` vẽ thẻ HTML riêng:
  - dòng 1: tên chỉ tiêu; dòng 2: **số tiền đầy đủ** (chữ đậm, tự xuống dòng nếu hẹp) + đơn vị "đ";
  - dòng 3: quy đổi gọn "≈ 4,51 tỷ đồng" / "≈ 409,3 triệu đồng" (hàm `ty_dong()`);
  - dòng cuối (gạch đứt): ghi chú cách tính.
  - Thẻ chính (TMĐT, Gms) có viền và chữ xanh đậm để nổi bật.
- Thẻ lưới tự co: 4 thẻ/hàng trên màn hình rộng, tự xuống hàng khi hẹp.
- Áp dụng ở: thanh bên (TMĐT + Gms + dự phòng), bước 3d (theo định mức QĐ 1688), bước 4 (Gms, NC, man-month,
  CPC + TNCT hoặc thuê PM), bước 6 (TMĐT, Gms, dự phòng, thuế GTGT).
- Thẻ man-month thêm quy đổi "≈ … người-năm"; thẻ CPC + TNCT ghi tách từng khoản.

**Kiểm tra**
- Trình duyệt 1400 px: bước 4 và 6 hiện đủ 4 thẻ một hàng, số không bị cắt; bước 3, 4, 6 không lỗi.
- Không đổi lõi tính toán → kết quả kiểm thử 19/19 giữ nguyên.

---

## 2026-10-09 – Lượt 3: Chuyển tab sang menu bên trái, sắp xếp lại bố cục
**Yêu cầu:** Thay các tab bằng menu bên trái như ảnh mẫu (PerfTool), chỉnh bố cục các phần cho rõ ràng.

**Đã sửa**
- `app.py` (viết lại phần giao diện, không đổi cách tính):
  - Thanh bên: tên ứng dụng + phiên bản 1.1.0, ô tên dự án, mục "📂 Mở / tạo dự án" (gộp mở JSON, tạo mới),
    nhóm **CÁC BƯỚC THỰC HIỆN** gồm 9 nút; bước đang mở tô màu, ✅ cho bước đã có dữ liệu; dưới cùng là TMĐT,
    Gms, dự phòng, số cảnh báo.
  - Mỗi bước là một trang: tiêu đề đánh số, dòng mô tả, các khung có viền đánh số 1a/1b/1c…
  - Thứ tự bước: 1 Nhập thông tin → 2 Thiết bị & dịch vụ → 3 Chi tiết công việc → 4 PM nội bộ → 5 QLDA tự thực hiện
    → 6 Tổng hợp chi phí → 7 Phân bổ vốn → 8 Cấu hình nâng cao → 9 Xuất Excel & lưu.
  - Nút "← bước trước / bước sau →" cuối mỗi trang.
  - Bước 3: chọn nhóm A–J bằng nút chọn ngang; bật/tắt nhóm bằng công tắc; 3b tổng hợp · 3c điều chỉnh · 3d QĐ 1688.
  - Bước 4, 6: thêm thẻ số liệu chính.
  - Nút Xuất Excel / Lưu JSON chuyển vào bước 9.
  - Sửa: bảng nhập liệu được dựng lại từ dữ liệu dự án khi quay lại một bước (Streamlit xoá trạng thái bảng của
    bước không hiển thị) → không mất dữ liệu đã nhập.
- `.streamlit/config.toml` (mới): màu chính xanh đậm #2F4A9E như ảnh mẫu; tắt gửi thống kê.
- `README.md`: cập nhật phần "Cách dùng" theo menu mới.

**Kiểm tra**
- `python -m pytest`: 19/19 đạt (lõi tính toán không đổi).
- Trình duyệt: mở lần lượt 9 bước – không lỗi; nhập tên dự án, chuyển sang bước 6 rồi quay lại – dữ liệu còn nguyên.

**Còn treo:** như lượt 1 (thuế PM nội bộ 0% hay 8%; tỷ lệ NĐ 19 = 17%).

---

## 2026-10-09 – Lượt 2: Bắt đầu ghi nhật ký
**Yêu cầu:** "Mỗi lần chỉnh sửa hãy ghi log lại cho tôi."

**Đã làm**
- Tạo `CHANGELOG.md` (file này) và ghi lại lượt 1.
- Thêm `CLAUDE.md`: quy tắc bắt buộc cập nhật nhật ký sau mỗi lần sửa.

**Kiểm tra:** không đổi mã nguồn → không cần chạy lại kiểm thử.

---

## 2026-10-09 – Lượt 1: Viết ứng dụng lần đầu
**Yêu cầu:** Đọc `YEU-CAU-FINAL-pm-du-toan-tt39.md`, viết ứng dụng xuất dự toán; giữa chừng người dùng bổ sung 2 file template Excel.

**Tạo mới**
- `dutoan/catalog.py` – danh mục công việc A–J, mốc neo S/M/L, 9 tỷ lệ PM nội bộ, bảng QĐ 1688 (tham chiếu).
- `dutoan/defaults.py` – tham số mặc định; bảng NĐ 193, TT 28 lấy từ template.
- `dutoan/scaling.py` – mô hình co giãn (log-log, EXP 0,6, bậc thang số chuyên gia).
- `dutoan/calc.py` – tính G = Gtb/Gdv + Gqlda + Gtv + Gk + Gdp; giải Gms khi nhập TMĐT; phân bổ vốn.
- `dutoan/excel_export.py` – xuất Excel theo bố cục 2 template, công thức sống, tên ô (named range), bật tính lặp.
- `app.py` – giao diện Streamlit 8 tab.
- `tests/test_calc.py` – 19 bài kiểm thử.
- `README.md`, `requirements.txt`, `chay_ung_dung.bat`, `.claude/launch.json`.

**Điều chỉnh sau khi đọc template**
- Đơn giá ngày chuyên gia = ROUND(lương tháng × hệ số nâng / 26); làm tròn TN, trước thuế, VAT như sheet Cp_*.
- Đơn giá kỹ sư = (Hcb + Hpc) × MLcs × (1 + Hdc) + (Hcb + Hpc) × MLcs × 21,5% (sheet Dongia_NgayCong).
- PM nội bộ: bậc kỹ sư theo từng vai trò như template; thuế/phí PM mặc định 0%.
- Thuê PM = Gms ÷ 8 năm × số năm thuê (TONG_HOP - Thue).
- Kiểm toán/thẩm tra theo bảng NĐ 193 của template; cơ sở = Gtb + Gqlda + Gtv + lệ phí + thẩm định giá (trước thuế).
- Lệ phí thẩm định = TMĐT × tỷ lệ TT 28 × 50% (TT 64) × 50% (có thẩm tra).
- Kiểm thử TT 41 chuyển sang Gk (k5); thêm k4 thẩm định giá.
- Nhóm G, H, J dùng CPC 55% / TNCT 6% cố định.
- NĐ 214 tính kèm VAT; giá gói = Gtb trước thuế ÷ số gói.
- Làm tròn TMĐT lên; nếu vượt Kdp tối đa thì làm tròn xuống.
- Phân bổ vốn áp dụng cho cả chế độ XD (mặc định như template: chuẩn bị đầu tư năm đầu, còn lại năm cuối).

**Sửa lỗi trong quá trình làm**
- Excel không mở được file: ô ghi chú bắt đầu bằng "=" bị hiểu là công thức; tên ô "TB50" trùng địa chỉ ô → đổi "TB_50".
- Vòng lặp TMĐT ↔ kiểm toán trong Excel kẹt lỗi #VALUE! → thêm IFERROR.
- Giao diện: bảng hiển thị hẹp (đổi `use_container_width` → `width="stretch"`), lỗi kiểu dữ liệu bảng,
  công tắc 3 trạng thái hiện "Choose an option", kết quả trễ một lượt khi sửa tham số ở tab sau.

**Kiểm tra**
- `python -m pytest`: 19/19 đạt.
- Excel 16 tính lại 6 kịch bản (XD/Thuê, nhập Gms/TMĐT, ghi đè, QLDA tự TH, Gms 60 tỷ): khớp Python đến từng đồng.
- Bấm thử 8 tab trên trình duyệt, ghi đè và xóa ghi đè, chuyển chế độ Thuê + nhập TMĐT.

**Còn treo – cần người dùng xác nhận**
- Thuế PM nội bộ 0% (template) hay 8% (bản yêu cầu ghi "+ VAT").
- Tỷ lệ NĐ 19 = 17%; chưa đối chiếu toàn văn TT 28, TT 07 (điều kiện M2–M4), QĐ 320, Phụ lục III TT 41, lương cơ sở.
