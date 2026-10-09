import pytest

from dutoan import storage


@pytest.fixture(autouse=True)
def tmp_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "PROJECTS_DIR", tmp_path / "projects")


def test_tao_luu_mo_xoa_du_an():
    pid = storage.create_project("Hệ thống Điều hành ABC")
    assert "he-thong-dieu-hanh-abc" in pid
    proj = storage.load_project(pid)
    assert proj["thong_tin"]["ten_du_an"] == "Hệ thống Điều hành ABC"
    proj["tham_so"]["gms"] = 7e9
    storage.save_project(pid, proj)
    assert storage.load_project(pid)["tham_so"]["gms"] == 7e9
    assert [x[0] for x in storage.list_projects()] == [pid]
    storage.delete_project(pid)
    assert storage.list_projects() == []


def test_nhap_tu_file_json_tao_du_an_moi():
    src = storage.load_project(storage.create_project("Gốc"))
    src["tham_so"]["gms"] = 1.5e9
    pid = storage.create_project(None, src)
    assert storage.load_project(pid)["tham_so"]["gms"] == 1.5e9
    assert len(storage.list_projects()) == 2


def test_file_hong_khong_lam_hong_danh_sach():
    storage.create_project("Tốt")
    (storage.PROJECTS_DIR / "hong.json").write_text("{không phải json", encoding="utf-8")
    assert len(storage.list_projects()) == 1
    assert "hong" in storage.BROKEN
