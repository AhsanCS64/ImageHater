"""Desktop dialogs for working with existing PDFs."""
from collections.abc import Callable
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from ..core.pdf import merge_pdfs, split_pdf

PDF = [("PDF documents", "*.pdf")]


def merge_dialog(root: tk.Tk, work: Callable, status: Callable) -> None:
    """Let the user arrange source PDFs before merging them."""
    paths = list(map(Path, filedialog.askopenfilenames(parent=root, filetypes=PDF)))
    if not paths:
        return
    if len(paths) < 2:
        messagebox.showinfo("Merge PDFs", "Select at least two PDFs together.", parent=root)
        return
    window = tk.Toplevel(root)
    window.title("Merge order")
    window.transient(root)
    window.grab_set()
    panel = ttk.Frame(window, padding=16)
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="Merge order", font=("Georgia", 17)).pack(anchor="w")
    items = tk.Listbox(panel, width=62, height=min(10,len(paths)), exportselection=False)
    items.pack(fill="x", pady=10)
    def refresh(index: int) -> None:
        items.delete(0, "end")
        for path in paths:
            items.insert("end", str(path))
        items.selection_set(index)
        items.see(index)
    def move(offset: int) -> None:
        index = items.curselection()[0]
        target = index + offset
        if 0 <= target < len(paths):
            paths[index], paths[target] = paths[target], paths[index]
            refresh(target)
    def save() -> None:
        name = filedialog.asksaveasfilename(parent=window, filetypes=PDF, defaultextension=".pdf")
        if name:
            window.destroy()
            work("Merging PDFs…", lambda: merge_pdfs(paths, Path(name)), lambda p: status(f"Saved {p.name}"))
    refresh(0)
    for label, command in [("Up", lambda: move(-1)), ("Down", lambda: move(1)), ("Merge and save", save)]:
        ttk.Button(panel, text=label, command=command).pack(side="left", padx=2)


def split_dialog(root: tk.Tk, work: Callable, status: Callable) -> None:
    """Ask for the source, inclusive page range and output location."""
    source = filedialog.askopenfilename(parent=root, filetypes=PDF)
    if not source:
        return
    value = simpledialog.askstring("Split PDF", "Pages to extract (for example 2-5 or 3)", parent=root)
    if value is None:
        return
    try:
        parts = value.split("-", 1)
        first, last = int(parts[0]), int(parts[-1])
        if first < 1 or last < first:
            raise ValueError
    except ValueError:
        messagebox.showerror("Split PDF", "Enter a page number or an ascending range.", parent=root)
        return
    name = filedialog.asksaveasfilename(parent=root, filetypes=PDF, defaultextension=".pdf")
    if name:
        work("Extracting pages…", lambda: split_pdf(Path(source), Path(name), first, last),
             lambda p: status(f"Saved {p.name}"))
