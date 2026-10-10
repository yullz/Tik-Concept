# UNHAPPENED — alternate-history shorts channel: concept, scripts and production pipeline

A complete build for a faceless TikTok and YouTube Shorts channel that rewrites history and
modern reality with one real divergence point per episode, cinematic AI visuals, and a locked
narrator voice. Videos run 61–90 s (target 72–80 s). Goal: ten million views in month one.

**Start here:** `docs/00-anti-slop-charter.md` (the rules), then `docs/01-channel-bible.md`
(names, character, pillars), `docs/02-format-beat-sheet.md` (the 75-second shape), and
`RUNBOOK.md` (how one episode is produced, gate by gate).

```
docs/        00 charter · 01 bible · 02 format · 03 growth plan · 04 pipeline · 05 visual style & prompts
             06 voice & sound · 07 topic backlog · 08 model policy
episodes/    thirteen launch episodes in posting order (research, script, 22–24 shots, prompts, metadata); shelved/ holds nine more
pipeline/    Python: validate · lint · promptsheet · tts · plan · assemble · qc · metadata · bundle · dryrun
styles/      the house look appended to every prompt
assets/      music, sfx and fonts (licensed, not in git)
renders/     per-episode working directories (not in git)
RUNBOOK.md   executor steps with exact Higgsfield MCP tool calls
CLAUDE.md    rules for the executing agent (Claude Opus 5.5)
```

## Quick start

```bash
pip install -r requirements.txt            # pyyaml, requests, pytest
python3 -m pytest -q pipeline/tests         # offline test suite (renders a dry run with ffmpeg)
python3 -m pipeline validate episodes/ep001-every-human-vanishes.yaml
python3 -m pipeline lint     episodes/ep001-every-human-vanishes.yaml
python3 -m pipeline dryrun   episodes/ep001-every-human-vanishes.yaml   # placeholder render, no credits
```

The dry run writes `renders/ep001-every-human-vanishes/dryrun.mp4`: real timing, captions, cards,
hinge line and end stamp over labelled placeholder shots. Everything after that (look key,
keyframes, motion, narration) spends Higgsfield credits and is described step by step in `RUNBOOK.md`.

## What the pipeline enforces

- Script shape: seven beats, a two-stage hook that covers the five-second qualified-view mark,
  a sourced hinge, three escalating phases with a mechanism each, a cost, a real dilemma.
- Word budget per target duration (2.2–2.8 words per second), numbers spelled out, banned
  phrases and prompt tokens rejected, short sentences.
- Shot grammar: sizes rotate, every phase has a human-scale shot, hook shots ≤ 2.5 s, no shot
  over 5 s except the final hold, hero object recurring, era sheet required before prompts.
- Technical QC on the master: 1080×1920, 30 fps, 61–90 s, −16 LUFS, no freezes or black.
- A human taste gate (`review.yaml`, 12 criteria, hard fails) before a publish bundle exists.

## Model policy

Designed and built by Claude Fable 5.1; produced week to week by Claude Opus 5.5 running the
runbook with the Higgsfield MCP tools and local ffmpeg. See `docs/08-model-policy.md`.
