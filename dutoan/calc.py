"""Tính toàn bộ cơ cấu chi phí: G = G_TB/DV + G_QLDA + G_TV + G_K + G_DP.

Bám theo 2 template (BẢNG TMĐT, các sheet Cp_*, 3_GMS_PM_NOI_BO, Dongia_NgayCong,
DinhMucKTKT) và các sửa đổi đã chốt trong YEU-CAU-FINAL. Mọi công thức ở đây được viết
lại y hệt thành công thức Excel trong excel_export.py; sửa chỗ này thì sửa cả chỗ kia.
"""
import math
from dataclasses import dataclass, field

from . import scaling
from .catalog import GROUP_BY_CODE, PM_ROLES, MULT_LABEL, DM1688, DM1688_X
from .defaults import KDP_MAX, KDP_MAX_THUE


# ---------------------------------------------------------------- tiện ích
def rnd(x, nd=0):
    """ROUND của Excel (làm tròn nửa lên, xa số 0)."""
    m = 10 ** nd
    return math.copysign(math.floor(abs(x) * m + 0.5 + 1e-9), x) / m


def vnd(x):
    return f"{x:,.0f}".replace(",", ".")


def ceil_to(x, unit):
    unit = unit if unit and unit > 0 else 1
    return math.ceil(x / unit - 1e-9) * unit


def floor_to(x, unit):
    unit = unit if unit and unit > 0 else 1
    return math.floor(x / unit + 1e-9) * unit


def round_tmdt(base, rate, ts):
    """Làm tròn TMĐT lên; nếu làm dự phòng vượt Kdp tối đa thì làm tròn xuống."""
    x = base * (1 + rate)
    t = ceil_to(x, ts["lam_tron"])
    if t - base > kdp_max(ts) * base + 1e-6:
        t = floor_to(x, ts["lam_tron"])
    return t


