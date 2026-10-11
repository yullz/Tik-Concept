# HANDOFF · Publishing chat (Claude Opus 5.5)

Paste this file as the first message of a new Claude Code session opened in this repository, or
say "Read HANDOFF-PUBLISHER.md and start." You are the publisher. You schedule and upload the
finished masters to TikTok and YouTube Shorts, run the posting-day checklist, and log results.
You never change a video, never post anything that has not passed the taste gate, and never
post the same body twice.

## 1. Inputs: what a finished episode looks like

The producer chat (`HANDOFF-PRODUCER.md`) leaves each finished episode in
`renders/<episode-id>/publish/`:

| File | Use |
|---|---|
| `<id>.mp4` | the master, 1080×1920, 30 fps, 61–90 s, captions and the UNHAPPENED stamp burned in |
| `cover.jpg` | the cover frame (choose the same moment in the TikTok and YouTube uploaders) |
| `metadata.json` / `metadata.md` | titles, description, hashtags, pinned comment, second comment, AI flags |
| `review.yaml`, `qc.json` | proof the taste gate and technical QC passed |

The bundle only exists if the gates passed (`pipeline bundle` refuses otherwise). If a folder
has an `.mp4` but no `review.yaml` with `watched_on_phone_twice: true`, do not post it; tell the owner.

## 2. Accounts and one-time setup

**TikTok (through the Higgsfield MCP, connected in this session):**
1. `tiktok_accounts` → if none, `tiktok_connect` and send the owner the authorise link (expires in ~10 minutes); then `tiktok_accounts` again until `active`.
2. The master must be Higgsfield-hosted for publishing: reserve with `media_upload` (`filename: <id>.mp4`, `content_type: video/mp4`), PUT the file with the returned curl command from the machine that holds it, then `media_confirm` with `type: video`. Keep the returned URL.

**YouTube (Data API v3, our own script):**
1. In Google Cloud: create a project, enable *YouTube Data API v3*, configure the OAuth consent screen (External; add the channel's Google account as a test user), create an OAuth client ID of type *Desktop app*, download the JSON to `secrets/youtube-client-secret.json` (git-ignored).
2. `pip install google-api-python-client google-auth-oauthlib`
3. The first `youtube-upload` opens a browser to authorise the channel; the token is cached in `secrets/youtube-token.json`.
4. Quota: 10,000 units a day; one upload costs 1,600, so at most six uploads a day until Google grants an increase (apply early; it needs a compliance audit).

**Instagram and Facebook Reels:** manual through Meta Business Suite's scheduler with the caption from `metadata.json → instagram.caption`; tick the AI label.

## 3. Build the schedule

```
python3 -m pipeline schedule --start 2026-10-20 --tz Europe/Sofia --slots 07:00,18:00
```
Writes `publish/schedule.yaml`: launch day gets only the evening slot, every later day gets both,
in file order (`ep001` first). Each entry has local and UTC times, the bundle path, the title,
the pinned comment and the second comment. Ask the owner for the launch date and timezone before
running it; after week one, lock the two slots that held the 5-second view rate best
(`docs/03-growth-plan-10M.md`) and regenerate.

Rules: one episode per slot, every platform gets the same master at its slot, never two posts
with the same body, never a re-upload with a different hook. Language accounts (later) get their
own re-cut masters from the producer, never this file.

## 4. TikTok: upload and schedule

TikTok's web uploader can schedule a post up to ten days ahead; the API route cannot. So:

1. The day before the slot, call `tiktok_prepare_publish` with `connector_id`, `mode: UPLOAD_TO_DRAFT`, `media_type: VIDEO`, `video_url` (the confirmed Higgsfield URL), `title` (≤ 150 characters: the TikTok title from metadata plus its five hashtags), `is_aigc: true`, `privacy_level: PUBLIC_TO_EVERYONE`, `allow_comment: true`, `allow_duet: true`, `allow_stitch: true`. The widget opens; the owner reviews and submits it. You never submit it yourself.
2. The owner opens the draft in the TikTok app or web uploader, sets the cover to the same frame as `cover.jpg`, and schedules it for the slot. Poll `tiktok_publish_status` with the `publish_id` until processed.
3. Alternative when the owner is at the keyboard at slot time: `mode: DIRECT_POST` at the slot, same fields, owner submits.
4. Within one minute of the post going live, the owner pins the pinned comment (TikTok has no API for pinning); the second comment goes from the team account. Log both in `publish/post-log.csv`.

## 5. YouTube Shorts: upload with a scheduled publish time

```
python3 -m pipeline youtube-upload episodes/<id>.yaml --publish-at 2026-10-21T18:00:00+03:00
```
Uploads private with `publishAt` set, so YouTube makes it public at the slot. It takes the
title (≤ 100 characters), description, tags and category from `metadata.json`, sets
`selfDeclaredMadeForKids: false` and `containsSyntheticMedia: true` (the altered-content
disclosure), and logs the video id and URL. Vertical and under three minutes is enough for it
to be a Short; no hashtag is required. Set the cover frame in YouTube Studio (Shorts take a
frame from the video) and, once live, link the previous episode as the related video.

After it is live:
```
python3 -m pipeline youtube-comment <video_id> --text "<pinned comment from metadata.json>"
```
then pin that comment in YouTube Studio (the API cannot pin). Post the second comment from the team account.

## 6. Posting-day checklist (every slot)

- T−24 h: bundle exists with a passing review; TikTok draft prepared; YouTube scheduled; Reels scheduled.
- T−0: confirm all three went live; pin the pinned comment within one minute; second comment within five.
- T+0 to T+60 min: reply to every real argument in one sentence each (never paragraphs, never insults); collect the best objection into `renders/<id>/replies.md` for the reply episode.
- T+24 h and T+7 d: record views, 5-second view rate, 3-second hold, average watch, completion, comments, shares, saves, follows per platform in `analytics/week-NN.csv` (header in `analytics/README.md`).
- Log everything in `publish/post-log.csv` (post id, URL, times, comment status, notes).

## 7. Compliance (these keep the account alive)

- Every post is labelled AI-generated on TikTok (`is_aigc`) and altered content on YouTube; the description carries "Alternate timeline".
- No third-party footage, music or audio is ever added at upload time; the master is final.
- No duplicates across the same account; no reposting a TikTok video to the same TikTok account; no "hook variants".
- Comments are a dilemma, not rage bait: the pinned comment takes one side with one fact, the second comment the other.
- Never post a video that fails `qc.json` or lacks a passing `review.yaml`, whatever the schedule says; a missed slot is better than a slop post.

## 8. The weekly loop (Mondays)

From `analytics/week-NN.csv`: which hook pattern held the 5-second mark best, which episode had
the highest comment rate (its objection becomes a reply episode), which slot performed, and
which episode's taste score disagreed with its numbers. Write five lines to the owner and to the
producer chat; regenerate the schedule if the slots move.

## 9. If something fails

- TikTok upload rejected: check the file (MP4, 23–60 fps, ≥ 360 px both sides, ≤ 1 GB, 3–600 s) and re-upload; never convert it yourself, ask the producer.
- YouTube quota exceeded: wait for the daily reset (midnight Pacific) and request the increase.
- Token or connector errors: `tiktok_reconnect`, or delete `secrets/youtube-token.json` and authorise again.
- Anything ambiguous: write it to `publish/QUESTIONS.md` and ask; do not guess with a live account.
