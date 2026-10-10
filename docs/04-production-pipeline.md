# 04 · Production Pipeline — one episode, end to end

Everything below is executed by `python -m pipeline <stage> episodes/<ep>.yaml`. Each stage
reads and writes `renders/<episode-id>/`, so a stage can be re-run without redoing the
previous ones. Stages have gates; a gate failure stops the run with the reason.

```
brief ─► research ─► write ─► lint/validate ─► promptsheet ─► keyframes ─► [HUMAN GATE A: stills]
      ─► motion ─► [HUMAN GATE B: clips] ─► tts ─► align ─► plan ─► assemble ─► qc
      ─► [HUMAN GATE C: scorecard] ─► metadata ─► publish bundle ─► post ─► analytics ─► replies
```

| # | Stage | Input → Output | Tool | Time | Gate |
|---|---|---|---|---|---|
| 0 | **Brief** | one line from `docs/07-topic-backlog.md` → `episodes/<id>.yaml` stub (`pipeline new`) | you | 2 min | none |
| 1 | **Research sheet** | brief → `research:` block in the YAML: the hinge with date and source, 5–8 facts with sources, era sheet (materials, architecture, uniforms, vehicles, light), the counterintuitive cost | Opus 5.5 later (`pipeline research`); written by hand in this build | 20 min | Hinge has a source or the episode is dropped |
| 2 | **Script + shot list** | research → `beats:` (VO per beat), `shots:` (size, location, prompt, motion, duration) | Opus 5.5 later (`pipeline write`); hand-written in this build | 30 min | `pipeline lint` and `pipeline validate` pass with zero errors (≤ 3 rewrite rounds) |
| 3 | **Prompt sheet** | shots + style bible → `renders/<id>/promptsheet.md` and `.json` (keyframe prompt, negative, motion prompt, model params per shot) | `pipeline promptsheet` | instant | none |
| 4 | **Keyframes** | prompt sheet → 2 variants per shot via Higgsfield `nano_banana_pro` 9:16 2K, with the episode **look key** as image reference | `pipeline keyframes` (REST) or the MCP batch tools; or paste from the sheet into the Higgsfield UI | 15 min for 24 shots | **Gate A (human):** open `renders/<id>/contact-sheet.html`, pick one variant per shot, reject any with artifacts. Rejections are regenerated with a reworded prompt. |
| 5 | **Motion** | approved stills → one 5 s clip per animated shot via `kling3_0` (std, silent) with the shot's motion prompt | `pipeline motion` or MCP | 20 min | **Gate B (human):** view every clip at 1×; reject morphing, extra limbs, warped architecture, flicker, text. Max one regeneration, then the shot becomes a parallax still. |
| 6 | **Narration** | `beats` VO text → `vo.mp3` + `words.json` with word timings | `pipeline tts` (ElevenLabs direct or Higgsfield) | 1 min | measured pace 2.2–2.8 w/s; no internal pause ≥ 0.8 s; else rewrite the line and regenerate (never time-stretch) |
| 7 | **Timeline** | words + shots → `edl.json` (cut points snapped to beat first-words) | `pipeline plan` | instant | total duration 61–90 s |
| 8 | **Assembly** | clips + stills + VO + music + SFX + captions + cards → `master.mp4` (1080×1920, 30 fps, H.264, −16 LUFS) | `pipeline assemble` (ffmpeg) | 3 min | ffmpeg exit 0 and a full decode |
| 9 | **QC** | master → `qc.json` (duration, resolution, fps, loudness, black/frozen frames, caption safe zones) | `pipeline qc` | 1 min | all technical checks pass |
| 10 | **Taste gate** | watch it twice on a phone, fill `renders/<id>/review.yaml` (12 criteria × 5) | you | 5 min | **Gate C:** ≥ 42/60 and no hard fail, else back to the failing stage |
| 11 | **Metadata** | YAML → `publish/<platform>.md` (title, description, hashtags, pinned comment, cover time, disclosures) | `pipeline metadata` (hand-written for the launch set; Opus 5.5 later) | instant | `review.yaml` passed |
| 12 | **Publish bundle** | master + covers + metadata + hook variants → `publish/` | `pipeline bundle` | instant | |
| 13 | **Post** | bundle → platforms | TikTok via Higgsfield `tiktok_prepare_publish` (MCP) or manual; YouTube Studio or Data API; Meta via Business Suite | 10 min | never auto-post without Gate C |
| 14 | **Analytics** | platform stats at 24 h and 7 d → `analytics/week-NN.csv` | manual export or API | weekly | the Monday loop (`docs/03-growth-plan-10M.md`) |
| 15 | **Replies** | best objection → `episodes/<id>-reply.yaml` | you + Opus 5.5 later | 30 min | same gates, shorter format |

