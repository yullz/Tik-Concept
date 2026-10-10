# 08 · Model policy — who does what

| Work | Model | Where |
|---|---|---|
| Channel design, format, growth plan, pipeline architecture, prompt grammar, this repository | **Claude Fable 5.1** (this build) | one-time |
| Weekly production runs: research sheets, episode scripts, shot lists, keyframe and motion prompts, metadata, localisations, reply-episode drafts, scorecard pre-fill | **Claude Opus 5.5** (`claude-opus-5-5`) | `pipeline/llm.py`, invoked by `python -m pipeline write`, `research`, `metadata`, `localize` |
| Image keyframes | Higgsfield · Nano Banana Pro (`nano_banana_pro`) | `pipeline/visuals.py` |
| Motion clips | Higgsfield · Kling 3.0 (`kling3_0`), Veo 3.1 Lite as budget fallback | `pipeline/visuals.py` |
| Narration | ElevenLabs (direct API) or ElevenLabs via Higgsfield (`text2speech_v2`, variant `elevenlabs`) | `pipeline/tts.py` |
| Word alignment for captions | ElevenLabs timestamps, else faster-whisper | `pipeline/align.py` |
| Assembly, captions, mix, QC | ffmpeg (local) | `pipeline/assemble.py`, `captions.py`, `qc.py` |

Rules for the Opus 5.5 stage:
- It is given the charter, the style bible, the beat sheet and the episode brief as a cached system prompt, and it writes the full episode YAML.
- Its output is not trusted: `pipeline lint` and `pipeline validate` run on it, and the failures are fed back for up to three rewrite rounds. A script that still fails is rejected, not patched by hand.
- Effort is set to `high`; thinking is adaptive (the default on this model); server-side refusal fallback is on. No sampling parameters are set.
- It never generates a fact without a source line in the research sheet. If it cannot source the hinge, the episode is dropped.
- Model identifiers never appear in any published asset.
