"""Build the prompt sheet: keyframe prompts, motion prompts and ready-to-send batch requests."""
from __future__ import annotations

import json
from pathlib import Path

from .config import load_style, render_dir
from .spec import Episode


def keyframe_prompt(ep: Episode, shot, style: dict) -> str:
    opener = style["size_openers"].get(shot.size, "")
    accent = style["accents"].get(ep.pillar, "")
    parts = [opener, shot.prompt.rstrip(",. "), style["light_rule"] if "light" not in shot.prompt.lower() else "",
             style["lens"], style["film"], accent, style["negative"]]
    return ", ".join(p.strip().rstrip(",") for p in parts if p and p.strip())


def motion_prompt(shot, style: dict) -> str:
    m = shot.motion.rstrip(",. ")
    return f"{m}, {style['motion_suffix']}"


def look_key_prompt(ep: Episode, style: dict) -> str:
    accent = style["accents"].get(ep.pillar, "")
    return ", ".join([ep.look_key_prompt.rstrip(",. "), style["lens"], style["film"], accent, style["negative"]])


def build_promptsheet(ep: Episode, style_name: str = "counterfact-v1") -> dict:
    style = load_style(style_name)
    sheet = {
        "episode": ep.id,
        "style": style_name,
        "aspect_ratio": style["aspect_ratio"],
        "look_key": {
            "model": style["keyframe_model"],
            "params": {"model": style["keyframe_model"], "prompt": look_key_prompt(ep, style),
                       "aspect_ratio": style["aspect_ratio"], "resolution": style["keyframe_resolution"]},
        },
        "shots": [],
    }
    for s in ep.shots:
        sheet["shots"].append({
            "shot": s.name, "index": s.index, "beat": s.beat, "size": s.size, "location": s.location,
            "mode": s.mode, "target_dur": s.dur, "hero_object": s.hero_object,
            "keyframe_prompt": keyframe_prompt(ep, s, style),
            "motion_prompt": motion_prompt(s, style) if s.mode == "video" else None,
        })
    return sheet


def batch_requests(sheet: dict, kind: str, lookkey_job: str | None = None,
                   keyframe_jobs: dict[str, str] | None = None, style_name: str = "counterfact-v1") -> list[list[dict]]:
    """Ready-to-send `requests` arrays for generate_image_batch / generate_video_batch, chunked by 12.

    kind="keyframes": two variants per shot (index = shot_index*10 + variant), with the look key as reference.
    kind="motion":    one clip per video shot, start_image = the selected keyframe job id.
    """
    style = load_style(style_name)
    reqs: list[dict] = []
    if kind == "keyframes":
        for s in sheet["shots"]:
            for variant in (1, 2):
                params = {"model": style["keyframe_model"], "prompt": s["keyframe_prompt"],
                          "aspect_ratio": sheet["aspect_ratio"], "resolution": style["keyframe_resolution"]}
                if lookkey_job:
                    params["medias"] = [{"role": "image_references", "value": lookkey_job}]
                reqs.append({"index": s["index"] * 10 + variant, "params": params})
    elif kind == "motion":
        keyframe_jobs = keyframe_jobs or {}
        for s in sheet["shots"]:
            if s["mode"] != "video":
                continue
            job = keyframe_jobs.get(s["shot"])
            if not job:
                continue
            params = {"model": style["video_model"], "prompt": s["motion_prompt"],
                      "aspect_ratio": sheet["aspect_ratio"], **style["video_params"],
                      "medias": [{"role": "start_image", "value": job}]}
            reqs.append({"index": s["index"], "params": params})
    else:
        raise ValueError(kind)
    return [reqs[i:i + 12] for i in range(0, len(reqs), 12)]


def write_promptsheet(ep: Episode, style_name: str = "counterfact-v1") -> Path:
    out = render_dir(ep.id)
    sheet = build_promptsheet(ep, style_name)
    (out / "promptsheet.json").write_text(json.dumps(sheet, indent=2))
    (out / "keyframe_batches.json").write_text(json.dumps(batch_requests(sheet, "keyframes"), indent=2))
    lines = [f"# Prompt sheet · {ep.title} ({ep.id})", "",
             f"Aspect {sheet['aspect_ratio']} · keyframes `{sheet['look_key']['model']}` · motion `{load_style(style_name)['video_model']}`", "",
             "## Look key (generate first, pass its job id as image_references to every keyframe)", "",
             "```", sheet["look_key"]["params"]["prompt"], "```", ""]
    for s in sheet["shots"]:
        lines += [f"## {s['shot']} · {s['beat']} · {s['size']} · {s['target_dur']}s · {s['mode']}" + (" · HERO OBJECT" if s['hero_object'] else ""),
                  f"*{s['location']}*", "", "Keyframe:", "```", s["keyframe_prompt"], "```"]
        if s["motion_prompt"]:
            lines += ["Motion:", "```", s["motion_prompt"], "```"]
        lines.append("")
    (out / "promptsheet.md").write_text("\n".join(lines))
    return out / "promptsheet.md"
