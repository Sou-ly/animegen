# Animegen

Convert webtoon chapters into animated videos using AI.

## Pipeline

1. **Download** — Downloads a webtoon chapter via `webtoon-downloader`
2. **Segment** — Splits the long strip into individual comic panels
3. **Analyze** — Describes each panel's content using Claude (Anthropic)
4. **Generate** — Produces a short video per panel via fal.ai (Kling)
5. **Assemble** — Stitches all panel videos into a final chapter video

## Requirements

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```bash
uv pip install -e .
```

Or with pip:

```bash
pip install -e .
```

Set the required environment variables:

```bash
export ANTHROPIC_API_KEY="your-key"
export FAL_KEY="your-key"
```

## Usage

```bash
animegen https://www.webtoons.com/en/fantasy/tower-of-god/list?title_no=95 1
```

Runs the full pipeline for chapter 1 of Tower of God.

### Partial runs

```bash
# Resume from analyze stage onward
animegen <url> <chapter> --start-stage analyze

# Stop after generate stage (skip assemble)
animegen <url> <chapter> --end-stage generate
```

## Configuration

Edit `config.yaml` to adjust settings:

| Section | Key | Description |
|---|---|---|
| `output` | `output_dir` | Output directory root (default: `./output`) |
| `segment` | `min_gap_height` | Minimum gap height between panels |
| `segment` | `gap_threshold` | Pixel intensity threshold for gap detection |
| `segment` | `blank_row_ratio` | Ratio of blank pixels to consider a row as a gap |
| `segment` | `min_panel_height` | Minimum height of a valid panel |
| `analyze` | `model` | Claude model to use for panel analysis |
| `analyze` | `max_context_panels` | Max preceding panels sent as context |
| `generate` | `model` | fal.ai model for video generation |
| `generate` | `duration` | Video duration per panel (seconds) |
| `generate` | `cfg_scale` | Guidance scale for generation |

## Output

```
output/
└── <series-slug>/
    └── ch<number>/
        ├── chapter_<n>.mp4      # Final assembled video
        ├── downloads/           # Raw webtoon images
        ├── panels/              # Segmented panel images
        ├── analysis/            # Claude analysis JSON
        └── videos/              # Per-panel generated videos
```
# animegen
