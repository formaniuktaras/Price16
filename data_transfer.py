"""Utilities for exporting and importing application data via Excel workbooks."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

import importlib

from database import export_catalog_dump, import_catalog_dump
from templates_service import (
    CSV_JSON_FALLBACK_NOTE,
    EXCEL_EXPORT_BLOCKED_MESSAGE,
    OPENPYXL_AVAILABLE,
    OPENPYXL_IMPORT_ERROR_DETAIL,
    OPENPYXL_INSTALL_HINT,
    Workbook,
)


class DataTransferError(RuntimeError):
    """Custom exception raised for import/export failures."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:  # pragma: no cover - mirrors base behaviour
        return self.message


DATA_ERR_NO_OPENPYXL = "NO_OPENPYXL"
DATA_ERR_INVALID_PAYLOAD = "INVALID_PAYLOAD"
DATA_ERR_IO = "IO_ERROR"
DATA_ERR_SAVE_FAILED = "SAVE_FAILED"
DATA_ERR_LOAD_FAILED = "LOAD_FAILED"
DATA_ERR_VALIDATION = "VALIDATION_FAILED"


def _require_openpyxl() -> None:
    if not OPENPYXL_AVAILABLE or EXCEL_EXPORT_BLOCKED_MESSAGE:
        message = EXCEL_EXPORT_BLOCKED_MESSAGE or "Експорт у Excel недоступний."
        detail = OPENPYXL_IMPORT_ERROR_DETAIL
        if detail and detail not in message:
            message = f"{message} (деталі: {detail})"
        message = f"{message}\n{OPENPYXL_INSTALL_HINT}{CSV_JSON_FALLBACK_NOTE}"
        raise DataTransferError(DATA_ERR_NO_OPENPYXL, message)
    if Workbook is None:
        raise DataTransferError(
            DATA_ERR_NO_OPENPYXL,
            "Експорт у формат Excel недоступний у цій конфігурації.",
        )


def _load_workbook_file(path: str):
    module = importlib.import_module("openpyxl")
    return module.load_workbook(path)


def _normalise_languages(raw: Iterable[str | None]) -> List[str]:
    seen = set()
    result: List[str] = []
    for entry in raw:
        if not isinstance(entry, str):
            continue
        code = entry.strip()
        if not code or code in seen:
            continue
        result.append(code)
        seen.add(code)
    return result


def export_all_data_to_excel(
    filename: str,
    templates: Dict[str, object],
    title_tags: Dict[str, object],
    export_fields: List[Dict[str, object]],
) -> str:
    """Export catalog, templates, parameters and export fields into an Excel file."""

    _require_openpyxl()

    if not filename:
        raise DataTransferError(DATA_ERR_IO, "Не вказано шлях для збереження файлу.")

    catalog = export_catalog_dump()

    workbook = Workbook()
    sheets = {}

    sheet = workbook.active
    sheet.title = "Категорії"
    sheet.append(["ID", "Назва", "Створено"])
    for entry in catalog.get("categories", []):
        sheet.append(
            [
                entry.get("id"),
                entry.get("name"),
                entry.get("created_at"),
            ]
        )
    sheets["Категорії"] = sheet

    sheet = workbook.create_sheet("Бренди")
    sheet.append(["ID", "Категорія ID", "Назва", "Створено"])
    for entry in catalog.get("brands", []):
        sheet.append(
            [
                entry.get("id"),
                entry.get("category_id"),
                entry.get("name"),
                entry.get("created_at"),
            ]
        )
    sheets["Бренди"] = sheet

    sheet = workbook.create_sheet("Моделі")
    sheet.append(["ID", "Бренд ID", "Назва", "Створено"])
    for entry in catalog.get("models", []):
        sheet.append(
            [
                entry.get("id"),
                entry.get("brand_id"),
                entry.get("name"),
                entry.get("created_at"),
            ]
        )
    sheets["Моделі"] = sheet

    sheet = workbook.create_sheet("Характеристики")
    sheet.append(["ID", "Модель ID", "Ключ", "Значення"])
    for entry in catalog.get("specs", []):
        sheet.append(
            [
                entry.get("id"),
                entry.get("model_id"),
                entry.get("key"),
                entry.get("value"),
            ]
        )
    sheets["Характеристики"] = sheet

    sheet = workbook.create_sheet("Параметри")
    sheet.append(["Тип", "Код", "Назва", "Увімкнено"])
    for entry in templates.get("template_languages", []) if isinstance(templates, dict) else []:
        if not isinstance(entry, dict):
            continue
        code = (entry.get("code") or "").strip()
        label = (entry.get("label") or "").strip() or code
        if not code:
            continue
        sheet.append(["language", code, label, ""])
    for entry in templates.get("film_types", []) if isinstance(templates, dict) else []:
        if not isinstance(entry, dict):
            continue
        name = (entry.get("name") or "").strip()
        if not name:
            continue
        enabled = "1" if entry.get("enabled") else "0"
        sheet.append(["film_type", "", name, enabled])
    sheets["Параметри"] = sheet

    sheet = workbook.create_sheet("Шаблони")
    sheet.append(["Ключ", "Дані (JSON)"])
    sheet.append(["templates", json.dumps(templates, ensure_ascii=False, indent=2)])
    sheet.append(["title_tags_templates", json.dumps(title_tags, ensure_ascii=False, indent=2)])
    sheets["Шаблони"] = sheet

    sheet = workbook.create_sheet("Експортні поля")
    sheet.append(["Позиція", "Поле", "Шаблон", "Увімкнено", "Мови"])
    for idx, entry in enumerate(export_fields, start=1):
        if not isinstance(entry, dict):
            continue
        field_name = (entry.get("field") or "").strip()
        template_text = entry.get("template", "")
        enabled = "1" if entry.get("enabled") else "0"
        languages_raw = entry.get("languages")
        if isinstance(languages_raw, str):
            languages_list = [languages_raw.strip()]
        elif isinstance(languages_raw, Iterable):
            languages_list = [
                str(code).strip()
                for code in languages_raw
                if isinstance(code, str) and code.strip()
            ]
        else:
            languages_list = []
        languages = ", ".join(_normalise_languages(languages_list))
        sheet.append([idx, field_name, template_text, enabled, languages])
    sheets["Експортні поля"] = sheet

    try:
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        workbook.save(filename)
    except PermissionError as exc:
        raise DataTransferError(
            DATA_ERR_IO,
            "Не вдалося зберегти Excel-файл: доступ заборонено. Закрийте файл, якщо він відкритий, та спробуйте знову.",
        ) from exc
    except OSError as exc:
        raise DataTransferError(DATA_ERR_IO, f"Не вдалося зберегти файл: {exc}") from exc
    finally:
        try:
            workbook.close()
        except Exception:  # pragma: no cover - best effort cleanup
            pass

    return filename


