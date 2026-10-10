"""`python -m pipeline <command> <episode.yaml>`"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from . import align, assemble as asm, captions, lint, metadata as meta, prompts, qc, spec, timeline, tts, visuals, contact_sheet
from .config import ASSETS_DIR, EPISODES_DIR, load_style, render_dir


def _ep(path: str) -> spec.Episode:
    return spec.load_episode(path)


def _print_issues(errors, warnings, label):
    for w in warnings:
        print(f"  warn  {w}")
    for e in errors:
        print(f"  ERROR {e}")
    print(f"{label}: {len(errors)} errors, {len(warnings)} warnings")


def cmd_validate(a):
    ep = _ep(a.episode)
    errors, warnings = spec.validate(ep)
    print(f"{ep.id}: {ep.word_count} words ≈ {ep.est_duration:.1f}s at 2.5 w/s (target {ep.target_duration}s); {len(ep.shots)} shots, "
          f"avg {sum(s.dur for s in ep.shots)/max(len(ep.shots),1):.2f}s planned")
    _print_issues(errors, warnings, "validate")
    return 1 if errors else 0


def cmd_lint(a):
    ep = _ep(a.episode)
    errors, warnings = lint.lint_episode(ep)
    _print_issues(errors, warnings, "lint")
    return 1 if errors else 0


def cmd_promptsheet(a):
    ep = _ep(a.episode)
    out = prompts.write_promptsheet(ep, a.style)
    print(f"wrote {out} and keyframe_batches.json ({len(ep.shots)} shots × 2 variants)")
    return 0


def cmd_contact(a):
    ep = _ep(a.episode)
    out = contact_sheet.write_contact_sheet(ep)
    print(f"wrote {out}; fill selections.yaml then run `select`")
    return 0


def cmd_select(a):
    ep = _ep(a.episode)
    s = contact_sheet.apply_selections(ep)
    print(json.dumps(s, indent=2))
    return 0


def cmd_motionbatch(a):
    ep = _ep(a.episode)
    jobs = json.loads(Path(a.keyframe_jobs).read_text())
    out = visuals.write_motion_batches(ep, jobs, a.style)
    print(f"wrote {out}")
    return 0


def cmd_ingest(a):
    ep = _ep(a.episode)
    mapping = json.loads(Path(a.mapping).read_text())
    saved = visuals.ingest(ep, mapping, a.kind)
    print(f"saved {len(saved)} files")
    return 0


def cmd_tts(a):
    ep = _ep(a.episode)
    rdir = render_dir(ep.id)
    if a.backend == "higgsfield":
        p = tts.write_higgsfield_request(ep)
        print(f"wrote {p}; run generate_audio with that body, then save the result as {rdir/'audio'/'vo.mp3'}")
        return 0
    vo, wj = tts.elevenlabs_tts(ep)
    dur = align.audio_duration(vo)
    pace = tts.measure_pace(ep, dur)
    print(json.dumps(pace))
    if pace["verdict"] != "ok":
        print("pace out of range: rewrite the line(s) and regenerate; never time-stretch")
        return 1
    return 0


def cmd_plan(a):
    ep = _ep(a.episode)
    rdir = render_dir(ep.id)
    vo = rdir / "audio" / "vo.mp3"
    if not vo.exists():
        vo = rdir / "audio" / "vo.wav"
    if not vo.exists():
        print(f"no narration at {rdir/'audio'}; run tts first (or dryrun)"); return 1
    wj = rdir / "audio" / "words.json"
    timed, source = align.get_words(ep, vo, wj if wj.exists() else None, allow_estimate=a.estimate)
    (rdir / "audio" / "words_timed.json").write_text(json.dumps(timed, indent=1))
    dur = align.audio_duration(vo)
    pace = tts.measure_pace(ep, dur)
    edl = timeline.build_edl(ep, timed, dur)
    timeline.write_edl(ep, edl)
    print(f"alignment: {source}; pace {pace['wps']} w/s ({pace['verdict']}); total {edl['total']}s; {len(edl['shots'])} shots")
    for w in edl["warnings"]:
        print(f"  warn  {w}")
    return 0


def cmd_assemble(a):
    ep = _ep(a.episode)
    rdir = render_dir(ep.id)
    edl = json.loads((rdir / "edl.json").read_text())
    timed = json.loads((rdir / "audio" / "words_timed.json").read_text())
    style = load_style(a.style)
    accent = {"never-fell": "#C9A227", "tomorrow-morning": "#2BB3C0", "early-arrival": "#E8872B", "the-hinge": "#B8322F"}.get(ep.pillar, "#C9A227")
    ass_text = captions.build_ass(ep, timed, edl, style, accent, with_captions=not a.no_captions)
    ass_path = captions.write_ass(rdir / "captions.ass", ass_text)
    vo = rdir / "audio" / "vo.mp3"
    if not vo.exists():
        vo = rdir / "audio" / "vo.wav"
    music = asm.find_music(ep) if not a.no_music else None
    out = rdir / ("master.mp4" if not a.placeholders else "dryrun.mp4")
    rep = asm.assemble(ep, edl, ass_path, vo, music, ASSETS_DIR / "sfx", out, allow_placeholders=a.placeholders, style_name=a.style)
    print(f"wrote {out} ({rep['duration']:.2f}s; placeholders {rep['placeholders']}; sfx placed {rep['sfx_placed']}; music {'yes' if music else 'no'})")
    return 0


def cmd_qc(a):
    ep = _ep(a.episode)
    rdir = render_dir(ep.id)
    master = rdir / ("dryrun.mp4" if a.placeholders else "master.mp4")
    if not master.exists():
        print(f"missing {master}"); return 1
    res = qc.technical_qc(ep, master, placeholders=a.placeholders)
    for k, v in res["checks"].items():
        print(f"  {'ok  ' if v else 'FAIL'} {k}")
    print(f"technical: {'PASS' if res['pass'] else 'FAIL'} · {res['duration']}s · {res['loudness']['integrated_lufs']} LUFS · peak {res['loudness']['true_peak_dbtp']} dBTP")
    ok, msg = qc.taste_gate(ep)
    print(f"taste gate: {msg}")
    return 0 if (res["pass"] and (ok or a.placeholders)) else 1


def cmd_metadata(a):
    ep = _ep(a.episode)
    out = meta.write_metadata(ep, a.channel)
    print(f"wrote {out}")
    return 0


def cmd_cover(a):
    ep = _ep(a.episode)
    rdir = render_dir(ep.id)
    master = rdir / "master.mp4"
    t = float(a.time if a.time is not None else (ep.metadata or {}).get("cover_time", 0.8))
    out = rdir / "publish" / "cover.jpg"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(master), "-frames:v", "1", "-q:v", "2", str(out)], check=True)
    print(f"wrote {out}")
    return 0


def cmd_bundle(a):
    ep = _ep(a.episode)
    rdir = render_dir(ep.id)
    ok, msg = qc.taste_gate(ep)
    if not ok:
        print(f"refusing to bundle: {msg}"); return 1
    q = rdir / "qc.json"
    if not q.exists() or not json.loads(q.read_text()).get("pass"):
        print("refusing to bundle: technical QC has not passed"); return 1
    meta.write_metadata(ep, a.channel)
    out = meta.bundle(ep, rdir / "master.mp4")
    print(f"bundle ready: {out}")
    return 0


def cmd_new(a):
    tpl = {
        "id": a.id, "series": a.series, "series_number": a.number, "pillar": a.series, "title": a.title,
        "hook_title": f"WHAT IF {a.title.upper()}", "file_number": f"FILE B-{a.number:04d}", "target_duration": 76,
        "stamp_text": "NEVER HAPPENED",
        "voice": {"direction": "calm dry archivist, British-leaning, unhurried, lets facts land", "voice_type": "preset", "voice_id": ""},
        "music": {"mood": "", "cue": f"assets/music/{a.series}-01.mp3"}, "look_key_prompt": "",
        "research": {"hinge": "", "hinge_date": "", "sources": [], "facts": [], "era_sheet": {}, "cost": ""},
        "beats": [{"id": b, "vo": "", "card": None} for b in spec.BEAT_ORDER], "shots": [],
        "dilemma": "", "pinned_comment": "", "metadata": {"cover_time": 1.0, "second_comment": "", "hashtags": []},
    }
    path = EPISODES_DIR / f"{a.id}.yaml"
    path.write_text(yaml.safe_dump(tpl, sort_keys=False, allow_unicode=True, width=120))
    print(f"wrote {path}")
    return 0


def cmd_dryrun(a):
    """Offline end-to-end: synthetic silent narration of the estimated length, placeholder shots, full assembly and QC."""
    ep = _ep(a.episode)
    rc = cmd_validate(a) | cmd_lint(a)
    if rc:
        return rc
    rdir = render_dir(ep.id)
    prompts.write_promptsheet(ep, a.style)
    vo = rdir / "audio" / "vo.wav"
    est = ep.word_count / 2.5 + 0.5 * (len(ep.beats) - 1)
    # a quiet tone burst per word would be noise; use near-silence so loudnorm has something to measure
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-t", f"{est:.2f}", "-i",
                    "sine=frequency=220:sample_rate=48000", "-af", "volume=0.02", str(vo)], check=True)
    wj = rdir / "audio" / "words.json"
    if wj.exists():
        wj.unlink()
    a.estimate = True
    cmd_plan(a)
    a.placeholders = True; a.no_captions = False; a.no_music = True
    cmd_assemble(a)
    return cmd_qc(a)


def cmd_write(a):
    from . import llm
    out = EPISODES_DIR / f"{a.id}.yaml"
    llm.write_episode(a.brief, out)
    print(f"wrote {out}")
    return 0


def cmd_localize(a):
    from . import llm
    out = llm.localize_episode(Path(a.episode), a.lang)
    print(f"wrote {out}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, **kw):
        sp = sub.add_parser(name, help=kw.pop("help", None))
        sp.set_defaults(fn=fn)
        return sp

    for name, fn in (("validate", cmd_validate), ("lint", cmd_lint), ("contact", cmd_contact), ("select", cmd_select)):
        add(name, fn).add_argument("episode")
    sp = add("promptsheet", cmd_promptsheet); sp.add_argument("episode"); sp.add_argument("--style", default="counterfact-v1")
    sp = add("motionbatch", cmd_motionbatch); sp.add_argument("episode"); sp.add_argument("keyframe_jobs"); sp.add_argument("--style", default="counterfact-v1")
    sp = add("ingest", cmd_ingest); sp.add_argument("episode"); sp.add_argument("mapping"); sp.add_argument("--kind", choices=["keyframes", "clips"], required=True)
    sp = add("tts", cmd_tts); sp.add_argument("episode"); sp.add_argument("--backend", choices=["elevenlabs", "higgsfield"], default="higgsfield")
    sp = add("plan", cmd_plan); sp.add_argument("episode"); sp.add_argument("--estimate", action="store_true")
    sp = add("assemble", cmd_assemble); sp.add_argument("episode"); sp.add_argument("--style", default="counterfact-v1")
    sp.add_argument("--placeholders", action="store_true"); sp.add_argument("--no-captions", action="store_true"); sp.add_argument("--no-music", action="store_true")
    sp = add("qc", cmd_qc); sp.add_argument("episode"); sp.add_argument("--placeholders", action="store_true")
    sp = add("metadata", cmd_metadata); sp.add_argument("episode"); sp.add_argument("--channel", default="Counterfact")
    sp = add("cover", cmd_cover); sp.add_argument("episode"); sp.add_argument("--time", type=float, default=None)
    sp = add("bundle", cmd_bundle); sp.add_argument("episode"); sp.add_argument("--channel", default="Counterfact")
    sp = add("dryrun", cmd_dryrun); sp.add_argument("episode"); sp.add_argument("--style", default="counterfact-v1")
    sp = add("new", cmd_new); sp.add_argument("id"); sp.add_argument("--series", required=True); sp.add_argument("--number", type=int, required=True); sp.add_argument("--title", required=True)
    sp = add("write", cmd_write); sp.add_argument("id"); sp.add_argument("--brief", required=True)
    sp = add("localize", cmd_localize); sp.add_argument("episode"); sp.add_argument("--lang", required=True)

    a = p.parse_args(argv)
    return a.fn(a)
