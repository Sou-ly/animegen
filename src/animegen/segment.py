import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _segment_single_image(image_path: Path, cfg: dict) -> list[np.ndarray]:
    img = cv2.imread(str(image_path))
    if img is None:
        raise RuntimeError(f"Failed to read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    blank_mask = gray > cfg["gap_threshold"]
    row_blank_ratio = blank_mask.sum(axis=1) / w

    is_gap = row_blank_ratio > cfg["blank_row_ratio"]

    panels = []
    panel_start = 0
    in_gap = False
    gap_start = 0
    min_gap = cfg["min_gap_height"]
    min_panel = cfg["min_panel_height"]

    for y in range(h):
        if is_gap[y] and not in_gap:
            gap_start = y
            in_gap = True
        elif not is_gap[y] and in_gap:
            if (y - gap_start) >= min_gap:
                panel = img[panel_start:gap_start]
                if panel.shape[0] >= min_panel:
                    panels.append(panel)
                panel_start = y
            in_gap = False

    last_panel = img[panel_start:h]
    if last_panel.shape[0] >= min_panel:
        panels.append(last_panel)

    return panels


def _is_all_white(panel: np.ndarray, threshold: int = 250) -> bool:
    gray = cv2.cvtColor(panel, cv2.COLOR_BGR2GRAY)
    return bool(np.all(gray > threshold))


def _is_mostly_blank(panel: np.ndarray, threshold: int = 240, ratio: float = 0.85) -> bool:
    gray = cv2.cvtColor(panel, cv2.COLOR_BGR2GRAY)
    return (gray > threshold).sum() / gray.size > ratio


def _panels_similar(panel1: np.ndarray, panel2: np.ndarray, threshold: float = 0.7) -> bool:
    hist1 = cv2.calcHist([panel1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist2 = cv2.calcHist([panel2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)
    return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL) > threshold


def _merge_similar_panels(panels: list[np.ndarray], cfg: dict) -> list[np.ndarray]:
    if len(panels) < 2:
        return panels

    sim_threshold = cfg.get("similarity_threshold", 0.7)
    merged = []
    current = panels[0]

    for next_panel in panels[1:]:
        if _is_all_white(current) or _is_all_white(next_panel):
            merged.append(current)
            current = next_panel
        elif _panels_similar(current, next_panel, sim_threshold):
            current = np.vstack([current, next_panel])
        else:
            merged.append(current)
            current = next_panel

    merged.append(current)
    return merged


def segment_panels(image_paths: list[Path], output_dir: str, cfg: dict) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    max_blank = cfg.get("max_blank_ratio", 0.85)

    panel_paths = []
    panel_idx = 0

    for i, image_path in enumerate(image_paths):
        panels = _segment_single_image(image_path, cfg)
        panels = _merge_similar_panels(panels, cfg)

        for panel in panels:
            if _is_mostly_blank(panel, cfg["gap_threshold"], max_blank):
                continue
            panel_file = out / f"panel_{panel_idx:04d}.png"
            cv2.imwrite(str(panel_file), panel)
            panel_paths.append(panel_file)
            panel_idx += 1

        if (i + 1) % 10 == 0 or i == len(image_paths) - 1:
            logger.info("Processed %d/%d strips (%d panels so far)", i + 1, len(image_paths), panel_idx)

    logger.info("Segmented %d images into %d panels", len(image_paths), len(panel_paths))
    return panel_paths
