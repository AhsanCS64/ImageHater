import numpy as np
from scanpdf.core.enhance import MODES, enhance


def test_modes() -> None:
    """Check channel layout, threshold values, contrast and source integrity."""
    image = np.random.default_rng(4).integers(20, 180, (120, 100, 3), dtype=np.uint8)
    source = image.copy()
    original, gray, binary, boosted = [enhance(image, mode) for mode in MODES]
    np.testing.assert_array_equal(original, source)
    np.testing.assert_array_equal(image, source)
    assert gray.shape == binary.shape == image.shape[:2]
    assert set(np.unique(binary)) == {0, 255}
    assert boosted.shape == image.shape and np.any(boosted != source)
