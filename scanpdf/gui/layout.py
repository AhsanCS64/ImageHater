"""Visual layout for the desktop scanning workspace."""
import tkinter as tk
from tkinter import ttk

from .corner_editor import CornerEditor

INK = "#143c36"
GREEN = "#146c54"
PAPER = "#fffdf7"
CREAM = "#f0eee4"
MUTED = "#556a61"
MODES = {"Original color": "original", "Grayscale": "grayscale",
         "Black & white": "black_and_white", "Color boost": "color_boost"}


def _label(parent, text, size=10, color=INK, family="Segoe UI", bold=False):
    return tk.Label(parent, text=text, background=parent["bg"], foreground=color,
                    font=(family, size, "bold" if bold else "normal"), anchor="w")


def _button(parent, text, action, primary=False):
    return ttk.Button(parent, text=text, command=action,
                      style="Primary.TButton" if primary else "Studio.TButton")


def build_workspace(app) -> None:
    """Arrange page management, editing and export in distinct work areas."""
    root = app.root
    root.configure(bg=CREAM)
    root.minsize(800, 540)
    root.geometry("1120x740")
    style = ttk.Style(root)
    style.theme_use("clam")
    for name, bg, fg, hover in [
        ("Studio.TButton", "#e7ede4", INK, "#d1e3d6"),
        ("Primary.TButton", GREEN, "white", "#095440"),
    ]:
        style.configure(name, background=bg, foreground=fg, borderwidth=0,
                        padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.map(name, background=[("pressed", "#508574"), ("active", hover)])
    style.configure("Pages.Treeview", background=PAPER, fieldbackground=PAPER,
                    foreground=INK, rowheight=62, borderwidth=0, font=("Segoe UI", 10))
    style.map("Pages.Treeview", background=[("selected", "#cce8d8")],
              foreground=[("selected", INK)])
    style.configure("TProgressbar", background="#66be92", troughcolor="#e2e8dc")

    banner = tk.Frame(root, bg=INK, padx=22, pady=12)
    banner.pack(fill="x")
    mark = tk.Canvas(banner, width=42, height=44, bg=INK, highlightthickness=0)
    mark.pack(side="left", padx=(0, 10))
    mark.create_polygon(5,10,26,4,35,33,14,40, fill="#82bd99")
    mark.create_polygon(11,8,30,8,37,15,37,37,11,37, fill="#faf1d9")
    for y, end in [(19,32),(24,29),(29,26)]:
        mark.create_line(16,y,end,y,fill=GREEN,width=2)
    _label(banner, "ScanPDF", 25, PAPER, "Georgia").pack(side="left")
    for title, command in [("Split PDF", app._split), ("Merge PDFs", app._merge)]:
        _button(banner, title, command).pack(side="right", padx=3)

    bottom = tk.Frame(root, bg="#e2e7db", padx=16, pady=5)
    bottom.pack(side="bottom", fill="x")
    app.status = tk.StringVar(value="Ready")
    _label(bottom, "●", 10, GREEN).pack(side="left", padx=(0,6))
    tk.Label(bottom, textvariable=app.status, bg=bottom["bg"], fg=INK).pack(side="left")
    app.progress = ttk.Progressbar(bottom, mode="indeterminate", length=85)
    footer = tk.Frame(root, bg=PAPER, padx=16, pady=9)
    footer.pack(side="bottom", fill="x")
    _label(footer, "PDF export", 16, INK, "Georgia").pack(side="left")
    app.max_mb = tk.StringVar(value="2")
    _button(footer, "Export PDF", app._export, True).pack(side="right", padx=(12,0))
    ttk.Entry(footer, textvariable=app.max_mb, width=6).pack(side="right")
    _label(footer, "Size limit (MB)").pack(side="right", padx=8)

    body = tk.Frame(root, bg=CREAM)
    body.pack(fill="both", expand=True, padx=12, pady=12)
    rail = tk.Frame(body, bg=PAPER, width=220, padx=10, pady=10)
    rail.pack(side="left", fill="y", padx=(0,10))
    rail.pack_propagate(False)
    app.tray_title = _label(rail, "Pages", 18, INK, "Georgia")
    app.tray_title.pack(fill="x")
    _button(rail, "+  Add photos", app._add, True).pack(fill="x", pady=(10,8))
    controls = tk.Frame(rail, bg=PAPER)
    controls.pack(side="bottom", fill="x", pady=(8,0))
    for label, offset in [("↑ Up", -1), ("↓ Down", 1)]:
        _button(controls, label, lambda n=offset: app._move(n)).pack(side="left", expand=True, fill="x", padx=1)
    app.tree = ttk.Treeview(rail, show="tree", selectmode="browse", style="Pages.Treeview")
    app.tree.column("#0", width=145, minwidth=50)
    scroll = ttk.Scrollbar(rail, command=app.tree.yview)
    scroll.pack(side="right",fill="y")
    app.tree.configure(yscrollcommand=scroll.set)
    app.tree.pack(fill="both", expand=True)
    app.tree.bind("<<TreeviewSelect>>", lambda _: app._display())

    desk = tk.Frame(body, bg=PAPER, padx=10, pady=8)
    desk.pack(side="left", fill="both", expand=True)
    app.title = _label(desk, "Document preview", 18, INK, "Georgia")
    app.title.pack(fill="x", pady=(0,6))
    tools = tk.Frame(desk, bg=PAPER)
    tools.pack(side="bottom", fill="x", pady=(8,0))
    _label(tools, "Finish").pack(side="left", padx=(0,6))
    app.mode = ttk.Combobox(tools, state="readonly", values=list(MODES), width=13)
    app.mode.current(0)
    app.mode.pack(side="left")
    app.mode.bind("<<ComboboxSelected>>", app._set_mode)
    for label, action in [("Save image", app._save), ("Preview", app._preview), ("Corners", app._edit)]:
        _button(tools, label, action).pack(side="right", padx=2)
    app.editor = CornerEditor(desk, app._changed)
    app.editor.pack(fill="both", expand=True)
    root.bind("<Control-o>", lambda _: app._add())
    root.bind("<Control-e>", lambda _: app._export())
