"""ffmpeg assembly: shots → picture; VO + music + SFX → mix; captions burned; one master.

Sources per shot, in priority order:
  renders/<id>/clips/shot-NN.mp4          (approved motion clip)
  renders/<id>/keyframes/shot-NN.png      (approved still → parallax push)
  placeholder (dry run only)              (labelled test pattern)
"""
from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

from .config import ASSETS_DIR, load_style, render_dir
from .spec import Episode

FPS = 30
W, H = 1080, 1920
PUNCH_IN_AFTER = 3.8     # seconds: shots at least this long get a hard punch-in at ~55%
PUNCH_IN_SCALE = 1.045
CLIP_PUSH = 0.03        # continuous push over a clip shot (1.00 -> 1.03) so nothing ever sits still


def _probe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def find_source(rdir: Path, shot_name: str, mode: str) -> tuple[str, Path | None]:
    clip = rdir / "clips" / f"{shot_name}.mp4"
    still = next((p for p in (rdir / "keyframes").glob(f"{shot_name}.*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}), None)
    if mode == "video" and clip.exists():
        return "clip", clip
    if still is not None:
        return "still", still
    if clip.exists():
        return "clip", clip
    return "placeholder", None


def _video_segment(idx: int, kind: str, src: Path | None, dur: float, label: str, seed: int) -> tuple[list[str], str]:
    """Return (input args, filter chain) producing [v{idx}] of exactly dur seconds."""
    frames = max(int(round(dur * FPS)), 1)
    tag = f"[v{idx}]"
    punch = dur >= PUNCH_IN_AFTER
    mid = max(int(frames * 0.55), 1)
    if kind == "clip":
        clip_len = _probe_duration(src)
        # use the middle of the clip when it is longer than needed (the model's first frames are the weakest)
        offset = max(0.0, min((clip_len - dur) * 0.35, clip_len - dur)) if clip_len > dur else 0.0
        inputs = ["-ss", f"{offset:.3f}", "-t", f"{dur + 0.2:.3f}", "-i", str(src)]
        # a generated clip is 5 s; a shot can run longer (beat snapping, the final hold). Pad by cloning the
        # last frame so the picture never runs short of the narration, and keep a continuous slow push
        # (1.00 -> 1.03) over the whole shot so neither a static clip start nor a padded tail ever freezes.
        punch_term = f"+if(gte(on,{mid}),{PUNCH_IN_SCALE-1.0:.3f},0)" if punch else ""
        chain = (f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,"
                 f"tpad=stop_mode=clone:stop_duration={dur + 1.0:.3f},"
                 f"scale={W*2}:{H*2},zoompan=z='1+{CLIP_PUSH:.3f}*on/{frames}{punch_term}':x='iw/2-(iw/zoom/2)':"
                 f"y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
                 f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p{tag}")
    elif kind == "still":
        inputs = ["-loop", "1", "-t", f"{dur + 0.2:.3f}", "-i", str(src)]
        # slow push 1.00 → 1.035 with a slight drift (zoompan works on a larger canvas to avoid jitter)
        punch_term = f"+if(gte(on,{mid}),{PUNCH_IN_SCALE-1.0:.3f},0)" if punch else ""
        chain = (f"[{idx}:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
                 f"zoompan=z='1+0.035*on/{frames}{punch_term}':x='iw/2-(iw/zoom/2)+({seed%7-3})*on/{frames}':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
                 f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p{tag}")
    else:
        hue = (seed * 47) % 360
        inputs = ["-f", "lavfi", "-t", f"{dur + 0.2:.3f}", "-i",
                  f"color=c=0x202830:s={W}x{H}:r={FPS},hue=h={hue}:s=0.6"]
        safe = label.replace("'", "").replace(":", " ")
        # the placeholder drifts so freeze detection behaves like a real clip
        chain = (f"[{idx}:v]drawtext=text='{safe}':fontcolor=white@0.6:fontsize=54:x=(w-text_w)/2+40*sin(t):y=h/2+30*cos(t/2),"
                 f"drawbox=x=90+60*t:y=600:w=120:h=8:color=white@0.25:t=fill,"
                 f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p{tag}")
    return inputs, chain


def assemble(ep: Episode, edl: dict, ass_path: Path | None, vo: Path, music: Path | None,
             sfx_dir: Path | None, out_path: Path, allow_placeholders: bool = False,
             style_name: str = "counterfact-v1") -> dict:
    style = load_style(style_name)
    rdir = render_dir(ep.id)
    inputs: list[str] = []
    chains: list[str] = []
    report = {"shots": [], "placeholders": 0}
    n = 0
    for e in edl["shots"]:
        kind, src = find_source(rdir, e["shot"], e["mode"])
        if kind == "placeholder":
            if not allow_placeholders:
                raise SystemExit(f"{e['shot']}: no approved clip or keyframe in {rdir}; run gates A/B first")
            report["placeholders"] += 1
        label = f"{e['shot']} {e['size']} {e['beat']}"
        ins, chain = _video_segment(n, kind, src, e["dur"], label, e["index"])
        inputs += ins; chains.append(chain)
        report["shots"].append({"shot": e["shot"], "source": kind, "file": str(src) if src else None, "dur": e["dur"]})
        n += 1
    vtags = "".join(f"[v{i}]" for i in range(n))
    chains.append(f"{vtags}concat=n={n}:v=1:a=0[vcat]")
    vfinal = "[vcat]"
    if ass_path is not None:
        chains.append(f"[vcat]ass={shlex.quote(str(ass_path))}[vsub]")
        vfinal = "[vsub]"

    # ---- audio ---------------------------------------------------------
    mix = style["mix"]
    a_idx = n
    inputs += ["-i", str(vo)]
    chains.append(f"[{a_idx}:a]aresample=48000,loudnorm=I={mix['voice_lufs']}:TP=-1.5:LRA=9,aformat=channel_layouts=stereo,asplit=2[vo][vo_key]")
    a_idx += 1
    audio_terms = ["[vo]"]
    if music is not None and music.exists():
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        chains.append(f"[{a_idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={mix['music_db_in_gaps']+16}dB,"
                      f"atrim=duration={edl['total']:.3f},afade=t=out:st={max(edl['total']-1.5,0):.2f}:d=1.5[mus_raw]")
        # sidechain duck under the voice
        chains.append(f"[mus_raw][vo_key]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=400:makeup=1[mus]")
        audio_terms.append("[mus]")
        a_idx += 1
    else:
        chains.append("[vo_key]anullsink")
    # SFX cues: assets/sfx/<slug>.wav placed at the shot start
    sfx_count = 0
    if sfx_dir is not None:
        for e in edl["shots"]:
            if not e.get("sfx"):
                continue
            slug = "".join(ch if ch.isalnum() else "-" for ch in e["sfx"].lower()).strip("-")
            cand = next((p for p in sfx_dir.glob(f"{slug}.*") if p.suffix.lower() in {".wav", ".mp3", ".ogg"}), None)
            if cand is None:
                continue
            inputs += ["-i", str(cand)]
            delay_ms = int(e["start"] * 1000)
            chains.append(f"[{a_idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={mix['sfx_peak_dbfs']+14}dB,adelay={delay_ms}|{delay_ms}[sfx{sfx_count}]")
            audio_terms.append(f"[sfx{sfx_count}]")
            a_idx += 1; sfx_count += 1
    if sfx_dir is not None:
        card_sfx = next((p for p in sfx_dir.glob("card.*") if p.suffix.lower() in {".wav", ".mp3", ".ogg"}), None)
        if card_sfx is not None:
            for e in edl["shots"]:
                if not e.get("card") or e["card"].get("style") == "title":
                    continue
                inputs += ["-i", str(card_sfx)]
                delay_ms = int(e["start"] * 1000)
                chains.append(f"[{a_idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={mix['sfx_peak_dbfs']+10}dB,adelay={delay_ms}|{delay_ms}[sfx{sfx_count}]")
                audio_terms.append(f"[sfx{sfx_count}]")
                a_idx += 1; sfx_count += 1
    chains.append(f"{''.join(audio_terms)}amix=inputs={len(audio_terms)}:duration=first:normalize=0,"
                  f"alimiter=limit=0.89:level=false,atrim=duration={edl['total']:.3f}[aout]")
    report["sfx_placed"] = sfx_count

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
           "-filter_complex", ";".join(chains), "-map", vfinal, "-map", "[aout]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
           "-t", f"{edl['total']:.3f}", str(out_path)]
    (rdir / "ffmpeg_cmd.txt").write_text(" ".join(shlex.quote(c) for c in cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"ffmpeg failed:\n{proc.stderr[-4000:]}")
    report["output"] = str(out_path)
    report["duration"] = _probe_duration(out_path)
    (rdir / "assemble_report.json").write_text(json.dumps(report, indent=2))
    return report


def find_music(ep: Episode) -> Path | None:
    cue = (ep.music or {}).get("cue")
    if cue:
        p = Path(cue)
        if not p.is_absolute():
            p = ASSETS_DIR.parent / p
        if p.exists():
            return p
    pillar_dir = ASSETS_DIR / "music"
    cands = sorted(p for p in pillar_dir.glob(f"{ep.pillar}*") if p.suffix.lower() in {".mp3", ".wav"})
    return cands[0] if cands else None
