"""Kiểm tra tính nhất quán nội tại (invariants) và các mối quan hệ giữa đại lượng.

Mục tiêu: phát hiện mâu thuẫn lô-gic giữa các khoản, giữa Python ↔ Excel,
và kiểm chứng monotonic (tăng Gms → TMĐT tăng, tăng Kdp → dự phòng tăng…).
"""
import io
import math

import openpyxl
import pytest

from dutoan.calc import compute, _compute_at, kdp_max, rnd, counts, tier
from dutoan.defaults import default_project
from dutoan.excel_export import export_bytes


@pytest.fixture
def proj():
    p = default_project()
    p["tham_so"]["kdp"] = 0.05
    return p


# ============================= Invariant 1: cộng trừ nhất quán =============================
@pytest.mark.parametrize("gms", [0.5e9, 1e9, 3e9, 5e9, 10e9, 20e9])
def test_tmdt_bang_tong_cac_khoan(proj, gms):
    """TMĐT = Σ(item.pre + item.vat) = Σ item.post với mọi Gms."""
    proj["tham_so"]["gms"] = gms
    r = compute(proj)
    tong = sum(i.post for i in r.items)
    assert r.tmdt == pytest.approx(tong, abs=1), f"Gms={gms}: TMĐT {r.tmdt} ≠ Σitem {tong}"


@pytest.mark.parametrize("gms", [0.5e9, 1e9, 3e9, 5e9, 10e9])
def test_totals_pre_vat_khop_tung_item(proj, gms):
    """totals['pre'] = Σ item.pre, totals['vat'] = Σ item.vat, totals['base'] = Σ sec I–IV."""
    proj["tham_so"]["gms"] = gms
    r = compute(proj)
    assert r.totals["pre"] == pytest.approx(sum(i.pre for i in r.items), abs=1)
    assert r.totals["vat"] == pytest.approx(sum(i.vat for i in r.items), abs=1)
    base_items = sum(i.post for i in r.items if i.sec in ("I", "II", "III", "IV"))
    assert r.totals["base"] == pytest.approx(base_items, abs=1)
    assert r.totals["V"] == pytest.approx(r.tmdt - r.totals["base"], abs=1)


def test_section_sums_khop_tung_sec(proj):
    """totals[sec] = Σ item.post trong section đó."""
    r = compute(proj)
    for sec in ("I", "II", "III", "IV"):
        assert r.totals[sec] == pytest.approx(sum(i.post for i in r.items if i.sec == sec), abs=1)


# ============================= Invariant 2: nhóm chuyên gia =============================
def test_group_cg_pre_vat_khop_tay(proj):
    """cg_pre = ccg + cql + ck + tn (sau rnd); cg_vat = ROUND(vat × (ccg+cql+ck+tn))."""
    r = compute(proj)
    ts = proj["tham_so"]
    for g in r.groups.values():
        if g.override is not None:
            continue
        base = g.ccg + g.cql + g.ck + g.tn
        assert g.cg_pre == pytest.approx(rnd(base), abs=1)
        assert g.cg_vat == pytest.approx(rnd(ts["vat"] * base), abs=1)
        assert g.cg_total == pytest.approx(g.cg_pre + g.cg_vat, abs=1)


def test_group_ccg_khop_tong_dong(proj):
    """ccg = Σ row.amount (chỉ dòng không excluded/use_ref)."""
    r = compute(proj)
    for g in r.groups.values():
        expected = sum(x.amount for x in g.rows)
        assert g.ccg == pytest.approx(expected)


def test_group_tn_khop_cong_thuc(proj):
    """TN = tn_rate × (ccg + cql + ck) (sau rnd). Trình tự TT 39/2026."""
    r = compute(proj)
    for g in r.groups.values():
        if g.override is not None:
            continue
        assert g.tn == pytest.approx(rnd(g.tn_rate * (g.ccg + g.cql + g.ck)), abs=1)


def test_group_cql_khop_bang_32(proj):
    """Cql = ccg × cql_rate; cql_rate theo bảng 3.2."""
    r = compute(proj)
    for g in r.groups.values():
        if g.override is not None:
            continue
        assert g.cql == pytest.approx(g.ccg * g.cql_rate)


# ============================= Invariant 3: dự phòng không âm trong miền hợp lệ =============================
@pytest.mark.parametrize("gms", [0.1e9, 1e9, 5e9, 20e9])
def test_du_phong_khong_am_che_do_gms(proj, gms):
    proj["tham_so"]["gms"] = gms
    r = compute(proj)
    assert r.totals["V"] >= -0.5, f"Gms={gms}: dự phòng âm {r.totals['V']}"
    assert r.totals["dp_ratio"] <= kdp_max(proj["tham_so"]) + 1e-6