Throughput: one person can run one Hero episode in about two hours of attention, most of it waiting on generation. A weekly batch of ten episodes runs research and scripts on Monday, keyframes Tuesday, motion Wednesday, assembly and QC Thursday, with Friday as the reply and buffer day.

## The look key (why episodes stay consistent)

Before any keyframe, generate one 9:16 **look key** image per episode: an empty establishing frame of the episode's world in the house style (lens, film, light). Every keyframe in that episode passes the look key as `image_references` so palette, grain and light stay locked. The look key is also the cover-frame candidate. Keys are stored under `renders/<id>/lookkey.png` and their prompt in the YAML (`look_key_prompt`).

## Gate A: still review (contact sheet)

`renders/<id>/contact-sheet.html` shows both variants per shot with the prompt beneath. For each shot you mark `A`, `B`, or `R` (regenerate) in `renders/<id>/selections.yaml`. Rejection reasons are picked from a fixed list so we learn which prompts fail: `anachronism`, `anatomy`, `text`, `warped-architecture`, `generic`, `wrong-size`, `off-palette`, `duplicate-of-another-shot`.

## Gate B: clip review

Same mechanism on `clips/`. Reject reasons: `morph`, `limb`, `flicker`, `static-start`, `text`, `wrong-camera`, `too-fast`. A shot that fails twice becomes a parallax still (the assembler animates the approved keyframe with a 2.5 % push and 1 % drift). No shot is ever shipped with a known artifact.

## Gate C: the taste scorecard (`review.yaml`)

Score each criterion 1–5. Hard fails are marked `hard_fail: true` and veto the episode regardless of total.

| # | Criterion | Hard fail if |
|---|---|---|
| 1 | The first 3 seconds contain the most specific image in the episode | the hook image is generic |
| 2 | The hinge is a real, dated, sourced event | no source |
| 3 | Every phase explains a mechanism ("because") | any phase is a list |
| 4 | Phases escalate (the reorder test fails) | |
| 5 | The turn is a cost the viewer did not expect | |
| 6 | The dilemma has two defensible sides | obvious answer |
| 7 | Era sheet respected in every shot (materials, architecture, uniforms) | a visible anachronism not intended by the premise |
| 8 | No visual artifacts at 1× on a phone | any morph, limb, warped text |
| 9 | Shot sizes rotate; no two consecutive wides | |
| 10 | Narration pace 2.2–2.8 w/s, no robotic cadence, pauses land | |
| 11 | Mix: voice clear, music felt not heard, at least six SFX cues | music louder than voice |
| 12 | Captions legible, inside safe zones, no typos | a typo |

Pass: total ≥ 42 and zero hard fails. The pipeline reads this file before building `publish/`.

## Where the models run (Higgsfield)

Two routes produce identical assets:
- **MCP route (verified in this build):** `generate_image_batch` / `generate_video_batch` with the prompt sheet, `jobs_wait`, download the result URLs into `renders/<id>/keyframes/` and `clips/`. This is what `pipeline promptsheet` is formatted for.
- **REST route (`pipeline keyframes`, `pipeline motion`):** `pipeline/visuals.py` posts to the Higgsfield Cloud API using endpoint templates in `.env`. The endpoint paths could not be verified from this container (docs blocked by network policy); confirm them once against the Higgsfield API docs and set `HIGGSFIELD_*_PATH`.
- **Manual route:** paste prompts from `promptsheet.md` into the Higgsfield app, drop the files into `renders/<id>/keyframes/shot-NN-a.png` etc. The assembler only cares about file names.

## Analytics CSV template

```
week,platform,account,episode_id,variant,posted_at,views_24h,views_7d,hold_3s_pct,avg_watch_pct,completion_pct,comments,shares,saves,follows
```
