"""HTML contact sheets for the human gates (A: stills, B: clips) and the selections file."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from .config import render_dir
from .spec import Episode

REJECT_STILL = ["anachronism", "anatomy", "text", "warped-architecture", "generic", "wrong-size", "off-palette", "duplicate-of-another-shot"]
REJECT_CLIP = ["morph", "limb", "flicker", "static-start", "text", "wrong-camera", "too-fast"]


def write_contact_sheet(ep: Episode) -> Path:
    rdir = render_dir(ep.id)
    sheet = json.loads((rdir / "promptsheet.json").read_text()) if (rdir / "promptsheet.json").exists() else {"shots": []}
    rows = []
    for s in sheet["shots"]:
        name = s["shot"]
        variants = sorted((rdir / "keyframes").glob(f"{name}-*.*"))
        clip = rdir / "clips" / f"{name}.mp4"
        imgs = "".join(f'<figure><img src="keyframes/{v.name}"><figcaption>{v.stem[-1].upper()}</figcaption></figure>' for v in variants)
        vid = f'<video src="clips/{clip.name}" controls muted loop></video>' if clip.exists() else "<em>no clip</em>"
        rows.append(f"""<section><h2>{name} · {s['beat']} · {s['size']} · {s['target_dur']}s</h2>
<p class="loc">{s['location']}</p><div class="media">{imgs}{vid}</div>
<details><summary>prompt</summary><pre>{s['keyframe_prompt']}</pre><pre>{s.get('motion_prompt') or ''}</pre></details></section>""")
    html = f"""<!doctype html><meta charset="utf-8"><title>{ep.id} · gates A/B</title>
<style>body{{font:14px system-ui;background:#111;color:#eee;margin:24px}} section{{border-top:1px solid #333;padding:16px 0}}
.media{{display:flex;gap:12px;flex-wrap:wrap}} img,video{{height:420px;border-radius:6px}} figure{{margin:0;text-align:center}}
pre{{white-space:pre-wrap;color:#bbb}} .loc{{color:#9ab}} h2{{margin:0 0 4px}}</style>
<h1>{ep.title} · {ep.file_number}</h1>
<p>Gate A: mark A / B / R per shot in <code>selections.yaml</code>. Reject reasons (stills): {', '.join(REJECT_STILL)}. Clips: {', '.join(REJECT_CLIP)}.</p>
{''.join(rows)}"""
    (rdir / "contact-sheet.html").write_text(html)
    sel = rdir / "selections.yaml"
    if not sel.exists():
        sel.write_text("# per shot: pick: A|B|R, reason: <from the fixed list when R>, clip: ok|R, clip_reason: ...\n" +
                       "\n".join(f"{s['shot']}: {{pick: '', reason: '', clip: '', clip_reason: ''}}" for s in sheet["shots"]) + "\n")
    return rdir / "contact-sheet.html"


def apply_selections(ep: Episode) -> dict:
    """Copy the chosen variant to keyframes/shot-NN.png so the assembler finds it. Returns a summary."""
    rdir = render_dir(ep.id)
    sel = yaml.safe_load((rdir / "selections.yaml").read_text()) or {}
    summary = {"approved": [], "regenerate": [], "clip_regenerate": []}
    for shot, v in sel.items():
        if not isinstance(v, dict):
            continue
        pick = str(v.get("pick", "")).upper()
        if pick in ("A", "B"):
            src = next((p for p in (rdir / "keyframes").glob(f"{shot}-{pick.lower()}.*")), None)
            if src:
                dst = rdir / "keyframes" / f"{shot}{src.suffix}"
                dst.write_bytes(src.read_bytes())
                summary["approved"].append(shot)
        elif pick == "R":
            summary["regenerate"].append({"shot": shot, "reason": v.get("reason", "")})
        if str(v.get("clip", "")).upper() == "R":
            summary["clip_regenerate"].append({"shot": shot, "reason": v.get("clip_reason", "")})
    (rdir / "selections_summary.json").write_text(json.dumps(summary, indent=2))
    return summary