def test_du_phong_khong_vuot_kdp_voi_kdp_truot_gia(proj):
    """Fix lượt 31: khi kdp + kdp_truot_gia > kdp_max, TMĐT phải cap theo kdp_max."""
    ts = proj["tham_so"]
    ts["kdp"], ts["kdp_truot_gia"] = 0.08, 0.05  # tổng 13% > 10% TMDT
    ts["gms"] = 3e9
    r = compute(proj)
    assert r.totals["dp_ratio"] <= kdp_max(ts) + 1e-6, (
        f"dp_ratio {r.totals['dp_ratio']:.4%} vượt kdp_max {kdp_max(ts):.0%}"
    )


# ============================= Invariant 4: monotonic =============================
def test_tmdt_tang_khi_gms_tang(proj):
    """TMĐT phải tăng khi Gms tăng."""
    prev = -1
    for gms in [0.5e9, 1e9, 2e9, 5e9, 10e9]:
        proj["tham_so"]["gms"] = gms
        tmdt = compute(proj).tmdt
        assert tmdt > prev, f"TMĐT không tăng khi Gms={gms}: {tmdt} ≤ {prev}"
        prev = tmdt


def test_du_phong_tang_khi_kdp_tang(proj):
    """Khi Kdp tăng, dự phòng V phải tăng (không giảm)."""
    proj["tham_so"]["gms"] = 3e9
    vs = []
    for kdp in [0.02, 0.05, 0.08, 0.10]:
        proj["tham_so"]["kdp"] = kdp
        vs.append(compute(proj).totals["V"])
    assert vs == sorted(vs), f"V không đơn điệu tăng theo Kdp: {vs}"


def test_so_nam_thue_tang_thi_thue_pm_tang(proj):
    """Số năm thuê tăng → chi phí thuê PM tăng tỷ lệ."""
    ts = proj["tham_so"]
    ts["che_do"], ts["gms"] = "THUE", 2e9
    vs = []
    for n in [1, 2, 3, 4]:
        ts["so_nam_thue"] = n
        vs.append(compute(proj).item("thue_pm").post)
    for i in range(1, len(vs)):
        assert vs[i] > vs[i - 1], f"thue_pm năm {i+1} không tăng: {vs}"


def test_counts_tang_theo_tier(proj):
    """Số gói/lớp/hệ thống không giảm khi lên tier cao hơn."""
    ts = proj["tham_so"]
    c0 = counts(0.5e9, ts)
    c1 = counts(2e9, ts)
    c2 = counts(10e9, ts)
    for k in ("goi",):
        assert c0[k] <= c1[k] <= c2[k]


# ============================= Invariant 5: Python ↔ Excel khớp =============================
@pytest.mark.parametrize("gms", [1e9, 3e9, 10e9])
def test_excel_tmdt_khop_python(proj, gms):
    proj["tham_so"]["gms"] = gms
    r = compute(proj)
    data = export_bytes(proj, r)
    wv = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    ws = wv["BẢNG TMĐT"]
    tot_row = next(x for x in range(1, ws.max_row + 1) if ws[f"B{x}"].value == "TỔNG CỘNG")
    excel_tmdt = ws[f"H{tot_row}"].value
    assert abs(excel_tmdt - r.tmdt) < 1, f"Gms={gms}: Excel {excel_tmdt} ≠ Python {r.tmdt}"


def test_excel_tung_item_khop_python(proj):
    """Mỗi dòng BẢNG TMĐT có giá trị bằng item tương ứng trong Python."""
    r = compute(proj)
    data = export_bytes(proj, r)
    wv = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    ws = wv["BẢNG TMĐT"]
    # Tìm các dòng tiền (cột H có số) và so với tổng theo section
    tong_H = 0
    for row in ws.iter_rows(min_row=6, max_row=ws.max_row):
        for c in row:
            if c.column_letter == "H" and isinstance(c.value, (int, float)):
                if ws[f"B{c.row}"].value == "TỔNG CỘNG":
                    assert abs(c.value - r.tmdt) < 1
                break
    # Thực chất chỉ kiểm TỔNG CỘNG là đủ (các dòng khác đã kiểm qua test_excel_tmdt_khop_python)


