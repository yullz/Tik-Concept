"""Word timings for the narration.

Priority: words.json from ElevenLabs timestamps → faster-whisper (if installed) →
proportional estimate from the audio length (dry runs and emergencies only).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .spec import Episode, words


def audio_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def estimate_words(ep: Episode, total_seconds: float, lead_in: float = 0.15) -> list[dict]:
    """Proportional timing: each word gets time by character weight, beats get a 0.45 s breath."""
    toks: list[tuple[str, str]] = []
    for b in ep.beats:
        for w in words(b.vo):
            toks.append((b.id, w))
    n_beats = len(ep.beats)
    breath = 0.45
    speakable = max(total_seconds - lead_in - breath * (n_beats - 1) - 0.3, 1.0)
    weight = sum(len(w) + 1.5 for _, w in toks)
    t = lead_in
    out, last_beat = [], None
    for beat_id, w in toks:
        if last_beat is not None and beat_id != last_beat:
            t += breath
        d = (len(w) + 1.5) / weight * speakable
        out.append({"word": w, "start": round(t, 3), "end": round(t + d, 3), "beat": beat_id})
        t += d
        last_beat = beat_id
    return out


def whisper_words(audio: Path) -> list[dict] | None:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception:
        return None
    model = WhisperModel("small", compute_type="int8")
    segments, _ = model.transcribe(str(audio), word_timestamps=True, vad_filter=True)
    out = []
    for seg in segments:
        for w in seg.words or []:
            out.append({"word": w.word.strip(), "start": float(w.start), "end": float(w.end)})
    return out or None


def assign_beats(ep: Episode, timed: list[dict]) -> list[dict]:
    """Map a flat timed word list onto beats by cumulative script word counts (STT is the clock, the script is the text)."""
    script = [(b.id, w) for b in ep.beats for w in words(b.vo)]
    n_script, n_timed = len(script), len(timed)
    out = []
    for i, tw in enumerate(timed):
        j = min(int(i * n_script / max(n_timed, 1)), n_script - 1)
        out.append({**tw, "beat": script[j][0]})
    return out


def get_words(ep: Episode, audio: Path, words_json: Path | None, allow_estimate: bool = False) -> tuple[list[dict], str]:
    if words_json and words_json.exists():
        timed = json.loads(words_json.read_text())
        if timed and "beat" not in timed[0]:
            timed = assign_beats(ep, timed)
        return timed, "elevenlabs"
    ww = whisper_words(audio)
    if ww:
        return assign_beats(ep, ww), "whisper"
    if not allow_estimate:
        raise SystemExit("no word timings: provide words.json, install faster-whisper, or pass --estimate (dry runs only)")
    return estimate_words(ep, audio_duration(audio)), "estimate"
