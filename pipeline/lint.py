"""Anti-slop linter for scripts and prompts (docs/00-anti-slop-charter.md).

Errors block the episode. Warnings are printed and counted on the scorecard.
"""
from __future__ import annotations

import re

from .spec import Episode, words

BANNED_PHRASES = [
    # narration reflexes
    "in a world where", "imagine a world", "little did they know", "the rest is history",
    "buckle up", "let's dive in", "dive in", "game-changer", "game changer", "mind-blowing",
    "mind blowing", "insane", "crazy", "unbelievable", "but here's the twist", "here's the twist",
    "plot twist", "fast forward", "and just like that", "changed everything", "everything changed",
    "forever changed", "changed forever", "the world would never be the same", "never be the same",
    "what do you think", "let me know in the comments", "comment below", "like and follow",
    "don't forget to", "welcome back", "in this video", "today we", "you won't believe",
    "wait for it", "spoiler alert", "it's giving", "literally", "basically", "you know", "i mean",
    "sort of", "kind of", "at the end of the day", "needless to say", "it goes without saying",
    "imagine", "picture this", "chaos", "unleash", "a testament to", "delve", "tapestry", "beacon",
    "in conclusion", "the dawn of", "stands as a", "nestled",
]
BANNED_PROMPT_TOKENS = [
    "8k", "4k", "hyper-detailed", "hyperdetailed", "ultra-detailed", "ultra detailed", "masterpiece",
    "trending on artstation", "artstation", "award-winning", "award winning", "epic", "lens flare",
    "glowing", "glow", "bloom", "particles", "sparkles", "hologram", "holographic", "futuristic city",
    "beautiful", "stunning", "breathtaking", "hyperrealistic", "hyper-realistic", "octane",
    "unreal engine", "dramatic lighting", "volumetric lighting", "cinematic masterpiece", "highly detailed",
    "intricate", "ethereal", "majestic", "neon",
]
BANNED_MOTION_TOKENS = ["zoom", "fast", "whip", "spin", "transform", "morph", "time-lapse", "timelapse", "explode"]
FILLER_RE = re.compile(r"\b(um|uh|y'know|ya know|okay\?|right\?)\b", re.I)
DIGIT_RE = re.compile(r"\d")
GENERIC_DILEMMA = ["what do you think", "which would you choose", "let me know", "comment"]
CONCRETE_HINTS = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    r"seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|"
    r"percent|metres|meters|kilometres|kilometers|miles|years?|centur(y|ies)|decades?|days?|weeks?|months?|tonnes?|tons?)\b",
    re.I,
)