def _parse_parameters_sheet(sheet) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    languages: List[Dict[str, object]] = []
    film_types: List[Dict[str, object]] = []
    if sheet is None:
        return languages, film_types

    rows = getattr(sheet, "iter_rows", None)
    if rows is None:
        return languages, film_types

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not row:
            continue
        raw_type = row[0]
        entry_type = str(raw_type).strip().lower() if isinstance(raw_type, str) else ""
        if not entry_type:
            continue
        if entry_type == "language":
            code = str(row[1]).strip() if isinstance(row[1], str) else ""
            label = str(row[2]).strip() if isinstance(row[2], str) else ""
            if not code:
                continue
            languages.append({"code": code, "label": label or code})
        elif entry_type == "film_type":
            name = ""
            if isinstance(row[2], str):
                name = row[2].strip()
            if not name and isinstance(row[1], str):
                name = row[1].strip()
            if not name:
                continue
            enabled_cell = row[3] if len(row) > 3 else None
            enabled_value = False
            if isinstance(enabled_cell, str):
                enabled_value = enabled_cell.strip().lower() in {"1", "true", "yes", "y", "так"}
            elif isinstance(enabled_cell, (int, float)):
                enabled_value = bool(enabled_cell)
            elif isinstance(enabled_cell, bool):
                enabled_value = enabled_cell
            film_types.append({"name": name, "enabled": enabled_value})

    return languages, film_types


def _parse_templates_sheet(sheet) -> Tuple[Optional[Dict[str, object]], Optional[Dict[str, object]]]:
    templates_data = None
    title_tags_data = None
    if sheet is None:
        return templates_data, title_tags_data

    rows = getattr(sheet, "iter_rows", None)
    if rows is None:
        return templates_data, title_tags_data

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not row:
            continue
        key = row[0]
        if not isinstance(key, str):
            continue
        payload = row[1]
        if not isinstance(payload, str):
            continue
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise DataTransferError(DATA_ERR_VALIDATION, f"Некоректний JSON у блоці '{key}': {exc}")
        if key == "templates":
            if not isinstance(data, dict):
                raise DataTransferError(DATA_ERR_VALIDATION, "Розділ 'templates' повинен містити об'єкт JSON.")
            templates_data = data
        elif key == "title_tags_templates":
            if not isinstance(data, dict):
                raise DataTransferError(
                    DATA_ERR_VALIDATION,
                    "Розділ 'title_tags_templates' повинен містити об'єкт JSON.",
                )
            title_tags_data = data

    return templates_data, title_tags_data


