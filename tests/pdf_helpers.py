"""Read test PDFs with the production parser when available."""
from pathlib import Path
from PIL import PdfParser


def page_widths(path: Path) -> list[float]:
    """Read page widths in document order."""
    try:
        from pypdf import PdfReader
    except ImportError:
        with PdfParser.PdfParser(buf=path.read_bytes()) as pdf:
            return [float(pdf.read_indirect(ref)[b"MediaBox"][2]) for ref in pdf.pages]
    return [float(page.mediabox.width) for page in PdfReader(path).pages]
