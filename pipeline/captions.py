"""Kinetic keyword captions, phase cards, the hinge line and the end stamp as one ASS file.

All typography is ours; nothing is ever rendered inside an AI image.

Layout (1080×1920, platform-safe): a header row at the top (the WHAT IF mark left, the file
number right) below the app's tabs; cards under the header; stat digits and the end question
in the upper-middle; captions at ~75 % height, above the description and clear of the icon
column; nothing in the bottom 420 px or the right 150 px.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .spec import Episode

W, H = 1080, 1920

# words a caption card must not end on (they dangle); sentence punctuation overrides this
FUNCTION_WORDS = {
    "a", "an", "the", "of", "to", "in", "on", "at", "for", "and", "or", "but", "nor", "with", "by", "from",
    "as", "is", "are", "was", "were", "be", "been", "being", "that", "this", "these", "those", "than", "then",
    "so", "its", "their", "our", "your", "my", "his", "her", "we", "they", "it", "he", "she", "you", "i",
    "into", "onto", "over", "under", "not", "no", "do", "does", "did", "has", "have", "had", "will", "would",
    "can", "cannot", "could", "should", "may", "might", "must", "which", "who", "whom", "what", "where",
    "when", "while", "if", "because", "until", "every", "each", "some", "any", "all", "both", "very", "too",
    "just", "only", "still", "also", "there", "here", "about", "through", "without", "within", "like",
    "old", "new", "same", "own", "first", "last", "next", "more", "most", "few", "many", "other", "whole",
    "one", "two", "three", "big", "small", "long", "short",
}
HARD_PUNCT = ".!?:;"
SOFT_PUNCT = ",—–"
MIN_CARD_SECONDS = 0.45


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


def _clean(word: str) -> str:
    """Caption text for a word: letters, digits, inner apostrophes and hyphens; no punctuation."""
    w = re.sub(r"\[[^\]]*\]", "", word)
    w = re.sub(r"[^\w'’\-]+", "", w)
    return w.strip("'’-")


def _break_kind(token: str) -> str | None:
    tail = token.rstrip("'\"”’)»")
    if not tail:
        return None
    if tail[-1] in HARD_PUNCT:
        return "hard"
    if tail[-1] in SOFT_PUNCT or tail.endswith("..."):
        return "soft"
    return None


def _script_tokens(ep: Episode) -> dict[str, list[str]]:
    """Per beat: the script's tokens with their punctuation attached ([tags] and (directions) removed)."""
    out: dict[str, list[str]] = {}
    for b in ep.beats:
        text = re.sub(r"\[[^\]]*\]", " ", b.vo)
        text = re.sub(r"\([^)]*\)", " ", text)
        out[b.id] = [t for t in text.split() if re.search(r"[A-Za-z0-9]", t)]
    return out


def _annotate(timed: list[dict], ep: Episode | None) -> list[dict]:
    """Return copies of the timed words with 'text' (clean caption word) and 'brk' (hard/soft/None).

    Punctuation comes from the script when the word counts match (ElevenLabs timestamps keep the
    script's words one to one); otherwise from the timed word itself (whisper keeps punctuation).
    """
    by_beat: dict[str, list[dict]] = defaultdict(list)
    for w in timed:
        by_beat[w["beat"]].append(w)
    script = _script_tokens(ep) if ep is not None else {}
    annotated: dict[int, dict] = {}
    for bid, ws in by_beat.items():
        toks = script.get(bid, [])
        use_script = len(toks) == len(ws)
        for i, w in enumerate(ws):
            raw = toks[i] if use_script else str(w["word"])
            annotated[id(w)] = {**w, "text": _clean(str(w["word"])) or _clean(raw), "brk": _break_kind(raw)}
    out = [annotated[id(w)] for w in timed]
    return [w for w in out if w["text"]]


def _is_function(w: dict) -> bool:
    return w["text"].lower() in FUNCTION_WORDS


