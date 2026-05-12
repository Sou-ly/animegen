import subprocess
from pathlib import Path


def assemble_video(video_paths: list[Path], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    concat_list = output_path.parent / "concat_list.txt"
    with open(concat_list, "w") as f:
        for vp in video_paths:
            f.write(f"file '{vp.resolve()}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ], check=True, capture_output=True)

    concat_list.unlink()
    print(f"Assembled {len(video_paths)} clips into {output_path}")
    return output_path
