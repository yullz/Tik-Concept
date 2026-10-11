from datetime import date

from pipeline import schedule


def test_schedule_launch_day_evening_then_two_a_day():
    entries = schedule.build_schedule(date(2026, 10, 20), "Europe/Sofia", ["07:00", "18:00"])
    tiktok = [e for e in entries if e["platform"] == "tiktok"]
    assert tiktok[0]["scheduled_local"].startswith("2026-10-20T18:00")
    assert tiktok[1]["scheduled_local"].startswith("2026-10-21T07:00")
    assert tiktok[2]["scheduled_local"].startswith("2026-10-21T18:00")
    assert tiktok[0]["scheduled_utc"] == "2026-10-20T15:00:00Z"
    assert len(entries) == 3 * len(tiktok)
    assert all(e["pinned_comment"] for e in tiktok)
