# Ứng dụng xuất dự toán phần mềm – TT 39/2026/TT-BKHCN

Web app (Python + Streamlit) tính **TMĐT / dự toán** dự án phần mềm theo yêu cầu trong
`YEU-CAU-FINAL-pm-du-toan-tt39.md`, bám theo 2 template Excel trong thư mục này.

## Cài đặt và chạy

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

Hoặc bấm đúp `chay_ung_dung.bat`. Trình duyệt mở `http://localhost:8501`.

## Cách dùng

**Dự án:** ở thanh bên trái, ô **Dự án** chọn dự án đã có (tên · ngày cập nhật); **➕ Tạo dự án mới** để tạo theo tên
hoặc nhập từ file `.json`; **⚠️ Xoá dự án** ở cuối thanh bên. Dự án được **tự động lưu** sau mỗi thay đổi vào
`workspace/projects/<mã>.json` (thư mục này không đưa lên git).

Menu **Các bước thực hiện** ở thanh bên trái (bước đang mở tô xanh, ✅ = đã có dữ liệu); cuối mỗi trang có nút
← bước trước / bước sau →. Thanh bên luôn hiện TMĐT, Gms, dự phòng và số cảnh báo.

1. **Nhập thông tin**: 1a thông tin dự án · 1b giá trị đầu vào (Gms hoặc TMĐT), Kdp · 1c hệ số & công tắc · 1d QTVH (chế độ thuê).
2. **Thiết bị & dịch vụ**: 2a thiết bị · 2b PM thương mại · 2c lắp đặt/CSDL/vận chuyển · 2d dịch vụ thuê năm · 2e chi phí khác Gk.
3. **Chi tiết công việc**: chọn nhóm A–J; 3a bảng công việc (sửa tay = ghi đè, tick **Dùng VB** để lấy số NĐ 214/NĐ 19)
   · 3b tổng hợp nhóm · 3c Ck, ghi đè tổng nhóm · 3d tham chiếu QĐ 1688.
4. **Phần mềm nội bộ**: man-month suy ngược từ Gms; sửa tỷ lệ và bậc kỹ sư từng vai trò.
5. **QLDA tự thực hiện**: Mẫu 02/DT-QLDA + nội dung chi Điều 30 NĐ 10/2021.
6. **Tổng hợp chi phí**: thẻ số liệu chính, cảnh báo, bảng TMĐT, so sánh với văn bản.
7. **Phân bổ vốn**: tỷ lệ % theo năm và số tiền từng năm.
8. **Cấu hình nâng cao**: lương, Bảng 3.2, mô hình co giãn, đơn giá kỹ sư, bảng NĐ 193/TT 28, NĐ 214...
9. **Xuất Excel & lưu**: tải file Excel; tải file dự án .json để sao lưu/chuyển máy (nhập lại ở **➕ Tạo dự án mới**).

## File Excel xuất ra

Bố cục theo 2 template (`01_THAM_SO`, `BẢNG TMĐT`, `Bang Tong hop_Phan bo von`, `1. Cp_LAP BCKTKT` … `6. Cp_TV THAM DINH THAU`,
`BANGLUONG_CG`, `Dongia_NgayCong`, `1_GMS_THIET_BI`, `2_GMS_PM_TM`, `3_GMS_PM_NOI_BO`, `6_DAO_TAO`, `7_TRIEN_KHAI`,
`QTVH`, `KIEM_THU_TT41`, `TONG_HOP - XD/Thue`, `DinhMuc_ND193_TT28`). Mọi số tiền là **công thức sống**, tham chiếu
tham số theo tên ở sheet `01_THAM_SO` (ô nền vàng là ô nhập). Số chuyên gia × số ngày ghi dạng giá trị, sửa được trong Excel.
Ở chế độ nhập Gms, TMĐT ↔ kiểm toán/lệ phí phụ thuộc vòng nên file bật *tính lặp* (iterative calculation).

Đã kiểm tra: Excel 16 tính lại 6 kịch bản (XD/Thuê, nhập Gms/TMĐT, ghi đè, QLDA tự thực hiện, Gms 60 tỷ) khớp
kết quả trên web đến từng đồng.

## Những điểm sửa so với template (theo yêu cầu đã chốt)

- Chi phí chung tư vấn theo bậc 55/50/45% (Bảng 3.2) thay vì cố định 55%.
- Thẩm định HSMT tối thiểu 2.000.000 đ (template công thức dùng 3.000.000 đ).
- Kiểm toán tối thiểu 1 triệu + VAT, thẩm tra QT tối thiểu 500.000 đ; hệ số 50% thẩm tra là công tắc.
- Tỷ lệ kiểm toán/thẩm tra nội suy theo NĐ 193 (bỏ ô gõ cứng 0,00373); bỏ `#REF!`, link ngoài, ô phân bổ gõ cứng.
- QLDA và tv1–tv5 tính từ công việc × chuyên gia × ngày (mô hình co giãn theo Gms).
- Kiểm thử độc lập TT 41 (nhóm I) đặt ở Gk (k5) như `BẢNG TMĐT`.

## Giả định cần bạn kiểm tra

- **Thuế PM nội bộ mặc định 0%** theo template (sheet `3_GMS_PM_NOI_BO`, dòng THUE). Bản yêu cầu ghi "+ VAT" → nếu cần
  thì đặt 8% ở *Cấu hình nâng cao*.
- Đào tạo, triển khai, QTVH (G, H, J) dùng CPC 55% / TNCT 6% như sheet dịch vụ của template, không theo Bảng 3.2.
- Thuê PM = Gms ÷ 8 năm × số năm thuê (như `TONG_HOP - Thue`).
- Giá gói thầu (NĐ 214) = Gtb trước thuế ÷ số gói thầu.
- Mốc tham chiếu NĐ 19: 17% (giám sát 10% + đánh giá 2 + 2 + 3%) chi phí QLDA các việc còn lại.
- Chưa đối chiếu toàn văn: lương cơ sở 2.530.000 đ, điều kiện M2–M4 (TT 07/2026), công thức gnc QĐ 320,
  bảng TT 28/2023, Phụ lục III TT 41. Tất cả đều là tham số sửa được.
- QĐ 1688 đã hết hiệu lực từ 01/07/2026 → chỉ hiển thị để tham chiếu.

## Cấu trúc mã

- `dutoan/catalog.py` – danh mục công việc A–J, mốc neo, tỷ lệ PM nội bộ, bảng QĐ 1688.
- `dutoan/defaults.py` – tham số mặc định của dự án.
- `dutoan/scaling.py` – mô hình co giãn (nội suy log-log, hệ số 0,6, bậc thang số chuyên gia).
- `dutoan/calc.py` – tính toàn bộ chi phí, giải Gms khi nhập TMĐT, phân bổ vốn.
- `dutoan/storage.py` – lưu/đọc/xoá dự án trong `workspace/projects`.
- `dutoan/excel_export.py` – xuất Excel có công thức (viết lại y hệt công thức trong `calc.py`).
- `app.py` – giao diện Streamlit (menu các bước ở thanh bên trái).
- `.streamlit/config.toml` – màu giao diện.
- `tests/` – kiểm thử: `python -m pytest`.
