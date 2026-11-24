from itertools import permutations

import numpy as np
import pytest

from scanpdf.core.transform import flatten_document, order_points


def test_corner_order() -> None:
    """Every permutation produces the same clockwise order."""
    corners = [[4, 8], [86, 5], [92, 70], [1, 63]]
    for permutation in permutations(corners):
        np.testing.assert_array_equal(order_points(permutation), corners)


def test_identity_size_and_pixels() -> None:
    """A full-frame crop preserves both dimensions and orientation."""
    image = np.arange(40 * 60, dtype=np.uint8).reshape(40, 60)
    actual = flatten_document(image, np.float32([[59,39],[0,0],[0,39],[59,0]]))
    np.testing.assert_array_equal(actual, image)


def test_collapsed_quad() -> None:
    """Duplicate handles have no valid perspective transform."""
    with pytest.raises(ValueError):
        order_points(np.zeros((4, 2)))
