"""Timeline / EDL: snap cuts to narration beats.

Each beat starts on its first spoken word. Inside a beat, shots split the beat's time in
proportion to their target durations (clamped to 1.5-5.0 s; the final shot holds to the end).
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import render_dir
from .spec import Episode, SHOT_MIN, SHOT_MAX

END_HOLD = 0.8   # seconds of picture after the last word (the stamp lands here)


def beat_windows(ep: Episode, timed_words: list[dict], audio_end: float) -> dict[str, tuple[float, float]]:
    starts: dict[str, float] = {}
    for w in timed_words:
        starts.setdefault(w["beat"], w["start"])
    order = [b.id for b in ep.beats]
    windows = {}
    for i, bid in enumerate(order):
        s = starts.get(bid)
        if s is None:
            continue
        nxt = next((starts[o] for o in order[i + 1:] if o in starts), None)
        e = nxt if nxt is not None else audio_end + END_HOLD
        windows[bid] = (0.0 if i == 0 else s, e)
    return windows


def build_edl(ep: Episode, timed_words: list[dict], audio_end: float) -> dict:
    windows = beat_windows(ep, timed_words, audio_end)
    edl, warnings = [], []
    t_cursor = 0.0
    for bid, (bs, be) in windows.items():
        shots = ep.shots_for(bid)
        if not shots:
            continue
        span = be - max(bs, t_cursor)
        total_target = sum(s.dur for s in shots)
        scale = span / total_target if total_target else 1.0
        if scale < 0.55:
            warnings.append(f"beat '{bid}': {len(shots)} shots squeezed into {span:.1f}s (scale {scale:.2f}); drop a shot")
        if scale > 1.7:
            warnings.append(f"beat '{bid}': shots stretched (scale {scale:.2f}); add a shot or tighten narration")
        t = max(bs, t_cursor)
        for i, s in enumerate(shots):
            d = s.dur * scale
            is_last_overall = s.index == len(ep.shots)
            if not is_last_overall:
                d = max(SHOT_MIN * 0.8, min(d, SHOT_MAX * 1.2))
            end = be if i == len(shots) - 1 else min(t + d, be)
            edl.append({"shot": s.name, "index": s.index, "beat": bid, "size": s.size, "mode": s.mode,
                        "start": round(t, 3), "end": round(end, 3), "dur": round(end - t, 3),
                        "sfx": s.sfx, "card": s.card})
            t = end
        t_cursor = be
    # beat cards: attach to the first shot of each beat that has no card of its own
    for b in ep.beats:
        if b.card:
            for e in edl:
                if e["beat"] == b.id and not e["card"]:
                    e["card"] = b.card
                    break
    total = edl[-1]["end"] if edl else 0.0
    return {"episode": ep.id, "total": round(total, 3), "audio_end": round(audio_end, 3),
            "beats": {k: [round(v[0], 3), round(v[1], 3)] for k, v in windows.items()},
            "shots": edl, "warnings": warnings}


def write_edl(ep: Episode, edl: dict) -> Path:
    out = render_dir(ep.id) / "edl.json"
    out.write_text(json.dumps(edl, indent=2))
    return out