def _split_sentence(ws: list[dict], max_words: int = 4, target: int = 3) -> list[list[dict]]:
    """Cost-minimising split of one sentence into 1-4 word cards.

    Costs: distance from the target length; a card ending on a function word (unless it closes the
    sentence); a one-word card; a soft-punctuation ending is rewarded. Exact DP, n <= ~40.
    """
    n = len(ws)
    if n == 0:
        return []
    INF = float("inf")
    best = [INF] * (n + 1); back = [0] * (n + 1); best[0] = 0.0
    for end in range(1, n + 1):
        for length in range(1, min(max_words, end) + 1):
            start = end - length
            if best[start] == INF:
                continue
            last = ws[end - 1]
            closes = end == n
            cost = abs(length - target) * 1.0
            if length == 1 and n > 1:
                cost += 2.5
            if not closes:
                if _is_function(last):
                    cost += 4.0
                if last["brk"] == "soft":
                    cost -= 1.5
            c = best[start] + cost
            if c < best[end]:
                best[end], back[end] = c, start
    cards, i = [], n
    while i > 0:
        cards.append(ws[back[i]:i]); i = back[i]
    return cards[::-1]


def group_words(timed: list[dict], ep: Episode | None = None, max_words: int = 4, max_gap: float = 0.55) -> list[dict]:
    """Caption cards of 1-4 words that follow the sentence: breaks at punctuation and pauses,
    never on a dangling function word, 2-3 words preferred."""
    ws = _annotate(timed, ep)
    # sentences: runs broken by hard punctuation, beat changes or pauses
    sentences: list[list[dict]] = []
    cur: list[dict] = []
    for w in ws:
        if cur and (w["beat"] != cur[-1]["beat"] or w["start"] - cur[-1]["end"] > max_gap):
            sentences.append(cur); cur = []
        cur.append(w)
        if w["brk"] == "hard":
            sentences.append(cur); cur = []
    if cur:
        sentences.append(cur)
    out: list[dict] = []
    for sent in sentences:
        for card in _split_sentence(sent, max_words=max_words):
            text = " ".join(x["text"] for x in card)
            out.append({"text": text, "start": card[0]["start"], "end": max(card[-1]["end"], card[0]["start"] + MIN_CARD_SECONDS),
                        "beat": card[0]["beat"]})
    for a, b in zip(out, out[1:]):
        if a["end"] > b["start"]:
            a["end"] = b["start"]
    return out


