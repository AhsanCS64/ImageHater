"""Classic document cleanup for uint8 RGB arrays."""
import cv2
import numpy as np

MODES = ("original", "grayscale", "black_and_white", "color_boost")


def enhance(image: np.ndarray, mode: str = "original") -> np.ndarray:
    """Return a cleaned RGB or single-channel image without changing the source."""
    if mode == "original":
        return image.copy()
    if mode == "color_boost":
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        lab[:, :, 0] = cv2.createCLAHE(2.0, (8, 8)).apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    if mode == "grayscale":
        return gray
    if mode == "black_and_white":
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 31, 11)
    raise ValueError(f"Unknown enhancement mode: {mode}")
