"""Platform metadata and the publish bundle."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .config import render_dir
from .spec import Episode

PILLAR_TAGS = {
    "never-fell": ["#alternatehistory", "#history", "#whatif", "#neverfell"],
    "tomorrow-morning": ["#whatif", "#science", "#physics", "#tomorrowmorning"],
    "early-arrival": ["#alternatehistory", "#history", "#whatif", "#earlyarrival"],
    "the-hinge": ["#alternatehistory", "#history", "#whatif", "#thehinge"],
}
SERIES_LABEL = {"never-fell": "Never Fell", "tomorrow-morning": "Tomorrow Morning",
                "early-arrival": "Early Arrival", "the-hinge": "The Hinge"}
DISCLOSURE = "Alternate timeline. Visuals are AI-generated; the hinge event and dates are real and sourced."


def build_metadata(ep: Episode, channel: str = "Counterfact") -> dict:
    m = ep.metadata or {}
    series = SERIES_LABEL.get(ep.series, ep.series.title())
    n = f"{ep.series_number:02d}"
    hook_line = ep.beat("hook").vo.split(".")[0].strip().rstrip("?") + "."
    sources = ep.research.get("sources", [])
    src_lines = "\n".join(f"- {s}" for s in sources)
    tiktok_title = m.get("tiktok", {}).get("title") or f"{hook_line} ({series} · {n})"
    yt_title = m.get("youtube", {}).get("title") or f"{hook_line} ({series} {n})"
    tags = m.get("hashtags") or PILLAR_TAGS.get(ep.pillar, ["#whatif", "#history"])
    description = m.get("youtube", {}).get("description") or (
        f"{ep.dilemma}\n\n{DISCLOSURE}\n\nThe hinge: {ep.research.get('hinge','')}\n\nSources:\n{src_lines}\n\n"
        f"{series} · episode {n} · {ep.file_number}\n{' '.join(tags)}")
    return {
        "episode": ep.id, "file_number": ep.file_number, "series": series, "number": n,
        "cover_time": m.get("cover_time", 0.8),
        "tiktok": {
            "title": tiktok_title[:150], "hashtags": tags[:5], "is_aigc": True,
            "description": f"{tiktok_title} {' '.join(tags[:5])}"[:2200],
            "pinned_comment": ep.pinned_comment,
            "second_comment": m.get("second_comment", ""),
            "post_slots": m.get("post_slots", ["07:00", "18:00"]),
        },
        "youtube": {
            "title": yt_title[:100], "description": description[:5000], "tags": [t.lstrip("#") for t in tags] + ["alternate history", "what if", channel.lower()],
            "altered_content_disclosure": True, "related_video": m.get("related_video", ""),
            "pinned_comment": ep.pinned_comment,
        },
        "instagram": {"caption": f"{hook_line}\n\n{ep.dilemma}\n\n{DISCLOSURE}\n\n{' '.join(tags[:5])}"[:2200],
                       "ai_label": True},
        "replies_to_prepare": m.get("replies_to_prepare", []),
    }


def write_metadata(ep: Episode, channel: str = "Counterfact") -> Path:
    out = render_dir(ep.id) / "publish"
    meta = build_metadata(ep, channel)
    (out / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    t, y, i = meta["tiktok"], meta["youtube"], meta["instagram"]
    md = [f"# Publish · {ep.title} · {ep.file_number}", "",
          "## TikTok", f"**Title:** {t['title']}", f"**Hashtags:** {' '.join(t['hashtags'])}",
          "**AI-generated content flag:** on", f"**Post slots:** {', '.join(t['post_slots'])}", "",
          f"**Pinned comment (post within 1 min, takes a side):** {t['pinned_comment']}", "",
          f"**Second comment (team account, other side):** {t['second_comment']}", "",
          "## YouTube Shorts", f"**Title:** {y['title']}", "", "**Description:**", "", y["description"], "",
          f"**Tags:** {', '.join(y['tags'])}", "**Altered content disclosure:** yes", "",
          "## Instagram / Facebook Reels", "", i["caption"], "",
          f"## Cover frame: {meta['cover_time']} s (export with `pipeline cover`)", ""]
    (out / "metadata.md").write_text("\n".join(md))
    return out / "metadata.md"


def bundle(ep: Episode, master: Path) -> Path:
    out = render_dir(ep.id) / "publish"
    shutil.copy2(master, out / f"{ep.id}.mp4")
    return out
