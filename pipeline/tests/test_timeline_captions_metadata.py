from pathlib import Path

from pipeline import align, captions, metadata, prompts, spec, timeline
from pipeline.config import load_style

EP = Path(__file__).resolve().parents[2] / "episodes" / "ep001-every-human-vanishes.yaml"


def test_estimate_and_edl_snap_to_beats():
    ep = spec.load_episode(EP)
    timed = align.estimate_words(ep, 80.0)
    assert timed[0]["beat"] == "hook" and timed[-1]["beat"] == "dilemma"
    edl = timeline.build_edl(ep, timed, 80.0)
    assert len(edl["shots"]) == len(ep.shots)
    # contiguous, monotonic
    for a, b in zip(edl["shots"], edl["shots"][1:]):
        assert abs(a["end"] - b["start"]) < 1e-6
        assert b["end"] > b["start"]
    # each beat's first shot starts at the beat's first word
    for bid, (bs, be) in edl["beats"].items():
        first = next(s for s in edl["shots"] if s["beat"] == bid)
        assert abs(first["start"] - bs) < 1e-6
    assert 61 <= edl["total"] <= 90


def test_captions_group_and_ass_has_sections():
    ep = spec.load_episode(EP)
    timed = align.estimate_words(ep, 80.0)
    edl = timeline.build_edl(ep, timed, 80.0)
    cards = captions.group_words(timed, ep)
    assert all(1 <= len(c["text"].split()) <= 4 for c in cards)
    assert all(a["end"] <= b["start"] + 1e-9 for a, b in zip(cards, cards[1:]))
    # cards follow the sentence: a card ends on a function word only where the script has punctuation there
    punct_after = set()
    for b in ep.beats:
        for tok in b.vo.split():
            core = tok.strip(".,;:!?\"'”’)—–[]")
            if core and tok.rstrip("\"'”’)")[-1:] in set(captions.HARD_PUNCT + captions.SOFT_PUNCT):
                punct_after.add(core.lower())
    for c in cards:
        last = c["text"].split()[-1].lower()
        if last in captions.FUNCTION_WORDS:
            assert last in punct_after, c
    # a one-word card only where the sentence itself is one word
    assert sum(1 for c in cards if len(c["text"].split()) == 1) <= 2
    ass = captions.build_ass(ep, timed, edl, load_style(), "#C9A227")
    for needle in ("[Script Info]", "Style: Caption", "Style: Stamp", "UNHAPPENED", ep.hook_title, ep.dilemma, "WHAT IF", ep.file_number):
        assert needle in ass
    # nothing is placed in the bottom safe zone (captions sit at ~75 % height) and the title clears the app's tabs
    style = load_style()["typography"]["safe_zone_px"]
    cap = next(l for l in ass.splitlines() if l.startswith("Style: Caption"))
    assert int(cap.split(",")[-2]) >= style["bottom"] + 40


def test_promptsheet_appends_house_style_and_batches_chunk():
    ep = spec.load_episode(EP)
    sheet = prompts.build_promptsheet(ep)
    kp = sheet["shots"][0]["keyframe_prompt"]
    assert "35 mm anamorphic" in kp and "no text" in kp and kp.startswith(ep.shots[0].size + ",")
    batches = prompts.batch_requests(sheet, "keyframes", lookkey_job="00000000-0000-4000-8000-000000000000")
    assert all(len(b) <= 12 for b in batches)
    assert sum(len(b) for b in batches) == 2 * len(ep.shots)
    assert batches[0][0]["params"]["medias"][0]["role"] == "image_references"
    motion = prompts.batch_requests(sheet, "motion", keyframe_jobs={"shot-01": "job-1"})
    assert motion[0][0]["params"]["model"] == "kling3_0" and motion[0][0]["params"]["sound"] == "off"


def test_metadata_has_disclosure_and_pinned_comment():
    ep = spec.load_episode(EP)
    m = metadata.build_metadata(ep)
    assert m["tiktok"]["is_aigc"] is True
    assert "Alternate timeline" in m["youtube"]["description"]
    assert m["tiktok"]["pinned_comment"] == ep.pinned_comment
    assert len(m["tiktok"]["hashtags"]) <= 5


def test_clip_segment_pads_short_clips_and_keeps_moving(tmp_path):
    import subprocess
    from pipeline import assemble as asm
    clip = tmp_path / "shot-01.mp4"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-t", "5", "-i",
                    "testsrc=size=720x1280:rate=24", "-pix_fmt", "yuv420p", str(clip)], check=True)
    inputs, chain = asm._video_segment(0, "clip", clip, 6.2, "shot-01", 1)
    assert "tpad=stop_mode=clone" in chain and "zoompan" in chain and "trim=duration=6.200" in chain
    out = tmp_path / "seg.mp4"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs, "-filter_complex", chain,
                    "-map", "[v0]", "-c:v", "libx264", "-preset", "ultrafast", str(out)], check=True)
    assert abs(asm._probe_duration(out) - 6.2) < 0.1


def test_hook_coverage_rule():
    ep = spec.load_episode(EP)
    for s in ep.shots_for("hook")[1:]:
        s.dur = 1.5
    errors, _ = spec.validate(ep)
    assert any("Add a hook shot" in e for e in errors)
