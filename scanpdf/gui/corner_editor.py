"""Aspect-preserving preview with draggable source-image coordinates."""
import tkinter as tk
from collections.abc import Callable

import numpy as np
from PIL import Image, ImageTk


def fit_box(source: tuple[int, int], view: tuple[int, int]) -> tuple[int, int, int, int]:
    """Return left, top, width and height of a centered image."""
    w, h = source
    vw, vh = view
    scale = min(vw / w, vh / h)
    width, height = max(1, round(w * scale)), max(1, round(h * scale))
    return (vw-width)//2, (vh-height)//2, width, height


class CornerEditor(tk.Canvas):
    """Display a bounded preview and edit corners in original pixel units."""

    def __init__(self, parent: tk.Widget, changed: Callable[[], None]) -> None:
        super().__init__(parent, bg="#173c36", highlightthickness=0, width=400, height=300)
        self.changed = changed
        self.preview = None
        self.points = None
        self.active = None
        self.bind("<Configure>", lambda _: self._draw())
        self.bind("<Button-1>", self._press)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", lambda _: setattr(self, "active", None))

    def show(self, preview: Image.Image, size: tuple[int, int], points: np.ndarray | None) -> None:
        """Show a preview with optional editable source-space points."""
        self.preview, self.source, self.points = preview, size, points
        self.active = None
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if self.preview is None:
            x, y = width/2, height/2-25
            for inset in range(0, 210, 14):
                self.create_oval(-220-inset, height-110-inset, 120+inset, height+180+inset,
                                 outline="#285047")
                self.create_oval(width-105-inset, -240-inset, width+185+inset, 70+inset,
                                 outline="#285047")
            self.create_polygon(x-70,y-43,x+14,y-69,x+54,y+35,x-32,y+60, fill="#68967d")
            self.create_polygon(x-55,y-52,x+26,y-60,x+43,y+46,x-40,y+55, fill="#bdcdb3")
            self.create_polygon(x-40,y-59,x+23,y-59,x+44,y-38,x+44,y+48,x-40,y+48,
                                fill="#f8efda")
            self.create_polygon(x+23,y-59,x+23,y-38,x+44,y-38,fill="#dfc997")
            for dy, length in [(-25,37),(-10,52),(0,44),(10,51),(20,30)]:
                self.create_line(x-26,y+dy,x-26+length,y+dy,fill="#6a8973",width=2)
            self.create_line(x-77,y+27,x+72,y-12,fill="#84e2ae",width=3)
            self.create_text(x,y+84,text="Your document workspace",font=("Georgia",20),fill="#fff5de")
            self.create_text(x,y+115,text="Add photos to start scanning",font=("Segoe UI",11),fill="#c0dacc")
            return
        margin = 16
        x, y, w, h = fit_box(self.source, (max(1,width-2*margin), max(1,height-2*margin)))
        x, y = x+margin, y+margin
        self.create_rectangle(x+4,y+5,x+w+4,y+h+5,fill="#0e2c25",outline="")
        self.origin = np.array([x, y])
        self.scale = np.array([max(1, w-1), max(1, h-1)]) / np.maximum(1, np.array(self.source)-1)
        self.photo = ImageTk.PhotoImage(self.preview.resize((w, h), Image.Resampling.BILINEAR))
        self.create_image(x, y, image=self.photo, anchor="nw")
        self._overlay()

    def _overlay(self) -> None:
        self.delete("handles")
        if self.points is None:
            return
        coords = self.points * self.scale + self.origin
        self.create_polygon(*coords.flatten(), outline="#2deab0", fill="", width=3, tags="handles")
        for x, y in coords:
            self.create_oval(x-7, y-7, x+7, y+7, fill="white", outline="#078963", width=3, tags="handles")

    def _press(self, event: tk.Event) -> None:
        if self.points is not None:
            distances = np.linalg.norm(self.points*self.scale+self.origin-[event.x,event.y], axis=1)
            self.active = int(np.argmin(distances)) if min(distances) <= 18 else None

    def _drag(self, event: tk.Event) -> None:
        if self.active is not None:
            self.points[self.active] = np.clip(([event.x,event.y]-self.origin)/self.scale,
                                               0, np.array(self.source)-1)
            self.changed()
            self._overlay()
