import base64
import json
from pathlib import Path

import anthropic


SYSTEM_PROMPT = """\
You analyze webtoon panels for animation. For each panel, return JSON with:
- "description": One sentence of what happens.
- "characters": Comma-separated character list.
- "setting": Brief setting description.
- "mood": One or two words for tone.
- "video_prompt": A concise cinematic motion prompt for image-to-video generation \
(describe camera movement, character actions, environmental effects - max 2 sentences).

Return ONLY valid JSON. No markdown fences."""


def analyze_panels(panel_paths: list[Path], cfg: dict) -> list[dict]:
    client = anthropic.Anthropic(api_key=cfg["anthropic_api_key"])
    analyze_cfg = cfg["analyze"]
    max_context = analyze_cfg["max_context_panels"]

    results = []
    accumulated = []

    for i, panel_path in enumerate(panel_paths):
        recent = accumulated[-max_context:]
        context_text = "\n".join(
            f"Panel {r['panel_index']+1}: {r['description']} "
            f"(Characters: {r['characters']}, Setting: {r['setting']}, Mood: {r['mood']})"
            for r in recent
        ) or "This is the first panel."

        image_data = base64.standard_b64encode(panel_path.read_bytes()).decode()
        ext = panel_path.suffix.lower()
        media_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(
            ext.lstrip("."), "image/png"
        )

        response = client.messages.create(
            model=analyze_cfg["model"],
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Panel {i+1} of this chapter.\n\nStory so far:\n{context_text}"},
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                ],
            }],
            system=SYSTEM_PROMPT,
        )

        raw = response.content[0].text
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # Retry once asking Claude to fix
            fix = client.messages.create(
                model=analyze_cfg["model"],
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": f"Fix this into valid JSON:\n{raw}"},
                ],
            )
            parsed = json.loads(fix.content[0].text)

        parsed["panel_path"] = str(panel_path)
        parsed["panel_index"] = i
        results.append(parsed)
        accumulated.append(parsed)
        print(f"Analyzed panel {i+1}/{len(panel_paths)}: {parsed.get('description', '')[:80]}")

    out_path = Path(analyze_cfg["output_dir"]) / "analysis.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Analysis saved to {out_path}")

    return results
