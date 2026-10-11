"""Posting schedule: turn the launch order into dated slots per platform.

`python3 -m pipeline schedule --start 2026-10-20 --tz Europe/Sofia --slots 18:00,07:00`
writes publish/schedule.yaml (one entry per episode per platform, local time and UTC) and
creates publish/post-log.csv if missing. Day one gets only the evening slot; every later day
gets every slot, so two episodes a day after launch day.
"""
from __future__ import annotations

import csv
import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from .config import EPISODES_DIR, ROOT, render_dir
from .metadata import build_metadata
from .spec import load_episode

PLATFORMS = ["tiktok", "youtube", "instagram"]
LOG_HEADER = ["episode_id", "file_number", "platform", "account", "scheduled_local", "scheduled_utc", "posted_at",
              "post_id", "url", "pinned_comment_posted", "second_comment_posted", "notes"]


def launch_order() -> list[Path]:
    return sorted(p for p in EPISODES_DIR.glob("ep*.yaml"))


def build_schedule(start: date, tz: str, slots: list[str], platforms: list[str] | None = None,
                   youtube_offset_minutes: int = 0) -> list[dict]:
    """Sequential slots: day one uses only the last slot of the list (the evening), then all slots daily."""
    zone = ZoneInfo(tz)
    platforms = platforms or PLATFORMS
    times = [time.fromisoformat(s) for s in slots]
    entries = []
    day = start
    slot_i = len(times) - 1          # launch day: evening slot only
    for path in launch_order():
        ep = load_episode(path)
        meta = build_metadata(ep)
        local = datetime.combine(day, times[slot_i], tzinfo=zone)
        for plat in platforms:
            when = local + timedelta(minutes=youtube_offset_minutes if plat == "youtube" else 0)
            entries.append({
                "episode_id": ep.id, "file_number": ep.file_number, "title": ep.title, "platform": plat,
                "scheduled_local": when.isoformat(), "scheduled_utc": when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "bundle": str(render_dir(ep.id) / "publish" / f"{ep.id}.mp4"),
                "caption_title": meta["tiktok"]["title"] if plat == "tiktok" else meta["youtube"]["title"],
                "pinned_comment": ep.pinned_comment, "second_comment": meta["tiktok"]["second_comment"],
            })
        slot_i += 1
        if slot_i >= len(times):
            slot_i = 0
            day += timedelta(days=1)
    return entries


def write_schedule(entries: list[dict]) -> Path:
    out = ROOT / "publish"; out.mkdir(exist_ok=True)
    (out / "schedule.yaml").write_text(yaml.safe_dump({"generated_for": len(entries), "entries": entries}, sort_keys=False, allow_unicode=True))
    log = out / "post-log.csv"
    if not log.exists():
        with log.open("w", newline="") as f:
            csv.writer(f).writerow(LOG_HEADER)
    return out / "schedule.yaml"


def append_log(row: dict) -> None:
    log = ROOT / "publish" / "post-log.csv"
    log.parent.mkdir(exist_ok=True)
    new = not log.exists()
    with log.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_HEADER)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in LOG_HEADER})
