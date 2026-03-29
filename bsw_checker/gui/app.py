"""BSW AUTOSAR Checker GUI Application.

macOS Calendar-inspired design using tkinter (cross-platform).
Clean, minimalist UI with sidebar navigation.
Per-module AUTOSAR version selection with checkbox enable/disable.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import threading
from pathlib import Path

from ..spec.module_registry import ModuleRegistry, SUPPORTED_VERSIONS
from ..parser.file_scanner import KNOWN_BSW_MODULES, scan_directory
from ..main import run_checks, ALL_CHECKERS

# ── Color Palette (macOS Calendar inspired) ──
COLORS = {
    "bg": "#F5F5F7",
    "sidebar_bg": "#E8E8ED",
    "sidebar_sel": "#D1D1D6",
    "card_bg": "#FFFFFF",
    "text_primary": "#1D1D1F",
    "text_secondary": "#86868B",
    "accent": "#0071E3",
    "accent_hover": "#0077ED",
    "pass_bg": "#E8F5E9",
    "pass_fg": "#2E7D32",
    "fail_bg": "#FFEBEE",
    "fail_fg": "#C62828",
    "warn_bg": "#FFF8E1",
    "warn_fg": "#F57F17",
    "info_bg": "#E3F2FD",
    "info_fg": "#1565C0",
    "border": "#D2D2D7",
    "divider": "#E5E5EA",
    "button_bg": "#0071E3",
    "button_fg": "#FFFFFF",
    "input_bg": "#FFFFFF",
    "input_border": "#C7C7CC",
    "verify_yes": "#34C759",
    "verify_no": "#FF3B30",
    "tag_bg": "#F2F2F7",
    "row_alt": "#FAFAFA",
}


class BSWCheckerApp:
    """Main GUI Application."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BSW AUTOSAR Spec Checker")
        self.root.geometry("1400x850")
        self.root.minsize(1100, 650)
        self.root.configure(bg=COLORS["bg"])

        self.registry = ModuleRegistry()
        self.results = []
        self.current_results = []
        self.reporter = None

        # Per-module state: {module_name: {"enabled": BooleanVar, "version": StringVar}}
        self.module_config: dict[str, dict] = {}

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=COLORS["bg"],
                         foreground=COLORS["text_primary"],
                         font=("Helvetica", 12))

        style.configure("Sidebar.TFrame", background=COLORS["sidebar_bg"])
        style.configure("Card.TFrame", background=COLORS["card_bg"])

        style.configure("Title.TLabel",
                         background=COLORS["bg"],
                         foreground=COLORS["text_primary"],
                         font=("Helvetica", 20, "bold"))

        style.configure("Results.Treeview",
                         background=COLORS["card_bg"],
                         foreground=COLORS["text_primary"],
                         fieldbackground=COLORS["card_bg"],
                         font=("Helvetica", 11),
                         rowheight=30)
        style.configure("Results.Treeview.Heading",
                         background=COLORS["sidebar_bg"],
                         foreground=COLORS["text_primary"],
                         font=("Helvetica", 11, "bold"))

    def _build_ui(self):
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True)

        # ── Sidebar (left, 320px) ──
        self.sidebar = tk.Frame(main, bg=COLORS["sidebar_bg"], width=320)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        tk.Frame(main, bg=COLORS["divider"], width=1).pack(side=tk.LEFT, fill=tk.Y)

        # ── Content (right) ──
        self.content = tk.Frame(main, bg=COLORS["bg"])
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_content()

    # ════════════════════════════════════════════
    #  SIDEBAR
    # ════════════════════════════════════════════
    def _build_sidebar(self):
        pad = 12

        # ── Title ──
        title_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        title_frame.pack(fill=tk.X, padx=pad, pady=(pad, 4))
        tk.Label(title_frame, text="BSW Checker",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_primary"],
                 font=("Helvetica", 18, "bold")).pack(anchor=tk.W)
        tk.Label(title_frame, text="AUTOSAR Spec Verification",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 11)).pack(anchor=tk.W)

        tk.Frame(self.sidebar, bg=COLORS["divider"], height=1).pack(fill=tk.X, padx=pad, pady=6)

        # ── Path ──
        tk.Label(self.sidebar, text="TARGET PATH",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 10, "bold")).pack(anchor=tk.W, padx=pad, pady=(4, 2))

        path_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        path_frame.pack(fill=tk.X, padx=pad)

        self.path_var = tk.StringVar()
        tk.Entry(path_frame, textvariable=self.path_var,
                 font=("Helvetica", 11), bg=COLORS["input_bg"],
                 relief="solid", bd=1).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        tk.Button(path_frame, text="...", command=self._browse_path,
                  bg=COLORS["sidebar_bg"], relief="flat",
                  font=("Helvetica", 12, "bold"), width=3).pack(side=tk.RIGHT, padx=(4, 0))

        # ── Additional Source Paths ──
        tk.Label(self.sidebar, text="ADDITIONAL PATHS (src, include, gen)",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 9, "bold")).pack(anchor=tk.W, padx=pad, pady=(4, 1))

        extra_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        extra_frame.pack(fill=tk.X, padx=pad)

        self.extra_paths_var = tk.StringVar()
        tk.Entry(extra_frame, textvariable=self.extra_paths_var,
                 font=("Helvetica", 10), bg=COLORS["input_bg"],
                 relief="solid", bd=1).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)
        tk.Button(extra_frame, text="+", command=self._add_extra_path,
                  bg=COLORS["sidebar_bg"], relief="flat",
                  font=("Helvetica", 12, "bold"), width=2).pack(side=tk.RIGHT, padx=(4, 0))

        self.extra_paths_list = tk.Listbox(self.sidebar, height=3,
                                            font=("Helvetica", 9),
                                            bg=COLORS["input_bg"], relief="solid", bd=1)
        self.extra_paths_list.pack(fill=tk.X, padx=pad, pady=(2, 2))

        rm_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        rm_frame.pack(fill=tk.X, padx=pad)
        tk.Button(rm_frame, text="Remove", command=self._remove_extra_path,
                  bg=COLORS["sidebar_bg"], relief="flat",
                  fg=COLORS["text_secondary"], font=("Helvetica", 9)).pack(side=tk.LEFT)

        # Auto-detect button
        tk.Button(self.sidebar, text="Scan & Auto-detect Modules",
                  command=self._auto_detect_modules,
                  bg=COLORS["tag_bg"], fg=COLORS["accent"],
                  relief="flat", font=("Helvetica", 11),
                  padx=8, pady=2).pack(fill=tk.X, padx=pad, pady=(4, 2))

        tk.Frame(self.sidebar, bg=COLORS["divider"], height=1).pack(fill=tk.X, padx=pad, pady=6)

        # ── Default Version + Bulk Actions ──
        ctrl_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        ctrl_frame.pack(fill=tk.X, padx=pad, pady=(0, 4))

        tk.Label(ctrl_frame, text="Default:",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 10)).pack(side=tk.LEFT)

        self.default_version_var = tk.StringVar(value="4.4.0")
        ver_combo = ttk.Combobox(ctrl_frame, textvariable=self.default_version_var,
                                  values=SUPPORTED_VERSIONS, state="readonly",
                                  width=8, font=("Helvetica", 10))
        ver_combo.pack(side=tk.LEFT, padx=(4, 8))

        tk.Button(ctrl_frame, text="All On", command=self._select_all_modules,
                  bg=COLORS["sidebar_bg"], relief="flat",
                  fg=COLORS["accent"], font=("Helvetica", 10)).pack(side=tk.LEFT)
        tk.Button(ctrl_frame, text="All Off", command=self._clear_module_selection,
                  bg=COLORS["sidebar_bg"], relief="flat",
                  fg=COLORS["text_secondary"], font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(4, 0))
        tk.Button(ctrl_frame, text="Set All Ver", command=self._set_all_versions,
                  bg=COLORS["sidebar_bg"], relief="flat",
                  fg=COLORS["accent"], font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(4, 0))

        # ── Module Table Header ──
        tk.Label(self.sidebar, text="MODULE CONFIGURATION",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 10, "bold")).pack(anchor=tk.W, padx=pad, pady=(4, 2))

        hdr = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        hdr.pack(fill=tk.X, padx=pad)
        tk.Label(hdr, text="Enable", width=6, bg=COLORS["sidebar_bg"],
                 fg=COLORS["text_secondary"], font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)
        tk.Label(hdr, text="Module", width=10, anchor=tk.W, bg=COLORS["sidebar_bg"],
                 fg=COLORS["text_secondary"], font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)
        tk.Label(hdr, text="AUTOSAR Ver", bg=COLORS["sidebar_bg"],
                 fg=COLORS["text_secondary"], font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)

        # ── Module Table (scrollable) ──
        table_outer = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        table_outer.pack(fill=tk.BOTH, expand=True, padx=pad, pady=(0, 4))

        canvas = tk.Canvas(table_outer, bg=COLORS["sidebar_bg"],
                            highlightthickness=0)
        scrollbar = tk.Scrollbar(table_outer, orient=tk.VERTICAL, command=canvas.yview)
        self.module_table_frame = tk.Frame(canvas, bg=COLORS["sidebar_bg"])

        self.module_table_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.module_table_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self._populate_module_table()

        # ── Run Button ──
        tk.Frame(self.sidebar, bg=COLORS["divider"], height=1).pack(fill=tk.X, padx=pad, pady=4)

        self.run_btn = tk.Button(self.sidebar, text="Run Verification",
                                  command=self._run_checks,
                                  bg=COLORS["button_bg"],
                                  fg=COLORS["button_fg"],
                                  font=("Helvetica", 14, "bold"),
                                  relief="flat", padx=20, pady=10,
                                  activebackground=COLORS["accent_hover"],
                                  activeforeground=COLORS["button_fg"])
        self.run_btn.pack(fill=tk.X, padx=pad, pady=(4, pad))

    def _populate_module_table(self):
        """Build per-module checkbox + version combo rows."""
        for w in self.module_table_frame.winfo_children():
            w.destroy()
        self.module_config.clear()

        # Collect all modules from all versions (union)
        all_modules = set()
        for ver in SUPPORTED_VERSIONS:
            all_modules.update(self.registry.get_supported_modules(ver))

        default_ver = self.default_version_var.get()

        for i, mod in enumerate(sorted(all_modules)):
            bg = COLORS["row_alt"] if i % 2 == 0 else COLORS["sidebar_bg"]

            row = tk.Frame(self.module_table_frame, bg=bg)
            row.pack(fill=tk.X, pady=0)

            enabled_var = tk.BooleanVar(value=False)
            version_var = tk.StringVar(value=default_ver)

            cb = tk.Checkbutton(row, variable=enabled_var,
                                 bg=bg, activebackground=bg,
                                 selectcolor=COLORS["accent"])
            cb.pack(side=tk.LEFT, padx=(8, 0))

            tk.Label(row, text=mod, width=10, anchor=tk.W,
                     bg=bg, fg=COLORS["text_primary"],
                     font=("Helvetica", 11)).pack(side=tk.LEFT)

            combo = ttk.Combobox(row, textvariable=version_var,
                                  values=SUPPORTED_VERSIONS,
                                  state="readonly", width=8,
                                  font=("Helvetica", 10))
            combo.pack(side=tk.LEFT, padx=(4, 8), pady=2)

            self.module_config[mod] = {
                "enabled": enabled_var,
                "version": version_var,
            }

    # ════════════════════════════════════════════
    #  CONTENT AREA
    # ════════════════════════════════════════════
    def _build_content(self):
        pad = 16

        # ── Header ──
        header = tk.Frame(self.content, bg=COLORS["bg"])
        header.pack(fill=tk.X, padx=pad, pady=(pad, 8))

        tk.Label(header, text="Verification Results",
                 bg=COLORS["bg"], fg=COLORS["text_primary"],
                 font=("Helvetica", 20, "bold")).pack(side=tk.LEFT)

        export_frame = tk.Frame(header, bg=COLORS["bg"])
        export_frame.pack(side=tk.RIGHT)
        tk.Button(export_frame, text="Export JSON", command=self._export_json,
                  bg=COLORS["tag_bg"], fg=COLORS["text_primary"],
                  relief="flat", font=("Helvetica", 11),
                  padx=12, pady=4).pack(side=tk.LEFT, padx=4)
        tk.Button(export_frame, text="Export Text", command=self._export_text,
                  bg=COLORS["tag_bg"], fg=COLORS["text_primary"],
                  relief="flat", font=("Helvetica", 11),
                  padx=12, pady=4).pack(side=tk.LEFT)

        # ── Summary cards ──
        self.summary_frame = tk.Frame(self.content, bg=COLORS["bg"])
        self.summary_frame.pack(fill=tk.X, padx=pad, pady=(0, 8))
        self._build_summary_cards()

        # ── Filter bar ──
        filter_frame = tk.Frame(self.content, bg=COLORS["bg"])
        filter_frame.pack(fill=tk.X, padx=pad, pady=(0, 8))

        tk.Label(filter_frame, text="Filter:", bg=COLORS["bg"],
                 fg=COLORS["text_secondary"], font=("Helvetica", 11)).pack(side=tk.LEFT)

        self.filter_var = tk.StringVar(value="all")
        for fval, flabel, fcolor in [
            ("all", "All", COLORS["text_primary"]),
            ("FAIL", "Failures", COLORS["fail_fg"]),
            ("WARN", "Warnings", COLORS["warn_fg"]),
            ("PASS", "Passes", COLORS["pass_fg"]),
            ("INFO", "Info", COLORS["info_fg"]),
        ]:
            tk.Radiobutton(filter_frame, text=flabel,
                           variable=self.filter_var, value=fval,
                           bg=COLORS["bg"], fg=fcolor,
                           selectcolor=COLORS["accent"],
                           activebackground=COLORS["bg"],
                           font=("Helvetica", 11),
                           command=self._apply_filter).pack(side=tk.LEFT, padx=8)

        tk.Label(filter_frame, text="Module:", bg=COLORS["bg"],
                 fg=COLORS["text_secondary"], font=("Helvetica", 11)).pack(side=tk.LEFT, padx=(16, 4))

        self.module_filter_var = tk.StringVar(value="All")
        self.module_filter_combo = ttk.Combobox(filter_frame,
                                                  textvariable=self.module_filter_var,
                                                  state="readonly",
                                                  font=("Helvetica", 11), width=15)
        self.module_filter_combo['values'] = ["All"]
        self.module_filter_combo.pack(side=tk.LEFT)
        self.module_filter_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        # ── Treeview ──
        tree_frame = tk.Frame(self.content, bg=COLORS["card_bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=pad, pady=(0, 4))

        columns = ("severity", "module", "version", "rule_id", "title", "verified")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                  style="Results.Treeview")

        self.tree.heading("severity", text="Status")
        self.tree.heading("module", text="Module")
        self.tree.heading("version", text="AR Ver")
        self.tree.heading("rule_id", text="Rule")
        self.tree.heading("title", text="Description")
        self.tree.heading("verified", text="Verified")

        self.tree.column("severity", width=60, minwidth=50)
        self.tree.column("module", width=70, minwidth=50)
        self.tree.column("version", width=60, minwidth=50)
        self.tree.column("rule_id", width=80, minwidth=60)
        self.tree.column("title", width=450, minwidth=200)
        self.tree.column("verified", width=70, minwidth=50)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                        command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_result_select)
        self.tree.tag_configure("PASS", background=COLORS["pass_bg"])
        self.tree.tag_configure("FAIL", background=COLORS["fail_bg"])
        self.tree.tag_configure("WARN", background=COLORS["warn_bg"])
        self.tree.tag_configure("INFO", background=COLORS["info_bg"])

        # ── Detail panel ──
        self.detail_frame = tk.Frame(self.content, bg=COLORS["card_bg"])
        self.detail_frame.pack(fill=tk.X, padx=pad, pady=(0, pad))
        self._build_detail_panel()

    def _build_summary_cards(self):
        for w in self.summary_frame.winfo_children():
            w.destroy()

        cards = [
            ("Total", "0", COLORS["text_primary"], COLORS["card_bg"]),
            ("Pass", "0", COLORS["pass_fg"], COLORS["pass_bg"]),
            ("Fail", "0", COLORS["fail_fg"], COLORS["fail_bg"]),
            ("Warn", "0", COLORS["warn_fg"], COLORS["warn_bg"]),
            ("Info", "0", COLORS["info_fg"], COLORS["info_bg"]),
        ]
        self.summary_labels = {}
        for label, value, fg, bg in cards:
            card = tk.Frame(self.summary_frame, bg=bg, padx=16, pady=8)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
            val_label = tk.Label(card, text=value, bg=bg, fg=fg,
                                  font=("Helvetica", 24, "bold"))
            val_label.pack()
            tk.Label(card, text=label, bg=bg, fg=fg, font=("Helvetica", 11)).pack()
            self.summary_labels[label] = val_label

    def _build_detail_panel(self):
        pad = 12

        self.detail_title = tk.Label(self.detail_frame,
                                      text="Select a result to view details",
                                      bg=COLORS["card_bg"],
                                      fg=COLORS["text_secondary"],
                                      font=("Helvetica", 14, "bold"),
                                      wraplength=800, justify=tk.LEFT)
        self.detail_title.pack(anchor=tk.W, padx=pad, pady=(pad, 4))

        self.detail_desc = tk.Text(self.detail_frame, bg=COLORS["card_bg"],
                                    fg=COLORS["text_primary"],
                                    font=("Helvetica", 11),
                                    height=4, wrap=tk.WORD, relief="flat", bd=0)
        self.detail_desc.pack(fill=tk.X, padx=pad, pady=(0, 4))
        self.detail_desc.config(state=tk.DISABLED)

        self.detail_meta = tk.Label(self.detail_frame, text="",
                                     bg=COLORS["card_bg"],
                                     fg=COLORS["text_secondary"],
                                     font=("Helvetica", 10),
                                     wraplength=800, justify=tk.LEFT)
        self.detail_meta.pack(anchor=tk.W, padx=pad, pady=(0, 4))

        verify_frame = tk.Frame(self.detail_frame, bg=COLORS["card_bg"])
        verify_frame.pack(anchor=tk.W, padx=pad, pady=(0, pad))

        tk.Button(verify_frame, text="Confirm", command=lambda: self._verify_result(True),
                  bg=COLORS["verify_yes"], fg="white", relief="flat",
                  font=("Helvetica", 11, "bold"), padx=12, pady=4).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(verify_frame, text="Reject", command=lambda: self._verify_result(False),
                  bg=COLORS["verify_no"], fg="white", relief="flat",
                  font=("Helvetica", 11, "bold"), padx=12, pady=4).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(verify_frame, text="Reset", command=lambda: self._verify_result(None),
                  bg=COLORS["tag_bg"], fg=COLORS["text_secondary"], relief="flat",
                  font=("Helvetica", 11), padx=12, pady=4).pack(side=tk.LEFT)

    # ════════════════════════════════════════════
    #  ACTIONS
    # ════════════════════════════════════════════
    def _browse_path(self):
        path = filedialog.askdirectory(title="Select BSW Source Directory")
        if path:
            self.path_var.set(path)

    def _add_extra_path(self):
        path = self.extra_paths_var.get().strip()
        if path and os.path.isdir(path):
            self.extra_paths_list.insert(tk.END, path)
            self.extra_paths_var.set("")
        elif not path:
            path = filedialog.askdirectory(title="Select Additional Source/Header Directory")
            if path:
                self.extra_paths_list.insert(tk.END, path)
        else:
            messagebox.showerror("Error", f"'{path}' is not a valid directory.")

    def _remove_extra_path(self):
        sel = self.extra_paths_list.curselection()
        if sel:
            self.extra_paths_list.delete(sel[0])

    def _get_extra_paths(self) -> list[str]:
        return list(self.extra_paths_list.get(0, tk.END))

    def _auto_detect_modules(self):
        """Scan all paths and auto-enable found modules."""
        target = self.path_var.get()
        if not target or not os.path.isdir(target):
            messagebox.showerror("Error", "Please select a valid directory first.")
            return

        extra = self._get_extra_paths()
        scan = scan_directory(target, source_paths=extra or None, parse_files=False)
        found = set(scan.module_names)

        count = 0
        for mod, cfg in self.module_config.items():
            if mod in found:
                cfg["enabled"].set(True)
                count += 1
            else:
                cfg["enabled"].set(False)

        messagebox.showinfo("Auto-detect",
                            f"Found {count} modules: {', '.join(sorted(found))}\n"
                            f"Total files scanned: {scan.total_files}")

    def _select_all_modules(self):
        for cfg in self.module_config.values():
            cfg["enabled"].set(True)

    def _clear_module_selection(self):
        for cfg in self.module_config.values():
            cfg["enabled"].set(False)

    def _set_all_versions(self):
        """Set all module versions to the default version."""
        ver = self.default_version_var.get()
        for cfg in self.module_config.values():
            cfg["version"].set(ver)

    def _get_version_map(self) -> dict[str, str]:
        """Build version_map from GUI state."""
        vm = {}
        for mod, cfg in self.module_config.items():
            if cfg["enabled"].get():
                vm[mod] = cfg["version"].get()
        return vm

    def _get_enabled_modules(self) -> list[str] | None:
        """Get list of enabled modules, or None if all enabled."""
        enabled = [mod for mod, cfg in self.module_config.items()
                    if cfg["enabled"].get()]
        return enabled if enabled else None

    def _run_checks(self):
        target = self.path_var.get()
        if not target or not os.path.isdir(target):
            messagebox.showerror("Error", "Please select a valid BSW source directory.")
            return

        version_map = self._get_version_map()
        modules = self._get_enabled_modules()
        default_ver = self.default_version_var.get()

        if not modules:
            messagebox.showwarning("Warning", "No modules selected. Enable at least one module.")
            return

        self.run_btn.config(state=tk.DISABLED, text="Running...")
        self.root.update()

        extra = self._get_extra_paths()

        def _do_check():
            try:
                self.reporter = run_checks(target, default_ver, modules,
                                            version_map=version_map,
                                            source_paths=extra or None)
                self.results = self.reporter.get_results_for_gui()
                self.root.after(0, self._display_results)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.run_btn.config(
                    state=tk.NORMAL, text="Run Verification"))

        threading.Thread(target=_do_check, daemon=True).start()

    def _display_results(self):
        total = len(self.results)
        passes = sum(1 for r in self.results if r["severity"] == "PASS")
        fails = sum(1 for r in self.results if r["severity"] == "FAIL")
        warns = sum(1 for r in self.results if r["severity"] == "WARN")
        infos = sum(1 for r in self.results if r["severity"] == "INFO")

        self.summary_labels["Total"].config(text=str(total))
        self.summary_labels["Pass"].config(text=str(passes))
        self.summary_labels["Fail"].config(text=str(fails))
        self.summary_labels["Warn"].config(text=str(warns))
        self.summary_labels["Info"].config(text=str(infos))

        modules = sorted(set(r["module"] for r in self.results))
        self.module_filter_combo['values'] = ["All"] + modules

        self._apply_filter()

    def _apply_filter(self):
        self.tree.delete(*self.tree.get_children())

        sev_filter = self.filter_var.get()
        mod_filter = self.module_filter_var.get()

        self.current_results = []
        for i, r in enumerate(self.results):
            if sev_filter != "all" and r["severity"] != sev_filter:
                continue
            if mod_filter != "All" and r["module"] != mod_filter:
                continue
            self.current_results.append((i, r))

        for idx, (orig_idx, r) in enumerate(self.current_results):
            verified_text = ""
            if r["verified"] is True:
                verified_text = "Confirmed"
            elif r["verified"] is False:
                verified_text = "Rejected"

            self.tree.insert("", tk.END, iid=str(idx),
                              values=(r["severity"], r["module"],
                                      r.get("autosar_version", ""),
                                      r["rule_id"], r["title"],
                                      verified_text),
                              tags=(r["severity"],))

    def _on_result_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        idx = int(selection[0])
        if idx >= len(self.current_results):
            return

        orig_idx, r = self.current_results[idx]

        self.detail_title.config(
            text=f"[{r['severity']}] [{r['rule_id']}] {r['title']}",
            fg=COLORS.get(f"{r['severity'].lower()}_fg", COLORS["text_primary"]))

        self.detail_desc.config(state=tk.NORMAL)
        self.detail_desc.delete("1.0", tk.END)
        self.detail_desc.insert("1.0", r["description"])
        self.detail_desc.config(state=tk.DISABLED)

        meta = []
        if r["file_path"]:
            loc = r["file_path"]
            if r["line_number"]:
                loc += f":{r['line_number']}"
            meta.append(f"Location: {loc}")
        if r.get("autosar_version"):
            meta.append(f"AUTOSAR Version: {r['autosar_version']}")
        if r["expected"]:
            meta.append(f"Expected: {r['expected']}")
        if r["actual"]:
            meta.append(f"Actual: {r['actual']}")
        if r["suggestion"]:
            meta.append(f"Suggestion: {r['suggestion']}")
        if r["autosar_ref"]:
            meta.append(f"AUTOSAR Ref: {r['autosar_ref']}")
        self.detail_meta.config(text="\n".join(meta))

    def _verify_result(self, verified):
        selection = self.tree.selection()
        if not selection:
            return

        idx = int(selection[0])
        if idx >= len(self.current_results):
            return

        orig_idx, r = self.current_results[idx]
        self.results[orig_idx]["verified"] = verified

        text = ""
        if verified is True:
            text = "Confirmed"
        elif verified is False:
            text = "Rejected"
        self.tree.set(selection[0], "verified", text)

    def _export_json(self):
        if not self.reporter:
            messagebox.showinfo("Info", "No results to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Export JSON", defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if path:
            data = json.loads(self.reporter.format_json())
            for i, result in enumerate(data.get("results", [])):
                if i < len(self.results):
                    result["verified"] = self.results[i]["verified"]
            Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
            messagebox.showinfo("Export", f"Report exported to {path}")

    def _export_text(self):
        if not self.reporter:
            messagebox.showinfo("Info", "No results to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Export Text", defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if path:
            Path(path).write_text(
                self.reporter.format_console(show_pass=True, show_info=True),
                encoding='utf-8')
            messagebox.showinfo("Export", f"Report exported to {path}")

    def run(self):
        self.root.mainloop()


def launch_gui():
    app = BSWCheckerApp()
    app.run()
