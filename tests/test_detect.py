import numpy as np
from PIL import Image, ImageDraw

from scanpdf.core.detect import detect_corners


def test_detect_scaled() -> None:
    """Corners map back to the large source canvas."""
    quad = [(240,120),(1560,220),(1410,990),(150,910)]
    photo = Image.new("RGB", (1800, 1100))
    ImageDraw.Draw(photo).polygon(quad, fill="white")
    np.testing.assert_allclose(detect_corners(np.asarray(photo)), quad, atol=7)


def test_blank() -> None:
    """A uniform frame requests manual corners."""
    assert detect_corners(np.zeros((120, 160), dtype=np.uint8)) is None
