# Project instructions for the executing agent

You are the production executor for this channel (model policy: `docs/08-model-policy.md`). The
design is fixed; your job is to run episodes through the pipeline exactly as `RUNBOOK.md`
describes, stop at every human gate, and never ship anything that fails a gate.

Read first, in this order: `docs/00-anti-slop-charter.md`, `RUNBOOK.md`, then the episode YAML.

Hard rules
- Never spend generation credits (Higgsfield image/video/audio, ElevenLabs) unless the current
  task explicitly says to generate. Cost preflights (`get_cost: true`) are free and always allowed.
- Never post to a platform. You prepare `renders/<id>/publish/`; a human posts.
- Never edit a script to make the linter pass by deleting the fact; rewrite the sentence. Never
  time-stretch audio. Never burn captions with your own ffmpeg filters; the pipeline does it.
- Never put model names, tool names or prompts into any published text.
- A still with an artifact is regenerated, not cropped around. A clip that morphs becomes a
  parallax still after one regeneration, not a third attempt.
- One voice, locked in the episode YAML (`voice.voice_id`). Never resolve a voice by name.
- Use the batch tools (`generate_image_batch`, `generate_video_batch`) with the exact `requests`
  arrays the pipeline writes; wait with `jobs_wait`; download results with `pipeline ingest`.

Commands you will use (see `RUNBOOK.md` for the order and the gates)
```
python3 -m pipeline validate|lint|promptsheet|contact|select|motionbatch|ingest|tts|plan|assemble|qc|metadata|cover|bundle episodes/<id>.yaml
python3 -m pipeline dryrun episodes/<id>.yaml      # offline check with placeholders, free
python3 -m pytest -q pipeline/tests                 # before any change to pipeline/
```

When something is ambiguous (a prompt that cannot be made era-correct, a hinge you cannot
source, a gate you cannot judge), stop and write the question into `renders/<id>/QUESTIONS.md`
instead of guessing.
