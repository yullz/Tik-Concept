"""Episode spec: load, normalise and validate the episode YAML.

Validation is structural and budgetary (durations, shot counts, size rotation).
Editorial quality rules live in lint.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

BEAT_ORDER = ["hook", "hinge", "phase1", "phase2", "phase3", "turn", "dilemma"]
SIZES = {"AERIAL", "WIDE", "MEDIUM", "CLOSE", "DETAIL", "POV", "MAP"}
MODES = {"video", "still"}
WORDS_PER_SECOND = 2.5          # planning rate; measured rate is checked after TTS
WPS_MIN, WPS_MAX = 2.2, 2.8          # measured pace band (after TTS)
WPS_BUDGET_MAX = 2.6                 # planning ceiling: scripts are written to this so pauses fit inside 90 s
MIN_DURATION, MAX_DURATION = 61.0, 90.0
SHOT_MIN, SHOT_MAX, HOOK_SHOT_MAX, FINAL_HOLD_MAX = 1.5, 5.0, 2.5, 6.0

WORD_RE = re.compile(r"[A-Za-z0-9'’\-]+")


def words(text: str) -> list[str]:
    """Spoken words only: strip [performed tags] and (direction)."""
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\([^)]*\)", " ", text)
    return WORD_RE.findall(text)


@dataclass
class Shot:
    index: int
    beat: str
    size: str
    location: str
    prompt: str
    motion: str
    dur: float
    mode: str = "video"
    sfx: str | None = None
    hero_object: bool = False
    card: dict | None = None

    @property
    def name(self) -> str:
        return f"shot-{self.index:02d}"


@dataclass
class Beat:
    id: str
    vo: str
    card: dict | None = None

    @property
    def word_count(self) -> int:
        return len(words(self.vo))

    @property
    def est_seconds(self) -> float:
        return self.word_count / WORDS_PER_SECOND


@dataclass
class Episode:
    id: str
    title: str
    pillar: str
    series: str
    series_number: int
    hook_title: str
    target_duration: float
    file_number: str
    beats: list[Beat]
    shots: list[Shot]
    research: dict
    voice: dict
    music: dict
    look_key_prompt: str
    dilemma: str
    pinned_comment: str
    metadata: dict
    localizations: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)
    path: Path | None = None

    # ---- derived -------------------------------------------------------
    @property
    def vo_text(self) -> str:
        return "\n\n".join(b.vo.strip() for b in self.beats)

    @property
    def word_count(self) -> int:
        return sum(b.word_count for b in self.beats)

    @property
    def est_duration(self) -> float:
        return self.word_count / WORDS_PER_SECOND + 0.8  # trailing hold

    def beat(self, beat_id: str) -> Beat:
        return next(b for b in self.beats if b.id == beat_id)

    def shots_for(self, beat_id: str) -> list[Shot]:
        return [s for s in self.shots if s.beat == beat_id]


def load_episode(path: str | Path) -> Episode:
    path = Path(path)
    with path.open() as f:
        raw = yaml.safe_load(f)
    return episode_from_dict(raw, path)


def episode_from_dict(raw: dict[str, Any], path: Path | None = None) -> Episode:
    beats = [Beat(id=b["id"], vo=str(b["vo"]).strip(), card=b.get("card")) for b in raw.get("beats", [])]
    shots = []
    for i, s in enumerate(raw.get("shots", []), start=1):
        shots.append(Shot(
            index=i, beat=s["beat"], size=str(s.get("size", "")).upper(),
            location=s.get("location", ""), prompt=s.get("prompt", "").strip(),
            motion=s.get("motion", "").strip(), dur=float(s.get("dur", 3.0)),
            mode=s.get("mode", "video"), sfx=s.get("sfx"), hero_object=bool(s.get("hero_object", False)), card=s.get("card"),
        ))
    return Episode(
        id=raw["id"], title=raw.get("title", raw["id"]), pillar=raw.get("pillar", ""),
        series=raw.get("series", ""), series_number=int(raw.get("series_number", 0)),
        hook_title=raw.get("hook_title", raw.get("title", "")),
        target_duration=float(raw.get("target_duration", 75)),
        file_number=raw.get("file_number", ""), beats=beats, shots=shots,
        research=raw.get("research", {}) or {}, voice=raw.get("voice", {}) or {},
        music=raw.get("music", {}) or {}, look_key_prompt=raw.get("look_key_prompt", ""),
        dilemma=raw.get("dilemma", ""), pinned_comment=raw.get("pinned_comment", ""),
        metadata=raw.get("metadata", {}) or {}, localizations=raw.get("localizations", {}) or {},
        raw=raw, path=path,
    )


def validate(ep: Episode) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    beat_ids = [b.id for b in ep.beats]
    if beat_ids != BEAT_ORDER:
        errors.append(f"beats must be exactly {BEAT_ORDER} in order, got {beat_ids}")
    if not ep.shots:
        errors.append("no shots")
    if not (MIN_DURATION <= ep.target_duration <= MAX_DURATION):
        errors.append(f"target_duration {ep.target_duration} outside {MIN_DURATION}-{MAX_DURATION}s")

    # word budget vs target duration
    lo, hi = ep.target_duration * WPS_MIN, ep.target_duration * WPS_BUDGET_MAX
    if not (lo <= ep.word_count <= hi):
        errors.append(f"VO has {ep.word_count} words; target {ep.target_duration}s needs {int(lo)}-{int(hi)} words at {WPS_MIN}-{WPS_BUDGET_MAX} w/s")

    # shots: fields, budgets, rotation
    known = set(beat_ids)
    for s in ep.shots:
        if s.beat not in known:
            errors.append(f"{s.name}: unknown beat '{s.beat}'")
        if s.size not in SIZES:
            errors.append(f"{s.name}: size must be one of {sorted(SIZES)}, got '{s.size}'")
        if s.mode not in MODES:
            errors.append(f"{s.name}: mode must be video|still")
        if len(s.prompt.split()) < 12:
            errors.append(f"{s.name}: prompt too thin (<12 words); name subject, action, setting, two era details, light")
        if s.mode == "video" and not s.motion:
            errors.append(f"{s.name}: video shot needs a motion prompt")
        is_last = s.index == len(ep.shots)
        max_dur = FINAL_HOLD_MAX if is_last else (HOOK_SHOT_MAX if s.beat == "hook" else SHOT_MAX)
        if not (SHOT_MIN <= s.dur <= max_dur):
            errors.append(f"{s.name}: dur {s.dur}s outside {SHOT_MIN}-{max_dur}s for its beat")
    # rotation: never three in a row with the same size; never two AERIAL in a row
    for a, b, c in zip(ep.shots, ep.shots[1:], ep.shots[2:]):
        if a.size == b.size == c.size:
            errors.append(f"{a.name}-{c.name}: three consecutive {a.size} shots; rotate sizes")
    for a, b in zip(ep.shots, ep.shots[1:]):
        if a.size == b.size == "AERIAL":
            errors.append(f"{a.name}-{b.name}: two consecutive AERIAL shots")
        if a.location and a.location == b.location:
            pass  # two in a row is allowed; three is checked below
    for a, b, c in zip(ep.shots, ep.shots[1:], ep.shots[2:]):
        if a.location and a.location == b.location == c.location:
            warnings.append(f"{a.name}-{c.name}: three consecutive shots in '{a.location}'; move")

    # per-beat shot budget vs narration estimate
    for beat in ep.beats:
        bs = ep.shots_for(beat.id)
        if not bs:
            errors.append(f"beat '{beat.id}' has no shots")
            continue
        planned = sum(s.dur for s in bs)
        est = beat.est_seconds if beat.id != "dilemma" else beat.est_seconds + 0.8
        if planned > est * 1.6 + 1.0:
            warnings.append(f"beat '{beat.id}': shots total {planned:.1f}s but narration is ~{est:.1f}s; shots will be shortened")
        if planned < est * 0.6:
            warnings.append(f"beat '{beat.id}': shots total {planned:.1f}s but narration is ~{est:.1f}s; shots will be stretched past 5s")
        if beat.id.startswith("phase") and not any(s.size in {"CLOSE", "POV", "DETAIL"} for s in bs):
            errors.append(f"beat '{beat.id}': needs at least one human-scale shot (CLOSE, POV or DETAIL)")

    # hook: first shot is the first shot; the hook must carry the viewer past 5 s (qualified view)
    hook_shots = ep.shots_for("hook")
    if hook_shots and ep.shots[0].beat != "hook":
        errors.append("the first shot must belong to the hook")
    hook_beat = ep.beat("hook") if "hook" in known else None
    if hook_beat is not None:
        if hook_beat.est_seconds < 4.6:
            errors.append(f"hook narration is ~{hook_beat.est_seconds:.1f}s; it must run past the 5-second qualified-view mark (>= 12 words: flat fact + open loop)")
        if len(hook_shots) < 2:
            errors.append("hook needs at least two shots (impossible image, then escalation) to hold 5 seconds")
        if sum(s.dur for s in hook_shots) < 5.0:
            errors.append("hook shots total under 5.0s; the hook must cover the 5-second qualified-view window")
        planned_hook = sum(s.dur for s in hook_shots)
        if hook_shots and planned_hook < hook_beat.est_seconds * 0.8:
            errors.append(f"hook shots total {planned_hook:.1f}s for ~{hook_beat.est_seconds:.1f}s of narration; they would stretch past 3s each. "
                          f"Add a hook shot (the first five seconds need a cut every 2-3 s)")
    dil_shots = ep.shots_for("dilemma")
    if "dilemma" in known and len(dil_shots) == 1 and ep.beat("dilemma").est_seconds + 0.8 > 6.5:
        errors.append(f"dilemma: one shot would hold ~{ep.beat('dilemma').est_seconds + 0.8:.1f}s; add a second ending shot (nothing holds past six seconds)")
    aerials = [s for s in ep.shots if s.size == "AERIAL"]
    if len(aerials) > 2:
        warnings.append(f"{len(aerials)} AERIAL shots; keep to two or fewer")
    if not any(s.hero_object for s in ep.shots):
        warnings.append("no shot is marked hero_object: true; the through-line object should recur in 4+ shots")
    elif sum(1 for s in ep.shots if s.hero_object) < 4:
        warnings.append("hero object appears in fewer than 4 shots")

    # research gate
    r = ep.research
    if not r.get("hinge") or not r.get("sources"):
        errors.append("research.hinge and research.sources are required (no source, no episode)")
    if not r.get("era_sheet"):
        errors.append("research.era_sheet is required before prompts are written")
    if not ep.dilemma or "?" not in ep.dilemma:
        errors.append("dilemma must be a question")
    if not ep.look_key_prompt:
        errors.append("look_key_prompt is required")
    return errors, warnings
