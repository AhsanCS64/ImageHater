from pathlib import Path

import numpy as np
import pytest
from pdf_helpers import page_widths

from scanpdf.core.pdf import build_pdf


def test_pdf_page_count_and_order(tmp_path: Path) -> None:
    """Two differing widths identify the exported pages and their order."""
    path = tmp_path / "pages.pdf"
    build_pdf((np.zeros((80, w, 3), np.uint8) for w in (200, 100)), path)
    widths = page_widths(path)
    assert len(widths) == 2
    assert widths[0] == pytest.approx(2 * widths[1])


def test_empty_export_preserves_destination(tmp_path: Path) -> None:
    """A failed export leaves an existing destination intact."""
    path = tmp_path / "pages.pdf"
    path.write_bytes(b"existing")
    with pytest.raises(ValueError):
        build_pdf([], path)
    assert path.read_bytes() == b"existing"


def test_merge_and_split_order(tmp_path: Path) -> None:
    """Extract a range crossing the boundary between merged documents."""
    pytest.importorskip("pypdf")
    from scanpdf.core.pdf import merge_pdfs, split_pdf
    first = build_pdf([np.zeros((140, w), np.uint8) for w in (160, 200)], tmp_path / "first.pdf")
    last = build_pdf([np.zeros((140, 250), np.uint8)], tmp_path / "last.pdf")
    expected = page_widths(first) + page_widths(last)
    merged = merge_pdfs([first, last], tmp_path / "merged.pdf")
    assert page_widths(merged) == expected
    extracted = split_pdf(merged, tmp_path / "extract.pdf", 2, 3)
    assert page_widths(extracted) == expected[1:]
