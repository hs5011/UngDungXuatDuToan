"""Danh mục công việc A–J và mốc neo (số chuyên gia × số ngày) tại Gms = 1 / 3 / 10 tỷ.

Nguồn: YEU-CAU-FINAL mục 5 và mục 8 (đã duyệt lượt 3, 5, 7).
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Task:
    id: str
    name: str
    grade: str
    anchors: tuple  # 3 phần tử: (số CG, số ngày) hoặc None tại mốc S / M / L
    mult: str = ""  # "" | "goi" | "lop" | "he_thong" | "nam"
    fixed: tuple | None = None  # (CG, ngày) cố định, không co giãn
    ref: str = ""  # khóa công thức "theo văn bản"
    switch: str = ""  # tên tham số bật/tắt việc này


@dataclass(frozen=True)
class Group:
    code: str
    short: str
    name: str
    section: str  # TB | DV | QLDA | TV | GK
    tasks: list = field(default_factory=list)


def _a(s):
    if s is None:
        return None
    e, d = s.split("x")
    return (int(e), int(d))


def T(id, name, grade, s, m, l, **kw):
    return Task(id, name, grade, (_a(s), _a(m), _a(l)), **kw)


GROUPS = [
    Group("A", "QLDA", "Chi phí quản lý dự án (thuê tư vấn QLDA)", "QLDA", [
        T("A1", "Lập kế hoạch tổng thể dự án", "M3", "1x2", "1x5", "2x7"),
        T("A2", "Điều phối, quản lý tiến độ, chất lượng, rủi ro", "M3", "1x8", "1x20", "2x30"),
        T("A3", "Quản lý hợp đồng, thanh toán, hồ sơ", "M4", "1x4", "1x10", "1x20"),
        T("A4", "Nghiệm thu từng giai đoạn, bàn giao", "M3", "1x2", "2x5", "2x10"),
        T("A5", "Lập hồ sơ hoàn thành, quyết toán", "M4", "1x4", "1x10", "2x15"),
        T("A6", "Báo cáo định kỳ, họp giao ban", "M4", None, "1x6", "1x12"),
        T("A7", "Quản lý thay đổi", "M3", None, "1x4", "1x8"),
        T("A8", "Giám sát, đánh giá đầu tư (NĐ 19/2026)", "M3", None, None, "1x10", ref="nd19"),
    ]),
    Group("B", "TV1", "Chi phí lập BCKT-KT (tv1)", "TV", [
        T("B1", "Khảo sát hiện trạng", "M3", "1x2", "2x3", "3x5"),
        T("B2", "Phân tích nghiệp vụ, đặc tả use case", "M3", "1x6", "2x8", "4x12"),
        T("B3", "Yêu cầu phi chức năng, ATTT, Khung kiến trúc", "M2", "1x2", "1x4", "2x8"),
        T("B4", "Thiết kế chi tiết", "M3", "1x5", "2x8", "3x15"),
        T("B5", "Phương án công nghệ", "M2", None, "1x3", "2x6"),
        T("B6", "Mô hình tổng thể, lô-gic, vật lý", "M2", None, None, "2x8"),
        T("B7", "Xác định TMĐT, dự toán", "M3", "1x2", "1x4", "2x6"),
        T("B8", "Phân tích hiệu quả, rủi ro, tiến độ", "M3", "1x1", "1x3", "2x4"),
        T("B9", "Hội thảo, lấy ý kiến", "M2", None, "1x2", "2x2"),
        T("B10", "Viết báo cáo, hoàn thiện hồ sơ", "M4", "1x3", "1x6", "2x8"),
    ]),
    Group("C", "TV2", "Chi phí thẩm tra BCKT-KT (tv2)", "TV", [
        T("C1", "Kiểm tra hồ sơ", "M3", "1x1", "1x1", "1x2"),
        T("C2", "Sự phù hợp chủ trương, Khung kiến trúc", "M3", "1x1", "1x1", "2x1"),
        T("C3", "Thẩm tra thiết kế", "M2", "1x2", "2x2", "2x4", switch="tham_tra_thiet_ke"),
        T("C4", "Thẩm tra khối lượng, TMĐT, dự toán", "M3", "1x1", "1x2", "2x3"),
        T("C5", "Thẩm tra hiệu quả, rủi ro, tiến độ", "M3", None, "1x1", "1x2"),
        T("C6", "Lập báo cáo thẩm tra", "M3", "1x1", "1x2", "1x4"),
        T("C7", "Giải trình, hoàn thiện", "M2", None, "1x1", "1x2"),
    ]),
    Group("D", "TV3", "Chi phí giám sát triển khai (tv3)", "TV", [
        T("D1", "Kiểm tra điều kiện triển khai", "M4", "1x1", "1x1", "1x2"),
        T("D2", "Kiểm tra năng lực nhà thầu", "M4", "1x1", "1x1", "1x2"),
        T("D3", "Giám sát thiết bị, phần mềm cài đặt", "M4", "2x5", "2x5", "2x8"),
        T("D4", "Giám sát triển khai", "M4", "2x15", "2x20", "3x30"),
        T("D5", "Giám sát khối lượng", "M4", "2x15", "2x10", "2x15"),
        T("D6", "Giám sát tiến độ", "M4", "2x3", "2x4", "2x6"),
        T("D7", "Giám sát thay đổi", "M4", None, "1x2", "1x4"),
        T("D8", "Nội dung giám sát khác", "M4", None, "1x2", "1x4"),
        T("D9", "Báo cáo kết quả giám sát", "M4", "2x3", "2x3", "2x5"),
    ]),
    Group("E", "TV4", "Chi phí lập E-HSMT, đánh giá E-HSDT (tv4)", "TV", [
        T("E1", "Lập kế hoạch lựa chọn nhà thầu (chung)", "M3", None, "1x3", "1x5", ref="nd214_khlcnt"),
        T("E2", "Lập E-HSMT (mỗi gói thầu)", "M3", "1x3", "1x4", "2x4", mult="goi", ref="nd214_lap_hsmt"),
        T("E3", "Đánh giá E-HSDT (mỗi gói thầu)", "M3", "1x3", "1x4", "2x4", mult="goi", ref="nd214_dg_hsdt"),
        T("E4", "Báo cáo kết quả lựa chọn nhà thầu (mỗi gói)", "M4", None, "1x2", "1x3", mult="goi"),
    ]),
    Group("F", "TV5", "Chi phí thẩm định E-HSMT, kết quả LCNT (tv5)", "TV", [
        T("F1", "Thẩm định kế hoạch lựa chọn nhà thầu", "M3", None, None, "1x2"),
        T("F2", "Thẩm định E-HSMT (mỗi gói thầu)", "M3", "1x1", "1x2", "1x3", mult="goi", ref="nd214_td_hsmt"),
        T("F3", "Thẩm định kết quả LCNT (mỗi gói thầu)", "M3", "1x1", "1x2", "1x2", mult="goi", ref="nd214_td_kq"),
    ]),
    Group("G", "DAO_TAO", "Chi phí đào tạo, chuyển giao", "TB", [
        T("G1", "Xây dựng chương trình, tài liệu HDSD", "M4", "1x5", "1x10", "2x10"),
        T("G2", "Đào tạo người dùng cuối (mỗi lớp)", "M4", "1x2", "1x2", "1x2", mult="lop", fixed=(1, 2)),
        T("G3", "Đào tạo quản trị, vận hành", "M3", "1x2", "1x3", "2x3"),
        T("G4", "Video, tài liệu HDSD điện tử", "M4", None, "1x5", "2x8"),
        T("G5", "Hỗ trợ sau đào tạo", "M4", None, None, "2x10"),
    ]),
    Group("H", "TRIEN_KHAI", "Chi phí triển khai trước nghiệm thu", "TB", [
        T("H1", "Cài đặt, triển khai lên môi trường vận hành", "M3", "1x2", "1x4", "2x6"),
        T("H2", "Cấu hình, tham số hóa hệ thống", "M3", "1x3", "1x6", "2x10"),
        T("H3", "Tích hợp, kết nối (mỗi hệ thống)", "M2", None, "1x8", "2x10", mult="he_thong"),
        T("H4", "Chuyển đổi dữ liệu từ hệ thống cũ", "M3", None, "2x10", "3x20"),
        T("H5", "Vận hành thử cùng người dùng (UAT)", "M4", "1x5", "2x8", "3x12"),
        T("H6", "Hỗ trợ, vận hành trước nghiệm thu", "M4", "1x10", "2x15", "3x30"),
    ]),
    Group("I", "KIEM_THU", "Chi phí kiểm thử độc lập (TT 41/2026)", "GK", [
        T("I1", "Lập kế hoạch, kịch bản kiểm thử", "M3", "1x2", "1x4", "2x5"),
        T("I2", "Kiểm thử chức năng", "M4", "1x5", "2x10", "3x20"),
        T("I3", "Kiểm thử phi chức năng", "M3", None, "2x5", "3x10"),
        T("I4", "Kiểm thử, đánh giá ATTT", "M3", "1x3", "2x5", "3x10"),
        T("I5", "Kiểm thử lại sau sửa lỗi", "M4", "1x2", "1x5", "2x8"),
        T("I6", "Báo cáo kiểm thử", "M4", "1x1", "1x3", "1x5"),
    ]),
    Group("J", "QTVH", "Chi phí quản trị, vận hành, bảo trì (theo năm)", "DV", [
        T("J1", "Bố trí nhân lực, nguồn lực", "M3", "1x2", "1x3", "1x5", mult="nam"),
        T("J2", "Quản trị ứng dụng", "M4", "1x24", "1x48", "2x60", mult="nam"),
        T("J3", "Quản trị CSDL", "M3", "1x12", "1x24", "1x36", mult="nam"),
        T("J4", "Bảo trì phần mềm", "M4", "1x24", "2x30", "3x40", mult="nam"),
        T("J5", "Bảo đảm ATTT", "M3", "1x12", "1x24", "2x24", mult="nam"),
        T("J6", "Helpdesk", "M4", None, "1x48", "2x60", mult="nam"),
        T("J7", "Báo cáo định kỳ", "M4", None, "1x6", "1x12", mult="nam"),
    ]),
]

GROUP_BY_CODE = {g.code: g for g in GROUPS}
TASK_BY_ID = {t.id: t for g in GROUPS for t in g.tasks}

MULT_LABEL = {"": "", "goi": "số gói thầu", "lop": "số lớp", "he_thong": "số hệ thống", "nam": "số năm"}

# Nhân công PM nội bộ (nhóm K) – tỷ lệ cố định theo template
PM_ROLES = [
    ("Nghiên cứu và phát triển", 0.02),
    ("Phân tích nghiệp vụ (BA)", 0.10),
    ("Kiến trúc, thiết kế hệ thống", 0.12),
    ("Thiết kế UI/UX", 0.03),
    ("Lập trình", 0.40),
    ("Kiểm thử nội bộ nhà thầu", 0.10),
    ("Tích hợp, quản lý cấu hình (DevOps)", 0.10),
    ("Phối hợp hiệu chỉnh theo kiểm thử, đánh giá ATTT độc lập", 0.03),
    ("Quản trị dự án", 0.10),
]

# Định mức QĐ 1688 (đã hết hiệu lực từ 01/07/2026) – CHỈ ĐỂ THAM CHIẾU.
# Mốc: chi phí PM nội bộ, CSDL (chưa thuế, tỷ đồng); giá trị: tỷ lệ %.
# Mỗi bảng: (dòng "PM nội bộ, CSDL", dòng "PM nội bộ, CSDL trong BCKT-KT").
DM1688_X = [7, 15, 20, 30, 50, 100, 150, 200]
DM1688 = {
    "A": ("Bảng 1 – Quản lý dự án",
          [2.809, 2.133, 1.964, 1.782, 1.71, 1.346, 1.287, 1.248],
          [1.855, 1.532, 1.532, 1.532, 1.532, 1.532, 1.532, 1.532]),
    "B": ("Bảng 2 – Lập dự án",
          [0.992, 0.906, 0.812, 0.763, 0.648, 0.485, 0.437, 0.381],
          [3.64, 3.24, 3.24, 3.24, 3.24, 3.24, 3.24, 3.24]),
    "C": ("Bảng 4 – Thẩm tra dự án",
          [0.126, 0.088, 0.085, 0.077, 0.065, 0.051, 0.042, 0.036],
          [0.126, 0.088, 0.085, 0.077, 0.065, 0.051, 0.042, 0.036]),
    "D": ("Bảng 9 – Giám sát",
          [2.063, 1.931, 1.833, 1.736, 1.595, 1.22, 1.091, 0.956],
          [2.063, 1.931, 1.833, 1.736, 1.595, 1.22, 1.091, 0.956]),
    "E": ("Bảng 8 – Lập HSMT, đánh giá HSDT thiết bị",
          [0.405, 0.336, 0.311, 0.265, 0.182, 0.119, 0.109, 0.102],
          [0.405, 0.336, 0.311, 0.265, 0.182, 0.119, 0.109, 0.102]),
}
