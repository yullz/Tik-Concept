"""Narration: ElevenLabs direct API (with word timestamps) or a Higgsfield request file.

Direct route writes renders/<id>/audio/vo.mp3 and words.json.
Higgsfield route writes renders/<id>/audio/tts_request.json for the executor (MCP) and
expects vo.mp3 to be dropped in afterwards; alignment then falls back to align.py.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from .config import env, render_dir
from .spec import Episode, words

ELEVEN_BASE = "https://api.elevenlabs.io/v1"


def narration_text(ep: Episode) -> str:
    """The exact text sent to the synthesiser: beats joined by a paragraph break, (direction) stripped."""
    text = "\n\n".join(b.vo.strip() for b in ep.beats)
    return re.sub(r"\([^)]*\)", "", text)


def higgsfield_request(ep: Episode) -> dict:
    """Request body for Higgsfield `generate_audio` (text2speech_v2 / elevenlabs), per docs/06."""
    v = ep.voice
    direction = v.get("direction", "calm dry archivist, unhurried, lets facts land")
    prompt = f"[{direction}, starts speaking immediately] {narration_text(ep)}"
    return {
        "model": "text2speech_v2",
        "variant": "elevenlabs",
        "voice_type": v.get("voice_type", "preset"),
        "voice_id": v.get("voice_id", env("HIGGSFIELD_VOICE_ID", "30fc8796-ceb6-4a66-b3a7-4a145ef7f346")),
        "prompt": prompt,
    }


def write_higgsfield_request(ep: Episode) -> Path:
    out = render_dir(ep.id) / "audio" / "tts_request.json"
    out.write_text(json.dumps(higgsfield_request(ep), indent=2))
    return out


def _chars_to_words(alignment: dict) -> list[dict]:
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]
    out, cur, s0, e0 = [], "", None, None
    for ch, st, en in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                out.append({"word": cur, "start": s0, "end": e0}); cur = ""
            continue
        if not cur:
            s0 = st
        cur += ch; e0 = en
    if cur:
        out.append({"word": cur, "start": s0, "end": e0})
    # keep only spoken tokens (drop bracket tags)
    return [w for w in out if not re.fullmatch(r"\[.*\]", w["word"])]


def elevenlabs_tts(ep: Episode) -> tuple[Path, Path | None]:
    import requests  # local import keeps offline stages dependency-light

    key = env("ELEVENLABS_API_KEY")
    voice = ep.voice.get("elevenlabs_voice_id") or env("ELEVENLABS_VOICE_ID")
    if not key or not voice:
        raise SystemExit("ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are required for the direct route")
    model = ep.voice.get("elevenlabs_model_id") or env("ELEVENLABS_MODEL_ID", "eleven_v3")
    settings = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.15, "speed": 0.95}
    settings.update(ep.voice.get("settings", {}))
    body = {"text": narration_text(ep), "model_id": model, "voice_settings": settings,
            "apply_text_normalization": "on"}
    out = render_dir(ep.id) / "audio"
    headers = {"xi-api-key": key, "Content-Type": "application/json"}
    # 1) try with timestamps
    r = requests.post(f"{ELEVEN_BASE}/text-to-speech/{voice}/with-timestamps",
                      params={"output_format": "mp3_44100_128"}, headers=headers, json=body, timeout=180)
    if r.ok:
        data = r.json()
        (out / "vo.mp3").write_bytes(base64.b64decode(data["audio_base64"]))
        align = data.get("normalized_alignment") or data.get("alignment")
        if align:
            wl = _chars_to_words(align)
            (out / "words.json").write_text(json.dumps(wl, indent=1))
            return out / "vo.mp3", out / "words.json"
        return out / "vo.mp3", None
    # 2) fall back to plain synthesis (alignment handled later by align.py)
    r2 = requests.post(f"{ELEVEN_BASE}/text-to-speech/{voice}", params={"output_format": "mp3_44100_128"},
                       headers=headers, json=body, timeout=180)
    r2.raise_for_status()
    (out / "vo.mp3").write_bytes(r2.content)
    return out / "vo.mp3", None


def measure_pace(ep: Episode, audio_seconds: float) -> dict:
    n = len(words(narration_text(ep)))
    wps = n / audio_seconds if audio_seconds else 0
    verdict = "ok" if 2.2 <= wps <= 2.8 else ("rushed" if wps > 2.8 else "slow")
    return {"words": n, "seconds": round(audio_seconds, 2), "wps": round(wps, 2), "verdict": verdict}
