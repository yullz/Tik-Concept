from pathlib import Path

from pipeline import align, captions, metadata, prompts, spec, timeline
from pipeline.config import load_style

EP = Path(__file__).resolve().parents[2] / "episodes" / "ep001-rome-never-fell.yaml"


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
    cards = captions.group_words(timed)
    assert all(1 <= len(c["text"].split()) <= 3 for c in cards)
    assert all(a["end"] <= b["start"] + 1e-9 for a, b in zip(cards, cards[1:]))
    ass = captions.build_ass(ep, timed, edl, load_style(), "#C9A227")
    for needle in ("[Script Info]", "Style: Caption", "Style: Stamp", "NEVER HAPPENED", "WHAT IF ROME NEVER FELL", ep.dilemma):
        assert needle in ass


def test_promptsheet_appends_house_style_and_batches_chunk():
    ep = spec.load_episode(EP)
    sheet = prompts.build_promptsheet(ep)
    kp = sheet["shots"][0]["keyframe_prompt"]
    assert "35 mm anamorphic" in kp and "no text" in kp and kp.startswith("WIDE,")
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
