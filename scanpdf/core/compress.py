"""Fit a complete PDF within a decimal megabyte budget."""
from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from .pdf import build_pdf


@dataclass(frozen=True)
class ExportResult:
    """Encoding settings and measured byte count for the saved PDF."""
    size_bytes: int
    quality: int
    scale: float


def compress_pdf(pages: Iterable[np.ndarray], destination: Path,
                 max_mb: float | None) -> ExportResult:
    """Lower JPEG quality first, then resolution, until the complete PDF fits."""
    if max_mb is None:
        build_pdf(pages, destination)
        return ExportResult(destination.stat().st_size, 92, 1.0)
    if not isfinite(max_mb) or max_mb <= 0:
        raise ValueError("Enter a positive, finite size in MB.")
    with TemporaryDirectory(dir=destination.parent) as directory:
        staging = Path(directory)
        sources = []
        for index, page in enumerate(pages):
            source = staging / f"{index}.npy"
            np.save(source, page, allow_pickle=False)
            sources.append(source)
        candidate = staging / "candidate.pdf"
        settings = [(q, 1.0) for q in (92, 80, 65, 50, 35)]
        settings.extend((35, scale) for scale in (0.8, 0.64, 0.5, 0.4, 0.32, 0.25))
        smallest = None
        for quality, scale in settings:
            images = (np.load(source, mmap_mode="r") for source in sources)
            build_pdf(images, candidate, quality=quality, scale=scale)
            size = candidate.stat().st_size
            if size <= max_mb * 1_000_000:
                candidate.replace(destination)
                return ExportResult(size, quality, scale)
            smallest = size if smallest is None else min(smallest, size)
        raise ValueError(f"Could not reach {max_mb:g} MB. Smallest attempt: "
                         f"{smallest:,} bytes. Increase the limit or export fewer pages.")