def build_ass(ep: Episode, timed: list[dict], edl: dict, style: dict, accent_hex: str,
              with_captions: bool = True) -> str:
    typo = style["typography"]
    font = typo.get("font", "Inter Display")
    sz = typo.get("safe_zone_px", {})
    top = int(sz.get("top", 200)); bottom = int(sz.get("bottom", 420))
    right = int(sz.get("right", 150)); left = int(sz.get("left", 70))
    caption_margin_v = bottom + 60                 # caption baseline at ~75 % of the height
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
Style: Caption,{font},{typo.get('caption_size_px', 84)},{white},{white},{black},&H80000000,1,0,0,0,100,100,1,0,1,0,3,2,{left + 20},{right + 20},{caption_margin_v},1
Style: Title,{font},{typo.get('card_size_px', 116)},{white},{white},{black},&H80000000,1,0,0,0,100,100,2,0,1,0,4,8,{left},{right},{top + 150},1
Style: Card,{font},72,{accent},{accent},{black},&H80000000,1,0,0,0,100,100,6,0,1,0,3,7,{left},{right},{top + 100},1
Style: File,{font},34,&H00BBBBBB,&H00BBBBBB,{black},&H80000000,0,0,0,0,100,100,4,0,1,0,2,9,{left},{right},{top},1
Style: Sigil,{font},34,{accent},{accent},{black},&H80000000,1,0,0,0,100,100,10,0,1,0,2,7,{left},{right},{top},1
Style: Question,{font},88,{white},{white},{black},&H80000000,1,0,0,0,100,100,1,0,1,0,4,5,{left + 20},{right + 20},0,1
Style: Stamp,{font},124,&H002F32B8,&H002F32B8,&H002F32B8,&H80000000,1,0,0,0,100,100,8,-8,1,6,0,5,80,160,0,1
Style: Stat,{font},150,{white},{white},{black},&H80000000,1,0,0,0,100,100,2,0,1,0,5,5,{left},{right},0,1
Style: StatLabel,{font},56,{accent},{accent},{black},&H80000000,1,0,0,0,100,100,8,0,1,0,3,5,{left},{right},0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev: list[str] = []
    total = edl["total"]
    cx = (left + (W - right)) // 2      # horizontal centre of the safe area (left of the icon column)

    def line(layer, start, end, style_name, text, extra=""):
        ev.append(f"Dialogue: {layer},{_ts(start)},{_ts(end)},{style_name},,0,0,0,,{extra}{_esc(text)}")

    # header row: the mark (left) and the file number (right), whole video, faint
    line(0, 0.0, total, "Sigil", "WHAT IF")
    if ep.file_number:
        line(0, 0.0, total, "File", ep.file_number)
    # title over the hook
    hook_end = edl["beats"].get("hook", [0, 5])[1]
    title_end = min(hook_end, 5.5)
    line(2, 0.0, title_end, "Title", ep.hook_title, "{\\fad(0,250)}")
    # cards at beat starts
    for e in edl["shots"]:
        c = e.get("card")
        if not c:
            continue
        st = c.get("style", "date")
        if st in ("title", "question"):
            continue
        if st == "stat":
            # big digits on screen while the voice says the words; label underneath
            parts = str(c["text"]).split("\n", 1)
            end = min(e["start"] + max(e["dur"], 2.4), total)
            line(2, e["start"] + 0.05, end, "Stat", parts[0],
                 f"{{\\pos({cx},900)\\fscx60\\fscy60\\t(0,160,\\fscx100\\fscy100)\\fad(80,200)}}")
            if len(parts) > 1:
                line(2, e["start"] + 0.2, end, "StatLabel", parts[1].strip(), f"{{\\pos({cx},1010)\\fad(120,200)}}")
            continue
        line(2, e["start"] + 0.05, min(e["start"] + 2.6, total), "Card", c["text"], "{\\fad(120,220)}")
    # hinge line: a thin bar under the captions that splits at the hinge beat
    hinge = edl["beats"].get("hinge")
    if hinge:
        hs = hinge[0]
        y = H - caption_margin_v + 40
        x0, x1 = left + 60, W - right - 60
        shape = f"m {x0} {y} l {x1} {y} l {x1} {y+4} l {x0} {y+4}"
        bar = f"{{\\p1\\an7\\pos(0,0)\\1c{accent}\\bord0\\shad0\\alpha&H20&}}{shape}{{\\p0}}"
        ev.append(f"Dialogue: 1,{_ts(max(hs-0.6,0))},{_ts(hs+0.6)},Caption,,0,0,0,,{bar}")
        up = f"{{\\p1\\an7\\pos(0,0)\\1c{accent}\\bord0\\shad0\\alpha&H20&\\move(0,0,0,-18,0,500)}}{shape}{{\\p0}}"
        dn = f"{{\\p1\\an7\\pos(0,0)\\1c{accent}\\bord0\\shad0\\alpha&H20&\\move(0,0,0,18,0,500)}}{shape}{{\\p0}}"
        ev.append(f"Dialogue: 1,{_ts(hs+0.6)},{_ts(hs+3.0)},Caption,,0,0,0,,{up}")
        ev.append(f"Dialogue: 1,{_ts(hs+0.6)},{_ts(hs+3.0)},Caption,,0,0,0,,{dn}")
    # captions
    if with_captions:
        title_words = ep.hook_title.upper()
        for c in group_words(timed, ep):
            if c["beat"] == "dilemma":
                continue  # the question card carries the ending
            text = c["text"].upper()
            if c["start"] < title_end and text in title_words:
                continue  # the title already shows these words
            line(3, c["start"], c["end"], "Caption", text)
    # ending: question + stamp
    dil = edl["beats"].get("dilemma")
    if dil:
        ds, de = dil
        q_start = ds + 0.3
        line(4, q_start, total, "Question", ep.dilemma, f"{{\\pos({cx},700)\\fad(200,0)}}")
        stamp_at = max(total - 1.1, q_start + 1.5)
        line(5, stamp_at, total, "Stamp", ep.raw.get("stamp_text", "UNHAPPENED"),
             f"{{\\pos({cx},1180)\\fscx140\\fscy140\\t(0,120,\\fscx100\\fscy100)}}")
    return header + "\n".join(ev) + "\n"


def write_ass(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path