def interp(x, xs, ys):
    """Nội suy tuyến tính giữa cận dưới/cận trên; ngoài bảng lấy giá trị đầu/cuối (như template)."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x < xs[i + 1]:
            return ys[i] - (ys[i] - ys[i + 1]) / (xs[i + 1] - xs[i]) * (x - xs[i])
    return ys[-1]


def kdp_max(ts):
    return KDP_MAX_THUE if ts["che_do"] == "THUE" else KDP_MAX[ts["loai_ho_so"]]


def tier(gms, ts):
    if gms >= ts["nguong_L"]:
        return 2
    if gms >= ts["nguong_M"]:
        return 1
    return 0


DEFAULT_COUNTS = {"goi": (2, 3, 5), "lop": (1, 3, 6), "he_thong": (0, 2, 5)}
COUNT_KEY = {"goi": "so_goi", "lop": "so_lop", "he_thong": "so_he_thong"}


def counts(gms, ts):
    t = tier(gms, ts)
    out = {k: (ts[COUNT_KEY[k]] if ts[COUNT_KEY[k]] is not None else v[t]) for k, v in DEFAULT_COUNTS.items()}
    out["nam"] = ts["so_nam_thue"]
    out[""] = 1
    return out


def day_price(grade, ts):
    """BANGLUONG_CG: ROUND(lương tháng × hệ số nâng / 26, 0)."""
    return rnd(ts["luong"][grade] * ts["he_so_nang"] / ts["ngay_thang"])


def cql_rate(ccg, ts):
    c = ts["cql"]
    if ccg <= c["nguong1"]:
        return c["r1"]
    if ccg < c["nguong2"]:
        return c["r2"]
    return c["r3"]


def tham_tra_tk_on(ts):
    v = ts["tham_tra_thiet_ke"]
    return (not ts["co_pm_noi_bo"]) if v is None else bool(v)


def ks_month_price(bac, ts):
    """Dongia_NgayCong: (Hcb + Hpc) × MLcs × (1 + Hdc) + (Hcb + Hpc) × MLcs × BH."""
    mlcb = (ts["ks_he_so"][bac - 1] + ts["ks_hpc"]) * ts["luong_co_so"]
    return mlcb * (1 + ts["hdc"][ts["vung"]]) + mlcb * ts["ks_bh"]


def ks_avg_month(ts):
    if ts["pm_don_gia_thang"]:
        return float(ts["pm_don_gia_thang"])
    bacs = ts["ks_bac_chon"] or [1]
    return sum(ks_month_price(b, ts) for b in bacs) / len(bacs)


def role_month_price(bac, ts):
    return ks_avg_month(ts) if bac in ("TB", None, "") else ks_month_price(int(bac), ts)


def pm_roles(ts):
    ratios = ts["pm_ty_le"] or [r for _, r in PM_ROLES]
    bacs = ts["pm_bac"] or ["TB"] * len(PM_ROLES)
    return [(n, ratios[i], bacs[i]) for i, (n, _) in enumerate(PM_ROLES)]


def line_pre(r):
    return float(r.get("so_luong") or 0) * float(r.get("don_gia") or 0)


def dm1688_rate(code, gms, ts):
    name, r2, r3 = DM1688[code]
    row = r3 if ts["loai_ho_so"] == "BCKTKT" else r2
    return name, rnd(interp(gms / 1e9, DM1688_X, row), 3)


# ---------------------------------------------------------------- kết quả
@dataclass
class Row:
    id: str
    name: str
    grade: str
    price: float
    auto_experts: int
    auto_days: int
    experts: int
    days: int
    mult: float
    mult_label: str
    mult_kind: str
    amount: float
    ref: str = ""
    ref_pre: float | None = None
    ref_value: float | None = None
    ref_note: str = ""
    use_ref: bool = False
    excluded: bool = False
    overridden: bool = False


@dataclass
class GroupResult:
    code: str
    name: str
    section: str
    rows: list
    ccg: float = 0.0
    cql_rate: float = 0.0
    tn_rate: float = 0.0
    cql: float = 0.0
    ck: float = 0.0
    tn: float = 0.0
    cg_pre: float = 0.0
    cg_vat: float = 0.0
    cg_total: float = 0.0
    ref_pre: float = 0.0
    ref_total: float = 0.0
    dm1688: dict | None = None
    override: float | None = None
    pre: float = 0.0
    vat: float = 0.0
    total: float = 0.0


@dataclass
class Item:
    key: str
    sec: str
    label: str
    kh: str
    pre: float
    vat: float
    note: str = ""

    @property
    def post(self):
        return self.pre + self.vat


@dataclass
class Result:
    gms: float
    tmdt: float
    counts: dict
    groups: dict = field(default_factory=dict)
    pm: dict = field(default_factory=dict)
    thue_pm: dict = field(default_factory=dict)
    qtvh_tron_goi: dict | None = None
    lists: dict = field(default_factory=dict)
    qlda_tu_th: dict | None = None
    fees: dict = field(default_factory=dict)
    items: list = field(default_factory=list)
    totals: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    compare: list = field(default_factory=list)
    phan_bo: dict = field(default_factory=dict)

    def item(self, key):
        for it in self.items:
            if it.key == key:
                return it
        return None


SEC_NAME = {"I": "CHI PHÍ TRANG THIẾT BỊ", "II": "CHI PHÍ QUẢN LÝ DỰ ÁN", "III": "CHI PHÍ TƯ VẤN ĐẦU TƯ",
            "IV": "CHI PHÍ KHÁC", "V": "CHI PHÍ DỰ PHÒNG"}
SEC_KH = {"I": "Gtb", "II": "Gqlda", "III": "Gtv", "IV": "Gk", "V": "Gdp"}


def sec_name(sec, ts):
    if sec == "I" and ts["che_do"] == "THUE":
        return "CHI PHÍ THUÊ DỊCH VỤ CÔNG NGHỆ SỐ"
    return SEC_NAME[sec]


def sec_kh(sec, ts):
    if sec == "I" and ts["che_do"] == "THUE":
        return "Gdv"
    return SEC_KH[sec]


# ---------------------------------------------------------------- nhóm A–J
def group_enabled(code, proj):
    ts = proj["tham_so"]
    if code in proj.get("nhom_tat", []):
        return False
    if code == "A":
        return ts["qlda"] == "THUE"
    if code == "I":
        return ts["co_pm_noi_bo"]
    if code == "J":
        return ts["che_do"] == "THUE" and not ts["j_tron_goi"]
    return True


def group_rates(g, ccg, ts):
    """Tư vấn/QLDA/kiểm thử: Cql theo Bảng 3.2; dịch vụ (đào tạo, triển khai, QTVH): CPC/TNCT theo đề xuất."""
    if g.section in ("TB", "DV"):
        return ts["pm_cpc"], ts["pm_tn"]
    return cql_rate(ccg, ts), ts["tn_tv"]


def nd214_ref(key, ts, ctx):
    """Template 5./6. Cp_TV THAU: ROUND(MIN(MAX(giá gói × tỷ lệ, min), max)) × (1 + VAT) × số gói."""
    n = ts["nd214"]
    goi = ctx["counts"]["goi"]
    labels = {"khlcnt": "lập KH LCNT", "lap_hsmt": "lập HSMT", "dg_hsdt": "đánh giá HSDT",
              "td_hsmt": "thẩm định HSMT", "td_kq": "thẩm định KQ LCNT"}
    k = key.replace("nd214_", "")
    r, lo, hi = n[k]
    if k == "khlcnt":
        pre = rnd(min(max(ctx["tv1_pre"] * r, lo), hi))
        note = f"NĐ 214: {r:.2%} × chi phí lập BCKT-KT (min {vnd(lo)}, max {vnd(hi)})"
    else:
        pre = rnd(min(max(ctx["gia_goi"] * r, lo), hi)) * goi
        note = f"NĐ 214: {labels[k]} {r:.2%} × giá gói (min {vnd(lo)}, max {vnd(hi)}) × {goi} gói"
    return pre, note


def compute_group(code, gms, proj, ctx):
    ts = proj["tham_so"]
    g = GROUP_BY_CODE[code]
    ov_all = proj.get("ghi_de", {})
    rows = []
    for t in g.tasks:
        if t.switch == "tham_tra_thiet_ke" and not tham_tra_tk_on(ts):
            continue
        if not scaling.is_active(t.anchors, gms, ts):
            continue
        ov = ov_all.get(t.id, {})
        if t.fixed:
            total = t.fixed[0] * t.fixed[1]
            ae, ad = t.fixed
        else:
            total = scaling.total_days(t.anchors, gms, ts)
            ae, ad = scaling.split(total, ts["bac_thang"])
        e = int(ov.get("so_cg") or ae)
        if ov.get("so_ngay"):
            d = int(ov["so_ngay"])
        elif ov.get("so_cg"):
            d = math.ceil(total / e)
        else:
            d = ad
        grade = ov.get("bac") or t.grade
        name = ov.get("ten") or ("Thiết kế cơ sở" if (t.id == "B4" and ts["thiet_ke"] == 2) else t.name)
        mult = ctx["counts"][t.mult]
        price = day_price(grade, ts)
        row = Row(t.id, name, grade, price, ae, ad, e, d, mult, MULT_LABEL[t.mult], t.mult, 0.0, ref=t.ref,
                  use_ref=bool(ov.get("dung_vb")) and t.ref != "", excluded=bool(ov.get("bo")),
                  overridden=any(ov.get(k) for k in ("so_cg", "so_ngay", "bac", "dung_vb", "bo", "ten")))
        if t.ref.startswith("nd214"):
            row.ref_pre, row.ref_note = nd214_ref(t.ref, ts, ctx)
        row.amount = 0.0 if (row.excluded or row.use_ref) else price * e * d * mult
        rows.append(row)

    # Công việc người dùng tự thêm: số chuyên gia × số ngày cố định (không co giãn theo Gms)
    for i, v in enumerate(proj.get("viec_them", {}).get(code, []), start=1):
        if not v.get("ten"):
            continue
        grade = v.get("bac") if v.get("bac") in ts["luong"] else "M3"
        e, d = int(v.get("so_cg") or 1), int(v.get("so_ngay") or 1)
        mult = float(v.get("he_so") or 1)
        price = day_price(grade, ts)
        rows.append(Row(f"{code}+{i}", v["ten"], grade, price, e, d, e, d, mult, "", "tuy_chon",
                        price * e * d * mult, overridden=True))

    res = GroupResult(code, g.name, g.section, rows)
    res.ccg = sum(r.amount for r in rows)
    res.cql_rate, res.tn_rate = group_rates(g, res.ccg, ts)
    for r in rows:
        if r.ref == "nd19":
            others = sum(x.amount for x in rows if x.id != r.id)
            r.ref_pre = rnd(ts["nd19_tl"] * others * (1 + res.cql_rate) * (1 + res.tn_rate))
            r.ref_note = f"NĐ 19/2026: {ts['nd19_tl']:.0%} × chi phí QLDA các việc còn lại (trước thuế)"
        if r.ref_pre is not None:
            r.ref_value = rnd(r.ref_pre * (1 + ts["vat"]))
    res.cql = res.ccg * res.cql_rate
    res.ck = float(proj.get("ck", {}).get(code) or 0)
    res.tn = rnd(res.tn_rate * (res.ccg + res.cql + res.ck))
    res.cg_pre = rnd(res.ccg + res.cql + res.ck + res.tn)
    res.cg_vat = rnd(ts["vat"] * (res.ccg + res.cql + res.ck + res.tn))
    res.cg_total = res.cg_pre + res.cg_vat
    chosen = [r for r in rows if r.use_ref and not r.excluded and r.ref_pre is not None]
    res.ref_pre = sum(r.ref_pre for r in chosen)
    res.ref_total = sum(r.ref_value for r in chosen)
    if code in DM1688 and gms > 0:
        name, rate = dm1688_rate(code, gms, ts)
        res.dm1688 = {"bang": name, "ty_le": rate, "gia_tri": rnd(gms * rate / 100 * (1 + ts["vat"]))}
    ovt = proj.get("ghi_de_nhom", {}).get(code)
    res.override = float(ovt) if ovt not in (None, "") else None
    if res.override is not None:
        res.total = res.override
        res.pre = rnd(res.override / (1 + ts["vat"]))
        res.vat = res.total - res.pre
    else:
        res.pre = res.cg_pre + res.ref_pre
        res.vat = res.cg_vat + (res.ref_total - res.ref_pre)
        res.total = res.pre + res.vat
    return res


# ---------------------------------------------------------------- nhóm K
def compute_pm(gms, ts):
    """3_GMS_PM_NOI_BO: Gms = NC × (1 + CPC) × (1 + TNCT) × (1 + thuế); NC = MM × Σ(tỷ lệ × đơn giá tháng)."""
    k = (1 + ts["pm_cpc"]) * (1 + ts["pm_tn"]) * (1 + ts["pm_thue"])
    nc = gms / k
    roles = [(n, r, b, role_month_price(b, ts)) for n, r, b in pm_roles(ts)]
    weighted = sum(r * p for _, r, _, p in roles)
    mm = nc / weighted if weighted else 0.0
    cpc = nc * ts["pm_cpc"]
    tn = (nc + cpc) * ts["pm_tn"]
    thue = (nc + cpc + tn) * ts["pm_thue"]
    rows = [{"vai_tro": n, "ty_le": r, "bac": b, "don_gia_thang": p, "mm": mm * r, "thanh_tien": mm * r * p}
            for n, r, b, p in roles]
    return {"gms": gms, "nc": nc, "cpc": cpc, "tn": tn, "thue": thue, "total": nc + cpc + tn + thue,
            "mm": mm, "roles": rows}


def compute_thue_pm(pm, ts):
    """TONG_HOP - Thue: tổng giá trị PM nội bộ ÷ khấu hao (8 năm) × số năm thuê."""
    n, kh = ts["so_nam_thue"], ts["khau_hao_nam"]
    f = n / kh
    return {"nc": pm["nc"] * f, "cpc": pm["cpc"] * f, "tn": pm["tn"] * f, "thue": pm["thue"] * f,
            "total": pm["total"] * f, "he_so": f}


def compute_tron_goi(ts):
    nc = ts["j_tron_goi_nam"] * ts["so_nam_thue"]
    cpc = nc * ts["pm_cpc"]
    tn = (nc + cpc) * ts["pm_tn"]
    vat = (nc + cpc + tn) * ts["vat"]
    return {"nc": nc, "cpc": cpc, "tn": tn, "vat": vat, "pre": nc + cpc + tn, "total": nc + cpc + tn + vat}


# ---------------------------------------------------------------- QLDA tự thực hiện
def compute_qlda_tu_th(proj):
    ts = proj["tham_so"]
    rows = []
    for r in proj["qlda_nhan_su"]:
        hs = sum(float(r.get(k) or 0) for k in ("he_so_luong", "pc_chuc_vu", "pc_khu_vuc", "pc_khac"))
        tien = hs * ts["luong_co_so"] * float(r.get("so_nguoi") or 0) * float(r.get("so_thang") or 0)
        rows.append({**r, "tong_he_so": hs, "thanh_tien": tien})
    luong = sum(r["thanh_tien"] for r in rows)
    bh = luong * ts["bh_qlda"]
    khac = sum(float(r.get("gia_tri") or 0) for r in proj["qlda_chi_khac"])
    return {"rows": rows, "luong": luong, "bh": bh, "chi_khac": khac, "total": luong + bh + khac}


# ---------------------------------------------------------------- G_K theo tỷ lệ (BẢNG TMĐT k1–k3)
def tb_factor(ts, g_tb, tmdt):
    v = ts["tb_tren_50"]
    on = (tmdt > 0 and g_tb / tmdt >= 0.5) if v is None else bool(v)
    return ts["he_so_tb"] if on else 1.0


def compute_fees(tmdt, base_pre, g_tb, ts):
    x = tmdt / 1e9
    tab = ts["bang_kiem_toan"]
    xs = [r[0] for r in tab]
    r_tt = rnd(interp(x, xs, [r[1] for r in tab]), 4)
    r_kt = rnd(interp(x, xs, [r[2] for r in tab]), 4)
    ptab = ts["bang_phi_tham_dinh"]
    r_ptd = rnd(interp(x, [r[0] for r in ptab], [r[1] for r in ptab]), 3)
    k_tb = tb_factor(ts, g_tb, tmdt)
    kt_on = ts["kiem_toan_doc_lap"]
    k_tt = ts["he_so_kt_doc_lap"] if kt_on else 1.0
    k_ptd = ts["ptd_giam_tt64"] * (0.5 if ts["ptd_co_tham_tra"] else 1.0)
    ptd = rnd(tmdt * r_ptd / 100 * k_ptd) if ts["phi_tham_dinh"] else 0.0
    tdg = float(ts["tham_dinh_gia"] or 0)
    co_so = base_pre + ptd + tdg  # (F6 + F9 + F10 + F19 + F20) của BẢNG TMĐT
    kt_pre = max(rnd(co_so * r_kt / 100 * k_tb), ts["kt_min"]) if kt_on else 0.0
    tt_pre = max(rnd(co_so * r_tt / 100 * k_tb * k_tt), ts["tt_min"])
    return {"tmdt": tmdt, "co_so": co_so, "ty_le_tt": r_tt, "ty_le_kt": r_kt, "ty_le_ptd": r_ptd,
            "he_so_tb": k_tb, "he_so_tt": k_tt, "he_so_ptd": k_ptd,
            "kiem_toan_pre": kt_pre, "kiem_toan_vat": rnd(kt_pre * ts["vat"]),
            "tham_tra": tt_pre, "phi_tham_dinh": ptd, "tham_dinh_gia": tdg}


# ---------------------------------------------------------------- tính tại một Gms
def _pre(proj, gms):
    """Mọi khoản không phụ thuộc TMĐT."""
    ts = proj["tham_so"]
    thue = ts["che_do"] == "THUE"
    res = Result(gms=gms, tmdt=0.0, counts=counts(gms, ts))
    ctx = {"counts": res.counts, "gia_goi": 0.0, "tv1_pre": 0.0}
    items = []

    def add(key, sec, label, kh, pre, vat, note=""):
        items.append(Item(key, sec, label, kh, pre, vat, note or DEFAULT_NOTES.get(key, "")))

    res.pm = compute_pm(gms, ts)
    lists = {}
    for k in ("thiet_bi", "pm_thuong_mai", "tb_khac", "dv_thue_nam"):
        pre = sum(line_pre(r) for r in proj[k])
        vat = sum(line_pre(r) * float(r.get("vat") or 0) for r in proj[k])
        lists[k] = (pre, vat)
    gk_khac = sum(float(r.get("gia_tri") or 0) for r in proj["gk_khac"])
    res.lists = lists

    def grp(code):
        if not group_enabled(code, proj):
            return None
        g = compute_group(code, gms, proj, ctx)
        res.groups[code] = g
        return g

    def add_grp(key, sec, label, kh, code, note=""):
        g = grp(code)
        if g is not None:
            add(key, sec, label, kh, g.pre, g.vat, note)
        return g

    n = ts["so_nam_thue"]
    if thue:
        res.thue_pm = t = compute_thue_pm(res.pm, ts)
        add("thue_pm", "I", "Chi phí thuê dịch vụ phần mềm (giá trị PM nội bộ ÷ khấu hao × số năm thuê)", "Gdvcns",
            t["total"] - t["thue"], t["thue"], f"Gms ÷ {ts['khau_hao_nam']} năm × {n} năm")
        if ts["j_tron_goi"]:
            res.qtvh_tron_goi = q = compute_tron_goi(ts)
            add("qtvh", "I", "Chi phí quản trị, vận hành, bảo trì dịch vụ (báo giá trọn gói)", "Gvh", q["pre"], q["vat"])
        else:
            add_grp("qtvh", "I", "Chi phí quản trị, vận hành, bảo trì dịch vụ", "Gvh", "J", f"{n} năm")
        pre, vat = lists["dv_thue_nam"]
        add("dv_nam", "I", "Chi phí dịch vụ hạ tầng kỹ thuật, dịch vụ thuê hằng năm", "Ghtkt", pre * n, vat * n, f"× {n} năm")
    else:
        label = "Chi phí phần mềm nội bộ theo yêu cầu riêng" if ts["co_pm_noi_bo"] else "Chi phí phần mềm"
        add("pm", "I", label, "Gms-pmnb", gms - res.pm["thue"], res.pm["thue"])
    add("thiet_bi", "I", "Chi phí mua sắm trang thiết bị công nghệ số", "Gms-tbs", *lists["thiet_bi"])
    add("pm_tm", "I", "Chi phí mua sắm phần mềm thương mại/phổ biến", "Gms-pmtm", *lists["pm_thuong_mai"])
    add("tb_khac", "I", "Chi phí lắp đặt, tạo lập CSDL, vận chuyển, khác thuộc GTB", "Gdvtk", *lists["tb_khac"])
    add_grp("dao_tao", "I", "Chi phí đào tạo, tập huấn hướng dẫn sử dụng, quản trị, vận hành", "Gđt", "G")
    add_grp("trien_khai", "I", "Chi phí triển khai, tích hợp, hỗ trợ trước nghiệm thu", "Gtk", "H")
    pre_I = sum(i.pre for i in items if i.sec == "I")
    ctx["gia_goi"] = pre_I / res.counts["goi"] if res.counts["goi"] else 0.0

    if ts["qlda"] == "THUE":
        add_grp("qlda", "II", "Chi phí quản lý dự án (thuê tư vấn)", "Gqlda", "A")
    else:
        res.qlda_tu_th = q = compute_qlda_tu_th(proj)
        add("qlda", "II", "Chi phí quản lý dự án (CĐT tự thực hiện – TT 70/2024)", "Gqlda", q["total"], 0.0, "Mẫu 02/DT-QLDA")

    tv1 = add_grp("tv1", "III", "Chi phí lập báo cáo kinh tế – kỹ thuật", "tv1", "B")
    ctx["tv1_pre"] = tv1.pre if tv1 else 0.0
    add_grp("tv2", "III", "Chi phí thẩm tra báo cáo kinh tế – kỹ thuật", "tv2", "C")
    add_grp("tv3", "III", "Chi phí tư vấn giám sát", "tv3", "D")
    add_grp("tv4", "III", "Chi phí tư vấn lập E-HSMT và đánh giá E-HSDT", "tv4", "E")
    add_grp("tv5", "III", "Chi phí tư vấn thẩm định E-HSMT và kết quả lựa chọn nhà thầu", "tv5", "F")

    if ts["co_pm_noi_bo"]:
        add_grp("kiem_thu", "IV", "Chi phí kiểm thử phần mềm nội bộ (TT 41/2026)", "k5", "I")
    if gk_khac:
        add("gk_khac", "IV", "Chi phí khác (nhập tay)", "k6", gk_khac, 0.0)
    res.items = items
    return res


FEE_KEYS = ("kiem_toan", "tham_tra", "phi_tham_dinh", "tham_dinh_gia")

# Ghi chú mặc định từng dòng của bảng tổng hợp (người dùng sửa được, lưu ở proj["ghi_chu"])
DEFAULT_NOTES = {
    "pm": "TT 39/2026/TT-BKHCN; Gms = NC × (1 + CPC) × (1 + TNCT) × (1 + thuế)",
    "thue_pm": "TT 39/2026; khấu hao PM tối đa 8 năm (96 tháng)",
    "qtvh": "Theo khối lượng, đơn giá chuyên gia (nhóm J)",
    "dv_nam": "Theo báo giá dịch vụ thuê hằng năm",
    "thiet_bi": "Khối lượng × đơn giá theo báo giá/thẩm định giá",
    "pm_tm": "Khối lượng × đơn giá theo báo giá/thẩm định giá",
    "tb_khac": "Khối lượng × đơn giá; NĐ 224/2026 Điều 49",
    "dao_tao": "Theo khối lượng, đơn giá chuyên gia (nhóm G)",
    "trien_khai": "Theo khối lượng, đơn giá chuyên gia (nhóm H)",
    "qlda": "Phương pháp chuyên gia – TT 39/2026, TT 07/2026/TT-BNV",
    "tv1": "Phương pháp chuyên gia – TT 39/2026, TT 07/2026/TT-BNV",
    "tv2": "Phương pháp chuyên gia – TT 39/2026, TT 07/2026/TT-BNV",
    "tv3": "Phương pháp chuyên gia – TT 39/2026, TT 07/2026/TT-BNV",
    "tv4": "Phương pháp chuyên gia; tham chiếu NĐ 214/2025 Điều 14",
    "tv5": "Phương pháp chuyên gia; tham chiếu NĐ 214/2025 Điều 14",
    "kiem_thu": "TT 41/2026/TT-BKHCN Điều 10 – kiểm thử độc lập",
    "gk_khac": "Nhập tay theo căn cứ",
    "kiem_toan": "NĐ 193/2026/NĐ-CP Điều 20",
    "tham_tra": "NĐ 193/2026/NĐ-CP Điều 20",
    "phi_tham_dinh": "TT 28/2023/TT-BTC; giảm 50% theo TT 64/2025/TT-BTC",
    "tham_dinh_gia": "Theo báo giá/quyết định",
    "du_phong": "TT 39/2026; NĐ 224/2026 Điều 49 – (Gtb + Gqlda + Gtv + Gk) × Kdp",
}
SEC_NOTES = {
    "I": "Gtb = Gms + Gdvtk",
    "II": "TT 39/2026 Điều 5",
    "III": "tv1 + tv2 + … + tv5",
    "IV": "k1 + k2 + … ",
    "V": "Không vượt Kdp tối đa",
}


def _finish(res, proj, tmdt):
    ts = proj["tham_so"]
    items = [i for i in res.items if i.key not in FEE_KEYS]
    base_pre = sum(i.pre for i in items if i.sec in ("I", "II", "III"))
    g_tb = sum(i.post for i in items if i.sec == "I")
    f = res.fees = compute_fees(tmdt, base_pre, g_tb, ts)
    fees = [
        Item("kiem_toan", "IV", "Chi phí kiểm toán", "k1", f["kiem_toan_pre"], f["kiem_toan_vat"], DEFAULT_NOTES["kiem_toan"]),
        Item("tham_tra", "IV", "Chi phí thẩm tra, phê duyệt quyết toán", "k2", f["tham_tra"], 0.0, DEFAULT_NOTES["tham_tra"]),
        Item("phi_tham_dinh", "IV", "Lệ phí thẩm định dự án", "k3", f["phi_tham_dinh"], 0.0, DEFAULT_NOTES["phi_tham_dinh"]),
        Item("tham_dinh_gia", "IV", "Chi phí thẩm định giá", "k4", f["tham_dinh_gia"], 0.0, DEFAULT_NOTES["tham_dinh_gia"]),
    ]
    i4 = next((n for n, i in enumerate(items) if i.sec == "IV"), len(items))
    res.items = items[:i4] + fees + items[i4:]
    return {s: sum(i.post for i in res.items if i.sec == s) for s in ("I", "II", "III", "IV")}


def _compute_at(proj, gms, tmdt_fixed=None):
    ts = proj["tham_so"]
    res = _pre(proj, gms)
    if tmdt_fixed is not None:
        tmdt = float(tmdt_fixed)
        sec = _finish(res, proj, tmdt)
        base = sum(sec.values())
    else:
        kdp = ts["kdp"] if ts["kdp"] is not None else kdp_max(ts)
        rate = kdp + ts["kdp_truot_gia"]
        tmdt = round_tmdt(sum(i.post for i in res.items), rate, ts)
        for _ in range(200):
            sec = _finish(res, proj, tmdt)
            base = sum(sec.values())
            new = round_tmdt(base, rate, ts)
            if abs(new - tmdt) < 0.5:
                break
            tmdt = new
    dp = tmdt - base
    res.tmdt = tmdt
    res.items.append(Item("du_phong", "V", "Chi phí dự phòng", "Gdp", dp, 0.0, DEFAULT_NOTES["du_phong"]))
    res.totals = {**sec, "V": dp, "base": base, "tmdt": tmdt, "dp_ratio": dp / base if base else 0.0,
                  "pre": sum(i.pre for i in res.items), "vat": sum(i.vat for i in res.items)}
    return res


def solve_gms(proj):
    """Chế độ nhập TMĐT: tìm Gms lớn nhất sao cho dự phòng ≥ mức tối thiểu (dự phòng nhỏ nhất)."""
    ts = proj["tham_so"]
    tmdt = ts["tmdt"]
    dp_min = ts["du_phong_toi_thieu"]

    def ok(g):
        return _compute_at(proj, g, tmdt).totals["V"] >= dp_min - 1e-6

    if not ok(0):
        return 0.0, False
    lo, hi = 0.0, float(tmdt)
    for _ in range(60):
        mid = (lo + hi) / 2
        if ok(mid):
            lo = mid
        else:
            hi = mid
    g = math.floor(lo / 1000) * 1000
    while g > 0 and not ok(g):
        g -= 1000
    return float(g), True


# ---------------------------------------------------------------- phân bổ vốn theo năm
YEAR1_THUE = {"tv1", "tv2", "tv4", "tv5", "phi_tham_dinh", "tham_dinh_gia", "thiet_bi", "pm_tm", "tb_khac",
              "dao_tao", "trien_khai", "kiem_thu"}
YEAR1_XD = {"tv1", "tv2", "tv4", "tv5", "phi_tham_dinh", "tham_dinh_gia"}
LAST = {"tham_tra", "kiem_toan"}


def so_nam_phan_bo(ts):
    return int(ts["so_nam_thue"] if ts["che_do"] == "THUE" else ts["so_nam_phan_bo"])


def default_alloc(key, n, che_do):
    if n <= 1:
        return [1.0]
    first = [1.0] + [0.0] * (n - 1)
    last = [0.0] * (n - 1) + [1.0]
    if che_do == "THUE":
        if key in YEAR1_THUE:
            return first
        if key in LAST:
            return last
        return [1.0 / n] * n
    return first if key in YEAR1_XD else last


def start_year(proj):
    try:
        return int(str(proj["thong_tin"]["thoi_diem"])[:4])
    except (ValueError, KeyError):
        return 2026


def compute_phan_bo(res, proj):
    ts = proj["tham_so"]
    n = so_nam_phan_bo(ts)
    saved = proj.get("phan_bo", {})
    rows = []
    for it in res.items:
        pct = saved.get(it.key)
        if not pct or len(pct) != n:
            pct = default_alloc(it.key, n, ts["che_do"])
        rows.append({"key": it.key, "nhom": it.sec, "noi_dung": it.label, "tong": it.post, "ty_le": list(pct),
                     "nam": [it.post * p for p in pct]})
    years = [sum(r["nam"][i] for r in rows) for i in range(n)]
    y0 = start_year(proj)
    return {"n": n, "rows": rows, "years": years, "labels": [f"Năm {y0 + i}" for i in range(n)]}


# ---------------------------------------------------------------- điểm vào
def compute(proj):
    ts = proj["tham_so"]
    warnings = []
    if ts["nhap"] == "TMDT":
        gms, feasible = solve_gms(proj)
        res = _compute_at(proj, gms, ts["tmdt"])
        if not feasible:
            warnings.append("TMĐT nhập vào nhỏ hơn tổng các chi phí khác ngay cả khi Gms = 0 → không có lời giải.")
    else:
        res = _compute_at(proj, ts["gms"])

    kmax = kdp_max(ts)
    if ts["nhap"] == "GMS" and ts["kdp"] is None:
        warnings.append(f"Chưa nhập Kdp áp dụng → tạm dùng mức tối đa {kmax:.0%}.")
    if ts["nhap"] == "GMS" and ts["kdp"] is not None and ts["kdp"] > kmax:
        warnings.append(f"Kdp áp dụng {ts['kdp']:.1%} vượt mức tối đa {kmax:.0%}.")
    if res.totals["dp_ratio"] > kmax + 1e-9:
        warnings.append(f"Dự phòng = {res.totals['dp_ratio']:.2%} của (Gtb + Gqlda + Gtv + Gk), vượt Kdp tối đa {kmax:.0%}.")
    if res.totals["V"] < 0:
        warnings.append("Dự phòng âm: các chi phí khác vượt TMĐT.")
    if ts["che_do"] == "THUE" and ts["so_nam_thue"] > ts["khau_hao_nam"]:
        warnings.append(f"Số năm thuê ({ts['so_nam_thue']}) vượt thời gian khấu hao tối đa {ts['khau_hao_nam']} năm (96 tháng).")
    if ts["he_so_nang"] > 1.5:
        warnings.append("Hệ số nâng lương chuyên gia vượt 1,5 lần (TT 07/2026/TT-BNV).")
    # So sánh từng công việc có định mức theo văn bản (NĐ 214, NĐ 19) với số tính theo chuyên gia
    for code, g in res.groups.items():
        for r in g.rows:
            if r.ref_value is None or r.excluded:
                continue
            cg = rnd(r.price * r.experts * r.days * r.mult * (1 + g.cql_rate) * (1 + g.tn_rate) * (1 + ts["vat"]))
            res.compare.append({
                "nhom": code, "nhom_ten": g.name, "ma": r.id, "cong_viec": r.name,
                "chuyen_gia": cg, "van_ban": r.ref_value, "can_cu": r.ref_note,
                "lech": (cg - r.ref_value) / r.ref_value if r.ref_value else 0.0,
                "dang_dung": "Văn bản" if r.use_ref else "Chuyên gia",
            })
    res.warnings = warnings
    res.phan_bo = compute_phan_bo(res, proj)
    return res
