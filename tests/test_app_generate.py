import sys
import types
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Provide lightweight stubs for optional GUI/dependency modules.
jinja2_stub = types.ModuleType("jinja2")
jinja2_stub.Template = object
jinja2_stub.TemplateError = Exception
sys.modules.setdefault("jinja2", jinja2_stub)


class _Widget:
    def __init__(self, *args, **kwargs):
        pass

    def pack(self, *args, **kwargs):
        return None

    def grid(self, *args, **kwargs):
        return None

    def place(self, *args, **kwargs):
        return None

    def configure(self, *args, **kwargs):
        return None

    def bind(self, *args, **kwargs):
        return None

    def destroy(self, *args, **kwargs):
        return None


class _CTkFont:
    def __init__(self, *args, **kwargs):
        pass


ctk_stub = types.ModuleType("customtkinter")
ctk_stub.CTk = type("CTk", (_Widget,), {})
ctk_stub.CTkToplevel = type("CTkToplevel", (_Widget,), {})
ctk_stub.CTkFrame = type("CTkFrame", (_Widget,), {})
ctk_stub.CTkEntry = type("CTkEntry", (_Widget,), {})
ctk_stub.CTkButton = type("CTkButton", (_Widget,), {})
ctk_stub.CTkLabel = type("CTkLabel", (_Widget,), {})
ctk_stub.CTkOptionMenu = type("CTkOptionMenu", (_Widget,), {})
ctk_stub.CTkTextbox = type("CTkTextbox", (_Widget,), {})
ctk_stub.CTkTabview = type("CTkTabview", (_Widget,), {})
ctk_stub.CTkProgressBar = type("CTkProgressBar", (_Widget,), {})
ctk_stub.CTkCheckBox = type("CTkCheckBox", (_Widget,), {})
ctk_stub.CTkFont = _CTkFont
ctk_stub.BooleanVar = type("BooleanVar", (), {"__init__": lambda self, *a, **k: None})
ctk_stub.get_appearance_mode = lambda: "light"
ctk_stub.set_appearance_mode = lambda mode: None
ctk_stub.set_default_color_theme = lambda theme: None

sys.modules.setdefault("customtkinter", ctk_stub)

import ui.app as app_module
from templates_service import ExportError, EXCEL_FORMAT_LABEL


class DummyVar:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


@pytest.fixture
def prepared_app(monkeypatch, tmp_path):
    app = app_module.App.__new__(app_module.App)

    # Stubs for progress reporting and persistence
    app._progress_reset = lambda *args, **kwargs: None
    app._progress_message = lambda *args, **kwargs: None
    app._progress_update = lambda *args, **kwargs: None
    app._progress_finish = lambda *args, **kwargs: None
    app._save_title_tags = lambda *args, **kwargs: None
    app._export_apply_detail = lambda *args, **kwargs: None

    app.ft_vars = [("TypeA", types.SimpleNamespace(get=lambda: True))]
    app.templates = {"film_types": [{"name": "TypeA", "enabled": True}]}
    app.title_tags_templates = {}
    app.export_fields = []
    app.export_language_vars = []
    app._collect_checked_model_ids = types.MethodType(lambda self: [], app)
    app._collect_selected_export_languages = types.MethodType(lambda self: [], app)
    app._template_language_codes = types.MethodType(lambda self: [], app)

    app.export_fmt_var = DummyVar(EXCEL_FORMAT_LABEL)
    app.out_folder_var = DummyVar(str(tmp_path))

    monkeypatch.setattr(app_module, "save_templates", lambda templates: None)
    monkeypatch.setattr(
        app_module,
        "generate_export_rows",
        lambda *args, **kwargs: ([{"col": "value"}], ["col"]),
    )

    return app


def test_generate_shows_export_error_code(monkeypatch, prepared_app):
    messages = []

    def fake_show_error(message):
        messages.append(message)
        return message

    monkeypatch.setattr(app_module, "show_error", fake_show_error)
    monkeypatch.setattr(app_module, "show_info", lambda message: None)

    def failing_export(*args, **kwargs):
        raise ExportError("TEST_CODE", "details")

    monkeypatch.setattr(app_module, "export_products", failing_export)

    prepared_app._generate()

    assert messages == ["Помилка експорту (код TEST_CODE): details"]


def test_generate_unexpected_exception_uses_fallback(monkeypatch, prepared_app):
    messages = []

    def fake_show_error(message):
        messages.append(message)
        return message

    monkeypatch.setattr(app_module, "show_error", fake_show_error)
    monkeypatch.setattr(app_module, "show_info", lambda message: None)

    def failing_export(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "export_products", failing_export)

    prepared_app._generate()

    assert messages == ["Не вдалося зберегти файли: boom"]
