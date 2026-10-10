"""Kinetic keyword captions, phase cards, the hinge line and the end stamp as one ASS file.

All typography is ours; nothing is ever rendered inside an AI image.
"""
from __future__ import annotations

import re
from pathlib import Path

from .spec import Episode

W, H = 1080, 1920


def _ts(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def _hex_to_ass(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}".upper()


def group_words(timed: list[dict], max_words: int = 3, max_gap: float = 0.55) -> list[dict]:
    """2-4 word cards; break on beat change, punctuation-ish gaps, or the word cap."""
    cards, cur = [], []
    for w in timed:
        if cur and (len(cur) >= max_words or w["beat"] != cur[-1]["beat"] or w["start"] - cur[-1]["end"] > max_gap):
            cards.append(cur); cur = []
        cur.append(w)
    if cur:
        cards.append(cur)
    out = []
    for c in cards:
        text = " ".join(re.sub(r"[\[\]]", "", x["word"]) for x in c).strip()
        text = re.sub(r"\s+", " ", text)
        out.append({"text": text, "start": c[0]["start"], "end": max(c[-1]["end"], c[0]["start"] + 0.35), "beat": c[0]["beat"]})
    # no overlaps
    for a, b in zip(out, out[1:]):
        if a["end"] > b["start"]:
            a["end"] = b["start"]
    return out


def build_ass(ep: Episode, timed: list[dict], edl: dict, style: dict, accent_hex: str,
              with_captions: bool = True) -> str:
    typo = style["typography"]
    font = typo.get("font", "Inter Display")
    sz = typo.get("safe_zone_px", {})
    bottom_margin = int(sz.get("bottom", 220)) + 120
    accent = _hex_to_ass(accent_hex)
    white = "&H00FFFFFF"
    black = "&H00000000"
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},{typo.get('caption_size_px', 64)},{white},{white},{black},&H80000000,1,0,0,0,100,100,1,0,1,0,3,2,60,140,{bottom_margin},1
Style: Title,{font},{typo.get('card_size_px', 110)},{white},{white},{black},&H80000000,1,0,0,0,100,100,2,0,1,0,4,8,60,140,160,1
Style: Card,{font},72,{accent},{accent},{black},&H80000000,1,0,0,0,100,100,6,0,1,0,3,7,60,140,{int(sz.get('top', 120)) + 110},1
Style: File,{font},34,&H00BBBBBB,&H00BBBBBB,{black},&H80000000,0,0,0,0,100,100,4,0,1,0,2,9,60,160,{int(sz.get('top', 120)) + 10},1
Style: Question,{font},88,{white},{white},{black},&H80000000,1,0,0,0,100,100,1,0,1,0,4,5,80,160,0,1
Style: Stamp,{font},124,&H002F32B8,&H002F32B8,&H002F32B8,&H80000000,1,0,0,0,100,100,8,-8,1,6,0,5,80,160,0,1
Style: Stat,{font},150,{white},{white},{black},&H80000000,1,0,0,0,100,100,2,0,1,0,5,5,60,140,0,1
Style: StatLabel,{font},56,{accent},{accent},{black},&H80000000,1,0,0,0,100,100,8,0,1,0,3,5,60,140,0,1
Style: Sigil,{font},40,{accent},{accent},{black},&H80000000,1,0,0,0,100,100,10,0,1,0,2,2,60,140,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev: list[str] = []
    total = edl["total"]

    def line(layer, start, end, style_name, text, extra=""):
        ev.append(f"Dialogue: {layer},{_ts(start)},{_ts(end)},{style_name},,0,0,0,,{extra}{_esc(text)}")

    # file number (whole video, faint)
    if ep.file_number:
        line(0, 0.0, total, "File", ep.file_number)
    # sigil
    line(0, 0.0, total, "Sigil", "WHAT IF")
    # title over the hook
    hook_end = edl["beats"].get("hook", [0, 5])[1]
    line(2, 0.0, min(hook_end, 5.5), "Title", ep.hook_title, "{\\fad(0,250)}")
    # cards at beat starts
    for e in edl["shots"]:
        c = e.get("card")
        if not c:
            continue
        st = c.get("style", "date")
        if st == "title":
            continue
        if st == "question":
            continue
        if st == "stat":
            # big digits on screen while the voice says the words; label underneath
            parts = str(c["text"]).split("\n", 1)
            end = min(e["start"] + max(e["dur"], 2.4), total)
            line(2, e["start"] + 0.05, end, "Stat", parts[0], "{\\pos(540,900)\\fscx60\\fscy60\\t(0,160,\\fscx100\\fscy100)\\fad(80,200)}")
            if len(parts) > 1:
                line(2, e["start"] + 0.2, end, "StatLabel", parts[1].strip(), "{\\pos(540,1010)\\fad(120,200)}")
            continue
        line(2, e["start"] + 0.05, min(e["start"] + 2.6, total), "Card", c["text"], "{\\fad(120,220)}")
    # hinge line: a thin bar that splits at the hinge beat
    hinge = edl["beats"].get("hinge")
    if hinge:
        hs = hinge[0]
        y = H - int(sz.get("bottom", 220)) - 60
        bar = f"{{\\p1\\an7\\pos(0,0)\\1c{accent}\\bord0\\shad0\\alpha&H20&}}m 160 {y} l 920 {y} l 920 {y+4} l 160 {y+4}{{\\p0}}"
        ev.append(f"Dialogue: 1,{_ts(max(hs-0.6,0))},{_ts(hs+0.6)},Caption,,0,0,0,,{bar}")
        up = f"{{\\p1\\an7\\pos(0,0)\\1c{accent}\\bord0\\shad0\\alpha&H20&\\move(0,0,0,-18,0,500)}}m 160 {y} l 920 {y} l 920 {y+4} l 160 {y+4}{{\\p0}}"
        dn = f"{{\\p1\\an7\\pos(0,0)\\1c{accent}\\bord0\\shad0\\alpha&H20&\\move(0,0,0,18,0,500)}}m 160 {y} l 920 {y} l 920 {y+4} l 160 {y+4}{{\\p0}}"
        ev.append(f"Dialogue: 1,{_ts(hs+0.6)},{_ts(hs+3.0)},Caption,,0,0,0,,{up}")
        ev.append(f"Dialogue: 1,{_ts(hs+0.6)},{_ts(hs+3.0)},Caption,,0,0,0,,{dn}")
    # captions
    if with_captions:
        for c in group_words(timed):
            if c["beat"] == "dilemma":
                continue  # the question card carries the ending
            line(3, c["start"], c["end"], "Caption", c["text"].upper())
    # ending: question + stamp
    dil = edl["beats"].get("dilemma")
    if dil:
        ds, de = dil
        q_start = ds + 0.3
        line(4, q_start, total, "Question", ep.dilemma, "{\\pos(540,700)\\fad(200,0)}")
        stamp_at = max(total - 1.1, q_start + 1.5)
        line(5, stamp_at, total, "Stamp", ep.raw.get("stamp_text", "NEVER HAPPENED"),
             "{\\pos(540,1180)\\fscx140\\fscy140\\t(0,120,\\fscx100\\fscy100)}")
    return header + "\n".join(ev) + "\n"


def write_ass(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path
