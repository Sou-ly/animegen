import logging
import urllib.request
from pathlib import Path

import fal_client

logger = logging.getLogger(__name__)


def _download_file(url: str, dest: Path):
    urllib.request.urlretrieve(url, str(dest))


def _common_args(gen_cfg: dict) -> dict:
    args = {"duration": gen_cfg["duration"]}
    for key in ("seed", "resolution", "aspect_ratio", "generate_audio"):
        if key in gen_cfg:
            args[key] = gen_cfg[key]
    return args


def generate_videos(analysis: list[dict], cfg: dict) -> list[Path]:
    fal_client.api_key = cfg["fal_api_key"]
    gen_cfg = cfg["generate"]
    output_dir = Path(gen_cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    first_model = gen_cfg.get("first_model", gen_cfg["model"])

    video_paths = []
    previous_video_url = None

    for i, item in enumerate(analysis):
        panel_path = Path(item["panel_path"])
        image_url = fal_client.upload_file(panel_path)

        if i == 0:
            arguments = {
                "prompt": item["video_prompt"],
                "image_url": image_url,
                **_common_args(gen_cfg),
            }
            model = first_model
        else:
            arguments = {
                "prompt": item["video_prompt"],
                "image_urls": [image_url],
                **_common_args(gen_cfg),
            }
            if previous_video_url:
                arguments["video_urls"] = [previous_video_url]
            model = gen_cfg["model"]

        result = fal_client.subscribe(model, arguments=arguments)

        video_url = result["video"]["url"]
        video_file = output_dir / f"panel_{item['panel_index']:03d}.mp4"
        _download_file(video_url, video_file)
        video_paths.append(video_file)
        previous_video_url = video_url

        logger.info("Generated video for panel %d: %s", item["panel_index"] + 1, video_file)

    return video_paths
