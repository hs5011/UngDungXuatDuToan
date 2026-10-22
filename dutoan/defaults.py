"""Tham số mặc định của một dự án. Mọi số ở đây đều sửa được trên giao diện."""
import copy

GRADES = ["M1", "M2", "M3", "M4"]

GRADE_NOTE = {
    "M1": "ĐH ≥ 15 năm; ThS ≥ 8 năm; trưởng nhóm, chủ trì",
    "M2": "ĐH 10–15 năm; ThS 5–8 năm",
    "M3": "ĐH 5–10 năm; ThS 3–5 năm",
    "M4": "ĐH < 5 năm; ThS < 3 năm",
}

LOAI_HO_SO = {"TMDT": "Tổng mức đầu tư", "DU_TOAN": "Dự toán", "BCKTKT": "BCKT-KT"}
KDP_MAX = {"TMDT": 0.10, "DU_TOAN": 0.07, "BCKTKT": 0.05}
KDP_MAX_THUE = 0.10

# Nội dung chi QLDA tự thực hiện – Điều 30(2) NĐ 10/2021/NĐ-CP (nguồn thứ cấp)
QLDA_CHI_KHAC = [
    "Đào tạo, bồi dưỡng",
    "Dịch vụ công cộng",
    "Văn phòng phẩm, thông tin, tuyên truyền",
    "Hội nghị, họp",
    "Công tác phí",
    "Thuê, sửa chữa, mua sắm tài sản",
    "Chi khác",
]


def _default():
    return {
        "thong_tin": {"ten_du_an": "", "chu_dau_tu": "", "thoi_diem": "2026-10-09"},
        "tham_so": {
            # Chế độ, hồ sơ
            "che_do": "XD",  # XD | THUE
            "loai_ho_so": "TMDT",
            "thiet_ke": 1,
            "co_pm_noi_bo": True,
            "qlda": "THUE",  # THUE | TU_TH
            # Đầu vào
            "nhap": "GMS",  # GMS | TMDT
            "gms": 3_000_000_000.0,
            "tmdt": 4_000_000_000.0,
            "du_phong_theo": "PCT",  # chế độ TMĐT: dự phòng tối thiểu theo PCT (Kdp %) | TIEN (đồng)
            "du_phong_toi_thieu": 0.0,
            "kdp": None,  # bắt buộc nhập; None → tạm dùng mức tối đa + cảnh báo
            "kdp_truot_gia": 0.0,
            "lam_tron": 1_000_000.0,
            "so_nam_thue": 3,
            "so_nam_phan_bo": 2,  # chế độ XD
            "khau_hao_nam": 8,
            "vat": 0.08,
            # Chuyên gia tư vấn (TT 07/2026/TT-BNV – mức tối đa)
            "luong": {"M1": 70_000_000.0, "M2": 55_000_000.0, "M3": 40_000_000.0, "M4": 30_000_000.0},
            "he_so_nang": 1.0,
            "ngay_thang": 26,
            "cql": {"nguong1": 1_000_000_000.0, "nguong2": 5_000_000_000.0, "r1": 0.55, "r2": 0.50, "r3": 0.45},
            "tn_tv": 0.06,
            # Mô hình co giãn
            "exp": 0.6,
            "bac_thang": [12, 40, 90, 160],
            "moc_neo": [1_000_000_000.0, 3_000_000_000.0, 10_000_000_000.0],
            "nguong_M": 1_000_000_000.0,
            "nguong_L": 5_000_000_000.0,
            "so_goi": None,  # None → theo quy mô 2/3/5
            # PM nội bộ (nhóm K)
            "pm_cpc": 0.55,
            "pm_tn": 0.06,
            "luong_co_so": 2_530_000.0,
            "ks_he_so": [2.34, 2.65, 2.96, 3.27, 3.58, 3.89, 4.20, 4.51],
            "vung": "I",
            "hdc": {"I": 1.2, "II": 0.9, "III": 0.7, "IV": 0.5},
            "ks_hpc": 0.0,
            "ks_bh": 0.215,  # BHXH 17,5% + BHYT 3% + BHTN 1% trên MLcb
            "ks_bac_chon": [1, 2, 3],
            "pm_don_gia_thang": None,  # ghi đè đơn giá tháng bình quân
            "pm_ty_le": None,  # None → tỷ lệ template
            "pm_bac": [3, 3, 3, "TB", "TB", "TB", "TB", "TB", 4],  # bậc KS từng vai trò (TB = bình quân)
            "pm_thue": 0.0,  # thuế/phí PM nội bộ (template = 0)
            # Công tắc
            "tham_tra_thiet_ke": None,  # None → tự động: tắt khi có PM nội bộ
            "kiem_toan_doc_lap": True,
            "tb_tren_50": None,  # None → tự động theo tỷ trọng
            "phi_tham_dinh": True,
            "j_tron_goi": False,
            "j_tron_goi_nam": 0.0,
            # Văn bản tham chiếu
            "nd19_tl": 0.17,
            "tham_chieu_1688": True,  # giám sát 10% + đánh giá 2% + 2% + 3% chi phí QLDA
            "nd214": {
                "khlcnt": [0.005, 5_000_000.0, 40_000_000.0],
                "lap_hsmt": [0.002, 3_000_000.0, 60_000_000.0],
                "dg_hsdt": [0.002, 3_000_000.0, 60_000_000.0],
                "td_hsmt": [0.001, 2_000_000.0, 60_000_000.0],
                "td_kq": [0.001, 3_000_000.0, 60_000_000.0],
            },
            # NĐ 193/2026 Điều 20 (theo template): [TMĐT tỷ đồng, % thẩm tra QT, % kiểm toán]
            "bang_kiem_toan": [
                [5, 0.57, 0.96],
                [10, 0.39, 0.645],
                [50, 0.285, 0.45],
                [100, 0.225, 0.345],
                [500, 0.135, 0.195],
                [1000, 0.09, 0.129],
                [10000, 0.048, 0.069],
            ],
            "kt_min": 1_000_000.0,
            "tt_min": 500_000.0,
            "he_so_tb": 0.7,
            "he_so_kt_doc_lap": 0.5,
            # TT 28/2023/TT-BTC (theo template): [TMĐT tỷ đồng, %]
            "bang_phi_tham_dinh": [
                [15, 0.019], [25, 0.017], [50, 0.015], [100, 0.0125], [200, 0.01],
                [500, 0.0075], [1000, 0.0047], [2000, 0.0025], [5000, 0.002], [10000, 0.001],
            ],
            "ptd_giam_tt64": 0.5,  # TT 64/2025/TT-BTC giảm 50%
            "ptd_co_tham_tra": True,  # có thẩm tra → mức thu 50%
            "tham_dinh_gia": 0.0,  # chi phí thẩm định giá (nhập)
            # QLDA tự thực hiện
            "bh_qlda": 0.235,
        },
        "thiet_bi": [],  # {ten, dvt, so_luong, don_gia, vat}
        "pm_thuong_mai": [],
        "tb_khac": [],  # CSDL, lắp đặt, vận chuyển...
        "dv_thue_nam": [],  # chế độ thuê: {ten, dvt, so_luong, don_gia, vat} theo năm
        "gk_khac": [],  # {ten, gia_tri}
        "qlda_nhan_su": [
            {"vi_tri": "Chỉ huy / Trưởng ban", "so_nguoi": 1, "he_so_luong": 4.40, "pc_chuc_vu": 0.5, "pc_khu_vuc": 0.0, "pc_khac": 0.0, "so_thang": 12},
            {"vi_tri": "Kế toán", "so_nguoi": 1, "he_so_luong": 3.00, "pc_chuc_vu": 0.0, "pc_khu_vuc": 0.0, "pc_khac": 0.0, "so_thang": 12},
            {"vi_tri": "Kỹ thuật", "so_nguoi": 1, "he_so_luong": 3.00, "pc_chuc_vu": 0.0, "pc_khu_vuc": 0.0, "pc_khac": 0.0, "so_thang": 12},
            {"vi_tri": "Hành chính – thư ký", "so_nguoi": 1, "he_so_luong": 2.34, "pc_chuc_vu": 0.0, "pc_khu_vuc": 0.0, "pc_khac": 0.0, "so_thang": 12},
        ],
        "qlda_chi_khac": [{"ten": t, "gia_tri": 0.0} for t in QLDA_CHI_KHAC],
        "ck": {},  # chi phí khác (Ck) của từng nhóm tư vấn
        "ghi_de": {},  # task_id → {so_cg, so_ngay, bac, dung_vb, bo}
        "ghi_de_nhom": {},  # code → tổng ghi đè
        "nhom_tat": [],  # mã nhóm không tính
        "ghi_chu": {},  # khoá dòng bảng tổng hợp → ghi chú người dùng sửa
        "viec_them": {},  # code → [{ten, bac, so_cg, so_ngay, he_so}] công việc người dùng tự thêm
        "phan_bo": {},  # key → [tỷ lệ năm 1..N]
    }


