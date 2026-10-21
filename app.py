"""Ứng dụng web tính TMĐT / dự toán phần mềm theo TT 39/2026/TT-BKHCN.

Chạy:  streamlit run app.py
"""
import datetime
import hashlib
import json
import math
import re

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from dutoan.calc import compute, kdp_max, ks_month_price, day_price, vnd, sec_name, sec_kh, SEC_NOTES
from dutoan.catalog import GROUP_BY_CODE, PM_ROLES, TASK_BY_ID
from dutoan import storage
from dutoan.defaults import GRADES, GRADE_NOTE, LOAI_HO_SO
from dutoan.excel_export import export_bytes

APP_VERSION = "1.1.0"

st.set_page_config(page_title="Dự toán phần mềm TT 39", page_icon="🧮", layout="wide")
st.markdown("""
<style>
section[data-testid="stSidebar"] .stButton button { justify-content: flex-start; padding-left: 1rem; }
.block-container, [data-testid="stMainBlockContainer"] { padding-top: 1.5rem !important; }
[data-testid="stSidebarHeader"] { height: 2rem !important; min-height: 0 !important; padding-top: .25rem !important;
                                  padding-bottom: 0 !important; margin-bottom: 0 !important; }
[data-testid="stSidebarUserContent"] { padding-top: 0 !important; margin-top: -0.5rem; }
[data-testid="stSidebarUserContent"] h2 { padding-top: 0; margin-top: 0; }
[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(iframe) { height: 0; overflow: hidden; margin: 0; }
.sb-block { margin-top: -0.6rem; padding-bottom: .55rem; }
.sb-block .kpi-grid { margin: 0; }
.sb-hr { height: 0; border-top: 1px solid #d9dde5; margin: .55rem 0; }
.sb-warn { color: #6b7280; font-size: .85rem; margin: .35rem 0 0 0; }
.sb-block .step-label { margin: .2rem 0 0 0; }
.step-label { color: #6b7280; font-size: 0.85rem; letter-spacing: .04em; margin: .25rem 0 .5rem 0; }
.page-desc { color: #6b7280; margin-top: -0.6rem; margin-bottom: 1rem; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: .25rem 0 1rem 0; }
.kpi { border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 16px; background: #fff; }
.kpi.main { border: 1.5px solid #2F4A9E; background: #F3F6FD; }
.kpi .lab { color: #6b7280; font-size: .85rem; margin-bottom: 4px; }
.kpi .val { font-size: 1.5rem; font-weight: 700; color: #1f2937; line-height: 1.25; overflow-wrap: anywhere;
            font-variant-numeric: tabular-nums; }
.kpi.main .val { color: #2F4A9E; }
.kpi .val .unit { font-size: .95rem; font-weight: 500; color: #6b7280; margin-left: 4px; }
.kpi .short { color: #374151; font-size: .9rem; margin-top: 2px; }
.kpi .sub { color: #6b7280; font-size: .8rem; margin-top: 6px; border-top: 1px dashed #e5e7eb; padding-top: 6px; }
section[data-testid="stSidebar"] .kpi { padding: 10px 12px; }
.tbl-wrap { overflow-x: auto; margin-bottom: .5rem; }
.tbl { width: 100%; border-collapse: collapse; font-size: .875rem; }
.tbl tr { height: 35px; }
.tbl th { background: #F1F3F7; color: #374151; font-weight: 600; text-align: left; padding: 0 10px; height: 35px; white-space: nowrap;
          border-bottom: 1px solid #e5e7eb; position: sticky; top: 0; }
.tbl td { padding: 0 10px; height: 35px; line-height: 1.2; border-bottom: 1px solid #eef0f4; vertical-align: middle;
          white-space: nowrap; }
.tbl td.num, .tbl th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.tbl tr.sec td { font-weight: 700; background: #F7F8FB; }
.tbl tr.total td { font-weight: 800; background: #E8EDF8; color: #2F4A9E; border-top: 2px solid #2F4A9E; }
.tbl tr.hot td { background: #FFF7E6; }
.tbl td.note { color: #6b7280; }
section[data-testid="stSidebar"] .kpi .val { font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("ver", 0)
ss.setdefault("step", 0)
ss.setdefault("pid", None)
ss.setdefault("proj", None)


def _hash(p):
    """Băm nội dung dự án (bỏ phần _meta ngày giờ) để biết có thay đổi cần lưu không."""
    data = {k: v for k, v in (p or {}).items() if k != "_meta"}
    return hashlib.md5(json.dumps(data, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def open_project(pid):
    ss.pid = pid
    ss.proj = storage.load_project(pid) if pid else None
    ss.saved_hash = _hash(ss.proj) if ss.proj else None
    ss.step = 0
    ss.ver += 1


def _ngay(iso):
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}" if len(iso) >= 10 else ""


with st.sidebar:
    st.markdown(f"## 🧮 Dự toán PM <span style='font-size:.9rem'>v{APP_VERSION}</span>", unsafe_allow_html=True)
    st.caption("TT 39/2026/TT-BKHCN · NĐ 224/2026")
    projects = storage.list_projects()
    if storage.BROKEN:
        st.warning("Không đọc được file dự án: " + "; ".join(f"`{k}`" for k in storage.BROKEN))
    ids = [x[0] for x in projects]
    labels = {pid: f"{name}  ·  {_ngay(upd)}" for pid, name, upd in projects}
    if ss.pid and ss.pid not in ids:  # dự án vừa bị xoá ở nơi khác
        open_project(None)
    sel = st.selectbox("Dự án", ids, index=ids.index(ss.pid) if ss.pid in ids else None,
                       placeholder="— Chọn dự án —", format_func=lambda i: labels.get(i, i), key=f"pick{ss.ver}")
    if sel != ss.pid:
        open_project(sel)
        st.rerun()
    with st.expander("➕ Tạo dự án mới", expanded=not ids):
        with st.form("new_project_form", clear_on_submit=True, border=False):
            new_name = st.text_input("Tên dự án")
            if st.form_submit_button("Tạo dự án", type="primary"):
                if new_name.strip():
                    open_project(storage.create_project(new_name.strip()))
                    st.rerun()
                else:
                    st.warning("Nhập tên dự án.")
        up = st.file_uploader("Hoặc nhập từ file dự án (.json) đã tải về máy", type="json",
                              help="File tải về ở bước 9b – sẽ được thêm thành một dự án trong danh sách")
        if up is not None and ss.get("loaded_sig") != (up.name, up.size):
            ss.loaded_sig = (up.name, up.size)
            try:
                open_project(storage.create_project(None, json.load(up)))
                st.rerun()
            except (ValueError, KeyError, TypeError) as e:
                st.error(f"File không đúng định dạng dự án: {e}")

if ss.proj is None:
    st.title("🧮 Dự toán phần mềm theo TT 39/2026/TT-BKHCN")
    st.info("**Tạo** hoặc **chọn** một dự án ở thanh bên trái để bắt đầu.")
    st.markdown(
        "**Quy trình 9 bước:** Nhập thông tin → Thiết bị & dịch vụ → Chi tiết công việc → Phần mềm nội bộ → "
        "QLDA tự thực hiện → Tổng hợp chi phí → Phân bổ vốn → Cấu hình nâng cao → Xuất Excel & lưu.  \n"
        "Dự án được **tự động lưu** trên máy (thư mục `workspace/projects`) sau mỗi thay đổi; lần sau chỉ cần chọn lại "
        "trong ô **Dự án**.")
    st.stop()

proj = ss.proj
ts = proj["tham_so"]


# ================================================================== tiện ích widget
def _get(path):
    d = proj
    for k in path:
        d = d[k]
    return d


def _set(path, v):
    d = proj
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = v


def w(kind, label, path, scale=1, **kw):
    """Widget gắn với một giá trị trong dự án; scale=100 để hiển thị phần trăm."""
    key = f"w{ss.ver}_" + ".".join(map(str, path))
    kw.pop("value", None)
    if key not in ss:
        cur = _get(path)
        if cur is None and kind == "number_input":
            kw["value"] = None
        else:
            ss[key] = cur * scale if (scale != 1 and cur is not None) else cur
    val = getattr(st, kind)(label, key=key, **kw)
    _set(path, val / scale if (scale != 1 and val is not None) else val)
    return val


def parse_money(text):
    digits = re.sub(r"[^0-9]", "", str(text or ""))
    return float(digits) if digits else None


def _fmt_money_cb(key):
    v = parse_money(ss.get(key))
    ss[key] = vnd(v) if v is not None else ""


def money_input(label, key, init, allow_empty=False, **kw):
    """Ô nhập số tiền dạng chữ, tự chèn dấu chấm phân cách hàng nghìn ngay khi gõ (xem fmt_script)."""
    if "(đồng)" not in label:
        label = f"{label} (đồng)"
    if key not in ss:
        ss[key] = vnd(init) if init is not None else ""
    st.text_input(label, key=key, on_change=_fmt_money_cb, args=(key,), placeholder=kw.pop("placeholder", "0"), **kw)
    v = parse_money(ss[key])
    return v if (v is not None or allow_empty) else 0.0


def money(label, path, allow_empty=False, **kw):
    key = f"w{ss.ver}_" + ".".join(map(str, path))
    v = money_input(label, key, _get(path), allow_empty=allow_empty, **kw)
    _set(path, v)
    return v


def date_field(label, path):
    """Ô ngày dd/mm/yyyy: gõ trực tiếp hoặc chọn trên lịch; lưu dạng yyyy-mm-dd."""
    key = f"w{ss.ver}_" + ".".join(map(str, path))
    if key not in ss:
        try:
            ss[key] = datetime.date.fromisoformat(str(_get(path))[:10])
        except ValueError:
            ss[key] = datetime.date.today()
    d = st.date_input(label, key=key, format="DD/MM/YYYY", min_value=datetime.date(2000, 1, 1),
                      max_value=datetime.date(2100, 12, 31))
    _set(path, d.isoformat() if d else "")


FMT_SCRIPT = r"""<script>
(function () {
  const win = window.parent, doc = win.document;
  if (win.__vndFmt) return;
  win.__vndFmt = true;
  const setter = Object.getOwnPropertyDescriptor(win.HTMLInputElement.prototype, 'value').set;
  const fmt = s => { const d = s.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
                     return d.replace(/\B(?=(\d{3})+(?!\d))/g, '.'); };
  doc.addEventListener('input', function (e) {
    const el = e.target;
    if (!el || el.tagName !== 'INPUT' || el.type !== 'text') return;
    if (!(el.getAttribute('aria-label') || '').includes('(đồng)')) return;
    const old = el.value, pos = el.selectionStart == null ? old.length : el.selectionStart;
    const right = old.slice(pos).replace(/\D/g, '').length;
    const nv = fmt(old);
    if (nv === old) return;
    setter.call(el, nv);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    let i = nv.length, c = 0;
    while (i > 0 && c < right) { i--; if (/\d/.test(nv[i])) c++; }
    el.setSelectionRange(i, i);
  }, true);
})();
</script>"""


def pct(label, path, **kw):
    return w("number_input", label, path, scale=100, min_value=0.0, step=0.5, format="%.2f", **kw)


def tri(label, path, auto_text):
    """Công tắc 3 trạng thái: tự động (None) / có / không."""
    to_ui = {None: "AUTO", True: "CO", False: "KHONG"}
    names = {"AUTO": auto_text, "CO": "Có", "KHONG": "Không"}
    key = f"w{ss.ver}_" + ".".join(map(str, path))
    if key not in ss:
        ss[key] = to_ui[_get(path)]
    v = st.selectbox(label, list(names), format_func=names.get, key=key)
    _set(path, {"AUTO": None, "CO": True, "KHONG": False}[v])


# Chuẩn bảng của hệ thống: mọi bảng dòng cao 35 px (ROW_STD), cột rộng vừa nội dung (editor()), bảng chỉ xem dùng HTML.


ROW_STD = 35  # px – chiều cao dòng chuẩn của bảng Streamlit


MIN_W = {"small": 64, "medium": 150, "large": 240}  # độ rộng tối thiểu (px) khi cột khai báo small/medium/large
CHAR_PX = 7.4  # độ rộng trung bình 1 ký tự (font 14px)


def _cell_text(v):
    v = clean(v)
    if v is None:
        return ""
    if isinstance(v, bool):
        return "xx"
    if isinstance(v, float) and v.is_integer() or isinstance(v, int):
        return f"{v:,.0f}"
    if isinstance(v, float):
        return f"{v:,.2f}"
    return str(v)


def editor(data, column_config=None, width=None, max_w=380, **kw):
    """st.data_editor với độ rộng từng cột vừa đủ nội dung dài nhất (không kéo giãn cả bảng)."""
    cfg = {}
    given = dict(column_config or {})
    for col in data.columns:
        c = dict(given.get(col) or {})
        if isinstance(c.get("width"), int):
            cfg[col] = c
            continue
        texts = [_cell_text(v) for v in data[col].tolist()]
        opts = (c.get("type_config") or {}).get("options") or []
        label = c.get("label") or str(col)
        n = max([len(label) + 3] + [len(t) for t in texts] + [len(str(o)) + 3 for o in opts])
        px = int(n * CHAR_PX + 28)
        px = max(px, MIN_W.get(c.get("width"), 56))
        c["width"] = min(px, max_w)
        cfg[col] = c
    for col, c in given.items():
        cfg.setdefault(col, c)
    return st.data_editor(data, column_config=cfg, width="content", **kw)


def ed_height(n, dynamic=False, row=None):
    """Chiều cao khung bảng sửa được để thấy hết các dòng, không phải cuộn."""
    return 40 + (row or ROW_STD) * (n + (1 if dynamic else 0))


def df_hash(df):
    return hashlib.md5(pd.util.hash_pandas_object(df.astype(str), index=True).values.tobytes()).hexdigest()[:10]


def clean(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return v


def snapshot(name, build):
    """Ảnh chụp dữ liệu ban đầu cho data_editor. Dựng lại từ dự án khi editor chưa hiển thị
    (Streamlit xoá trạng thái widget khi chuyển sang bước khác)."""
    snap, ed = f"snap{ss.ver}_{name}", f"ed{ss.ver}_{name}"
    if snap not in ss or ed not in ss:
        ss[snap] = build()
    return ss[snap], ed


def list_editor(key, cols, labels, money_cols=(), pct_cols=()):
    def build():
        rows = [{c: (r.get(c) * 100 if c in pct_cols and r.get(c) is not None else r.get(c)) for c in cols} for r in proj[key]]
        return pd.DataFrame(rows, columns=cols)

    base, ed_key = snapshot(key, build)
    cfg = {c: st.column_config.Column(labels[i], width="large" if c in ("ten", "vi_tri") else
                                      ("medium" if c in ("phuong_phap", "nguon", "ghi_chu") else None))
           for i, c in enumerate(cols)}
    for c in money_cols:
        cfg[c] = st.column_config.NumberColumn(labels[cols.index(c)], min_value=0, step=1000, format="localized")
    for c in pct_cols:
        cfg[c] = st.column_config.NumberColumn(labels[cols.index(c)] + " (%)", min_value=0, max_value=100, step=1)
    df = editor(base, height=ed_height(len(base), True, ROW_STD), num_rows="dynamic", key=ed_key,
                        column_config=cfg, width="stretch")
    out = []
    for rec in df.to_dict("records"):
        rec = {k: clean(v) for k, v in rec.items()}
        if not any(v not in (None, "") for v in rec.values()):
            continue
        for c in pct_cols:
            rec[c] = (rec[c] or 0) / 100
        out.append(rec)
    proj[key] = out


def show_table(rows, money_cols=(), pct_cols=(), height=None, bold_rows=()):
    """Bảng chỉ để xem: HTML, chữ dài tự xuống dòng, cột số căn phải (cùng kiểu bảng 6a).
    bold_rows: chỉ số các dòng in đậm (ví dụ dòng tổng)."""
    if not rows:
        return
    headers = list(dict.fromkeys(k for r in rows for k in r))
    num_idx = {headers.index(c) for c in (*money_cols, *pct_cols) if c in headers}
    for k, h in enumerate(headers):  # cột toàn số cũng căn phải
        vals = [r.get(h) for r in rows if clean(r.get(h)) is not None]
        if vals and all(isinstance(v, (int, float)) for v in vals):
            num_idx.add(k)
    out = []
    for n, r in enumerate(rows):
        cells = []
        for h in headers:
            v = r.get(h)
            if clean(v) is None:
                v = ""
            elif h in money_cols and isinstance(v, (int, float)):
                v = vnd(v)
            elif h in pct_cols and isinstance(v, (int, float)):
                v = f"{v:.2%}".replace(".", ",")
            elif isinstance(v, float):
                v = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            cells.append(v)
        out.append((cells, "sec" if n in bold_rows else ""))
    html_table(headers, out, num_cols=tuple(num_idx))

def reset_widgets():
    ss.ver += 1


def ty_dong(x):
    """Quy đổi gọn: 4.510.000.000 → '≈ 4,51 tỷ đồng'."""
    if abs(x) >= 1e9:
        return f"≈ {x / 1e9:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".").rstrip("0").rstrip(",") + " tỷ đồng"
    if abs(x) >= 1e6:
        return f"≈ {x / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".").rstrip("0").rstrip(",") + " triệu đồng"
    return ""


def kpi_cards(cards, target=st, as_html=False):
    """Thẻ số liệu hiển thị ĐẦY ĐỦ con số (không cắt '…').
    cards: list dict(label, value, unit='đ', short=None, sub='', main=False); value là số hoặc chuỗi."""
    html = []
    for c in cards:
        v = c["value"]
        unit = c.get("unit", "đ")
        val = vnd(v) if isinstance(v, (int, float)) else str(v)
        short = c.get("short", ty_dong(v) if isinstance(v, (int, float)) and unit == "đ" else "")
        html.append(
            f"<div class='kpi{' main' if c.get('main') else ''}'><div class='lab'>{c['label']}</div>"
            f"<div class='val'>{val}<span class='unit'>{unit}</span></div>"
            + (f"<div class='short'>{short}</div>" if short else "")
            + (f"<div class='sub'>{c['sub']}</div>" if c.get("sub") else "") + "</div>")
    out = "<div class='kpi-grid'>" + "".join(html) + "</div>"
    if as_html:
        return out
    target.markdown(out, unsafe_allow_html=True)


def page_header(title, desc):
    st.title(f"{ss.step + 1}. {title}")
    st.markdown(f"<div class='page-desc'>{desc}</div>", unsafe_allow_html=True)


def nav_buttons():
    st.divider()
    a, _, b = st.columns([1, 3, 1])
    if ss.step > 0 and a.button(f"← {STEPS[ss.step - 1][0]}", width="stretch"):
        ss.step -= 1
        st.rerun()
    if ss.step < len(STEPS) - 1 and b.button(f"{STEPS[ss.step + 1][0]} →", type="primary", width="stretch"):
        ss.step += 1
        st.rerun()


# ================================================================== các bước
STEPS = [
    ("Nhập thông tin", "📝"),
    ("Thiết bị & dịch vụ", "🖥️"),
    ("Chi tiết công việc", "👥"),
    ("Phần mềm nội bộ", "💻"),
    ("QLDA tự thực hiện", "🏛️"),
    ("Tổng hợp chi phí", "📊"),
    ("Phân bổ vốn", "📅"),
    ("Cấu hình nâng cao", "⚙️"),
    ("Xuất Excel & lưu", "📤"),
]

# Tính một lần ở đầu lượt; nếu bước đang mở sửa tham số thì cuối lượt tính lại (xem cuối file).
res = compute(proj)


def proj_hash():
    return _hash(proj)


computed_hash = proj_hash()


def step_done(i):
    """Dấu ✅ cho bước đã có dữ liệu / không có cảnh báo."""
    if i == 0:
        return bool(proj["thong_tin"]["ten_du_an"]) and (ts["kdp"] is not None or ts["nhap"] == "TMDT")
    if i == 1:
        return any(proj[k] for k in ("thiet_bi", "pm_thuong_mai", "tb_khac", "dv_thue_nam"))
    if i == 4:
        return ts["qlda"] == "TU_TH"
    if i == 5:
        return not res.warnings
    return i in (2, 3, 6, 7)


# ================================================================== thanh bên
with st.sidebar:
    # Gộp thành một khối để không bị Streamlit chèn khoảng trống giữa các phần tử
    card = kpi_cards([{"label": "Tổng mức đầu tư", "value": res.tmdt, "main": True,
                       "sub": f"Gms {vnd(res.gms)} đ<br>Dự phòng {vnd(res.totals['V'])} đ "
                              f"({res.totals['dp_ratio']:.2%})".replace(".00%", "%")}], as_html=True)
    warn = (f"<div class='sb-warn'>⚠️ {len(res.warnings)} cảnh báo – xem bước 6</div>" if res.warnings else "")
    st.markdown(f"<div class='sb-block'><div class='sb-hr'></div>{card}{warn}<div class='sb-hr'></div>"
                "<div class='step-label'>CÁC BƯỚC THỰC HIỆN</div></div>", unsafe_allow_html=True)
    for i, (name, icon) in enumerate(STEPS):
        mark = "✅" if step_done(i) else icon
        if st.button(f"{mark}  {i + 1}. {name}", key=f"nav_{i}", width="stretch",
                     type="primary" if i == ss.step else "secondary"):
            ss.step = i
            st.rerun()
    st.markdown("<div class='sb-hr'></div>", unsafe_allow_html=True)
    confirm = ss.get("del_confirm") == ss.pid
    with st.expander("⚠️ Xoá dự án", expanded=confirm):
        st.caption(f"Xoá vĩnh viễn dự án **{proj['thong_tin']['ten_du_an'] or ss.pid}** khỏi máy. "
                   "Nên tải file .json sao lưu (bước 9) trước khi xoá.")
        if not confirm:
            if st.button("Xoá dự án này", width="stretch"):
                ss.del_confirm = ss.pid
                st.rerun()
        else:
            st.warning("Bấm **Xác nhận xoá** để xoá vĩnh viễn, không khôi phục được.")
            a_, b_ = st.columns(2)
            if a_.button("Xác nhận xoá", type="primary", width="stretch"):
                storage.delete_project(ss.pid)
                ss.del_confirm = None
                open_project(None)
                st.rerun()
            if b_.button("Huỷ", width="stretch"):
                ss.del_confirm = None
                st.rerun()


# ================================================================== BƯỚC 1
def step_thong_tin():
    page_header("Nhập thông tin dự án", "Khai báo thông tin chung, chế độ đầu tư, giá trị đầu vào (Gms hoặc TMĐT) và các hệ số, "
                "công tắc. Các con số chi tiết khác được tính tự động.")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1a. Thông tin dự án")
            w("text_input", "Tên dự án *", ("thong_tin", "ten_du_an"))
            w("text_input", "Chủ đầu tư", ("thong_tin", "chu_dau_tu"))
            date_field("Thời điểm lập dự toán (dd/mm/yyyy)", ("thong_tin", "thoi_diem"))
            w("selectbox", "Loại hồ sơ", ("tham_so", "loai_ho_so"), options=list(LOAI_HO_SO), format_func=LOAI_HO_SO.get)
            a, b = st.columns(2)
            with a:
                w("radio", "Chế độ", ("tham_so", "che_do"), options=["XD", "THUE"],
                  format_func={"XD": "Xây dựng (mua sắm)", "THUE": "Thuê dịch vụ"}.get)
                w("radio", "Thiết kế", ("tham_so", "thiet_ke"), options=[1, 2], format_func=lambda x: f"0{x} bước", horizontal=True)
            with b:
                w("radio", "Quản lý dự án", ("tham_so", "qlda"), options=["THUE", "TU_TH"],
                  format_func={"THUE": "Thuê tư vấn QLDA", "TU_TH": "CĐT tự thực hiện"}.get)
                w("checkbox", "Có phần mềm nội bộ", ("tham_so", "co_pm_noi_bo"))
        with c2:
            st.subheader("1b. Giá trị đầu vào & dự phòng")
            w("radio", "Nhập theo", ("tham_so", "nhap"), options=["GMS", "TMDT"],
              format_func={"GMS": "Giá trị phần mềm (Gms)", "TMDT": "Tổng mức đầu tư (TMĐT)"}.get, horizontal=True)
            if ts["nhap"] == "GMS":
                money("Giá trị phần mềm Gms (đồng) *", ("tham_so", "gms"))
                kpi_cards([{"label": "→ Tổng mức đầu tư tính ra", "value": res.tmdt, "main": True,
                            "sub": f"Gms + các chi phí khác + dự phòng {res.totals['dp_ratio']:.2%}".replace(".", ",")}])
            else:
                money("TMĐT (đồng) *", ("tham_so", "tmdt"))
                kpi_cards([{"label": "→ Giá trị phần mềm Gms tương ứng", "value": res.gms, "main": True,
                            "sub": f"Gms lớn nhất để dự phòng nhỏ nhất · dự phòng {vnd(res.totals['V'])} đ "
                                   + f"({res.totals['dp_ratio']:.2%})".replace(".", ",")}])
                w("radio", "Dự phòng tối thiểu theo", ("tham_so", "du_phong_theo"), options=["PCT", "TIEN"],
                  format_func={"PCT": "Tỷ lệ Kdp (%)", "TIEN": "Số tiền (đồng)"}.get, horizontal=True)
            kmax = kdp_max(ts)
            if ts["nhap"] == "TMDT" and ts["du_phong_theo"] == "TIEN":
                money("Dự phòng tối thiểu (đồng)", ("tham_so", "du_phong_toi_thieu"))
            elif ts["nhap"] == "TMDT":
                w("number_input", f"Kdp tối thiểu (%) – tối đa {kmax:.0%}", ("tham_so", "kdp"), scale=100, min_value=0.0,
                  max_value=100.0, step=0.5, format="%.2f", placeholder="Nhập %, để trống = 0%",
                  help="Dự phòng ≥ (Kdp + dự phòng trượt giá) × (Gtb + Gqlda + Gtv + Gk); Gms lấy lớn nhất thoả điều kiện.")
            else:
                w("number_input", f"Kdp áp dụng (%) * – tối đa {kmax:.0%}", ("tham_so", "kdp"), scale=100, min_value=0.0,
                  max_value=100.0, step=0.5, format="%.2f", placeholder="Bắt buộc nhập, không mặc định")
            a, b = st.columns(2)
            with a:
                pct("Dự phòng trượt giá (%)", ("tham_so", "kdp_truot_gia"), help="NĐ 224 Điều 49.7")
            with b:
                money("Làm tròn TMĐT (đồng)", ("tham_so", "lam_tron"))
            if ts["che_do"] == "THUE":
                w("number_input", "Số năm thuê", ("tham_so", "so_nam_thue"), min_value=1, max_value=20, step=1)
            else:
                w("number_input", "Số năm phân bổ vốn", ("tham_so", "so_nam_phan_bo"), min_value=1, max_value=10, step=1)

    st.subheader("1c. Hệ số & công tắc")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Thuế**")
            pct("Thuế GTGT (%)", ("tham_so", "vat"))
            st.caption("Lương cơ sở, hệ số lương, lương chuyên gia: bước 8 → 8a.")
            money("Chi phí thẩm định giá (đồng)", ("tham_so", "tham_dinh_gia"))
        with c2:
            st.markdown("**Công tắc**")
            tri("Thẩm tra thiết kế", ("tham_so", "tham_tra_thiet_ke"),
                f"Tự động ({'tắt – nhà thầu lập thiết kế' if ts['co_pm_noi_bo'] else 'bật'})")
            tri("Thiết bị ≥ 50% giá trị (kiểm toán × 70%)", ("tham_so", "tb_tren_50"), "Tự động theo tỷ trọng")
            w("checkbox", "Có kiểm toán độc lập (thẩm tra QT × 50%)", ("tham_so", "kiem_toan_doc_lap"))
            w("checkbox", "Tính lệ phí thẩm định dự án", ("tham_so", "phi_tham_dinh"))
            w("checkbox", "Có thẩm tra (lệ phí thẩm định × 50%)", ("tham_so", "ptd_co_tham_tra"))
        with c3:
            st.markdown(f"**Quy mô** – để trống = tự động theo Gms (hiện: {res.counts['goi']} gói, "
                        f"{res.counts['lop']} lớp, {res.counts['he_thong']} hệ thống)")
            w("number_input", "Số gói thầu (mặc định 2/3/5)", ("tham_so", "so_goi"), min_value=1, step=1, placeholder="Tự động")
            w("number_input", "Số lớp đào tạo (1/3/6)", ("tham_so", "so_lop"), min_value=0, step=1, placeholder="Tự động")
            w("number_input", "Số hệ thống tích hợp (0/2/5)", ("tham_so", "so_he_thong"), min_value=0, step=1, placeholder="Tự động")

    if ts["che_do"] == "THUE":
        st.subheader("1d. Quản trị, vận hành (chế độ thuê)")
        with st.container(border=True):
            w("checkbox", "QTVH theo báo giá trọn gói (thay cho bóc tách nhóm J)", ("tham_so", "j_tron_goi"))
            if ts["j_tron_goi"]:
                money("Nhân công QTVH trọn gói / năm – trước CPC, TNCT, VAT (đồng)", ("tham_so", "j_tron_goi_nam"))


# ================================================================== BƯỚC 2
LCOLS = ["ten", "dvt", "so_luong", "don_gia", "vat", "phuong_phap", "nguon", "ghi_chu"]
LLABELS = ["Khoản mục", "ĐVT", "Khối lượng", "Đơn giá trước thuế", "Thuế suất", "Phương pháp xác định giá", "Nguồn giá", "Ghi chú"]


def list_block(code, title, key, note=""):
    st.subheader(f"{code}. {title}")
    if note:
        st.caption(note)
    with st.container(border=True):
        list_editor(key, LCOLS, LLABELS, money_cols=("don_gia",), pct_cols=("vat",))
        pre, vat = res.lists.get(key, (0, 0))
        st.caption(f"Cộng: trước thuế {vnd(pre)} đ · thuế {vnd(vat)} đ · sau thuế **{vnd(pre + vat)} đ**")


def step_thiet_bi():
    page_header("Thiết bị, phần mềm & dịch vụ", "Nhập danh mục mua sắm theo khối lượng × đơn giá. Thêm dòng ở cuối bảng; "
                "xoá dòng bằng cách chọn dòng rồi bấm thùng rác.")
    list_block("2a", "Thiết bị phần cứng (Gms-tbs)", "thiet_bi")
    list_block("2b", "Phần mềm thương mại/phổ biến (Gms-pmtm)", "pm_thuong_mai")
    list_block("2c", "Lắp đặt, tạo lập CSDL, vận chuyển, chi phí khác thuộc GTB (Gdvtk)", "tb_khac")
    if ts["che_do"] == "THUE":
        list_block("2d", "Dịch vụ thuê hằng năm – hạ tầng, đường truyền…", "dv_thue_nam",
                   f"Đơn giá 1 năm; tự nhân {ts['so_nam_thue']} năm thuê.")
    st.subheader("2e. Chi phí khác nhập tay thuộc Gk")
    with st.container(border=True):
        list_editor("gk_khac", ["ten", "gia_tri"], ["Khoản mục", "Giá trị (đồng)"], money_cols=("gia_tri",))


# ================================================================== BƯỚC 3
def step_cong_viec():
    page_header("Chi tiết công việc theo chuyên gia", "Mỗi nhóm chi phí liệt kê công việc – bậc – số chuyên gia – số ngày – đơn giá. "
                "Số liệu tự co giãn theo quy mô Gms. Sửa trực tiếp trong bảng; thêm việc mới ở dòng trống cuối bảng.")
    codes = [c for c in "ABCDEFGHIJ" if c in res.groups or c in proj["nhom_tat"]]
    if not codes:
        st.info("Không có nhóm nào áp dụng.")
        return
    if ss.get("grp_pick") not in codes:
        ss.grp_pick = codes[0]
    pick = st.radio("Nhóm chi phí", codes, key="grp_pick", horizontal=True,
                    format_func=lambda c: f"{c}. {GROUP_BY_CODE[c].short.replace('_', ' ')}")
    g = res.groups.get(pick)

    # ---------------- 3a. Bảng công việc (gồm cả việc tự thêm)
    with st.container(border=True):
        head, tog = st.columns([4, 1])
        head.subheader(f"3a. {GROUP_BY_CODE[pick].name}")
        on = tog.toggle("Tính nhóm này", value=pick not in proj["nhom_tat"], key=f"on{ss.ver}_{pick}")
        if on and pick in proj["nhom_tat"]:
            proj["nhom_tat"].remove(pick)
            st.rerun()
        if not on and pick not in proj["nhom_tat"]:
            proj["nhom_tat"].append(pick)
            st.rerun()
        if not g:
            st.info("Nhóm này đang tắt.")
            return
        st.caption(f"Quy mô Gms {vnd(res.gms)} đ · {res.counts['goi']} gói thầu · {res.counts['lop']} lớp · "
                   f"{res.counts['he_thong']} hệ thống · {res.counts['nam']} năm.  \n"
                   "• **Sửa**: tên việc, Bậc, Số CG, Số ngày (ô đã sửa đánh dấu ✎; cột *Tự động* là số theo mô hình).  \n"
                   "• **Thêm việc**: bấm ➕ trên góc bảng hoặc vào dòng trống cuối bảng, gõ tên việc (mã A+1, A+2…; "
                   "số CG × ngày nhập tay, không co giãn).  \n"
                   "• **Xoá**: tick cột *Xoá* (việc mặc định bỏ tick để khôi phục) hoặc chọn dòng rồi bấm 🗑.")
        nonce_key = f"nonce_{pick}"
        ss.setdefault(nonce_key, 0)
        rows = list(g.rows)
        base = pd.DataFrame([{
            "Mã": r.id, "Công việc": r.name, "Bậc": r.grade,
            "Tự động": "nhập tay" if r.mult_kind == "tuy_chon" else f"{r.auto_experts} × {r.auto_days}",
            "Số CG": r.experts, "Số ngày": r.days, "Hệ số": r.mult, "Đơn giá ngày": r.price,
            "Thành tiền": r.amount, "Theo văn bản (sau thuế)": r.ref_value,
            "Dùng VB": r.use_ref, "Xoá": r.excluded, "Ghi đè": "✎" if r.overridden else ""} for r in rows])
        cfg = {
            "Mã": st.column_config.TextColumn(width="small"),
            "Công việc": st.column_config.TextColumn(width="large"),
            "Bậc": st.column_config.SelectboxColumn("Bậc", options=GRADES, width="small", default="M3"),
            "Số CG": st.column_config.NumberColumn("Số CG", min_value=1, step=1, width="small", default=1),
            "Số ngày": st.column_config.NumberColumn("Số ngày", min_value=1, step=1, width="small", default=1),
            "Hệ số": st.column_config.NumberColumn(width="small", default=1.0,
                                                   help="Số gói thầu / số lớp / số hệ thống / số năm. Việc mặc định: "
                                                        "đổi ở bước 1 (Quy mô). Việc tự thêm: nhập trực tiếp"),
            "Đơn giá ngày": st.column_config.NumberColumn(format="localized"),
            "Thành tiền": st.column_config.NumberColumn(format="localized"),
            "Theo văn bản (sau thuế)": st.column_config.NumberColumn(format="localized"),
            "Dùng VB": st.column_config.CheckboxColumn(help="Lấy số theo văn bản (NĐ 214, NĐ 19) thay cho số chuyên gia"),
            "Xoá": st.column_config.CheckboxColumn(help="Loại việc khỏi dự toán; việc mặc định bỏ tick để khôi phục"),
            "Ghi đè": st.column_config.TextColumn(width="small"),
        }
        ed = editor(base, height=ed_height(len(base), True, ROW_STD),
                            key=f"grp{ss.ver}_{pick}_{ss[nonce_key]}_{df_hash(base)}", hide_index=True,
                            width="stretch", num_rows="dynamic", column_config=cfg,
                            disabled=["Mã", "Tự động", "Đơn giá ngày", "Thành tiền", "Theo văn bản (sau thuế)", "Ghi đè"])

        def num(v, default):
            v = clean(v)
            return default if v is None else v

        changed = False
        them = []
        for idx, r in enumerate(rows):
            if r.mult_kind == "tuy_chon":  # việc tự thêm
                if idx not in ed.index:
                    changed = True
                    continue
                b = ed.loc[idx]
                if bool(b["Xoá"]):
                    changed = True
                    continue
                rec = {"ten": clean(b["Công việc"]) or r.name, "bac": num(b["Bậc"], "M3"),
                       "so_cg": int(num(b["Số CG"], 1)), "so_ngay": int(num(b["Số ngày"], 1)),
                       "he_so": float(num(b["Hệ số"], 1))}
                if rec != {"ten": r.name, "bac": r.grade, "so_cg": r.experts, "so_ngay": r.days, "he_so": r.mult}:
                    changed = True
                them.append(rec)
                continue
            ov = dict(proj["ghi_de"].get(r.id, {}))
            if idx not in ed.index:  # xoá dòng việc mặc định = đánh dấu Xoá
                ov["bo"] = True
            else:
                a, b = base.loc[idx], ed.loc[idx]
                if clean(b["Công việc"]) and b["Công việc"] != a["Công việc"]:
                    ov["ten"] = b["Công việc"] if b["Công việc"] != TASK_BY_ID[r.id].name else None
                if clean(b["Bậc"]) and b["Bậc"] != a["Bậc"]:
                    ov["bac"] = b["Bậc"] if b["Bậc"] != TASK_BY_ID[r.id].grade else None
                if b["Số CG"] != a["Số CG"] and clean(b["Số CG"]):
                    ov["so_cg"] = int(b["Số CG"])
                    ov.pop("so_ngay", None)
                if b["Số ngày"] != a["Số ngày"] and clean(b["Số ngày"]):
                    ov["so_ngay"] = int(b["Số ngày"])
                if bool(b["Dùng VB"]) != bool(a["Dùng VB"]):
                    ov["dung_vb"] = bool(b["Dùng VB"]) and r.ref != ""
                if bool(b["Xoá"]) != bool(a["Xoá"]):
                    ov["bo"] = bool(b["Xoá"])
                if clean(b["Hệ số"]) != clean(a["Hệ số"]):
                    changed = True  # hệ số việc mặc định không sửa ở đây → làm mới bảng
            ov = {k: v for k, v in ov.items() if v}
            if ov != proj["ghi_de"].get(r.id, {}):
                if ov:
                    proj["ghi_de"][r.id] = ov
                else:
                    proj["ghi_de"].pop(r.id, None)
                changed = True
        for idx in ed.index:
            if idx in base.index:
                continue
            b = ed.loc[idx]
            name = clean(b["Công việc"])
            if name:  # dòng mới chỉ được ghi nhận khi đã có tên việc
                them.append({"ten": name, "bac": num(b["Bậc"], "M3"), "so_cg": int(num(b["Số CG"], 1)),
                             "so_ngay": int(num(b["Số ngày"], 1)), "he_so": float(num(b["Hệ số"], 1))})
                changed = True
        if changed:
            if them:
                proj["viec_them"][pick] = them
            else:
                proj["viec_them"].pop(pick, None)
            ss[nonce_key] += 1
            st.rerun()
        notes = [f"**{r.id}**: {r.ref_note}" for r in rows if r.ref_note]
        if notes:
            st.caption("Theo văn bản – " + " · ".join(notes))

    # ---------------- 3b. Tổng hợp nhóm
    st.subheader("3b. Tổng hợp chi phí của nhóm")
    with st.container(border=True):
        st.caption("Cách hình thành tổng chi phí nhóm theo TT 39: chi phí chuyên gia → chi phí chung → chi phí khác "
                   "→ thu nhập chịu thuế tính trước → thuế GTGT.")
        service = g.section in ("TB", "DV")
        sec_lab = "Chi phí chung (CPC)" if service else "Chi phí quản lý (Cql)"
        sec_how = (f"{g.cql_rate:.0%} × Ccg – theo đề xuất" if service else
                   f"{g.cql_rate:.0%} × Ccg – Bảng 3.2 (Ccg ≤ 1 tỷ: 55%; < 5 tỷ: 50%; ≥ 5 tỷ: 45%)")
        left, right = st.columns([3, 1])
        with left:
            show_table([
                {"Khoản": "I. Chi phí chuyên gia trực tiếp (Ccg)", "Cách tính": "Σ số CG × số ngày × hệ số × đơn giá ngày", "Giá trị (đ)": g.ccg},
                {"Khoản": f"II. {sec_lab}", "Cách tính": sec_how, "Giá trị (đ)": g.cql},
                {"Khoản": "III. Chi phí khác (Ck)", "Cách tính": "nhập ở mục 3c", "Giá trị (đ)": g.ck},
                {"Khoản": "IV. Thu nhập chịu thuế tính trước (TN)", "Cách tính": f"{g.tn_rate:.0%} × (Ccg + Cql + Ck)", "Giá trị (đ)": g.tn},
                {"Khoản": "V. Cộng trước thuế", "Cách tính": "Ccg + Cql + Ck + TN", "Giá trị (đ)": g.cg_pre},
                {"Khoản": "VI. Thuế GTGT", "Cách tính": f"{ts['vat']:.0%} × trước thuế", "Giá trị (đ)": g.cg_vat},
                {"Khoản": "Cộng sau thuế (theo chuyên gia)", "Cách tính": "V + VI", "Giá trị (đ)": g.cg_total},
                {"Khoản": "Cộng các dòng 'Dùng VB'", "Cách tính": "số theo văn bản, đã gồm thuế", "Giá trị (đ)": g.ref_total},
            ], money_cols=("Giá trị (đ)",), bold_rows=(4, 6))
        with right:
            kpi_cards([{"label": "TỔNG NHÓM (sau thuế)", "value": g.total, "main": True,
                        "sub": "đang dùng số ghi đè" if g.override is not None else "= theo chuyên gia + dòng văn bản"},
                       {"label": "Trước thuế", "value": g.pre, "sub": f"thuế GTGT {vnd(g.vat)} đ"}])

    # ---------------- 3c. Điều chỉnh
    st.subheader("3c. Điều chỉnh thủ công")
    with st.container(border=True):
        a, b, c = st.columns(3)
        with a:
            ck = money_input("Chi phí khác Ck của nhóm (đồng)", f"ck{ss.ver}_{pick}", proj["ck"].get(pick) or 0,
                             help="Ví dụ: công tác phí, thuê phương tiện… cộng vào trước khi tính TN và VAT")
            if ck != float(proj["ck"].get(pick) or 0):
                proj["ck"][pick] = ck
                st.rerun()
        with b:
            use_ov = st.checkbox("Ghi đè tổng nhóm (sau thuế)", value=g.override is not None, key=f"ovc{ss.ver}_{pick}",
                                 help="Bỏ qua cách tính chuyên gia, dùng con số nhập tay")
            if use_ov:
                v = money_input("Tổng nhóm ghi đè (đồng)", f"ov{ss.ver}_{pick}",
                                g.override if g.override is not None else g.cg_total + g.ref_total)
                if g.override != v:
                    proj["ghi_de_nhom"][pick] = v
                    st.rerun()
            elif g.override is not None:
                proj["ghi_de_nhom"].pop(pick, None)
                st.rerun()
        with c:
            if st.button("↺ Khôi phục mặc định của nhóm", width="stretch",
                         help="Xoá mọi ghi đè, Ck, khôi phục việc đã xoá; giữ nguyên việc tự thêm"):
                for t in GROUP_BY_CODE[pick].tasks:
                    proj["ghi_de"].pop(t.id, None)
                proj["ghi_de_nhom"].pop(pick, None)
                proj["ck"].pop(pick, None)
                reset_widgets()
                st.rerun()

    # ---------------- 3d. Tham chiếu QĐ 1688
    st.subheader("3d. Tham chiếu định mức QĐ 1688")
    with st.container(border=True):
        if g.dm1688:
            left, right = st.columns([3, 1])
            with left:
                st.markdown(f"**{g.dm1688['bang']}**: {g.dm1688['ty_le']:.3f}% × Gms × (1 + VAT) "
                            f"= {g.dm1688['ty_le']:.3f}% × {vnd(res.gms)} × {1 + ts['vat']:.2f}")
                st.caption("QĐ 1688 đã hết hiệu lực từ 01/07/2026 – số này chỉ để so sánh, không phải căn cứ pháp lý. "
                           "Nếu muốn dùng, bấm nút để đặt làm tổng nhóm (ghi đè).")
                if st.button("Dùng số định mức làm tổng nhóm"):
                    proj["ghi_de_nhom"][pick] = g.dm1688["gia_tri"]
                    reset_widgets()
                    st.rerun()
            with right:
                kpi_cards([{"label": "Theo định mức (sau thuế)", "value": g.dm1688["gia_tri"],
                            "sub": f"Chênh lệch so với chuyên gia: {vnd(g.dm1688['gia_tri'] - g.cg_total)} đ"}])
        else:
            st.caption("Nhóm này không có bảng định mức tham chiếu.")


# ================================================================== BƯỚC 4
def step_pm():
    page_header("Phần mềm nội bộ (nhóm K)", "Man-month suy ngược từ Gms: Gms = NC × (1 + CPC) × (1 + TNCT) × (1 + thuế); "
                "nhân công chia theo 9 tỷ lệ vai trò.")
    pm = res.pm
    thue = ts["che_do"] == "THUE"
    kpi_cards([
        {"label": "Giá trị phần mềm Gms", "value": res.gms, "main": True, "sub": "= NC + CPC + TNCT + thuế"},
        {"label": "Nhân công (NC)", "value": pm["nc"], "sub": f"Gms ÷ (1 + {ts['pm_cpc']:.0%}) ÷ (1 + {ts['pm_tn']:.0%}) ÷ (1 + {ts['pm_thue']:.0%})"},
        {"label": "Tổng man-month", "value": f"{pm['mm']:,.1f}".replace(".", ","), "unit": "MM",
         "sub": f"≈ {pm['mm'] / 12:,.1f} người-năm".replace(".", ",")},
        ({"label": "Thuê phần mềm", "value": res.thue_pm["total"],
          "sub": f"Gms ÷ {ts['khau_hao_nam']} năm × {ts['so_nam_thue']} năm"} if thue else
         {"label": "CPC + TNCT", "value": pm["cpc"] + pm["tn"],
          "sub": f"CPC {vnd(pm['cpc'])} đ<br>TNCT {vnd(pm['tn'])} đ"}),
    ])
    st.subheader("4a. Bảng nhân công")
    show_table([{"Vai trò": r["vai_tro"], "Tỷ lệ": r["ty_le"], "Bậc KS": r["bac"], "Đơn giá tháng": r["don_gia_thang"],
                 "MM": round(r["mm"], 2), "Thành tiền": r["thanh_tien"]} for r in pm["roles"]] +
               [{"Vai trò": f"Chi phí chung (CPC {ts['pm_cpc']:.0%})", "Thành tiền": pm["cpc"]},
                {"Vai trò": f"Thu nhập chịu thuế tính trước ({ts['pm_tn']:.0%})", "Thành tiền": pm["tn"]},
                {"Vai trò": f"Thuế/phí ({ts['pm_thue']:.0%})", "Thành tiền": pm["thue"]},
                {"Vai trò": "TỔNG (= Gms)", "Thành tiền": pm["total"]}],
               money_cols=("Đơn giá tháng", "Thành tiền"), pct_cols=("Tỷ lệ",), bold_rows=(len(pm["roles"]) + 3,))
    if ts["che_do"] == "THUE":
        st.info(f"Thuê phần mềm = Gms ÷ {ts['khau_hao_nam']} năm × {ts['so_nam_thue']} năm = **{vnd(res.thue_pm['total'])} đ**")
    st.subheader("4b. Tỷ lệ và bậc kỹ sư từng vai trò")
    with st.container(border=True):
        def build():
            ratios = ts["pm_ty_le"] or [r for _, r in PM_ROLES]
            return pd.DataFrame({"Vai trò": [n for n, _ in PM_ROLES], "Tỷ lệ %": [r * 100 for r in ratios],
                                 "Bậc KS": [str(b) for b in ts["pm_bac"]]})
        base, ed_key = snapshot("pmroles", build)
        ed = editor(base, key=ed_key, hide_index=True, disabled=["Vai trò"], width="stretch",
                            column_config={"Bậc KS": st.column_config.SelectboxColumn(options=["TB"] + [str(i) for i in range(1, 9)])})
        ts["pm_ty_le"] = [float(x or 0) / 100 for x in ed["Tỷ lệ %"]]
        ts["pm_bac"] = [b if b == "TB" else int(b) for b in ed["Bậc KS"]]
        tot = sum(ts["pm_ty_le"])
        if abs(tot - 1) > 1e-6:
            st.warning(f"Tổng tỷ lệ = {tot:.0%}, khác 100%.")
        st.caption("TB = bình quân các bậc chọn ở Cấu hình nâng cao (mặc định KS-B1/B2/B3).")


# ================================================================== BƯỚC 5
def step_qlda():
    page_header("QLDA – chủ đầu tư tự thực hiện", "TT 70/2024/TT-BTC: dự toán chi theo Mẫu 02/DT-QLDA và nội dung chi "
                "Điều 30 NĐ 10/2021/NĐ-CP.")
    if ts["qlda"] != "TU_TH":
        st.info("Đang chọn **thuê tư vấn QLDA** (nhóm A) – bảng dưới chưa được tính. Đổi ở bước 1 → 1a → Quản lý dự án.")
    st.subheader("5a. Bảng tính lương năm (Mẫu 02/DT-QLDA)")
    with st.container(border=True):
        list_editor("qlda_nhan_su", ["vi_tri", "so_nguoi", "he_so_luong", "pc_chuc_vu", "pc_khu_vuc", "pc_khac", "so_thang"],
                    ["Vị trí", "Số người", "Hệ số lương", "PC chức vụ", "PC khu vực", "PC khác", "Số tháng"])
        st.caption(f"Thành tiền = (hệ số lương + phụ cấp) × lương cơ sở {vnd(ts['luong_co_so'])} đ × số người × số tháng; "
                   "bảo hiểm " + f"{ts['bh_qlda']:.1%}".replace(".", ",") + ". Lương cơ sở, hệ số lương, phụ cấp, tỷ lệ bảo hiểm cũng sửa được tập "
                   "trung ở bước 8 → 8a.")
    st.subheader("5b. Nội dung chi khác (Điều 30 NĐ 10/2021)")
    with st.container(border=True):
        list_editor("qlda_chi_khac", ["ten", "gia_tri"], ["Nội dung", "Giá trị (đồng)"], money_cols=("gia_tri",))
    if res.qlda_tu_th:
        q = res.qlda_tu_th
        st.success(f"Lương {vnd(q['luong'])} + bảo hiểm {vnd(q['bh'])} + chi khác {vnd(q['chi_khac'])} = **{vnd(q['total'])} đ**")


# ================================================================== BƯỚC 6
def html_table(headers, rows, num_cols=()):
    """Bảng HTML: rows = list (cells, css_class). Cột số căn phải."""
    esc = lambda x: str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    th = "".join(f"<th class='{'num' if i in num_cols else ''}'>{esc(h)}</th>" for i, h in enumerate(headers))
    body = []
    for cells, cls in rows:
        tds = "".join(f"<td class='{'num' if i in num_cols else ('note' if headers[i] == 'Ghi chú' else '')}'>{esc(c)}</td>"
                      for i, c in enumerate(cells))
        body.append(f"<tr class='{cls}'>{tds}</tr>")
    st.markdown(f"<div class='tbl-wrap'><table class='tbl'><thead><tr>{th}</tr></thead>"
                f"<tbody>{''.join(body)}</tbody></table></div>",
                unsafe_allow_html=True)


def note_of(key, default):
    return proj["ghi_chu"].get(key, default)


def step_tong_hop():
    page_header("Tổng hợp chi phí", "G = Gtb + Gqlda + Gtv + Gk + Gdp (TT 39 Điều 5; NĐ 224 Điều 49).")
    kpi_cards([
        {"label": "Tổng mức đầu tư", "value": res.tmdt, "main": True,
         "sub": f"{LOAI_HO_SO[ts['loai_ho_so']]} · trước thuế {vnd(res.totals['pre'])} đ"},
        {"label": "Giá trị phần mềm Gms", "value": res.gms,
         "sub": "giá trị nhập" if ts["nhap"] == "GMS" else "giải ngược từ TMĐT (dự phòng nhỏ nhất)"},
        {"label": "Dự phòng", "value": res.totals["V"],
         "sub": f"{res.totals['dp_ratio']:.2%} cơ sở · tối đa {kdp_max(ts):.0%}".replace(".", ",")},
        {"label": "Thuế GTGT", "value": res.totals["vat"], "sub": f"thuế suất {ts['vat']:.0%}"},
    ])
    for m in res.warnings:
        st.warning(m)

    # ---------------- 6a
    st.subheader("6a. Bảng tổng hợp")
    show_zero = st.toggle("Hiện cả các dòng bằng 0 ở mục I", value=False, key="show_zero_I")
    rows, note_rows = [], []
    for sec in ("I", "II", "III", "IV", "V"):
        its = [i for i in res.items if i.sec == sec]
        if sec in ("II", "V") and its:
            sec_key, sec_default = its[0].key, its[0].note
        else:
            sec_key, sec_default = "sec_" + sec, SEC_NOTES[sec]
        note = note_of(sec_key, sec_default)
        rows.append(([sec, sec_name(sec, ts), sec_kh(sec, ts), vnd(sum(i.pre for i in its)), vnd(sum(i.vat for i in its)),
                      vnd(sum(i.post for i in its)), note], "sec"))
        note_rows.append({"key": sec_key, "Dòng": f"{sec}. {sec_name(sec, ts)}", "Ghi chú": note, "_default": sec_default})
        if sec in ("II", "V"):
            continue
        n = 0
        for i in its:
            if sec == "I" and not show_zero and abs(i.post) < 0.5:
                continue
            n += 1
            note = note_of(i.key, i.note)
            rows.append(([n, i.label, i.kh, vnd(i.pre), vnd(i.vat), vnd(i.post), note], ""))
            note_rows.append({"key": i.key, "Dòng": f"{sec}.{n} {i.label}", "Ghi chú": note, "_default": i.note})
    rows.append((["*", "TỔNG CỘNG", "G", vnd(res.totals["pre"]), vnd(res.totals["vat"]), vnd(res.tmdt),
                  note_of("tong", "Gtb + Gqlda + Gtv + Gk + Gdp")], "total"))
    note_rows.append({"key": "tong", "Dòng": "TỔNG CỘNG", "Ghi chú": note_of("tong", "Gtb + Gqlda + Gtv + Gk + Gdp"),
                      "_default": "Gtb + Gqlda + Gtv + Gk + Gdp"})
    html_table(["STT", "Nội dung chi phí", "Ký hiệu", "Trước thuế", "Thuế GTGT", "Sau thuế", "Ghi chú"], rows,
               num_cols=(3, 4, 5))
    f = res.fees
    st.caption(f"Kiểm toán / thẩm tra QT (NĐ 193): {f['ty_le_kt']:.4f}% / {f['ty_le_tt']:.4f}% tại TMĐT "
               f"{f['tmdt'] / 1e9:,.3f} tỷ; cơ sở {vnd(f['co_so'])} đ; hệ số thiết bị {f['he_so_tb']:.2f}. "
               f"Lệ phí thẩm định (TT 28): {f['ty_le_ptd']:.3f}% × {f['he_so_ptd']:.0%}.")

    with st.expander("✏️ Sửa cột Ghi chú (lưu vào dự án và xuất ra Excel)"):
        base = pd.DataFrame([{"Dòng": r["Dòng"], "Ghi chú": r["Ghi chú"]} for r in note_rows])
        ed = editor(base, height=ed_height(len(base)), max_w=620, key=f"gc{ss.ver}_{df_hash(base)}",
                            hide_index=True, width="stretch",
                            disabled=["Dòng"], column_config={"Ghi chú": st.column_config.TextColumn(width="large")})
        changed = False
        for r, (_, b) in zip(note_rows, ed.iterrows()):
            new = clean(b["Ghi chú"]) or ""
            if new != r["Ghi chú"]:
                if new == r["_default"]:
                    proj["ghi_chu"].pop(r["key"], None)
                else:
                    proj["ghi_chu"][r["key"]] = new
                changed = True
        if changed:
            st.rerun()
        if proj["ghi_chu"] and st.button("↺ Khôi phục ghi chú mặc định"):
            proj["ghi_chu"] = {}
            st.rerun()

    # ---------------- 6b
    if res.compare:
        st.subheader("6b. So sánh số chuyên gia với số theo văn bản")
        st.markdown(
            "Một số công việc có **mức chi phí quy định sẵn trong văn bản**: lập/thẩm định hồ sơ mời thầu, đánh giá hồ sơ "
            "dự thầu (NĐ 214/2025), giám sát – đánh giá đầu tư (NĐ 19/2026). Bảng dưới đặt cạnh nhau **số tính theo "
            "chuyên gia** (số CG × ngày × đơn giá + chi phí chung + TN + VAT) và **số theo văn bản** để bạn chọn.  \n"
            "**Mã việc** là mã dòng trong bảng ở bước 3: chữ cái = nhóm chi phí (A = QLDA, B = tv1 lập BCKT-KT, "
            "C = tv2 thẩm tra, D = tv3 giám sát, **E = tv4 lập E-HSMT & đánh giá E-HSDT**, **F = tv5 thẩm định**), "
            "số = thứ tự việc trong nhóm. Tick **Dùng VB** để lấy số văn bản thay cho số chuyên gia.")
        base = pd.DataFrame([{
            "Mã việc": c["ma"], "Nhóm chi phí": f"{c['nhom']}. " + (lambda t: t[:1].upper() + t[1:])(c["nhom_ten"].replace("Chi phí ", "", 1)), "Công việc": c["cong_viec"],
            "Theo chuyên gia (đ)": vnd(c["chuyen_gia"]), "Theo văn bản (đ)": vnd(c["van_ban"]),
            "Chênh lệch": f"{c['lech']:+.0%}", "Dùng VB": c["dang_dung"] == "Văn bản",
            "Căn cứ văn bản": c["can_cu"]} for c in res.compare])
        ed = editor(base, height=ed_height(len(base)), max_w=720, key=f"cmp{ss.ver}_{df_hash(base)}",
                            hide_index=True, width="stretch",
                            disabled=[c for c in base.columns if c != "Dùng VB"],
                            column_config={"Mã việc": st.column_config.TextColumn(width="small"),
                                           "Nhóm chi phí": st.column_config.TextColumn(width="medium"),
                                           "Công việc": st.column_config.TextColumn(width="medium"),
                                           "Căn cứ văn bản": st.column_config.TextColumn(width="large"),
                                           "Dùng VB": st.column_config.CheckboxColumn(
                                               help="Tick = dùng số văn bản; bỏ tick = dùng số chuyên gia")})
        changed = False
        for c, (_, b) in zip(res.compare, ed.iterrows()):
            want = bool(b["Dùng VB"])
            if want != (c["dang_dung"] == "Văn bản"):
                ov = dict(proj["ghi_de"].get(c["ma"], {}))
                ov["dung_vb"] = want
                ov = {k: v for k, v in ov.items() if v}
                if ov:
                    proj["ghi_de"][c["ma"]] = ov
                else:
                    proj["ghi_de"].pop(c["ma"], None)
                changed = True
        if changed:
            st.rerun()
        st.caption("Chênh lệch = (chuyên gia − văn bản) ÷ văn bản. Số văn bản đã gồm VAT; giá gói thầu = Gtb trước thuế ÷ số gói.")


# ================================================================== BƯỚC 7
def step_phan_bo():
    page_header("Phân bổ vốn theo năm", "Mặc định: " + (
        "chuẩn bị đầu tư, mua sắm, đào tạo, triển khai vào năm đầu; thuê, vận hành, QLDA, giám sát, dự phòng chia đều; "
        "quyết toán năm cuối." if ts["che_do"] == "THUE" else "chuẩn bị đầu tư vào năm đầu; chi phí phần mềm nội bộ chia đều cho các năm; "
        "phần còn lại năm cuối. Đổi số năm ở bước 1 → 1b."))
    pb = res.phan_bo
    n = pb["n"]
    labels = pb["labels"]
    secs = [s for s in ("I", "II", "III", "IV", "V") if any(r["nhom"] == s for r in pb["rows"])]

    # ---------------- 7a. Tỷ lệ – có dòng nhóm I, II, … (dòng nhóm không sửa được)
    st.subheader("7a. Tỷ lệ phân bổ (%)")
    with st.container(border=True):
        st.caption("Nhập % từng năm cho mỗi khoản mục (tổng một dòng = 100%). Dòng in hoa là nhóm chi phí, chỉ để xem.")
        recs, meta = [], []
        for sec in secs:
            recs.append({"STT": sec, "Nội dung": sec_name(sec, ts), **{l: None for l in labels}})
            meta.append(None)
            for k, r in enumerate([x for x in pb["rows"] if x["nhom"] == sec], start=1):
                recs.append({"STT": str(k), "Nội dung": "    " + r["noi_dung"],
                             **{labels[i]: round(r["ty_le"][i] * 100, 4) for i in range(n)}})
                meta.append(r["key"])
        base = pd.DataFrame(recs)
        ss.setdefault("pb_nonce", 0)
        ed = editor(base, height=ed_height(len(base), row=ROW_STD), max_w=620,
                    key=f"pb{ss.ver}_{ss.pb_nonce}_{df_hash(base)}", hide_index=True, disabled=["STT", "Nội dung"],
                    placeholder="",
                    column_config={l: st.column_config.NumberColumn(l + " (%)", min_value=0, max_value=100) for l in labels})
        if not ed.equals(base):
            for (_, row), key in zip(ed.iterrows(), meta):
                if key is not None:
                    proj["phan_bo"][key] = [float(clean(row[l]) or 0) / 100 for l in labels]
            ss.pb_nonce += 1  # sửa vào dòng nhóm sẽ bị bỏ qua và bảng được làm mới
            st.rerun()
        if st.button("↺ Khôi phục phân bổ mặc định"):
            proj["phan_bo"] = {}
            st.rerun()

    # ---------------- 7b. Số tiền theo năm – có dòng nhóm in đậm như bảng 6a
    st.subheader("7b. Số tiền theo năm")
    rows = []
    for sec in secs:
        items = [x for x in pb["rows"] if x["nhom"] == sec]
        tong = sum(x["tong"] for x in items)
        nam = [sum(x["nam"][i] for x in items) for i in range(n)]
        rows.append(([sec, sec_name(sec, ts), vnd(tong), *[vnd(v) for v in nam], vnd(tong - sum(nam))], "sec"))
        for k, x in enumerate(items, start=1):
            rows.append(([k, x["noi_dung"], vnd(x["tong"]), *[vnd(v) for v in x["nam"]],
                          vnd(x["tong"] - sum(x["nam"]))], ""))
    rows.append((["*", "TỔNG CỘNG", vnd(res.tmdt), *[vnd(v) for v in pb["years"]],
                  vnd(res.tmdt - sum(pb["years"]))], "total"))
    html_table(["STT", "Nội dung chi phí", "Giá trị sau thuế", *labels, "Còn lại"], rows,
               num_cols=tuple(range(2, 3 + n + 1)))
    st.caption("Cột *Còn lại* = giá trị − tổng các năm; khác 0 nghĩa là tỷ lệ của dòng đó chưa đủ 100%.")


# ================================================================== BƯỚC 8
def step_cau_hinh():
    page_header("Cấu hình nâng cao", "Mọi số dưới đây là tham số; mặc định lấy theo template và các văn bản đã đối chiếu. "
                "Một số mục chưa đối chiếu toàn văn (lương cơ sở, điều kiện M2–M4, công thức QĐ 320) – kiểm tra trước khi dùng.")
    # ---------------- 8a. Mọi tham số lương tập trung một chỗ
    st.subheader("8a. Lương & hệ số lương")
    with st.container(border=True):
        st.caption("Mọi thông số lương của dự án nằm ở đây: khi nhà nước đổi lương cơ sở, hệ số lương hay mức lương "
                   "chuyên gia thì chỉ cần sửa trong mục này. Áp dụng cho **dự án đang mở**; muốn dự án mới tự lấy mức "
                   "mới thì sửa mặc định trong `dutoan/defaults.py`.")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Lương cơ sở & đơn giá kỹ sư (QĐ 320)**")
            money("Lương cơ sở (đồng)", ("tham_so", "luong_co_so"),
                  help="Dùng cho đơn giá kỹ sư (PM nội bộ, bước 4) và lương QLDA tự thực hiện (bước 5)")
            w("selectbox", "Vùng (Hdc)", ("tham_so", "vung"), options=["I", "II", "III", "IV"])
            w("number_input", "Hệ số phụ cấp Hpc", ("tham_so", "ks_hpc"), min_value=0.0, step=0.1)
            pct("BHXH + BHYT + BHTN kỹ sư (%)", ("tham_so", "ks_bh"))
            w("multiselect", "Bậc kỹ sư lấy bình quân", ("tham_so", "ks_bac_chon"), options=list(range(1, 9)))
            money("Ghi đè đơn giá tháng bình quân (đồng)", ("tham_so", "pm_don_gia_thang"), allow_empty=True,
                  placeholder="Để trống = theo công thức")
            st.caption("Gms là số nhập nên lương tăng thì **số man-month PM nội bộ giảm**, Gms không đổi.")
        with c2:
            st.markdown("**Hệ số lương kỹ sư (Hcb) – sửa cột Hệ số**")
            base = pd.DataFrame([{"Bậc": f"KS-B{b}", "Hệ số": ts["ks_he_so"][b - 1],
                                  "Đơn giá tháng": vnd(ks_month_price(b, ts))} for b in range(1, 9)])
            ed = editor(base, height=ed_height(len(base)), key=f"kshs{ss.ver}_{df_hash(base)}", hide_index=True,
                        disabled=["Bậc", "Đơn giá tháng"],
                        column_config={"Hệ số": st.column_config.NumberColumn(min_value=0.0, step=0.01, format="%.2f"),
                                       "Đơn giá tháng": st.column_config.TextColumn("Đơn giá tháng (đồng)")})
            new = [float(clean(x) or 0) for x in ed["Hệ số"]]
            if new != [float(x) for x in ts["ks_he_so"]]:
                ts["ks_he_so"] = new
                st.rerun()
        with c3:
            st.markdown("**Chuyên gia tư vấn (TT 07/2026/TT-BNV)**")
            for gname in GRADES:
                money(f"{gname} – lương tối đa/tháng (đồng)", ("tham_so", "luong", gname), help=GRADE_NOTE[gname])
            w("number_input", "Hệ số nâng lương chuyên gia (1,0 – 1,5)", ("tham_so", "he_so_nang"), min_value=0.1,
              max_value=2.0, step=0.05)
            w("number_input", "Số ngày làm việc/tháng", ("tham_so", "ngay_thang"), min_value=1, step=1)
            st.caption("Đơn giá ngày = lương tháng × hệ số nâng ÷ số ngày: " + " · ".join(
                f"{g} {vnd(day_price(g, ts))} đ" for g in GRADES))

        st.markdown("**Hệ số lương cán bộ QLDA tự thực hiện (Mẫu 02/DT-QLDA)** – thêm/xoá người, số người, số tháng "
                    "ở bước 5")
        cols = ["vi_tri", "he_so_luong", "pc_chuc_vu", "pc_khu_vuc", "pc_khac"]
        labs = ["Vị trí", "Hệ số lương", "PC chức vụ", "PC khu vực", "PC khác"]
        qbase = pd.DataFrame([{lab: r.get(c) for c, lab in zip(cols, labs)} for r in proj["qlda_nhan_su"]], columns=labs)
        if len(qbase):
            qed = editor(qbase, height=ed_height(len(qbase)), key=f"qlhs{ss.ver}_{df_hash(qbase)}", hide_index=True,
                         disabled=["Vị trí"],
                         column_config={l: st.column_config.NumberColumn(l, min_value=0.0, step=0.01, format="%.2f")
                                        for l in labs[1:]})
            if not qed.equals(qbase):
                for r, (_, b) in zip(proj["qlda_nhan_su"], qed.iterrows()):
                    for c, lab in zip(cols[1:], labs[1:]):
                        r[c] = float(clean(b[lab]) or 0)
                st.rerun()
        else:
            st.caption("Chưa có cán bộ QLDA – thêm ở bước 5.")
        pct("Tỷ lệ BHXH, BHYT, BHTN, KPCĐ cán bộ QLDA (%)", ("tham_so", "bh_qlda"))

    st.subheader("8b. Chi phí chung tư vấn – Bảng 3.2")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            money("Ngưỡng 1: Ccg ≤", ("tham_so", "cql", "nguong1"))
            money("Ngưỡng 2: Ccg <", ("tham_so", "cql", "nguong2"))
        with c2:
            pct("Bậc 1 (%)", ("tham_so", "cql", "r1"))
            pct("Bậc 2 (%)", ("tham_so", "cql", "r2"))
            pct("Bậc 3 (%)", ("tham_so", "cql", "r3"))
        with c3:
            pct("Thu nhập chịu thuế tính trước – tư vấn (%)", ("tham_so", "tn_tv"))

    st.subheader("8c. Mô hình co giãn theo quy mô")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            w("number_input", "Hệ số co giãn EXP (0,5 – 0,8)", ("tham_so", "exp"), min_value=0.1, max_value=1.5, step=0.05)
            for i in range(4):
                w("number_input", f"Ngày công ≤ … → {i + 1} chuyên gia", ("tham_so", "bac_thang", i), min_value=1, step=1)
        with c2:
            for i, lab in enumerate(("S", "M", "L")):
                money(f"Mốc neo {lab} (Gms)", ("tham_so", "moc_neo", i))
        with c3:
            money("Việc quy mô M xuất hiện khi Gms ≥", ("tham_so", "nguong_M"))
            money("Việc quy mô L xuất hiện khi Gms ≥", ("tham_so", "nguong_L"))

    st.subheader("8d. Phần mềm nội bộ")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            pct("Chi phí chung CPC (%)", ("tham_so", "pm_cpc"))
            pct("Thu nhập chịu thuế TNCT (%)", ("tham_so", "pm_tn"))
        with c2:
            pct("Thuế/phí PM nội bộ (%) – template 0%", ("tham_so", "pm_thue"))
            w("number_input", "Khấu hao PM (năm)", ("tham_so", "khau_hao_nam"), min_value=1, step=1)

    st.subheader("8e. Văn bản tham chiếu (NĐ 19, NĐ 193, NĐ 214, TT 28)")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            pct("NĐ 19/2026 giám sát + đánh giá (% chi phí QLDA)", ("tham_so", "nd19_tl"))
            pct("Giảm lệ phí theo TT 64/2025 (%)", ("tham_so", "ptd_giam_tt64"))
        with c2:
            money("Kiểm toán tối thiểu", ("tham_so", "kt_min"))
            money("Thẩm tra QT tối thiểu", ("tham_so", "tt_min"))
        with c3:
            pct("Hệ số khi thiết bị ≥ 50% (%)", ("tham_so", "he_so_tb"))
            pct("Hệ số thẩm tra khi có kiểm toán (%)", ("tham_so", "he_so_kt_doc_lap"))
        st.markdown("**NĐ 214/2025 Điều 14 – tỷ lệ, tối thiểu, tối đa**")
        labels = {"khlcnt": "Lập KH tổng thể LCNT (× chi phí lập BCKT-KT)", "lap_hsmt": "Lập HSMT", "dg_hsdt": "Đánh giá HSDT",
                  "td_hsmt": "Thẩm định HSMT", "td_kq": "Thẩm định KQ LCNT"}
        for k, lab in labels.items():
            a, b, c = st.columns(3)
            with a:
                pct(f"{lab} – tỷ lệ (%)", ("tham_so", "nd214", k, 0))
            with b:
                money("tối thiểu", ("tham_so", "nd214", k, 1))
            with c:
                money("tối đa", ("tham_so", "nd214", k, 2))
        a, b = st.columns(2)
        with a:
            st.markdown("**NĐ 193/2026 Điều 20** – TMĐT (tỷ), % thẩm tra QT, % kiểm toán")
            base, ed_key = snapshot("kt", lambda: pd.DataFrame(ts["bang_kiem_toan"], columns=["TMĐT (tỷ)", "% thẩm tra", "% kiểm toán"]))
            ed = editor(base, key=ed_key, num_rows="dynamic", hide_index=True, width="stretch")
            ts["bang_kiem_toan"] = sorted([[float(x) for x in r] for r in ed.dropna().values.tolist()])
        with b:
            st.markdown("**TT 28/2023/TT-BTC** – TMĐT (tỷ), tỷ lệ % phí thẩm định")
            base, ed_key = snapshot("ptd", lambda: pd.DataFrame(ts["bang_phi_tham_dinh"], columns=["TMĐT (tỷ)", "Tỷ lệ %"]))
            ed = editor(base, key=ed_key, num_rows="dynamic", hide_index=True, width="stretch")
            ts["bang_phi_tham_dinh"] = sorted([[float(x) for x in r] for r in ed.dropna().values.tolist()])


# ================================================================== BƯỚC 9
def step_xuat():
    page_header("Xuất Excel & lưu dự án", "File Excel theo bố cục 2 template, mọi số tiền là công thức sống; "
                "file .json lưu toàn bộ dự án để mở lại sau.")
    name = (proj["thong_tin"]["ten_du_an"] or "du_an").strip().replace(" ", "_")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("9a. Xuất Excel")
        with st.container(border=True):
            st.write(f"**{proj['thong_tin']['ten_du_an'] or '(chưa đặt tên)'}** – TMĐT **{vnd(res.tmdt)} đ**")
            BLOCKERS = ("không có lời giải", "Dự phòng âm")
            blocked = res.gms <= 0 or any(b in m for m in res.warnings for b in BLOCKERS)
            for m in res.warnings:
                if any(b in m for b in BLOCKERS):
                    st.error("⛔ " + m)
                else:
                    st.caption("⚠️ " + m)
            if res.gms <= 0:
                st.error("⛔ Gms phải > 0 (quay lại bước 1 nhập Gms hoặc TMĐT hợp lệ).")
            st.download_button("⬇️ Tải file Excel", export_bytes(proj, res), file_name=f"Du_toan_{name}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary",
                               width="stretch", disabled=blocked)
            st.caption("Gồm: 01_THAM_SO (toàn bộ tham số), BẢNG TMĐT (kèm ghi chú đã sửa), phân bổ vốn theo năm, "
                       "các sheet Cp_* tư vấn, đào tạo, triển khai, QTVH, kiểm thử TT 41, PM nội bộ, QLDA tự thực hiện, "
                       "danh mục thiết bị/PM/Gk nhập tay, đơn giá chuyên gia & kỹ sư, bảng NĐ 193/TT 28, so sánh văn bản (6b). "
                       "Ô nền vàng là ô nhập. Mọi ô công thức đã kèm sẵn giá trị nên xem trước trên điện thoại/Zalo "
                       "cũng thấy đủ số.")
    with c2:
        st.subheader("9b. Sao lưu dự án về máy tính")
        with st.container(border=True):
            st.markdown(
                "Dự án **đã được tự động lưu** trong ứng dụng (thư mục `workspace/projects`) và chọn lại được ở ô "
                "**Dự án** trên thanh bên trái. Muốn **sao lưu riêng** hoặc **chuyển sang máy khác**, bấm nút dưới đây để "
                "**tải file dự án (.json) về máy tính** – file chứa toàn bộ thông tin, tham số, thiết bị, công việc đã sửa, "
                "ghi chú, phân bổ vốn.")
            st.download_button(f"💾 Tải file dự án về máy ({name}.json)",
                               json.dumps(proj, ensure_ascii=False, indent=1).encode("utf-8"),
                               file_name=f"{name}.json", mime="application/json", type="primary", width="stretch")
            st.markdown(
                "**Cách mở lại file .json:** thanh bên trái → **➕ Tạo dự án mới** → ô **Hoặc nhập từ file dự án (.json)** → "
                "**Browse files** (hoặc kéo thả) → chọn file. Dự án được thêm vào danh sách và mở ra ngay.")
            st.caption("File tải về nằm ở thư mục tải về mặc định của trình duyệt (thường là Downloads).")


PAGES = [step_thong_tin, step_thiet_bi, step_cong_viec, step_pm, step_qlda, step_tong_hop, step_phan_bo,
         step_cau_hinh, step_xuat]
with st.sidebar:  # khung script ẩn đặt cuối thanh bên để không tạo khoảng trống ở trang chính
    if hasattr(st, "iframe"):  # Streamlit mới: components.v1.html sắp bị gỡ, in cảnh báo mỗi lần chạy lại
        st.iframe(FMT_SCRIPT, height=1)
    else:
        components.html(FMT_SCRIPT, height=0)
PAGES[ss.step]()
nav_buttons()

# Tự động lưu dự án khi có thay đổi
if ss.pid and _hash(proj) != ss.get("saved_hash"):
    storage.save_project(ss.pid, proj)
    ss.saved_hash = _hash(proj)

# Tham số vừa sửa ở bước đang mở → tính lại ngay để số liệu (thanh bên, bảng) không bị trễ một lượt.
if proj_hash() != computed_hash:
    st.rerun()