def _find_phrases(text: str, phrases: list[str]) -> list[str]:
    low = " " + re.sub(r"\s+", " ", text.lower()) + " "
    hits = []
    for p in phrases:
        if re.search(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", low):
            hits.append(p)
    return hits


def lint_episode(ep: Episode) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    # ---- narration -----------------------------------------------------
    full = ep.vo_text
    for p in _find_phrases(full, BANNED_PHRASES):
        errors.append(f"VO: banned phrase '{p}'")
    if FILLER_RE.search(full):
        errors.append("VO: conversational filler")
    if DIGIT_RE.search(full):
        errors.append("VO: digits in narration; spell every number and date out")

    hook = ep.beat("hook").vo
    first_sentence = re.split(r"[.!?]", hook, maxsplit=1)[0]
    if len(words(first_sentence)) > 8:
        errors.append(f"hook: first sentence has {len(words(first_sentence))} words; max 8")
    if not hook.lower().startswith("what if"):
        errors.append("hook must open with the words 'What if' (brand and label)")

    # one concrete per beat (number, name, place, unit)
    for b in ep.beats:
        if b.id in ("hook", "dilemma"):
            continue
        has_number = bool(CONCRETE_HINTS.search(b.vo))
        has_proper = bool(re.search(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}", b.vo))
        if not (has_number or has_proper):
            errors.append(f"beat '{b.id}': no concrete (a number, a name, a place, a unit)")
        # mechanism check for phases
        if b.id.startswith("phase") and not re.search(r"\b(because|so|which means|that means|therefore|without|with no|no longer|forces|needs|cannot|can't)\b", b.vo, re.I):
            warnings.append(f"beat '{b.id}': no causal word (because / so / which means); explain the mechanism")
        sentences = [s for s in re.split(r"[.!?]+", b.vo) if words(s)]
        for s in sentences:
            n = len(words(s))
            if n > 30:
                errors.append(f"beat '{b.id}': a sentence has {n} words; split it (max 30)")
            elif n > 22:
                warnings.append(f"beat '{b.id}': a sentence has {n} words; shorter sentences hold retention")
        if sentences and sum(len(words(s)) for s in sentences) / len(sentences) > 17:
            warnings.append(f"beat '{b.id}': average sentence over 17 words; keep sentences short")
        # repeated modifier within a line
        toks = [w.lower() for w in words(b.vo)]
        for i in range(len(toks) - 1):
            window = toks[i + 1:i + 6]
            if len(toks[i]) > 5 and toks[i] in window:
                warnings.append(f"beat '{b.id}': '{toks[i]}' repeated within six words")
                break
    # no sentence repeated across beats
    seen = set()
    for b in ep.beats:
        for s in re.split(r"[.!?]+", b.vo):
            key = " ".join(w.lower() for w in words(s))
            if len(key) > 20 and key in seen:
                errors.append(f"beat '{b.id}': sentence repeated: '{s.strip()[:40]}'")
            seen.add(key)

    # turn + dilemma shape
    turn = ep.beat("turn").vo
    if not re.search(r"\b(but|yet|except|cost|price|lost|loses|never|without)\b", turn, re.I):
        warnings.append("turn: no cost language (but / cost / lost / never); the turn must be a cost")
    dil = ep.beat("dilemma").vo
    if "ours did" not in dil.lower():
        errors.append("dilemma beat must contain the sign-off 'Ours did.'")
    if "?" not in dil:
        errors.append("dilemma beat must end on a question")
    for p in _find_phrases(ep.dilemma + " " + dil, GENERIC_DILEMMA):
        errors.append(f"dilemma: generic ending '{p}'; write a trade, blame, prediction or identity dilemma")
    tags = re.findall(r"\[[^\]]*\]", full)
    if len(tags) > 2:
        warnings.append(f"{len(tags)} performed tags; keep to two per episode")

    # ---- prompts -------------------------------------------------------
    for s in ep.shots:
        for t in _find_phrases(s.prompt, BANNED_PROMPT_TOKENS):
            errors.append(f"{s.name}: banned prompt token '{t}'")
        for t in _find_phrases(s.motion, BANNED_MOTION_TOKENS):
            errors.append(f"{s.name}: banned motion token '{t}'")
        if re.search(r"\b(text|sign|banner|billboard|headline|caption|letters?)\b", s.prompt, re.I) and not re.search(r"illegible|no text", s.prompt, re.I):
            warnings.append(f"{s.name}: mentions text/signage; say 'illegible at this distance' or remove")
        if re.search(r"\b(face|portrait|close-up of .* face)\b", s.prompt, re.I) and s.size in {"CLOSE", "DETAIL"}:
            warnings.append(f"{s.name}: close-up of a face; prefer hands, objects, backs of heads")
        if not re.search(r"\b(light|lamp|sun|dusk|dawn|overcast|torch|candle|screen|window|noon|night|morning|fire|lit|glare|shade|shadow|lantern|star|moon|spot|beam|lightning|glint|filament|haze)\w*", s.prompt, re.I):
            warnings.append(f"{s.name}: no light cue in the prompt")
    for t in _find_phrases(ep.look_key_prompt, BANNED_PROMPT_TOKENS):
        errors.append(f"look_key_prompt: banned token '{t}'")

    # ---- research ------------------------------------------------------
    r = ep.research
    if r.get("sources") and len(r["sources"]) < 2:
        warnings.append("research: fewer than two sources")
    if not r.get("cost"):
        errors.append("research.cost (what this timeline loses) is required; it is the turn")
    return errors, warnings
