# RUNBOOK — producing one episode (executor: Claude Opus 5.5 with the Higgsfield MCP)

Nothing here spends credits until step 4. Steps 1–3 and 7–12 are local and free.
Costs are from this account's preflights (2026-10-10): keyframe 2 credits, Kling 3.0 std 5 s
silent clip 7.5; narration is billed by ElevenLabs characters on the channel's own key (~1,200
characters per episode). A Hero episode is ≈ 300 Higgsfield credits.

## 0. Pick the episode
`episodes/<id>.yaml` exists and is marked ready in `docs/07-topic-backlog.md`. If it does not
exist, the writing stage (`python3 -m pipeline write <id> --brief "..."`) drafts it; a human
reviews the research block before anything else happens.

## 1. Validate and lint (free)
```
python3 -m pipeline validate episodes/<id>.yaml
python3 -m pipeline lint episodes/<id>.yaml
```
Zero errors required. Fix warnings when they are cheap (a missing light cue, a causal word).

## 2. Prompt sheet (free)
```
python3 -m pipeline promptsheet episodes/<id>.yaml
```
Writes `renders/<id>/promptsheet.md`, `promptsheet.json`, `keyframe_batches.json`.

## 3. Dry run (free)
```
python3 -m pipeline dryrun episodes/<id>.yaml
```
Produces `renders/<id>/dryrun.mp4` with placeholder shots and silent narration of the
estimated length. Watch it: the cut rhythm and the cards should already feel right.

## 4. Look key (2 credits)
Call `generate_image` (not batch; it is one image) with `promptsheet.json → look_key.params`
and `get_cost: true` first. Then generate. Keep the `job_id`; it is the `image_references`
value for every keyframe. Save the image to `renders/<id>/lookkey.png`.

## 5. Keyframes (≈ 96 credits for 24 shots × 2 variants)
For each chunk in `keyframe_batches.json`, add `"medias": [{"role": "image_references",
"value": "<lookkey job_id>"}]` to every item (the pipeline already does this if you pass the
look key: `python3 -c "..."` is unnecessary; just edit the JSON or regenerate the sheet with
the id), then:
```
generate_image_batch({ requests: <chunk> })      # ≤ 12 per call
jobs_wait({ jobs: [{index, job_id}, ...], timeout_seconds: 15 })   # repeat until all_terminal
```
Index convention: `shot_index * 10 + variant` (21 → shot-02 variant a, 22 → shot-02 variant b).
Collect `{ "shot-02-a": url, "shot-02-b": url, ... }` into `renders/<id>/keyframe_results.json`
and download:
```
python3 -m pipeline ingest episodes/<id>.yaml renders/<id>/keyframe_results.json --kind keyframes
python3 -m pipeline contact episodes/<id>.yaml
```
Also keep `{ "shot-02-a": job_id, ... }` in `renders/<id>/keyframe_jobs.json` (needed for motion).
Failed or `nsfw` items: resubmit only those indices once, reworded (never the whole batch).

## GATE A (human)
Open `renders/<id>/contact-sheet.html` on a phone-sized window. Fill `selections.yaml`
(`pick: A|B|R`, reason from the fixed list). Then:
```
python3 -m pipeline select episodes/<id>.yaml
```
Regenerate every `R` with a reworded prompt (same index, variant `c`), re-ingest, re-select.
Do not continue with any shot unapproved.

## 6. Motion (≈ 150 credits for 20 video shots)
Build `renders/<id>/selected_jobs.json` = `{ "shot-02": "<job_id of the chosen variant>", ... }`.
```
python3 -m pipeline motionbatch episodes/<id>.yaml renders/<id>/selected_jobs.json
```
Submit each chunk of `motion_batches.json` with `generate_video_batch`, wait with `jobs_wait`,
collect `{ "shot-02": url }` into `clip_results.json`, then:
```
python3 -m pipeline ingest episodes/<id>.yaml renders/<id>/clip_results.json --kind clips
python3 -m pipeline contact episodes/<id>.yaml
```
Preset recommendation responses (`submission_failed` + `preset_recommendation`): resubmit that
index with `declined_preset_id`. Never ask; never stop.

## GATE B (human)
Review clips at 1× in the contact sheet. Mark `clip: R` with a reason. One regeneration per
shot (reword the motion prompt: slower camera, fewer moving things). A second failure: set the
shot's `mode: still` in the episode YAML; the assembler animates the approved keyframe.

## 7. Narration (ElevenLabs, your key; character cost only)
```
python3 -m pipeline tts episodes/<id>.yaml
```
Uses the locked `voice.elevenlabs_voice_id` and `model_id` (Eleven v4) from the YAML, writes
`renders/<id>/audio/vo.mp3` plus `words.json` (timestamps, or forced alignment as fallback) and
prints the measured pace. 2.2–2.8 words per second required; otherwise rewrite the beat and run
again. Never time-stretch. If no voice is locked yet, run the audition first (docs/06).

## 8. Timeline (free)
```
python3 -m pipeline plan episodes/<id>.yaml
```
Needs word timings: ElevenLabs `words.json`, else faster-whisper if installed. Pace must be
2.2–2.8 w/s; if not, rewrite the offending beat and regenerate the narration (never stretch).
`--estimate` is for dry runs only.

## 9. Assemble (free)
Put the licensed music cue at the path in `music.cue` and SFX files in `assets/sfx/<slug>.wav`
(slug = the shot's `sfx` text, lowercase, hyphens). Then:
```
python3 -m pipeline assemble episodes/<id>.yaml
python3 -m pipeline qc episodes/<id>.yaml
```
QC must pass every technical check. It also creates `renders/<id>/review.yaml`.

## GATE C (human)
Watch `master.mp4` twice on a phone. Fill `review.yaml`. ≥ 42/60 and zero hard fails.
Anything less goes back to the failing stage; the YAML is edited, not the video.

## 10. Metadata, cover, bundle (free)
```
python3 -m pipeline metadata episodes/<id>.yaml
python3 -m pipeline cover episodes/<id>.yaml
python3 -m pipeline bundle episodes/<id>.yaml
```
`bundle` refuses to run without a passing review and QC.

## 11. Post (the publishing chat)
Hand `renders/<id>/publish/` to the publishing chat (`HANDOFF-PUBLISHER.md`): it schedules the
slot, prepares the TikTok draft through the Higgsfield MCP, uploads to YouTube with a scheduled
publish time, and runs the posting-day checklist. The producer never posts.

## 12. After posting
Log the 24 h and 7 d numbers in `analytics/`. Save the best objection to
`renders/<id>/replies.md`; it seeds the reply episode.

## Recovery rules
- A job with unknown submission outcome (timeout): never resubmit blindly; list recent jobs first.
- A sandbox or download that failed: re-download from the stored URLs in `*_results.json`.
- Credits short mid-run: stop after the current wave, write the remaining indices to
  `renders/<id>/PENDING.json`, and report.
