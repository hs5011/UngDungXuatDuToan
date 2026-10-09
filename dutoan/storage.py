"""Lưu/đọc dự án trong thư mục workspace/projects/<id>.json (tự động lưu, chọn lại được ở thanh bên)."""
import json
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from .defaults import default_project, merge_defaults

PROJECTS_DIR = Path(__file__).resolve().parent.parent / "workspace" / "projects"
BROKEN: dict = {}  # id → lỗi khi đọc (lần gọi list_projects gần nhất)


def slugify(text):
    s = unicodedata.normalize("NFD", (text or "").replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "du-an"


def _path(pid):
    return PROJECTS_DIR / f"{pid}.json"


def _now():
    return datetime.now().isoformat(timespec="seconds")


def list_projects():
    """[(id, tên, cập nhật lúc)] mới nhất trước."""
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    BROKEN.clear()
    out = []
    for f in PROJECTS_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            meta = d.get("_meta", {})
            name = (d.get("thong_tin") or {}).get("ten_du_an") or meta.get("ten") or "(chưa đặt tên)"
            out.append((f.stem, name, meta.get("updated_at", "")))
        except Exception as e:  # noqa: BLE001 – file hỏng: báo, không làm hỏng danh sách
            BROKEN[f.stem] = str(e)[:200]
    return sorted(out, key=lambda x: x[2], reverse=True)


def save_project(pid, proj):
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    data = dict(proj)
    meta = dict(data.get("_meta") or {})
    meta.setdefault("created_at", _now())
    meta["updated_at"] = _now()
    data["_meta"] = meta
    proj["_meta"] = meta
    tmp = _path(pid).with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, _path(pid))  # ghi nguyên tử: không để file dở dang khi lỗi giữa chừng


def load_project(pid):
    return merge_defaults(json.loads(_path(pid).read_text(encoding="utf-8")))


def _new_id(name):
    return f"{datetime.now():%Y%m%d-%H%M%S}-{slugify(name)[:30]}"


def create_project(name, data=None):
    """Tạo dự án mới (rỗng theo mặc định, hoặc từ dữ liệu file .json nhập vào). Trả về id."""
    proj = merge_defaults(data) if data else default_project()
    proj.pop("_meta", None)
    if name:
        proj["thong_tin"]["ten_du_an"] = name
    pid = _new_id(proj["thong_tin"]["ten_du_an"] or "du-an")
    while _path(pid).exists():
        pid += "-1"
    save_project(pid, proj)
    return pid


def delete_project(pid):
    try:
        _path(pid).unlink()
    except FileNotFoundError:
        pass
