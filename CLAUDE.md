# Quy tắc làm việc trong dự án này

- **Bắt buộc ghi nhật ký:** sau MỖI lần chỉnh sửa mã nguồn, tham số hay tài liệu, thêm một mục vào đầu
  `CHANGELOG.md` (mới nhất ở trên) gồm: ngày, yêu cầu của người dùng, nội dung đã sửa theo từng file,
  kiểm tra đã chạy (pytest, đối chiếu Excel), việc còn treo. Viết bằng tiếng Việt.
- Sửa công thức trong `dutoan/calc.py` thì sửa tương ứng trong `dutoan/excel_export.py` (hai bên phải khớp),
  rồi chạy `python -m pytest`.
- Không sửa 2 file template Excel và 2 file yêu cầu `.md` gốc.
- **Git:** repo `https://github.com/hs5011/UngDungXuatDuToan.git` (nhánh `main`, CÔNG KHAI). Sau mỗi lần người dùng
  duyệt thay đổi: ghi CHANGELOG → `git add` → `git commit` (mô tả tiếng Việt) → `git push`. Chưa duyệt thì chưa đẩy.
- Không đẩy 2 template Excel và 2 file yêu cầu `.md` gốc (đã chặn trong `.gitignore`) trừ khi người dùng cho phép.
- **Chuẩn bảng (bắt buộc cho mọi bảng mới/sửa):**
  - Mọi dòng cao **35 px** (bảng lưới: `ed_height(..., ROW_STD)`, không dùng `row_height`; bảng HTML `.tbl` cố định 35 px),
    chữ không xuống dòng; bảng rộng thì cuộn ngang.
  - Bảng sửa được dùng `editor()` (cột rộng vừa nội dung, không kéo giãn); bảng chỉ xem dùng `show_table()`/`html_table()`.
  - Số tiền có dấu chấm phân cách, căn phải; dòng nhóm I–V in đậm nền xám, dòng TỔNG CỘNG in đậm nền xanh.
  - Bảng liệt kê khoản mục chi phí phải chia theo nhóm I, II, III, IV, V.
- **Chuẩn nhập liệu:** ô tiền dùng `money()`/`money_input()` (nhãn chứa "(đồng)", tự chèn dấu chấm khi gõ);
  ô ngày dùng `date_field()` dạng dd/mm/yyyy; thẻ số liệu dùng `kpi_cards()` (hiện đủ số, không cắt).