def _parse_export_fields_sheet(sheet) -> List[Dict[str, object]]:
    if sheet is None:
        return []
    rows = getattr(sheet, "iter_rows", None)
    if rows is None:
        return []

    fields: List[Tuple[int, Dict[str, object]]] = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not row:
            continue
        position_raw = row[0]
        try:
            position = int(position_raw)
        except (TypeError, ValueError):
            position = len(fields) + 1
        field_name = (row[1] or "").strip() if isinstance(row[1], str) else ""
        template_text = row[2] if isinstance(row[2], str) else ""
        enabled_cell = row[3] if len(row) > 3 else None
        languages_cell = row[4] if len(row) > 4 else ""

        enabled = False
        if isinstance(enabled_cell, str):
            enabled = enabled_cell.strip().lower() in {"1", "true", "yes", "y", "так"}
        elif isinstance(enabled_cell, (int, float)):
            enabled = bool(enabled_cell)
        elif isinstance(enabled_cell, bool):
            enabled = enabled_cell

        if isinstance(languages_cell, str):
            raw_codes = [part.strip() for part in languages_cell.split(",")]
        elif isinstance(languages_cell, Iterable):
            raw_codes = [str(part).strip() for part in languages_cell]
        else:
            raw_codes = []
        languages = _normalise_languages(raw_codes)

        fields.append(
            (
                position,
                {
                    "field": field_name,
                    "template": template_text,
                    "enabled": enabled,
                    "languages": languages,
                },
            )
        )

    fields.sort(key=lambda item: item[0])
    return [payload for _pos, payload in fields]


def import_all_data_from_excel(filename: str) -> Dict[str, object]:
    """Import catalog, templates and export settings from an Excel workbook."""

    _require_openpyxl()

    if not filename:
        raise DataTransferError(DATA_ERR_LOAD_FAILED, "Не вказано файл для імпорту.")
    if not os.path.exists(filename):
        raise DataTransferError(DATA_ERR_LOAD_FAILED, "Файл не знайдено.")

    try:
        workbook = _load_workbook_file(filename)
    except FileNotFoundError as exc:
        raise DataTransferError(DATA_ERR_LOAD_FAILED, "Файл не знайдено.") from exc
    except OSError as exc:
        raise DataTransferError(DATA_ERR_LOAD_FAILED, f"Не вдалося відкрити файл: {exc}") from exc

    try:
        sheets = {name: workbook[name] for name in getattr(workbook, "sheetnames", [])}

        templates_sheet = sheets.get("Шаблони")
        parameters_sheet = sheets.get("Параметри")
        export_sheet = sheets.get("Експортні поля")

        catalog_payload = {
            "categories": [],
            "brands": [],
            "models": [],
            "specs": [],
        }

        if "Категорії" in sheets:
            sheet = sheets["Категорії"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row:
                    continue
                catalog_payload["categories"].append(
                    {"id": row[0], "name": row[1], "created_at": row[2]}
                )

        if "Бренди" in sheets:
            sheet = sheets["Бренди"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row:
                    continue
                catalog_payload["brands"].append(
                    {
                        "id": row[0],
                        "category_id": row[1],
                        "name": row[2],
                        "created_at": row[3] if len(row) > 3 else None,
                    }
                )

        if "Моделі" in sheets:
            sheet = sheets["Моделі"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row:
                    continue
                catalog_payload["models"].append(
                    {
                        "id": row[0],
                        "brand_id": row[1],
                        "name": row[2],
                        "created_at": row[3] if len(row) > 3 else None,
                    }
                )

        if "Характеристики" in sheets:
            sheet = sheets["Характеристики"]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row:
                    continue
                catalog_payload["specs"].append(
                    {
                        "id": row[0],
                        "model_id": row[1],
                        "key": row[2],
                        "value": row[3] if len(row) > 3 else None,
                    }
                )

        templates_data, title_tags_data = _parse_templates_sheet(templates_sheet)
        languages, film_types = _parse_parameters_sheet(parameters_sheet)
        export_fields = _parse_export_fields_sheet(export_sheet)

        if templates_data is None:
            templates_data = {}
        if languages:
            templates_data["template_languages"] = languages
        if film_types:
            templates_data["film_types"] = film_types
        if title_tags_data is None:
            title_tags_data = {}

        import_catalog_dump(catalog_payload)

        from templates_service import (
            load_export_fields,
            load_templates,
            load_title_tags_templates,
            save_export_fields,
            save_templates,
            save_title_tags_templates,
        )

        try:
            save_templates(templates_data)
            save_title_tags_templates(title_tags_data)
            if export_fields:
                save_export_fields(export_fields)
        except OSError as exc:
            raise DataTransferError(DATA_ERR_SAVE_FAILED, f"Не вдалося зберегти дані: {exc}") from exc

        refreshed_templates = load_templates()
        refreshed_title_tags = load_title_tags_templates(refreshed_templates)
        refreshed_export_fields = load_export_fields()

        return {
            "templates": refreshed_templates,
            "title_tags_templates": refreshed_title_tags,
            "export_fields": refreshed_export_fields,
        }
    finally:
        try:
            workbook.close()
        except Exception:  # pragma: no cover - defensive close
            pass