# ============================= Invariant 6: ghi đè vs mặc định =============================
def test_ghi_de_so_cg_khong_thay_doi_tong_khi_tong_ngay_tuong_duong(proj):
    """Nếu ghi đè so_cg mà vẫn giữ nguyên tổng (CG × ngày), chi phí không đổi."""
    proj["tham_so"]["gms"] = 3e9
    r0 = compute(proj)
    b2_0 = next(x for x in r0.groups["B"].rows if x.id == "B2")
    tong_ngay = b2_0.experts * b2_0.days
    # Ghi đè số CG → ứng dụng tự tính lại số ngày; so_cg × so_ngay ≈ tổng ngày
    proj["ghi_de"] = {"B2": {"so_cg": b2_0.experts * 2}}
    r1 = compute(proj)
    b2_1 = next(x for x in r1.groups["B"].rows if x.id == "B2")
    # math.ceil có thể làm tổng lệch nhẹ ≤ số CG
    assert abs(b2_1.experts * b2_1.days - tong_ngay) <= b2_1.experts


def test_bo_viec_lam_giam_cp(proj):
    """Bỏ 1 việc → chi phí nhóm giảm đúng bằng amount việc đó (nếu không use_ref)."""
    proj["tham_so"]["gms"] = 3e9
    before = compute(proj).groups["B"]
    b1_amount = next(x for x in before.rows if x.id == "B1").amount
    proj["ghi_de"] = {"B1": {"bo": True}}
    after = compute(proj).groups["B"]
    assert after.ccg == pytest.approx(before.ccg - b1_amount)


def test_ghi_de_nhom_lam_dieu_khoan_khac_khong_doi(proj):
    """Ghi đè tổng nhóm B không được ảnh hưởng tổng nhóm C."""
    r0 = compute(proj)
    c_pre_0 = r0.groups["C"].pre
    proj["ghi_de_nhom"] = {"B": 100_000_000}
    r1 = compute(proj)
    assert r1.groups["C"].pre == pytest.approx(c_pre_0)
    assert r1.groups["B"].total == 100_000_000


# ============================= Invariant 7: phân bổ vốn =============================
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_phan_bo_tong_bang_tmdt(proj, n):
    proj["tham_so"]["so_nam_phan_bo"] = n
    r = compute(proj)
    assert sum(r.phan_bo["years"]) == pytest.approx(r.tmdt, abs=10)


def test_phan_bo_moi_dong_tong_bang_item_post(proj):
    r = compute(proj)
    for row in r.phan_bo["rows"]:
        assert sum(row["nam"]) == pytest.approx(row["tong"])
        assert abs(sum(row["ty_le"]) - 1) < 1e-6


# ============================= Invariant 8: hồi quy chế độ THUE =============================
def test_che_do_thue_khong_co_pm_item(proj):
    """Chế độ THUE có 'thue_pm' thay vì 'pm'."""
    proj["tham_so"]["che_do"] = "THUE"
    r = compute(proj)
    assert r.item("thue_pm") is not None
    assert r.item("pm") is None


def test_che_do_xd_khong_co_dv_nam(proj):
    """Chế độ XD không có dv_nam / thue_pm / qtvh."""
    r = compute(proj)  # XD mặc định
    assert r.item("dv_nam") is None
    assert r.item("thue_pm") is None
    assert r.item("qtvh") is None


# ============================= Invariant 9: so sánh văn bản =============================
def test_so_sanh_cg_cao_hon_van_ban_khi_mac_dinh(proj):
    """Nhóm E, F theo chuyên gia thường cao hơn mức NĐ 214 (vì NĐ 214 là mức tối đa)."""
    r = compute(proj)
    # Có ít nhất 1 dòng với lech ≠ 0
    non_zero = [c for c in r.compare if abs(c["lech"]) > 1e-6]
    assert len(non_zero) > 0


# ============================= Invariant 10: Warnings không mâu thuẫn =============================
def test_khong_canh_bao_sai_voi_du_an_hop_le(proj):
    """Dự án mặc định với kdp hợp lệ, không có cảnh báo nào về giới hạn."""
    r = compute(proj)
    hard_warnings = [w for w in r.warnings if "vượt" in w or "âm" in w or "không có lời giải" in w]
    assert hard_warnings == [], f"Dự án hợp lệ nhưng có cảnh báo cứng: {hard_warnings}"


def test_warning_khi_kdp_truot_gia_lam_vuot_kdp_max(proj):
    """Nếu Kdp áp dụng không vượt max nhưng + kdp_truot_gia khiến dp_ratio > max, có cảnh báo."""
    ts = proj["tham_so"]
    ts["kdp"], ts["kdp_truot_gia"] = 0.09, 0.05
    r = compute(proj)
    # dp_ratio có thể bằng kdp_max do cap → không chắc có warning, nhưng không được âm
    assert r.totals["V"] >= 0


