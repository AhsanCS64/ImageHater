"""Multi-page photo workspace for ScanPDF."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections.abc import Callable

import numpy as np
from PIL import Image, ImageOps, ImageTk

from ..core.detect import detect_corners
from ..core.enhance import enhance
from ..core.compress import ExportResult, compress_pdf
from ..core.transform import flatten_document
from .layout import build_workspace, MODES as MODE_LABELS
from .pdf_tools import merge_dialog, split_dialog


@dataclass
class Page:
    """Keep compact previews and editable corners for one source photo."""
    path: Path
    size: tuple[int, int]
    preview: Image.Image
    points: np.ndarray
    detected: bool
    flat: Image.Image | None = None
    mode: str = "original"


def _read(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def _load(path: Path) -> Page:
    image = _read(path)
    w, h = image.size
    points = detect_corners(np.asarray(image))
    detected = points is not None
    if points is None:
        points = np.float32([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]])
    image.thumbnail((1200, 1200))
    return Page(path, (w, h), image, points, detected)


def _flatten(page: Page) -> Image.Image:
    source = _read(page.path)
    if source.size != page.size:
        raise ValueError("The source dimensions changed. Add the photo again.")
    return Image.fromarray(enhance(flatten_document(np.asarray(source), page.points), page.mode))


class Workspace:
    """Manage page order, selection and asynchronous image operations."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("ScanPDF")
        root.geometry("1000x680")
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.pages: dict[str, Page] = {}
        self.icons = {}
        self.busy = False
        build_workspace(self)
        root.protocol("WM_DELETE_WINDOW", self._close)

    def _merge(self) -> None:
        if not self.busy:
            merge_dialog(self.root, self._work, self.status.set)

    def _split(self) -> None:
        if not self.busy:
            split_dialog(self.root, self._work, self.status.set)

    def _close(self) -> None:
        self.pool.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()

    def _selected(self) -> Page | None:
        selection = self.tree.selection()
        return self.pages.get(selection[0]) if selection else None

    def _display(self) -> None:
        page = self._selected()
        if page:
            self.mode.set(next(label for label, mode in MODE_LABELS.items() if mode == page.mode))
            self.title.configure(text=page.path.name)
            self.tray_title.configure(text=f"Pages  ·  {len(self.pages)}")
            if page.flat is None:
                self.editor.show(page.preview, page.size, page.points)
            else:
                self.editor.show(page.flat, page.flat.size, None)
            if not self.busy:
                self.status.set("Flattened preview" if page.flat else
                                "Drag corners to adjust" if page.detected else
                                "No document found. Position the four handles.")

    def _changed(self) -> None:
        self.status.set("Corners adjusted")

    def _set_mode(self, event: tk.Event) -> None:
        page = self._selected()
        if page and not self.busy:
            page.mode = MODE_LABELS[self.mode.get()]
            page.flat = None
            self._preview()

    def _export(self) -> None:
        if self.busy or not self.pages:
            return
        raw = self.max_mb.get().strip()
        try:
            limit = float(raw) if raw else None
            if limit is not None and (not np.isfinite(limit) or limit <= 0):
                raise ValueError
        except ValueError:
            messagebox.showerror("ScanPDF", "Enter a positive size in MB or leave it blank.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not filename:
            return
        destination = Path(filename)
        if destination.suffix.lower() != ".pdf":
            messagebox.showerror("ScanPDF", "Choose a filename ending in .pdf.")
            return
        ordered = [replace(self.pages[key], points=self.pages[key].points.copy())
                   for key in self.tree.get_children()]
        def export() -> ExportResult:
            return compress_pdf((np.asarray(_flatten(page)) for page in ordered), destination, limit)

        def report(result: ExportResult) -> None:
            self.status.set(f"Saved {destination.name}")
            messagebox.showinfo("PDF exported", f"{destination.name}\n{len(ordered)} pages · "
                                f"{result.size_bytes:,} bytes\nJPEG quality {result.quality}/100 · "
                                f"{result.scale:.0%} dimensions", parent=self.root)

        self._work("Exporting PDF…", export,
                   report)

    def _work(self, label: str, task: Callable, done: Callable) -> None:
        self.busy = True
        self.mode.configure(state="disabled")
        self.editor.configure(state="disabled")
        self.progress.pack(side="left", padx=6)
        self.progress.start()
        self.status.set(label)
        future = self.pool.submit(task)

        def poll() -> None:
            if not future.done():
                self.root.after(40, poll)
                return
            self.busy = False
            self.mode.configure(state="readonly")
            self.progress.stop()
            self.progress.pack_forget()
            self.editor.configure(state="normal")
            try:
                result = future.result()
            except Exception as exc:
                self._display()
                self.status.set("Operation failed")
                messagebox.showerror("ScanPDF", str(exc), parent=self.root)
            else:
                done(result)

        self.root.after(40, poll)

    def _add(self) -> None:
        if self.busy:
            return
        paths = filedialog.askopenfilenames(filetypes=[("Photos", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp"), ("All files", "*")])
        if not paths:
            return

        def load_batch() -> tuple[list[Page], list[str]]:
            pages, errors = [], []
            for path in map(Path, paths):
                try:
                    pages.append(_load(path))
                except Exception as exc:
                    errors.append(f"{path.name}: {exc}")
            return pages, errors

        def insert(result: tuple[list[Page], list[str]]) -> None:
            pages, errors = result
            first = None
            for page in pages:
                thumb = page.preview.copy()
                thumb.thumbnail((48, 48))
                icon = ImageTk.PhotoImage(thumb)
                key = self.tree.insert("", "end", text=page.path.name, image=icon)
                self.pages[key], self.icons[key] = page, icon
                first = first or key
            if first:
                self.tree.selection_set(first)
                self.tree.see(first)
            self.status.set("Ready")
            self._display()
            if errors:
                messagebox.showwarning("Unreadable photos", "\n".join(errors))

        self._work(f"Opening {len(paths)} photo(s)…", load_batch, insert)

    def _move(self, offset: int) -> None:
        selection = self.tree.selection()
        if selection:
            key = selection[0]
            index = self.tree.index(key) + offset
            if 0 <= index < len(self.pages):
                self.tree.move(key, "", index)
                self.tree.see(key)

    def _edit(self) -> None:
        page = self._selected()
        if page and not self.busy:
            page.flat = None
            self._display()

    def _preview(self) -> None:
        page = self._selected()
        if page is None or self.busy:
            return
        def preview() -> Image.Image:
            image = _flatten(page)
            image.thumbnail((1200, 1200))
            return image

        def show(image: Image.Image) -> None:
            page.flat = image
            self._display()

        self._work("Flattening…", preview, show)

    def _save(self) -> None:
        page = self._selected()
        if page is None or self.busy:
            return
        filename = filedialog.asksaveasfilename(defaultextension=".png", initialfile=page.path.stem+"-flat.png",
                                                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if filename:
            dest = Path(filename)
            if any(dest.resolve() == p.path.resolve() for p in self.pages.values()):
                messagebox.showerror("ScanPDF", "Choose a different filename to preserve the source photo.")
                return
            self._work("Saving…", lambda: _flatten(page).save(dest),
                       lambda _: self.status.set(f"Saved {dest.name}"))


def main() -> None:
    """Open the ScanPDF desktop application."""
    root = tk.Tk()
    Workspace(root)
    root.mainloop()
