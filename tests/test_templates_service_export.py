import sys
import types
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

jinja2_stub = types.ModuleType("jinja2")
jinja2_stub.Template = object
jinja2_stub.TemplateError = Exception
sys.modules.setdefault("jinja2", jinja2_stub)

import templates_service as ts


class DummySheet:
    def __init__(self):
        self.rows = []
        self.title = ""

    def append(self, row):
        self.rows.append(tuple(row))


class DummyWorkbook:
    def __init__(self, save_exc):
        self.active = DummySheet()
        self._save_exc = save_exc
        self.closed = False

    def save(self, filename):
        raise self._save_exc

    def close(self):
        self.closed = True


@pytest.fixture
def excel_context(monkeypatch):
    monkeypatch.setattr(ts, "OPENPYXL_AVAILABLE", True)
    monkeypatch.setattr(ts, "EXCEL_EXPORT_BLOCKED_MESSAGE", "")
    monkeypatch.setattr(ts, "OPENPYXL_IMPORT_ERROR_DETAIL", "")


def test_export_products_missing_dependency(monkeypatch, tmp_path):
    monkeypatch.setattr(ts, "OPENPYXL_AVAILABLE", False)
    monkeypatch.setattr(ts, "EXCEL_EXPORT_BLOCKED_MESSAGE", "")
    monkeypatch.setattr(ts, "OPENPYXL_IMPORT_ERROR_DETAIL", "")

    with pytest.raises(ts.ExportError) as excinfo:
        ts.export_products([], [], ts.EXCEL_FORMAT_LABEL, str(tmp_path))

    assert excinfo.value.code == ts.EXPORT_ERR_NO_OPENPYXL
    assert "Експорт у Excel" in excinfo.value.message


def test_export_products_permission_error(monkeypatch, tmp_path, excel_context):
    def make_workbook():
        return DummyWorkbook(PermissionError("denied"))

    monkeypatch.setattr(ts, "Workbook", make_workbook)

    with pytest.raises(ts.ExportError) as excinfo:
        ts.export_products([["value"]], ["col"], ts.EXCEL_FORMAT_LABEL, str(tmp_path))

    assert excinfo.value.code == ts.EXPORT_ERR_PERMISSION
    assert "доступ заборонено" in excinfo.value.message


def test_export_products_os_error(monkeypatch, tmp_path, excel_context):
    def make_workbook():
        return DummyWorkbook(OSError("disk full"))

    monkeypatch.setattr(ts, "Workbook", make_workbook)

    with pytest.raises(ts.ExportError) as excinfo:
        ts.export_products([["value"]], ["col"], ts.EXCEL_FORMAT_LABEL, str(tmp_path))

    assert excinfo.value.code == ts.EXPORT_ERR_OS_ERROR
    assert "disk full" in excinfo.value.message


def test_export_products_unknown_format():
    with pytest.raises(ts.ExportError) as excinfo:
        ts.export_products([], [], "custom", ".")

    assert excinfo.value.code == ts.EXPORT_ERR_UNKNOWN_FORMAT


def test_export_products_folder_preparation_failure(monkeypatch, tmp_path):
    target = tmp_path / "nested"

    def fake_exists(path):
        return False

    def fake_makedirs(path, exist_ok=True):
        raise OSError("cannot create directory")

    monkeypatch.setattr(ts.os.path, "exists", fake_exists)
    monkeypatch.setattr(ts.os, "makedirs", fake_makedirs)

    with pytest.raises(ts.ExportError) as excinfo:
        ts.export_products([], [], ts.CSV_FORMAT_LABEL, str(target))

    assert excinfo.value.code == ts.EXPORT_ERR_FOLDER_PREP
    assert "підготувати теку" in excinfo.value.message