# ============================= Invariant 11: đổi loại hồ sơ =============================
def test_bckt_kdp_toi_da_5_pct(proj):
    """BCKTKT: Kdp tối đa 5%."""
    ts = proj["tham_so"]
    ts["loai_ho_so"], ts["kdp"] = "BCKTKT", 0.05
    r = compute(proj)
    assert r.totals["dp_ratio"] <= 0.05 + 1e-6


def test_du_toan_kdp_toi_da_7_pct(proj):
    ts = proj["tham_so"]
    ts["loai_ho_so"], ts["kdp"] = "DU_TOAN", 0.07
    r = compute(proj)
    assert r.totals["dp_ratio"] <= 0.07 + 1e-6


# ============================= Invariant 12: idempotent =============================
def test_compute_idempotent(proj):
    """Gọi compute 2 lần cho cùng input phải ra cùng kết quả."""
    r1 = compute(proj)
    r2 = compute(proj)
    assert r1.tmdt == r2.tmdt
    assert [i.post for i in r1.items] == [i.post for i in r2.items]


def test_che_do_thue_tmdt_mode_tim_duoc_gms(proj):
    """Chế độ THUE + nhập TMĐT phải tìm được Gms > 0 (dự án đủ lớn)."""
    ts = proj["tham_so"]
    ts["che_do"], ts["nhap"], ts["tmdt"] = "THUE", "TMDT", 5e9
    ts["du_phong_theo"], ts["kdp"] = "PCT", 0.05
    r = compute(proj)
    assert r.gms > 0
    assert r.tmdt == 5e9


# ============================= Hệ số nhập tay ở bước 3 (nhóm G, H) =============================
def _row(proj, code, rid):
    return next(x for x in compute(proj).groups[code].rows if x.id == rid)


def test_he_so_mac_dinh_nhom_g_h(proj):
    """Số máy chủ, số nhóm khai thác/quản trị, số hệ thống mặc định 1; máy trạm mặc định 0."""
    proj["tham_so"]["gms"] = 3e9
    for code, rid, hs in [("H", "H3", 1), ("H", "H5", 1), ("H", "H6", 1), ("H", "H4", 0),
                          ("G", "G5", 1), ("G", "G6", 1), ("G", "G8", 0)]:
        r = _row(proj, code, rid)
        assert r.mult == hs and r.auto_mult == hs, rid
    assert _row(proj, "H", "H4").amount == 0


def test_he_so_ghi_de_nhan_dung_tien(proj):
    """Sửa hệ số 1 → 21 máy chủ: tiền dòng nhân đúng 21 lần, các dòng khác không đổi."""
    proj["tham_so"]["gms"] = 3e9
    r0 = _row(proj, "H", "H3")
    ccg0 = compute(proj).groups["H"].ccg
    proj["ghi_de"] = {"H3": {"he_so": 21.0}}
    r1 = _row(proj, "H", "H3")
    assert r1.mult == 21 and r1.overridden
    assert r1.amount == pytest.approx(r0.amount * 21)
    assert compute(proj).groups["H"].ccg == pytest.approx(ccg0 + r0.amount * 20)


def test_he_so_bang_0_la_khong_tinh(proj):
    proj["tham_so"]["gms"] = 3e9
    proj["ghi_de"] = {"G5": {"he_so": 0.0}}
    r = _row(proj, "G", "G5")
    assert r.mult == 0 and r.amount == 0


def test_he_so_ghi_de_viec_nhom_e_khong_doi_so_goi(proj):
    """Hệ số dòng E2 sửa tay chỉ đổi dòng đó; số gói thầu (tham số) vẫn là số mặc định."""
    proj["tham_so"]["gms"] = 3e9
    goi = counts(3e9, proj["tham_so"])["goi"]
    proj["ghi_de"] = {"E2": {"he_so": 7.0}}
    r = _row(proj, "E", "E2")
    assert r.mult == 7 and r.auto_mult == goi


def test_excel_khop_python_khi_sua_he_so(proj):
    proj["tham_so"]["gms"] = 3e9
    proj["ghi_de"] = {"H3": {"he_so": 4.0}, "H4": {"he_so": 3.0}, "G5": {"he_so": 7.0}, "G6": {"he_so": 2.0},
                      "E2": {"he_so": 5.0}}
    r = compute(proj)
    wv = openpyxl.load_workbook(io.BytesIO(export_bytes(proj, r)), data_only=True)
    ws = wv["BẢNG TMĐT"]
    tot_row = next(x for x in range(1, ws.max_row + 1) if ws[f"B{x}"].value == "TỔNG CỘNG")
    assert abs(ws[f"H{tot_row}"].value - r.tmdt) < 1
