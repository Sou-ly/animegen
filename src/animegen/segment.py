from pathlib import Path

import cv2
import numpy as np


def _detect_text_rows(image_path: Path, ocr, padding: int = 15) -> np.ndarray:
    """Run OCR on an image and return a boolean mask of rows that contain text."""
    img = cv2.imread(str(image_path))
    h = img.shape[0]
    has_text = np.zeros(h, dtype=bool)

    for res in ocr.predict(str(image_path)):
        for poly in res['dt_polys']:
            ymin = max(0, int(min(p[1] for p in poly)) - padding)
            ymax = min(h, int(max(p[1] for p in poly)) + padding)
            has_text[ymin:ymax] = True

    return has_text


def _segment_single_image(image_path: Path, cfg: dict, text_rows: np.ndarray) -> list[np.ndarray]:
    img = cv2.imread(str(image_path))
    if img is None:
        raise RuntimeError(f"Failed to read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    blank_mask = gray > cfg["gap_threshold"]
    row_blank_ratio = blank_mask.sum(axis=1) / w

    # A row is a gap candidate only if it's blank AND has no text
    is_gap = (row_blank_ratio > cfg["blank_row_ratio"]) & ~text_rows

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


def _is_mostly_blank(panel: np.ndarray, threshold: int = 240, ratio: float = 0.85) -> bool:
    gray = cv2.cvtColor(panel, cv2.COLOR_BGR2GRAY)
    return (gray > threshold).sum() / gray.size > ratio


def _init_ocr():
    import logging
    logging.disable(logging.DEBUG)
    from paddleocr import PaddleOCR
    return PaddleOCR(lang='en')


def segment_panels(image_paths: list[Path], output_dir: str, cfg: dict) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    max_blank = cfg.get("max_blank_ratio", 0.85)

    print("Loading OCR model for text detection...")
    ocr = _init_ocr()

    panel_paths = []
    panel_idx = 0

    for i, image_path in enumerate(image_paths):
        text_rows = _detect_text_rows(image_path, ocr, padding=cfg.get("text_padding", 15))
        panels = _segment_single_image(image_path, cfg, text_rows)
        for panel in panels:
            if _is_mostly_blank(panel, cfg["gap_threshold"], max_blank):
                continue
            panel_file = out / f"panel_{panel_idx:04d}.png"
            cv2.imwrite(str(panel_file), panel)
            panel_paths.append(panel_file)
            panel_idx += 1
        if (i + 1) % 10 == 0 or i == len(image_paths) - 1:
            print(f"  Processed {i+1}/{len(image_paths)} strips ({panel_idx} panels so far)")

    print(f"Segmented {len(image_paths)} images into {len(panel_paths)} panels")
    return panel_paths
