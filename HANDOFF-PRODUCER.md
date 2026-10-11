# HANDOFF · Production chat (Claude Opus 5.5)

Paste this file as the first message of a new Claude Code session, or open this repository in
Claude Code and say: "Read HANDOFF-PRODUCER.md and start." You are the producer. Your job is to
turn the written episodes in `episodes/` into finished, reviewed video masters, one at a time,
exactly as the runbook says, and to stop at every human gate.

## 1. What this is

UNHAPPENED is a faceless TikTok and YouTube Shorts channel: 75-second cinematic "what if"
videos (every human vanishes tonight, the Moon is gone, the Earth stops spinning...) narrated
by one locked voice, built from AI keyframes animated into short clips, with our own typography.
The design is finished and fixed. Thirteen launch episodes are fully written: research sheet
with sources, seven-beat script, 22–24 shots with keyframe and motion prompts, stat cards,
metadata and pinned comments. All thirteen pass `validate` and `lint` with zero errors.

Read, in this order, before doing anything: `docs/00-anti-slop-charter.md`, `CLAUDE.md`,
`RUNBOOK.md`, then the episode you are producing. The other docs are reference:
`docs/04-production-pipeline.md` (stages and the scorecard), `docs/05-visual-style-and-prompt-library.md`
(the look and the reject vocabulary), `docs/06-voice-and-sound.md` (voice and mix).

## 2. What you need connected

- This repository, branch `claude/bold-franklin-zsmgu7` (or wherever the owner says it lives now).
- The Higgsfield MCP server (image, video, batch, jobs_wait, media upload). Check `balance` first.
- `ELEVENLABS_API_KEY` in `.env` (copy `.env.example`). Narration runs on the direct ElevenLabs API, Eleven v4.
- ffmpeg, python3, `pip install -r requirements.txt`. Run `python3 -m pytest -q pipeline/tests` once; all green.
- Licensed music beds in `assets/music/` and SFX in `assets/sfx/` (file names in those folders' READMEs). If they are missing, produce the master without a bed and say so in the report; never substitute AI music.

## 3. Credit and spending rules (hard)

- This handoff authorises generation for the thirteen launch episodes only, inside the budgets below. Anything else (extra variants, experiments, more episodes) needs the owner's explicit yes in chat.
- Measured costs on this account: keyframe 2 credits (Nano Banana Pro, 9:16, 2K), Kling 3.0 standard 5 s silent clip 7.5, look key 2. A full episode is about 300 credits (24 shots × 2 keyframe variants, 20 animated shots, 20 % retries). Narration is billed to the ElevenLabs key in characters (~1,200 per episode).
- Preflight with `get_cost: true` before the first paid call of each stage; it is free.
- Stop and report when the Higgsfield balance drops below 350 credits, or before any single episode would exceed 400. Never top up.
- Never use `use_unlim` unless the owner says to. If a batch call returns `unlim_choice`, nothing was submitted: ask, then resubmit.

## 4. Order of operations for the launch

**Step 0 — lock the voice (once).** The Archivist is not cast yet.
```
python3 -m pipeline audition --list-models --search "documentary narrator" --gender male
python3 -m pipeline audition "Frederick Surrey" "Haseeb - British Documentary" --gender male
python3 -m pipeline audition --search "documentary" --gender female
```
Confirm the real v4 `model_id` from `--list-models` (expected `eleven_v4`) and set it in `.env`.
Send the owner `renders/_audition/README.md` and the files, wait for the pick, then write the
chosen `voice_id` into every episode's `voice.elevenlabs_voice_id` and commit. One voice, forever.

**Step 1 — the first episode end to end** (`episodes/ep001-every-human-vanishes.yaml`), following
`RUNBOOK.md` sections 1–10 in order: validate → lint → promptsheet → dryrun (free, watch it) →
look key (show it to the owner) → `promptsheet --lookkey-job <id>` → keyframes (batch, 2 variants per shot,
every request carrying the look key as `image_references`) → **Gate A** (owner picks, you apply `select`)
→ motion (batch) → **Gate B** → tts → plan → assemble → qc → **Gate C** (owner fills
`review.yaml`) → metadata → cover → bundle. Do not start episode two until episode one has a
passing `review.yaml`; the first episode teaches us which prompts fail.

**Step 2 — the rest, in file order** (`ep002` … `ep013`), two or three in flight at a time at most,
never more than one waiting at the same gate. The owner reviews on a phone; make it easy: one
message per gate with the contact sheet path and what you need decided.

## 5. Gates: what you do and do not do

- **Gate A (stills):** build `contact-sheet.html`, ask for picks, apply `selections.yaml`. A still with an artifact, an anachronism, generated text, or a generic look is regenerated with a reworded prompt (same index, variant `c`), never cropped around. Two failures: tell the owner, propose a different image, wait.
- **Gate B (clips):** anything that morphs, grows limbs, flickers, starts static or shows text is regenerated once with a slower camera and fewer moving things; on a second failure set `mode: still` for that shot (the assembler animates the approved keyframe). Never ship a known artifact.
- **Gate C (taste):** the owner scores `review.yaml`; you only create the template and run `qc`. If it fails, go back to the failing stage and edit the YAML, never the video file.
- Narration pace outside 2.2–2.8 words per second: rewrite the beat (keep the fact, change the sentence), regenerate; never stretch audio. Keep every lint rule; if you cannot satisfy one honestly, write the question to `renders/<id>/QUESTIONS.md` and move to another episode.

## 6. What finished looks like

`renders/<id>/publish/` holds `<id>.mp4` (1080×1920, 30 fps, 61–90 s, −16 LUFS, captions and
stamp burned in), `cover.jpg`, `metadata.json`, `metadata.md`, and the sidecars (`qc.json`,
`review.yaml`, `edl.json`, `tts_meta.json`). The publishing chat (`HANDOFF-PUBLISHER.md`) takes
it from there; you never post anything.

## 7. Reporting

After every episode, one message in this shape:

```
B-0001 Every Human Vanishes Tonight — DONE / BLOCKED
credits spent: 287 (keyframes 104, motion 165, look key 2, retries 16) · balance now 2,571
narration: 203 words, 2.46 w/s, timestamps route
gates: A 24/24 approved (3 regenerated: anachronism ×2, text ×1) · B 20/20 (1 → still) · C 51/60
open questions: none / see renders/ep001-every-human-vanishes/QUESTIONS.md
```

## 8. Open items you will hit

- The logo is not chosen yet (`assets/brand/logo-candidates.md`); the end stamp in the videos is typography and does not need it.
- Music and SFX files may be missing; see section 2.
- `.env` Higgsfield REST paths are unverified; use the MCP tools, as the runbook does.
- The shelved episodes in `episodes/shelved/` are not part of this run.
