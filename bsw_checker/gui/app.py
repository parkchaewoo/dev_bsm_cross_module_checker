"""BSW AUTOSAR Checker GUI Application.

macOS Calendar-inspired design using tkinter (cross-platform).
Clean, minimalist UI with sidebar navigation.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import threading
from pathlib import Path

from ..spec.module_registry import ModuleRegistry, SUPPORTED_VERSIONS
from ..parser.file_scanner import KNOWN_BSW_MODULES
from ..main import run_checks, ALL_CHECKERS

# ── Color Palette (macOS Calendar inspired) ──
COLORS = {
    "bg": "#F5F5F7",           # Light gray background
    "sidebar_bg": "#E8E8ED",   # Sidebar background
    "sidebar_sel": "#D1D1D6",  # Sidebar selected
    "card_bg": "#FFFFFF",      # Card/panel background
    "text_primary": "#1D1D1F", # Primary text
    "text_secondary": "#86868B",  # Secondary text
    "accent": "#0071E3",       # Blue accent (Apple blue)
    "accent_hover": "#0077ED",
    "pass_bg": "#E8F5E9",      # Green for PASS
    "pass_fg": "#2E7D32",
    "fail_bg": "#FFEBEE",      # Red for FAIL
    "fail_fg": "#C62828",
    "warn_bg": "#FFF8E1",      # Amber for WARN
    "warn_fg": "#F57F17",
    "info_bg": "#E3F2FD",      # Blue for INFO
    "info_fg": "#1565C0",
    "border": "#D2D2D7",
    "divider": "#E5E5EA",
    "button_bg": "#0071E3",
    "button_fg": "#FFFFFF",
    "input_bg": "#FFFFFF",
    "input_border": "#C7C7CC",
    "verify_yes": "#34C759",   # Green checkmark
    "verify_no": "#FF3B30",    # Red X
    "tag_bg": "#F2F2F7",
}


class BSWCheckerApp:
    """Main GUI Application."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BSW AUTOSAR Spec Checker")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 600)
        self.root.configure(bg=COLORS["bg"])

        self.registry = ModuleRegistry()
        self.results = []
        self.current_results = []
        self.reporter = None

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        """Configure ttk styles for macOS Calendar look."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=COLORS["bg"],
                         foreground=COLORS["text_primary"],
                         font=("Helvetica", 12))

        style.configure("Sidebar.TFrame", background=COLORS["sidebar_bg"])
        style.configure("Card.TFrame", background=COLORS["card_bg"],
                         relief="flat")

        style.configure("Title.TLabel",
                         background=COLORS["bg"],
                         foreground=COLORS["text_primary"],
                         font=("Helvetica", 20, "bold"))

        style.configure("Subtitle.TLabel",
                         background=COLORS["bg"],
                         foreground=COLORS["text_secondary"],
                         font=("Helvetica", 13))

        style.configure("Sidebar.TLabel",
                         background=COLORS["sidebar_bg"],
                         foreground=COLORS["text_primary"],
                         font=("Helvetica", 13))

        style.configure("SidebarTitle.TLabel",
                         background=COLORS["sidebar_bg"],
                         foreground=COLORS["text_secondary"],
                         font=("Helvetica", 11, "bold"))

        style.configure("Accent.TButton",
                         background=COLORS["button_bg"],
                         foreground=COLORS["button_fg"],
                         font=("Helvetica", 13, "bold"),
                         padding=(20, 8))
        style.map("Accent.TButton",
                   background=[("active", COLORS["accent_hover"])])

        style.configure("Card.TLabel",
                         background=COLORS["card_bg"],
                         foreground=COLORS["text_primary"],
                         font=("Helvetica", 12))

        style.configure("CardTitle.TLabel",
                         background=COLORS["card_bg"],
                         foreground=COLORS["text_primary"],
                         font=("Helvetica", 14, "bold"))

        style.configure("Pass.TLabel", background=COLORS["pass_bg"],
                         foreground=COLORS["pass_fg"], font=("Helvetica", 12))
        style.configure("Fail.TLabel", background=COLORS["fail_bg"],
                         foreground=COLORS["fail_fg"], font=("Helvetica", 12))
        style.configure("Warn.TLabel", background=COLORS["warn_bg"],
                         foreground=COLORS["warn_fg"], font=("Helvetica", 12))
        style.configure("Info.TLabel", background=COLORS["info_bg"],
                         foreground=COLORS["info_fg"], font=("Helvetica", 12))

        # Treeview style
        style.configure("Results.Treeview",
                         background=COLORS["card_bg"],
                         foreground=COLORS["text_primary"],
                         fieldbackground=COLORS["card_bg"],
                         font=("Helvetica", 11),
                         rowheight=32)
        style.configure("Results.Treeview.Heading",
                         background=COLORS["sidebar_bg"],
                         foreground=COLORS["text_primary"],
                         font=("Helvetica", 11, "bold"))

    def _build_ui(self):
        """Build the main UI layout."""
        # Main container
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True)

        # ── Sidebar (left) ──
        self.sidebar = tk.Frame(main, bg=COLORS["sidebar_bg"], width=280)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # ── Divider ──
        tk.Frame(main, bg=COLORS["divider"], width=1).pack(side=tk.LEFT, fill=tk.Y)

        # ── Content area (right) ──
        self.content = tk.Frame(main, bg=COLORS["bg"])
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_content()

    def _build_sidebar(self):
        """Build sidebar with configuration options."""
        pad = 16

        # ── Logo/Title ──
        title_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        title_frame.pack(fill=tk.X, padx=pad, pady=(pad, 8))

        tk.Label(title_frame, text="BSW Checker",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_primary"],
                 font=("Helvetica", 18, "bold")).pack(anchor=tk.W)
        tk.Label(title_frame, text="AUTOSAR Spec Verification",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 11)).pack(anchor=tk.W)

        tk.Frame(self.sidebar, bg=COLORS["divider"], height=1).pack(fill=tk.X, padx=pad, pady=8)

        # ── Path Selection ──
        tk.Label(self.sidebar, text="TARGET PATH",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 10, "bold")).pack(anchor=tk.W, padx=pad, pady=(8, 4))

        path_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        path_frame.pack(fill=tk.X, padx=pad)

        self.path_var = tk.StringVar()
        path_entry = tk.Entry(path_frame, textvariable=self.path_var,
                              font=("Helvetica", 11),
                              bg=COLORS["input_bg"],
                              relief="solid",
                              bd=1)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        browse_btn = tk.Button(path_frame, text="...",
                               command=self._browse_path,
                               bg=COLORS["sidebar_bg"],
                               relief="flat",
                               font=("Helvetica", 12, "bold"),
                               width=3)
        browse_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # ── AUTOSAR Version ──
        tk.Frame(self.sidebar, bg=COLORS["divider"], height=1).pack(fill=tk.X, padx=pad, pady=8)
        tk.Label(self.sidebar, text="AUTOSAR VERSION",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 10, "bold")).pack(anchor=tk.W, padx=pad, pady=(8, 4))

        self.version_var = tk.StringVar(value="4.4.0")
        for ver in SUPPORTED_VERSIONS:
            rb = tk.Radiobutton(self.sidebar, text=f"AUTOSAR {ver}",
                                variable=self.version_var, value=ver,
                                bg=COLORS["sidebar_bg"],
                                fg=COLORS["text_primary"],
                                selectcolor=COLORS["accent"],
                                activebackground=COLORS["sidebar_bg"],
                                font=("Helvetica", 12),
                                command=self._on_version_change)
            rb.pack(anchor=tk.W, padx=(pad + 8, pad), pady=2)

        # ── Module Selection ──
        tk.Frame(self.sidebar, bg=COLORS["divider"], height=1).pack(fill=tk.X, padx=pad, pady=8)
        tk.Label(self.sidebar, text="MODULES",
                 bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 10, "bold")).pack(anchor=tk.W, padx=pad, pady=(8, 4))

        # Module listbox with scrollbar
        mod_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        mod_frame.pack(fill=tk.BOTH, expand=True, padx=pad, pady=(0, 8))

        mod_scroll = tk.Scrollbar(mod_frame)
        mod_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.module_listbox = tk.Listbox(mod_frame,
                                          selectmode=tk.MULTIPLE,
                                          font=("Helvetica", 11),
                                          bg=COLORS["input_bg"],
                                          relief="solid",
                                          bd=1,
                                          yscrollcommand=mod_scroll.set,
                                          exportselection=False)
        self.module_listbox.pack(fill=tk.BOTH, expand=True)
        mod_scroll.config(command=self.module_listbox.yview)

        self._populate_modules()

        # Select All / Deselect All
        btn_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar_bg"])
        btn_frame.pack(fill=tk.X, padx=pad, pady=(0, 8))

        tk.Button(btn_frame, text="Select All",
                  command=self._select_all_modules,
                  bg=COLORS["sidebar_bg"], relief="flat",
                  fg=COLORS["accent"], font=("Helvetica", 11)
                  ).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Clear",
                  command=self._clear_module_selection,
                  bg=COLORS["sidebar_bg"], relief="flat",
                  fg=COLORS["text_secondary"], font=("Helvetica", 11)
                  ).pack(side=tk.LEFT, padx=(8, 0))

        # ── Run Button ──
        tk.Frame(self.sidebar, bg=COLORS["divider"], height=1).pack(fill=tk.X, padx=pad, pady=4)

        self.run_btn = tk.Button(self.sidebar, text="Run Verification",
                                  command=self._run_checks,
                                  bg=COLORS["button_bg"],
                                  fg=COLORS["button_fg"],
                                  font=("Helvetica", 14, "bold"),
                                  relief="flat",
                                  padx=20, pady=10,
                                  activebackground=COLORS["accent_hover"],
                                  activeforeground=COLORS["button_fg"])
        self.run_btn.pack(fill=tk.X, padx=pad, pady=pad)

    def _build_content(self):
        """Build main content area."""
        pad = 16

        # ── Header bar ──
        header = tk.Frame(self.content, bg=COLORS["bg"])
        header.pack(fill=tk.X, padx=pad, pady=(pad, 8))

        tk.Label(header, text="Verification Results",
                 bg=COLORS["bg"], fg=COLORS["text_primary"],
                 font=("Helvetica", 20, "bold")).pack(side=tk.LEFT)

        # Export buttons
        export_frame = tk.Frame(header, bg=COLORS["bg"])
        export_frame.pack(side=tk.RIGHT)

        tk.Button(export_frame, text="Export JSON",
                  command=self._export_json,
                  bg=COLORS["tag_bg"], fg=COLORS["text_primary"],
                  relief="flat", font=("Helvetica", 11),
                  padx=12, pady=4).pack(side=tk.LEFT, padx=4)

        tk.Button(export_frame, text="Export Text",
                  command=self._export_text,
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

        tk.Label(filter_frame, text="Filter:",
                 bg=COLORS["bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 11)).pack(side=tk.LEFT)

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
                           command=self._apply_filter
                           ).pack(side=tk.LEFT, padx=8)

        # Module filter
        tk.Label(filter_frame, text="Module:",
                 bg=COLORS["bg"], fg=COLORS["text_secondary"],
                 font=("Helvetica", 11)).pack(side=tk.LEFT, padx=(16, 4))

        self.module_filter_var = tk.StringVar(value="All")
        self.module_filter_combo = ttk.Combobox(filter_frame,
                                                  textvariable=self.module_filter_var,
                                                  state="readonly",
                                                  font=("Helvetica", 11),
                                                  width=15)
        self.module_filter_combo['values'] = ["All"]
        self.module_filter_combo.pack(side=tk.LEFT)
        self.module_filter_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        # ── Results Treeview ──
        tree_frame = tk.Frame(self.content, bg=COLORS["card_bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=pad, pady=(0, 4))

        columns = ("severity", "module", "rule_id", "title", "verified")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                  style="Results.Treeview")

        self.tree.heading("severity", text="Status")
        self.tree.heading("module", text="Module")
        self.tree.heading("rule_id", text="Rule")
        self.tree.heading("title", text="Description")
        self.tree.heading("verified", text="Verified")

        self.tree.column("severity", width=70, minwidth=60)
        self.tree.column("module", width=80, minwidth=60)
        self.tree.column("rule_id", width=80, minwidth=60)
        self.tree.column("title", width=500, minwidth=200)
        self.tree.column("verified", width=80, minwidth=60)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                        command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL,
                                        command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set,
                             xscrollcommand=tree_scroll_x.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.bind("<<TreeviewSelect>>", self._on_result_select)
        self.tree.tag_configure("PASS", background=COLORS["pass_bg"])
        self.tree.tag_configure("FAIL", background=COLORS["fail_bg"])
        self.tree.tag_configure("WARN", background=COLORS["warn_bg"])
        self.tree.tag_configure("INFO", background=COLORS["info_bg"])

        # ── Detail Panel ──
        self.detail_frame = tk.Frame(self.content, bg=COLORS["card_bg"],
                                      relief="flat", bd=0)
        self.detail_frame.pack(fill=tk.X, padx=pad, pady=(0, pad))
        self._build_detail_panel()

    def _build_summary_cards(self):
        """Build summary statistic cards."""
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        cards = [
            ("Total", "0", COLORS["text_primary"], COLORS["card_bg"]),
            ("Pass", "0", COLORS["pass_fg"], COLORS["pass_bg"]),
            ("Fail", "0", COLORS["fail_fg"], COLORS["fail_bg"]),
            ("Warn", "0", COLORS["warn_fg"], COLORS["warn_bg"]),
            ("Info", "0", COLORS["info_fg"], COLORS["info_bg"]),
        ]

        self.summary_labels = {}
        for label, value, fg, bg in cards:
            card = tk.Frame(self.summary_frame, bg=bg, padx=16, pady=8,
                            relief="flat", bd=0)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

            val_label = tk.Label(card, text=value, bg=bg, fg=fg,
                                  font=("Helvetica", 24, "bold"))
            val_label.pack()
            tk.Label(card, text=label, bg=bg, fg=fg,
                     font=("Helvetica", 11)).pack()
            self.summary_labels[label] = val_label

    def _build_detail_panel(self):
        """Build the detail panel for selected result."""
        pad = 12

        # Title
        self.detail_title = tk.Label(self.detail_frame,
                                      text="Select a result to view details",
                                      bg=COLORS["card_bg"],
                                      fg=COLORS["text_secondary"],
                                      font=("Helvetica", 14, "bold"),
                                      wraplength=800, justify=tk.LEFT)
        self.detail_title.pack(anchor=tk.W, padx=pad, pady=(pad, 4))

        # Description
        self.detail_desc = tk.Text(self.detail_frame,
                                    bg=COLORS["card_bg"],
                                    fg=COLORS["text_primary"],
                                    font=("Helvetica", 11),
                                    height=5, wrap=tk.WORD,
                                    relief="flat", bd=0)
        self.detail_desc.pack(fill=tk.X, padx=pad, pady=(0, 4))
        self.detail_desc.config(state=tk.DISABLED)

        # Meta info
        self.detail_meta = tk.Label(self.detail_frame, text="",
                                     bg=COLORS["card_bg"],
                                     fg=COLORS["text_secondary"],
                                     font=("Helvetica", 10),
                                     wraplength=800, justify=tk.LEFT)
        self.detail_meta.pack(anchor=tk.W, padx=pad, pady=(0, 4))

        # Verify buttons
        verify_frame = tk.Frame(self.detail_frame, bg=COLORS["card_bg"])
        verify_frame.pack(anchor=tk.W, padx=pad, pady=(0, pad))

        self.verify_accept_btn = tk.Button(
            verify_frame, text="Confirm (Verified)",
            command=lambda: self._verify_result(True),
            bg=COLORS["verify_yes"], fg="white",
            relief="flat", font=("Helvetica", 11, "bold"),
            padx=12, pady=4)
        self.verify_accept_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.verify_reject_btn = tk.Button(
            verify_frame, text="Reject (False Positive)",
            command=lambda: self._verify_result(False),
            bg=COLORS["verify_no"], fg="white",
            relief="flat", font=("Helvetica", 11, "bold"),
            padx=12, pady=4)
        self.verify_reject_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.verify_reset_btn = tk.Button(
            verify_frame, text="Reset",
            command=lambda: self._verify_result(None),
            bg=COLORS["tag_bg"], fg=COLORS["text_secondary"],
            relief="flat", font=("Helvetica", 11),
            padx=12, pady=4)
        self.verify_reset_btn.pack(side=tk.LEFT)

    def _populate_modules(self):
        """Populate module listbox based on selected version."""
        self.module_listbox.delete(0, tk.END)
        version = self.version_var.get()
        modules = self.registry.get_supported_modules(version)
        for mod in modules:
            self.module_listbox.insert(tk.END, mod)

    def _on_version_change(self):
        self._populate_modules()

    def _browse_path(self):
        path = filedialog.askdirectory(title="Select BSW Source Directory")
        if path:
            self.path_var.set(path)

    def _select_all_modules(self):
        self.module_listbox.select_set(0, tk.END)

    def _clear_module_selection(self):
        self.module_listbox.selection_clear(0, tk.END)

    def _run_checks(self):
        """Run verification in a background thread."""
        target = self.path_var.get()
        if not target or not os.path.isdir(target):
            messagebox.showerror("Error", "Please select a valid BSW source directory.")
            return

        version = self.version_var.get()
        selected_indices = self.module_listbox.curselection()
        modules = None
        if selected_indices:
            modules = [self.module_listbox.get(i) for i in selected_indices]

        self.run_btn.config(state=tk.DISABLED, text="Running...")
        self.root.update()

        def _do_check():
            try:
                self.reporter = run_checks(target, version, modules)
                self.results = self.reporter.get_results_for_gui()
                self.root.after(0, self._display_results)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, lambda: self.run_btn.config(
                    state=tk.NORMAL, text="Run Verification"))

        threading.Thread(target=_do_check, daemon=True).start()

    def _display_results(self):
        """Display results in the treeview."""
        # Update summary
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

        # Update module filter
        modules = sorted(set(r["module"] for r in self.results))
        self.module_filter_combo['values'] = ["All"] + modules

        self._apply_filter()

    def _apply_filter(self):
        """Apply severity and module filters to results."""
        self.tree.delete(*self.tree.get_children())

        severity_filter = self.filter_var.get()
        module_filter = self.module_filter_var.get()

        self.current_results = []
        for i, r in enumerate(self.results):
            if severity_filter != "all" and r["severity"] != severity_filter:
                continue
            if module_filter != "All" and r["module"] != module_filter:
                continue
            self.current_results.append((i, r))

        for idx, (orig_idx, r) in enumerate(self.current_results):
            verified_text = ""
            if r["verified"] is True:
                verified_text = "Confirmed"
            elif r["verified"] is False:
                verified_text = "Rejected"

            self.tree.insert("", tk.END,
                              iid=str(idx),
                              values=(r["severity"], r["module"],
                                      r["rule_id"], r["title"],
                                      verified_text),
                              tags=(r["severity"],))

    def _on_result_select(self, event):
        """Handle result selection in treeview."""
        selection = self.tree.selection()
        if not selection:
            return

        idx = int(selection[0])
        if idx >= len(self.current_results):
            return

        orig_idx, r = self.current_results[idx]

        # Update detail panel
        self.detail_title.config(
            text=f"[{r['severity']}] [{r['rule_id']}] {r['title']}",
            fg=COLORS.get(f"{r['severity'].lower()}_fg", COLORS["text_primary"]))

        self.detail_desc.config(state=tk.NORMAL)
        self.detail_desc.delete("1.0", tk.END)
        self.detail_desc.insert("1.0", r["description"])
        self.detail_desc.config(state=tk.DISABLED)

        meta_parts = []
        if r["file_path"]:
            loc = r["file_path"]
            if r["line_number"]:
                loc += f":{r['line_number']}"
            meta_parts.append(f"Location: {loc}")
        if r["expected"]:
            meta_parts.append(f"Expected: {r['expected']}")
        if r["actual"]:
            meta_parts.append(f"Actual: {r['actual']}")
        if r["suggestion"]:
            meta_parts.append(f"Suggestion: {r['suggestion']}")
        if r["autosar_ref"]:
            meta_parts.append(f"AUTOSAR Ref: {r['autosar_ref']}")

        self.detail_meta.config(text="\n".join(meta_parts))

    def _verify_result(self, verified):
        """Set verification status for selected result."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a result to verify.")
            return

        idx = int(selection[0])
        if idx >= len(self.current_results):
            return

        orig_idx, r = self.current_results[idx]
        self.results[orig_idx]["verified"] = verified

        # Update treeview
        verified_text = ""
        if verified is True:
            verified_text = "Confirmed"
        elif verified is False:
            verified_text = "Rejected"

        self.tree.set(selection[0], "verified", verified_text)

    def _export_json(self):
        if not self.reporter:
            messagebox.showinfo("Info", "No results to export. Run verification first.")
            return

        path = filedialog.asksaveasfilename(
            title="Export JSON Report",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            # Include verification statuses
            data = json.loads(self.reporter.format_json())
            for i, result in enumerate(data.get("results", [])):
                if i < len(self.results):
                    result["verified"] = self.results[i]["verified"]

            Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                   encoding='utf-8')
            messagebox.showinfo("Export", f"Report exported to {path}")

    def _export_text(self):
        if not self.reporter:
            messagebox.showinfo("Info", "No results to export. Run verification first.")
            return

        path = filedialog.asksaveasfilename(
            title="Export Text Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            Path(path).write_text(
                self.reporter.format_console(show_pass=True, show_info=True),
                encoding='utf-8')
            messagebox.showinfo("Export", f"Report exported to {path}")

    def run(self):
        self.root.mainloop()


def launch_gui():
    """Launch the GUI application."""
    app = BSWCheckerApp()
    app.run()
