import json
import logging
import re
from pathlib import Path
from urllib.parse import urlparse

from animegen.config import load_config
from animegen.download import download_chapter
from animegen.logger import setup as setup_logging
from animegen.segment import segment_panels
from animegen.analyze import analyze_panels
from animegen.generate import generate_videos
from animegen.assemble import assemble_video

logger = logging.getLogger(__name__)

STAGES = ["download", "segment", "analyze", "generate", "assemble"]


def _slug_from_url(url: str) -> str:
    """Extract a filesystem-safe slug from a webtoon URL.

    e.g. https://www.webtoons.com/en/fantasy/tower-of-god/list?title_no=95
         -> 'tower-of-god'
    """
    path = urlparse(url).path  # /en/fantasy/tower-of-god/list
    parts = [p for p in path.strip("/").split("/") if p and p != "list"]
    # The series name is typically the last meaningful segment before /list
    if parts:
        slug = parts[-1]
    else:
        slug = "unknown"
    # Sanitize
    slug = re.sub(r"[^\w\-]", "_", slug)
    return slug


def _make_dirs(cfg: dict, slug: str, chapter: int) -> dict:
    """Build per-series/chapter output directories and return them as a dict."""
    base = Path(cfg.get("output_dir", "./output")) / slug / f"ch{chapter}"
    dirs = {
        "downloads": base / "downloads",
        "panels": base / "panels",
        "analysis": base / "analysis",
        "videos": base / "videos",
        "final": base,
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def _should_run(stage: str, start: str, end: str) -> bool:
    si = STAGES.index(start)
    ei = STAGES.index(end)
    ci = STAGES.index(stage)
    return si <= ci <= ei


def _past_end(stage: str, end: str) -> bool:
    return STAGES.index(stage) > STAGES.index(end)


def _load_images(dirs: dict) -> list[Path]:
    d = dirs["downloads"]
    images = sorted(p for p in d.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
    if not images:
        raise RuntimeError(f"No downloaded images found in {d}")
    return images


def _load_panels(dirs: dict) -> list[Path]:
    d = dirs["panels"]
    panels = sorted(d.glob("panel_*.png"))
    if not panels:
        raise RuntimeError(f"No panel images found in {d}")
    return panels


def _load_analysis(dirs: dict) -> list[dict]:
    p = dirs["analysis"] / "analysis.json"
    if not p.exists():
        raise RuntimeError(f"No analysis file found at {p}")
    return json.loads(p.read_text())


def _load_videos(dirs: dict) -> list[Path]:
    d = dirs["videos"]
    videos = sorted(d.glob("panel_*.mp4"))
    if not videos:
        raise RuntimeError(f"No video files found in {d}")
    return videos


def run_pipeline(url: str, chapter: int, config_path: str = "config.yaml",
                 start_stage: str = "download", end_stage: str = "assemble"):
    cfg = load_config(config_path)
    slug = _slug_from_url(url)
    dirs = _make_dirs(cfg, slug, chapter)

    setup_logging(dirs["final"], chapter)

    logger.info("Project: %s chapter %d", slug, chapter)
    logger.info("Output:  %s", dirs["final"])

    # Stage 1: Download
    if _should_run("download", start_stage, end_stage):
        image_paths = download_chapter(url, chapter, str(dirs["downloads"]))
    elif not _past_end("download", end_stage):
        image_paths = _load_images(dirs)

    # Stage 2: Segment
    if _past_end("segment", end_stage):
        return
    if _should_run("segment", start_stage, end_stage):
        panel_paths = segment_panels(image_paths, str(dirs["panels"]), cfg["segment"])
    else:
        panel_paths = _load_panels(dirs)

    # Stage 3: Analyze
    if _past_end("analyze", end_stage):
        return
    if _should_run("analyze", start_stage, end_stage):
        cfg["analyze"]["output_dir"] = str(dirs["analysis"])
        analysis = analyze_panels(panel_paths, cfg)
    else:
        analysis = _load_analysis(dirs)

    # Stage 4: Generate
    if _past_end("generate", end_stage):
        return
    if _should_run("generate", start_stage, end_stage):
        cfg["generate"]["output_dir"] = str(dirs["videos"])
        video_paths = generate_videos(analysis, cfg)
    else:
        video_paths = _load_videos(dirs)

    # Stage 5: Assemble
    if _should_run("assemble", start_stage, end_stage):
        output_path = dirs["final"] / f"chapter_{chapter}.mp4"
        assemble_video(video_paths, output_path)
        logger.info("Done! Output: %s", output_path)
