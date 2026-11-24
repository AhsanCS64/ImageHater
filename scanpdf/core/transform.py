"""Perspective correction in source-image coordinates."""
import cv2
import numpy as np


def order_points(points: np.ndarray) -> np.ndarray:
    """Return four convex vertices clockwise from the upper-left corner."""
    pts = np.asarray(points, dtype=np.float32)
    if pts.shape != (4, 2) or not np.isfinite(pts).all():
        raise ValueError("Select four finite corner coordinates.")
    hull = cv2.convexHull(pts, clockwise=False).reshape(-1, 2)
    if len(hull) != 4 or cv2.contourArea(hull) < 4:
        raise ValueError("Move the handles to four distinct outer corners.")
    first = np.lexsort((hull[:, 1], hull.sum(axis=1)))[0]
    return np.roll(hull, -first, axis=0)


def flatten_document(image: np.ndarray, points: np.ndarray) -> np.ndarray:
    """Warp the source to a rectangle using the longer opposing edges."""
    quad = order_points(points)
    top, right, bottom, left = np.linalg.norm(quad - np.roll(quad, -1, axis=0), axis=1)
    width = max(2, round(float(max(top, bottom))) + 1)
    height = max(2, round(float(max(left, right))) + 1)
    dst = np.float32([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]])
    matrix = cv2.getPerspectiveTransform(quad, dst)
    return cv2.warpPerspective(image, matrix, (width, height))
