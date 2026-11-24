"""Find paper boundaries on a smaller working image."""
import cv2
import numpy as np

from .transform import order_points


def detect_corners(image: np.ndarray) -> np.ndarray | None:
    """Find a prominent four-sided document in an RGB or grayscale uint8 image."""
    h, w = image.shape[:2]
    if min(h, w) < 2:
        return None
    scale = min(1.0, 1000 / max(h, w))
    size = (max(1, round(w * scale)), max(1, round(h * scale)))
    small = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY) if small.ndim == 3 else small
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 40, 120)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        if cv2.contourArea(contour) < max(4, gray.size * 0.05):
            break
        poly = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        if len(poly) == 4 and cv2.isContourConvex(poly):
            return order_points(poly.reshape(4, 2) * [w / size[0], h / size[1]])
    return None
