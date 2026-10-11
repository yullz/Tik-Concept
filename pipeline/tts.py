"""Narration through the ElevenLabs API (Eleven v4), with word timings.

Direct route (default):
  1. POST /v1/text-to-speech/{voice}/with-timestamps  → vo.mp3 + words.json (character alignment → words)
  2. if the model/plan refuses timestamps: POST /v1/text-to-speech/{voice} → vo.mp3, then
     POST /v1/forced-alignment (audio + the exact script) → words.json
  3. align.py falls back to faster-whisper, then to a proportional estimate (dry runs only).

The `audition` command synthesises the audition script with several candidate voices so the
narrator is chosen by ear, then locked by voice_id in the episode YAML (never by name).
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from .config import RENDERS_DIR, env, render_dir
from .spec import Episode, words

ELEVEN_BASE = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL = "eleven_v4"            # Eleven v4 (Sept 2026). Confirm the exact id with `pipeline audition --list-models`.
DEFAULT_SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "use_speaker_boost": True}
V3_PLUS_ONLY = ("stability", "similarity_boost", "use_speaker_boost")   # Eleven v3/v4 have no style or speed sliders
DEFAULT_OUTPUT_FORMAT = "mp3_44100_192"                                 # 192 kbps needs Creator tier or above; 128 is the fallback
TAG_RE = re.compile(r"\[[^\]]*\]")

AUDITION_SCRIPT = (
    "What if Rome never fell. Not in four seventy-six. Not ever. Tonight, the Senate votes on the Moon. "
    "One autumn night, two seventy-five. Aurelian, the emperor who stitched the broken empire back together in five years, "
    "is murdered by his officers. Here, the plot fails. This is how it happens. "
    "[exhale] But an empire with no rivals has no reason to invent. Printing, banking, steam, all came from states fighting to survive. "
    "That timeline never happened. Ours did. So, honestly: would you trade the internet for Rome?"
)


def narration_text(ep: Episode) -> str:
    """The exact text sent to the synthesiser: beats joined by a paragraph break, (direction) stripped."""
    text = "\n\n".join(b.vo.strip() for b in ep.beats)
    return re.sub(r"\([^)]*\)", "", text)


def _chars_to_words(alignment: dict) -> list[dict]:
    """Character timings -> spoken words. Audio tags such as [exhale] or a bracketed direction are
    timed by the API like any other characters; they are skipped here so they never become words."""
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]
    out, cur, s0, e0, in_tag = [], "", None, None, False
    for ch, st, en in zip(chars, starts, ends):
        if ch == "[":
            if cur:
                out.append({"word": cur, "start": s0, "end": e0}); cur = ""
            in_tag = True
            continue
        if in_tag:
            if ch == "]":
                in_tag = False
            continue
        if ch.isspace():
            if cur:
                out.append({"word": cur, "start": s0, "end": e0}); cur = ""
            continue
        if not cur:
            s0 = st
        cur += ch; e0 = en
    if cur:
        out.append({"word": cur, "start": s0, "end": e0})
    return [w for w in out if re.search(r"[A-Za-z0-9]", w["word"])]


class ElevenLabs:
    def __init__(self, api_key: str | None = None):
        self.key = api_key or env("ELEVENLABS_API_KEY")
        if not self.key:
            raise SystemExit("ELEVENLABS_API_KEY is required (put it in .env)")

    def _h(self, json_body: bool = True) -> dict:
        h = {"xi-api-key": self.key}
        if json_body:
            h["Content-Type"] = "application/json"
        return h

    def _req(self, method: str, path: str, **kw):
        import requests
        kw.setdefault("timeout", 300)
        r = requests.request(method, f"{ELEVEN_BASE}{path}", headers=kw.pop("headers", self._h()), **kw)
        return r

    # ---- discovery ---------------------------------------------------------
    def models(self) -> list[dict]:
        r = self._req("GET", "/models"); r.raise_for_status()
        return r.json()

    def my_voices(self) -> list[dict]:
        r = self._req("GET", "/voices"); r.raise_for_status()
        return r.json().get("voices", [])

    def search_library(self, search: str, gender: str | None = None, page_size: int = 20, **filters) -> list[dict]:
        params = {"search": search, "page_size": page_size, "language": "en", **filters}
        if gender:
            params["gender"] = gender
        r = self._req("GET", "/shared-voices", params=params); r.raise_for_status()
        return r.json().get("voices", [])

    def add_library_voice(self, public_owner_id: str, voice_id: str, new_name: str) -> dict:
        r = self._req("POST", f"/voices/add/{public_owner_id}/{voice_id}", json={"new_name": new_name}); r.raise_for_status()
        return r.json()

    # ---- synthesis ---------------------------------------------------------
    def tts(self, voice_id: str, text: str, model_id: str, settings: dict, out_mp3: Path,
            output_format: str | None = None, language_code: str | None = None) -> tuple[Path, list[dict] | None, str]:
        output_format = output_format or env("ELEVENLABS_OUTPUT_FORMAT", DEFAULT_OUTPUT_FORMAT)
        body = {"text": text, "model_id": model_id, "voice_settings": settings, "apply_text_normalization": "on"}
        if language_code:
            body["language_code"] = language_code

        def post(path):
            r = self._req("POST", path, params={"output_format": output_format}, json=body)
            if r.status_code in (400, 403, 422) and "output_format" in r.text and output_format != "mp3_44100_128":
                # the plan does not allow 192 kbps: retry once at the default bitrate
                print(f"  ElevenLabs refused output_format {output_format}; retrying with mp3_44100_128")
                r = self._req("POST", path, params={"output_format": "mp3_44100_128"}, json=body)
            return r

        r = post(f"/text-to-speech/{voice_id}/with-timestamps")
        if r.ok:
            data = r.json()
            out_mp3.write_bytes(base64.b64decode(data["audio_base64"]))
            align = data.get("normalized_alignment") or data.get("alignment")
            return out_mp3, (_chars_to_words(align) if align else None), "elevenlabs-timestamps"
        if r.status_code not in (400, 404, 422):
            # auth, credits, rate limit, server errors: say so, do not retry blindly on another endpoint
            raise SystemExit(f"ElevenLabs with-timestamps failed ({r.status_code}): {r.text[:400]}")
        print(f"  with-timestamps not available ({r.status_code}: {r.text[:160]}); plain synthesis + forced alignment")
        r2 = post(f"/text-to-speech/{voice_id}")
        if not r2.ok:
            raise SystemExit(f"ElevenLabs TTS failed ({r2.status_code}): {r2.text[:400]}")
        out_mp3.write_bytes(r2.content)
        return out_mp3, self.forced_alignment(out_mp3, TAG_RE.sub("", text)), "elevenlabs-forced-alignment"

    def forced_alignment(self, audio: Path, text: str) -> list[dict] | None:
        """POST /v1/forced-alignment: returns character and word timings for a given audio + transcript."""
        with audio.open("rb") as f:
            r = self._req("POST", "/forced-alignment", headers=self._h(json_body=False),
                          files={"file": (audio.name, f, "audio/mpeg")}, data={"text": text})
        if not r.ok:
            return None
        data = r.json()
        if data.get("words"):
            return [{"word": w.get("text", w.get("word", "")), "start": float(w["start"]), "end": float(w["end"])}
                    for w in data["words"] if re.search(r"[A-Za-z0-9]", str(w.get("text", w.get("word", ""))))]
        if data.get("characters"):
            return _chars_to_words({"characters": [c["text"] for c in data["characters"]],
                                    "character_start_times_seconds": [c["start"] for c in data["characters"]],
                                    "character_end_times_seconds": [c["end"] for c in data["characters"]]})
        return None


def voice_config(ep: Episode) -> tuple[str, str, dict]:
    v = ep.voice or {}
    voice_id = v.get("elevenlabs_voice_id") or env("ELEVENLABS_VOICE_ID")
    if not voice_id:
        raise SystemExit("no voice locked: set voice.elevenlabs_voice_id in the episode (or ELEVENLABS_VOICE_ID); pick one with `pipeline audition`")
    model_id = v.get("model_id") or env("ELEVENLABS_MODEL_ID", DEFAULT_MODEL)
    settings = {**DEFAULT_SETTINGS, **(v.get("settings") or {})}
    if model_id.startswith(("eleven_v3", "eleven_v4")):
        # v3/v4 accept only stability, similarity and speaker boost; style/speed would be rejected or ignored
        settings = {k: val for k, val in settings.items() if k in V3_PLUS_ONLY}
    return voice_id, model_id, settings


def elevenlabs_tts(ep: Episode) -> tuple[Path, Path | None, str]:
    client = ElevenLabs()
    voice_id, model_id, settings = voice_config(ep)
    text = narration_text(ep)
    direction = (ep.voice or {}).get("direction")
    if direction:
        # v4 reads bracketed natural-language direction as an audio tag; keep it short and put it first
        text = f"[{direction}] {text}"
    out = render_dir(ep.id) / "audio"
    mp3, timed, route = client.tts(voice_id, text, model_id, settings, out / "vo.mp3")
    wj = None
    if timed:
        wj = out / "words.json"
        wj.write_text(json.dumps(timed, indent=1))
    (out / "tts_meta.json").write_text(json.dumps({"voice_id": voice_id, "model_id": model_id, "settings": settings, "route": route}, indent=2))
    return mp3, wj, route


def measure_pace(ep: Episode, audio_seconds: float) -> dict:
    n = len(words(narration_text(ep)))
    wps = n / audio_seconds if audio_seconds else 0
    verdict = "ok" if 2.2 <= wps <= 2.8 else ("rushed" if wps > 2.8 else "slow")
    return {"words": n, "seconds": round(audio_seconds, 2), "wps": round(wps, 2), "verdict": verdict}


def audition(candidates: list[str], model_id: str | None = None, gender: str | None = None,
             list_models: bool = False, search: str | None = None) -> Path:
    """Synthesise the audition script with each candidate (a voice_id or a Voice Library name) into renders/_audition/."""
    from .align import audio_duration

    client = ElevenLabs()
    out = RENDERS_DIR / "_audition"; out.mkdir(parents=True, exist_ok=True)
    report: dict = {"model_id": model_id or env("ELEVENLABS_MODEL_ID", DEFAULT_MODEL), "takes": []}
    if list_models:
        report["models"] = [{"model_id": m.get("model_id"), "name": m.get("name"), "can_do_text_to_speech": m.get("can_do_text_to_speech")} for m in client.models()]
        for m in report["models"]:
            print(f"  {m['model_id']:<28} {m['name']}")
    if search:
        found = client.search_library(search, gender=gender)
        report["library_search"] = [{"name": v.get("name"), "voice_id": v.get("voice_id"), "public_owner_id": v.get("public_owner_id"),
                                     "accent": v.get("accent"), "gender": v.get("gender"), "use_case": v.get("use_case"),
                                     "descriptive": v.get("descriptive"), "preview_url": v.get("preview_url")} for v in found]
        for v in report["library_search"]:
            print(f"  {v['name']:<36} {v['voice_id']}  {v['accent'] or ''} {v['gender'] or ''}  {v['use_case'] or ''}")
    mine = {v["name"].lower(): v for v in client.my_voices()}
    n_words = len(words(AUDITION_SCRIPT))
    for cand in candidates:
        voice_id, label = cand, cand
        if not re.fullmatch(r"[A-Za-z0-9]{20}", cand):
            # resolve a name: own voices first, then the library (adds it to the account under the same name)
            v = mine.get(cand.lower())
            if v is None:
                hits = [h for h in client.search_library(cand, gender=gender) if cand.lower() in (h.get("name") or "").lower()]
                if not hits:
                    print(f"  skip: no voice named '{cand}'"); continue
                h = hits[0]
                client.add_library_voice(h["public_owner_id"], h["voice_id"], h["name"])
                v = {"voice_id": h["voice_id"], "name": h["name"]}
            voice_id, label = v["voice_id"], v["name"]
        slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        mp3, timed, route = client.tts(voice_id, AUDITION_SCRIPT, report["model_id"], DEFAULT_SETTINGS, out / f"{slug}.mp3")
        secs = audio_duration(mp3)
        pause = None
        if timed:
            gaps = [b["start"] - a["end"] for a, b in zip(timed, timed[1:])]
            pause = round(max(gaps), 2) if gaps else None
        take = {"label": label, "voice_id": voice_id, "file": str(mp3), "seconds": round(secs, 2), "wps": round(n_words / secs, 2) if secs else None,
                "longest_pause": pause, "route": route}
        report["takes"].append(take)
        print(f"  {label:<36} {voice_id}  {take['seconds']}s  {take['wps']} w/s  pause {pause}")
    (out / "audition.json").write_text(json.dumps(report, indent=2))
    (out / "README.md").write_text("# Audition\n\nListen blind, in this order, on phone speakers:\n\n" +
        "\n".join(f"- {t['label']} ({t['voice_id']}): `{Path(t['file']).name}` {t['seconds']}s, {t['wps']} w/s" for t in report["takes"]) +
        "\n\nScore: clarity of 'two seventy-five', weight of 'This is how it happens', whether the exhale sounds human, whether the last line darkens without crawling.\n"
        "Lock the winner: set `voice.elevenlabs_voice_id` in every episode YAML (or ELEVENLABS_VOICE_ID in .env).\n")
    return out
