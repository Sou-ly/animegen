import urllib.request
from pathlib import Path

import fal_client


def _download_file(url: str, dest: Path):
    urllib.request.urlretrieve(url, str(dest))


def generate_videos(analysis: list[dict], cfg: dict) -> list[Path]:
    fal_client.api_key = cfg["fal_api_key"]
    gen_cfg = cfg["generate"]
    output_dir = Path(gen_cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    video_paths = []

    for item in analysis:
        panel_path = Path(item["panel_path"])
        image_url = fal_client.upload_file(panel_path)

        result = fal_client.subscribe(gen_cfg["model"], arguments={
            "prompt": item["video_prompt"],
            "image_url": image_url,
            "duration": gen_cfg["duration"],
            "cfg_scale": gen_cfg.get("cfg_scale", 0.5),
        })

        video_url = result["video"]["url"]
        video_file = output_dir / f"panel_{item['panel_index']:03d}.mp4"
        _download_file(video_url, video_file)
        video_paths.append(video_file)
        print(f"Generated video for panel {item['panel_index']+1}: {video_file}")

    return video_paths
