"""Build an ordered PDF without holding all source photos in memory."""
from collections.abc import Iterable
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image


def build_pdf(pages: Iterable[np.ndarray], destination: Path, *, quality: int = 92,
              scale: float = 1.0) -> Path:
    """Encode ordered pages, preserving their nominal print size when downsampling."""
    try:
        import img2pdf
    except ModuleNotFoundError as exc:
        if exc.name != "img2pdf":
            raise
        img2pdf = None
    with TemporaryDirectory(dir=destination.parent) as directory:
        staging = Path(directory)
        output = staging / "document.pdf"
        encoded = []
        count = 0
        for count, array in enumerate(pages, 1):
            image = Image.fromarray(array)
            if scale != 1:
                size = tuple(max(1, round(dim * scale)) for dim in image.size)
                image = image.resize(size, Image.Resampling.LANCZOS)
            dpi = max(1, round(200 * scale))
            if img2pdf is None:
                image.save(output, "PDF", append=count > 1, resolution=dpi, quality=quality)
            else:
                path = staging / f"{count}.jpg"
                image.save(path, quality=quality, dpi=(dpi, dpi))
                encoded.append(str(path))
        if not count:
            raise ValueError("Add at least one photo before exporting.")
        if img2pdf is not None:
            with output.open("wb") as stream:
                img2pdf.convert(*encoded, outputstream=stream)
        output.replace(destination)
    return destination

def _write_selection(sources: list[Path], destination: Path,
                     span: tuple[int, int] | None = None) -> Path:
    if any(path.resolve() == destination.resolve() for path in sources):
        raise ValueError("Choose an output filename different from the source PDFs.")
    with TemporaryDirectory(dir=destination.parent) as directory:
        staging = Path(directory)
        output = staging / "output.pdf"
        try:
            from pypdf import PdfWriter, PdfReader
        except ImportError as exc:
            raise ValueError("Install the PDF editing dependency with: python -m pip install pypdf") from exc
        writer = PdfWriter()
        try:
            for source in sources:
                reader = PdfReader(source)
                if span and span[1] > len(reader.pages):
                    raise ValueError("Page range exceeds this PDF.")
                writer.append(reader, pages=(span[0]-1, span[1]) if span else None)
            writer.write(str(output))
        finally:
            writer.close()
        output.replace(destination)
    return destination


def merge_pdfs(sources: list[Path], destination: Path) -> Path:
    """Join source PDFs in the specified order."""
    if len(sources) < 2:
        raise ValueError("Choose at least two PDFs.")
    return _write_selection(sources, destination)


def split_pdf(source: Path, destination: Path, first: int, last: int) -> Path:
    """Export an inclusive, one-based page range."""
    if first < 1 or last < first:
        raise ValueError("Enter a valid range, such as 1-3.")
    return _write_selection([source], destination, (first, last))
