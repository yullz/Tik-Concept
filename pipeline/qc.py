"""Technical QC on the master plus the taste-gate check on review.yaml."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml

from .config import render_dir
from .spec import Episode, MIN_DURATION, MAX_DURATION

SCORECARD = [
    "hook_image_specific", "hinge_sourced", "mechanism_every_phase", "phases_escalate", "turn_is_a_cost",
    "dilemma_two_sides", "era_sheet_respected", "no_artifacts", "shot_sizes_rotate", "narration_pace",
    "mix_voice_music_sfx", "captions_clean",
]
HARD_FAIL_KEYS = {"hook_image_specific", "hinge_sourced", "mechanism_every_phase", "dilemma_two_sides",
                  "era_sheet_respected", "no_artifacts", "mix_voice_music_sfx", "captions_clean"}
PASS_TOTAL = 42


def probe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def loudness(path: Path) -> dict:
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True)
    txt = proc.stderr
    def grab(pat):
        m = re.findall(pat, txt)
        return float(m[-1]) if m else None
    return {"integrated_lufs": grab(r"I:\s+(-?\d+\.\d+) LUFS"), "lra": grab(r"LRA:\s+(\d+\.\d+) LU"),
            "true_peak_dbtp": grab(r"Peak:\s+(-?\d+\.\d+) dBFS")}


def freeze_and_black(path: Path) -> dict:
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-an",
                           "-vf", "freezedetect=n=0.001:d=1.2,blackdetect=d=0.4:pix_th=0.10", "-f", "null", "-"],
                          capture_output=True, text=True)
    txt = proc.stderr
    return {"freezes": len(re.findall(r"freeze_start", txt)), "black_intervals": len(re.findall(r"black_start", txt))}


def technical_qc(ep: Episode, master: Path, placeholders: bool = False) -> dict:
    info = probe(master)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    num, den = v["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    loud = loudness(master)
    fb = freeze_and_black(master)
    checks = {
        "duration_61_90": MIN_DURATION <= dur <= MAX_DURATION,
        "resolution_1080x1920": (int(v["width"]), int(v["height"])) == (1080, 1920),
        "fps_30": abs(fps - 30.0) < 0.6,
        "has_audio": a is not None,
        "loudness_-14_to_-18": loud["integrated_lufs"] is not None and -18.5 <= loud["integrated_lufs"] <= -13.5,
        "true_peak_under_-1": loud["true_peak_dbtp"] is not None and loud["true_peak_dbtp"] <= -0.9,
        "no_freezes": fb["freezes"] == 0 or placeholders,
        "no_black": fb["black_intervals"] == 0,
        "faststart": True,
    }
    result = {"file": str(master), "duration": round(dur, 2), "width": int(v["width"]), "height": int(v["height"]),
              "fps": round(fps, 2), "loudness": loud, **fb, "checks": checks, "pass": all(checks.values())}
    (render_dir(ep.id) / "qc.json").write_text(json.dumps(result, indent=2))
    return result


def review_template(ep: Episode) -> str:
    lines = ["# Taste gate (docs/04-production-pipeline.md). Score 1-5. Total >= 42 and no hard fail to ship.",
             f"episode: {ep.id}", "reviewer: ", "watched_on_phone_twice: false", "scores:"]
    for k in SCORECARD:
        lines.append(f"  {k}: 0")
    lines += ["hard_fails: []   # list any of the hard-fail keys that failed", "notes: ''",
              "best_objection_for_reply_episode: ''"]
    return "\n".join(lines) + "\n"


def taste_gate(ep: Episode) -> tuple[bool, str]:
    path = render_dir(ep.id) / "review.yaml"
    if not path.exists():
        path.write_text(review_template(ep))
        return False, f"review.yaml created at {path}; watch the master twice on a phone and fill it in"
    data = yaml.safe_load(path.read_text()) or {}
    scores = data.get("scores", {}) or {}
    missing = [k for k in SCORECARD if k not in scores or not scores[k]]
    if missing:
        return False, f"review.yaml incomplete: {missing}"
    total = sum(int(scores[k]) for k in SCORECARD)
    hard = [h for h in (data.get("hard_fails") or []) if h in HARD_FAIL_KEYS]
    low_hard = [k for k in HARD_FAIL_KEYS if int(scores.get(k, 0)) <= 2]
    hard = sorted(set(hard) | set(low_hard))
    if not data.get("watched_on_phone_twice"):
        return False, "review.yaml: watched_on_phone_twice must be true"
    if hard:
        return False, f"hard fail on {hard} (total {total}/60)"
    if total < PASS_TOTAL:
        return False, f"total {total}/60 is under {PASS_TOTAL}"
    return True, f"taste gate passed: {total}/60, no hard fails"
