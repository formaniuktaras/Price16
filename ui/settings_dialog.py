"""Settings dialog (Total Commander style)."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, Optional

import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, ttk

import customtkinter as ctk

from app_paths import get_data_dir
from settings_service import default_settings


class SettingsDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent: ctk.CTk,
        current_settings: Dict[str, Any],
        on_apply: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.title("Налаштування")
        self.geometry("820x520")
        self.minsize(720, 420)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self._parent = parent
        self._on_apply = on_apply
        self._default_settings = default_settings()
        self._draft_settings = deepcopy(current_settings)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._build_ui()
        self._select_category("Загальні")

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        left = ctk.CTkFrame(container, width=200)
        left.pack(side="left", fill="y", padx=(0, 8), pady=8)

        right = ctk.CTkFrame(container)
        right.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=8)

        self._category_list = tk.Listbox(left, height=8, exportselection=False)
        self._category_list.pack(fill="both", expand=True, padx=8, pady=8)
        categories = ["Загальні", "Оформлення", "Кольори", "Шрифти"]
        for item in categories:
            self._category_list.insert(tk.END, item)
        self._category_list.bind("<<ListboxSelect>>", self._on_category_select)
        if categories:
            self._category_list.selection_set(0)
            self._category_list.activate(0)

        self._panels: Dict[str, ctk.CTkFrame] = {}
        self._build_general_panel(right)
        self._build_appearance_panel(right)
        self._build_colors_panel(right)
        self._build_fonts_panel(right)

        footer = ctk.CTkFrame(self)
        footer.pack(fill="x", padx=12, pady=(0, 12))

        reset_btn = ctk.CTkButton(footer, text="Скинути все", command=self._reset_all)
        reset_btn.pack(side="left", padx=6, pady=6)

        button_box = ctk.CTkFrame(footer, fg_color="transparent")
        button_box.pack(side="right", padx=6, pady=6)

        ok_btn = ctk.CTkButton(button_box, text="OK", width=90, command=self._on_ok)
        ok_btn.pack(side="left", padx=4)
        cancel_btn = ctk.CTkButton(button_box, text="Cancel", width=90, command=self._on_cancel)
        cancel_btn.pack(side="left", padx=4)
        apply_btn = ctk.CTkButton(button_box, text="Apply", width=90, command=self._on_apply_click)
        apply_btn.pack(side="left", padx=4)

    def _build_general_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent)
        panel.pack(fill="both", expand=True)
        self._panels["Загальні"] = panel

        data_dir = str(get_data_dir())
        ctk.CTkLabel(panel, text="Каталог даних:").pack(anchor="w", padx=12, pady=(12, 4))
        data_entry = ctk.CTkEntry(panel)
        data_entry.insert(0, data_dir)
        data_entry.configure(state="readonly")
        data_entry.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(panel, text="Папка експорту (за замовчуванням):").pack(anchor="w", padx=12, pady=(12, 4))
        self._export_folder_var = tk.StringVar(value=self._draft_settings.get("export_folder", ""))
        export_entry = ctk.CTkEntry(panel, textvariable=self._export_folder_var)
        export_entry.pack(fill="x", padx=12, pady=(0, 4))

        browse_btn = ctk.CTkButton(panel, text="Обрати...", command=self._choose_export_folder)
        browse_btn.pack(anchor="e", padx=12, pady=(0, 8))

    def _build_appearance_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent)
        panel.pack(fill="both", expand=True)
        self._panels["Оформлення"] = panel

        ctk.CTkLabel(panel, text="Режим оформлення:").pack(anchor="w", padx=12, pady=(12, 4))
        self._appearance_var = tk.StringVar(value=self._draft_settings.get("appearance_mode", "Dark"))
        appearance_menu = ctk.CTkOptionMenu(panel, values=["System", "Light", "Dark"], variable=self._appearance_var)
        appearance_menu.pack(anchor="w", padx=12, pady=(0, 12))

        ctk.CTkLabel(panel, text="Тема профілю:").pack(anchor="w", padx=12, pady=(8, 4))
        self._profile_var = tk.StringVar(value=self._draft_settings.get("theme_profile", "dark"))
        profile_menu = ctk.CTkOptionMenu(
            panel,
            values=["dark", "light"],
            variable=self._profile_var,
            command=self._on_profile_change,
        )
        profile_menu.pack(anchor="w", padx=12, pady=(0, 8))

    def _build_colors_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent)
        panel.pack(fill="both", expand=True)
        self._panels["Кольори"] = panel

        self._color_vars: Dict[str, tk.StringVar] = {}
        labels = [
            ("background", "Background"),
            ("surface", "Surface / Panel"),
            ("widget_fg", "Widget FG"),
            ("text", "Text"),
            ("accent", "Accent"),
            ("danger", "Danger"),
            ("border", "Border"),
        ]
        for key, label in labels:
            ctk.CTkLabel(panel, text=f"{label}:").pack(anchor="w", padx=12, pady=(8, 2))
            var = tk.StringVar()
            entry = ctk.CTkEntry(panel, textvariable=var)
            entry.pack(fill="x", padx=12, pady=(0, 4))
            self._color_vars[key] = var

    def _build_fonts_panel(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent)
        panel.pack(fill="both", expand=True)
        self._panels["Шрифти"] = panel

        ctk.CTkLabel(panel, text="Family:").pack(anchor="w", padx=12, pady=(12, 4))
        families = sorted(set(tkfont.families(self)))
        self._font_family_var = tk.StringVar()
        family_combo = ttk.Combobox(panel, values=families, textvariable=self._font_family_var)
        family_combo.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(panel, text="Base size:").pack(anchor="w", padx=12, pady=(8, 4))
        self._font_base_var = tk.StringVar()
        base_entry = ctk.CTkEntry(panel, textvariable=self._font_base_var)
        base_entry.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(panel, text="Heading size:").pack(anchor="w", padx=12, pady=(8, 4))
        self._font_heading_var = tk.StringVar()
        heading_entry = ctk.CTkEntry(panel, textvariable=self._font_heading_var)
        heading_entry.pack(fill="x", padx=12, pady=(0, 8))

    def _select_category(self, name: str) -> None:
        for panel_name, panel in self._panels.items():
            if panel_name == name:
                panel.pack(fill="both", expand=True)
            else:
                panel.pack_forget()
        if name in {"Кольори", "Шрифти"}:
            self._refresh_profile_fields()

    def _on_category_select(self, _event: tk.Event) -> None:
        selection = self._category_list.curselection()
        if not selection:
            return
        name = self._category_list.get(selection[0])
        self._select_category(name)

    def _on_profile_change(self, _value: str) -> None:
        self._collect_profile_fields()
        self._refresh_profile_fields()

    def _refresh_profile_fields(self) -> None:
        profile = self._profile_var.get() or "dark"
        themes = self._draft_settings.setdefault("themes", {})
        theme = themes.setdefault(profile, {})
        colors = theme.setdefault("colors", {})
        fonts = theme.setdefault("fonts", {})

        for key, var in self._color_vars.items():
            var.set(colors.get(key, ""))

        self._font_family_var.set(str(fonts.get("family", "")))
        self._font_base_var.set(str(fonts.get("base_size", "")))
        self._font_heading_var.set(str(fonts.get("heading_size", "")))

    def _collect_profile_fields(self) -> None:
        profile = self._profile_var.get() or "dark"
        themes = self._draft_settings.setdefault("themes", {})
        theme = themes.setdefault(profile, {})
        colors = theme.setdefault("colors", {})
        fonts = theme.setdefault("fonts", {})

        for key, var in self._color_vars.items():
            colors[key] = var.get().strip()

        fonts["family"] = self._font_family_var.get().strip()
        fonts["base_size"] = self._font_base_var.get().strip()
        fonts["heading_size"] = self._font_heading_var.get().strip()

    def _collect_common_fields(self) -> None:
        self._draft_settings["appearance_mode"] = self._appearance_var.get()
        self._draft_settings["theme_profile"] = self._profile_var.get()
        self._draft_settings["export_folder"] = self._export_folder_var.get().strip()

    def _apply_internal(self) -> None:
        self._collect_profile_fields()
        self._collect_common_fields()
        if self._on_apply:
            self._on_apply(deepcopy(self._draft_settings))

    def _on_ok(self) -> None:
        self._apply_internal()
        self.destroy()

    def _on_cancel(self) -> None:
        self.destroy()

    def _on_apply_click(self) -> None:
        self._apply_internal()

    def _reset_all(self) -> None:
        self._draft_settings = deepcopy(self._default_settings)
        self._appearance_var.set(self._draft_settings.get("appearance_mode", "Dark"))
        self._profile_var.set(self._draft_settings.get("theme_profile", "dark"))
        self._export_folder_var.set(self._draft_settings.get("export_folder", ""))
        self._refresh_profile_fields()

    def _choose_export_folder(self) -> None:
        path = filedialog.askdirectory(parent=self)
        if path:
            self._export_folder_var.set(path)
