import logging
import subprocess
from collections import Counter
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


def _filter_ads(images: list[Path]) -> list[Path]:
    """Remove promo/ad images by filtering out images whose width differs from the majority."""
    if len(images) <= 1:
        return images
    widths = [Image.open(p).size[0] for p in images]
    most_common_width = Counter(widths).most_common(1)[0][0]
    filtered = [p for p, w in zip(images, widths) if w == most_common_width]
    if len(filtered) < len(images):
        logger.info("Filtered %d ad/promo images (width != %d)", len(images) - len(filtered), most_common_width)
    return filtered


def download_chapter(url: str, chapter: int, output_dir: str) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "webtoon-downloader", url,
            "--start", str(chapter),
            "--end", str(chapter),
            "--separate",
            "--out", str(out),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"webtoon-downloader failed:\n{result.stderr}")

    images = sorted(
        p for p in out.rglob("*")
        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    )
    if not images:
        raise RuntimeError(f"No images found in {out} after download")

    images = _filter_ads(images)
    logger.info("Downloaded %d images to %s", len(images), out)
    return images