def default_project():
    return copy.deepcopy(_default())


NUMERIC_TS_KEYS = (
    "gms", "tmdt", "kdp", "kdp_truot_gia", "du_phong_toi_thieu", "lam_tron",
    "so_nam_thue", "so_nam_phan_bo", "khau_hao_nam", "vat", "he_so_nang",
    "ngay_thang", "tn_tv", "exp", "nguong_M", "nguong_L", "pm_cpc", "pm_tn",
    "luong_co_so", "ks_hpc", "pm_thue", "nd19_tl", "kt_min", "tt_min",
    "he_so_tb", "he_so_kt_doc_lap", "ptd_giam_tt64", "tham_dinh_gia",
    "bh_qlda", "ks_bh", "j_tron_goi_nam",
)
LIST_KEYS = ("thiet_bi", "pm_thuong_mai", "tb_khac", "dv_thue_nam", "gk_khac",
             "qlda_nhan_su", "qlda_chi_khac", "nhom_tat")


def _coerce_num(v):
    if isinstance(v, str):
        try:
            return float(v.replace(" ", "").replace(",", "."))
        except ValueError:
            return v
    return v


def merge_defaults(data):
    """Bổ sung khóa thiếu khi mở file JSON cũ; chuẩn hoá kiểu số & list."""
    base = default_project()

    def merge(dst, src):
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict) and k not in ("ghi_de", "ghi_de_nhom", "ck", "phan_bo", "viec_them", "ghi_chu"):
                merge(dst[k], v)
            else:
                dst[k] = v

    merge(base, data or {})
    if data and "du_phong_theo" not in data.get("tham_so", {}):
        base["tham_so"]["du_phong_theo"] = "TIEN"  # file cũ chỉ có dự phòng tối thiểu theo số tiền
    # Ép kiểu các khoá số (file cũ có thể lưu str)
    ts = base["tham_so"]
    for k in NUMERIC_TS_KEYS:
        if k in ts:
            ts[k] = _coerce_num(ts[k])
    # Normalize list key = None → []
    for k in LIST_KEYS:
        if base.get(k) is None:
            base[k] = []
    return base
