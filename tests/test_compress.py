from pathlib import Path

import numpy as np
import pytest
from pdf_helpers import page_widths

from scanpdf.core.compress import compress_pdf


@pytest.mark.parametrize("limit,stage", [(2, "original"), (0.12, "quality"), (0.03, "resize")])
def test_compression_stages(tmp_path: Path, limit: float, stage: str) -> None:
    """Measure real PDF bytes and verify the expected compression stage."""
    path = tmp_path / "pages.pdf"
    rng = np.random.default_rng(19)
    pages = (rng.integers(0, 256, (350, 400, 3), dtype=np.uint8) for _ in range(2))
    result = compress_pdf(pages, path, limit)
    assert result.size_bytes == path.stat().st_size <= limit * 1_000_000
    actual = "resize" if result.scale < 1 else "quality" if result.quality < 92 else "original"
    assert actual == stage
    assert len(page_widths(path)) == 2


def test_unreachable_limit(tmp_path: Path) -> None:
    """An unsuccessful attempt preserves the previous export."""
    dest = tmp_path / "existing.pdf"
    dest.write_bytes(b"previous")
    with pytest.raises(ValueError, match="Smallest attempt"):
        compress_pdf([np.zeros((80, 90), np.uint8)], dest, 0.0001)
    assert dest.read_bytes() == b"previous"
