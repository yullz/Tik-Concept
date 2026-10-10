# 00 · The Anti-Slop Charter

This is the constitution of the channel. Every other document and every pipeline gate
defers to it. "AI slop" is not a look, it is a set of specific, detectable failures.
We list them, we ban them, and the pipeline refuses to ship a video that carries one.

## What slop actually is (so we can test for it)

| Layer | The slop failure | What it looks like | Our countermeasure |
|---|---|---|---|
| Idea | Premise with no hinge | "What if dinosaurs had guns" | Every episode names ONE real divergence point (a decision, a date, a physical constraint) and reasons forward from real mechanisms. |
| Script | Generic, interchangeable prose | "In a world where… little did they know… the rest is history" | Banned-phrase list enforced by `pipeline lint`. One new concrete fact per line. Numbers spelled out. Hook sentence ≤ 8 words. |
| Script | Lists instead of arcs | fact, fact, fact | Mandatory shape: hook → hinge → three escalating phases → the turn (the cost) → a real dilemma. The reorder test: if two phases can be swapped, rewrite. |
| Script | Fake stakes | "Everything would change forever" | Stakes must be physical and dated: a city, a number, a named person, a thing you can film. |
| Visual | Prompt-salad imagery | "epic, 8k, hyper-detailed, masterpiece, lens flare, glowing particles" | Those tokens are banned in prompts (the linter rejects them). We prompt like a cinematographer: subject, action, lens, light, weather, era-correct materials. |
| Visual | Anachronism and nonsense | Roman jets with 1990s cockpit glass, Victorian plastic | Each episode has a Research Sheet: era references (architecture, uniforms, materials, typography). Prompts cite them. Reviewer checks against the sheet. |
| Visual | Morphing, melting, extra limbs, warped text | the classic tells | Keyframe-first: stills are approved by a human BEFORE motion is bought. Motion clips are short (≤ 5 s generated, ≤ 3.5 s used), camera-driven, with subjects that do not transform. No generated text in frame, ever; typography is ours. |
| Visual | Samey coverage | every shot a drone wide at golden hour | Shot-size rotation is enforced in the spec: WIDE / MEDIUM / CLOSE / DETAIL / POV, varied on every cut. Max two consecutive shots of the same size. |
| Audio | Robotic read, machine-gun pacing | flat TTS at 3+ words/sec | Locked narrator voice, delivery direction per beat, 2.2–2.8 words/sec enforced, performed pauses written into the script, one voice forever. |
| Audio | Silence under visuals, or stock "epic" music loop | | Three-layer mix: voice, a deliberate music bed chosen per episode mood, and a sound-design pass (at least 6 diegetic SFX cues per episode). Ducked and loudness-normalised. |
| Edit | Slideshow feel | stills held 4–5 s with slow zoom | Average shot 3 s; hook shots ≤ 2.5 s; hard cuts on narration beats; motion from frame one. |
| Edit | Caption wallpaper | every word in Comic bubble font across the frame | One typeface, kinetic keyword captions (2–4 words per card), platform safe zones, phase cards with real dates. |
| Process | Auto-post without eyes | | A human taste gate (12-point scorecard) is required before `publish/` is produced. The pipeline will not build a publish bundle without a passing `review.yaml`. |
| Ethics | Passing counterfactual as fact | | Every episode opens on-screen with the word WHAT IF and closes with "Alternate timeline" in the description. We label AI-generated content on both platforms (TikTok AIGC flag, YouTube altered-content disclosure). |

## The ten hard rules (the linter and QC enforce what they can)

1. **One hinge per episode.** Name the exact real-world divergence in the first 15 seconds.
2. **Mechanism, not magic.** Each phase explains *why* the next thing happens (logistics, economics, physics, politics). If the script cannot say "because", cut the beat.
3. **One new concrete per line.** A number, a name, a place, a material, a date. Adjectives do not count.
4. **No banned phrases.** See `pipeline/lint.py` for the list. Add to it whenever a phrase starts feeling like a reflex.
5. **Numbers spelled out in the VO, digits only on screen.** Spoken digits blow the timing and sound robotic.
6. **Stills before motion.** No video credits are spent on a shot whose keyframe was not approved.
7. **Era sheet before prompts.** No prompt is written without the episode's research sheet (materials, architecture, uniforms, vehicles, light).
8. **No generated text in frame.** All typography is ours (caption and phase-card system).
9. **The ending is a dilemma, not a poll.** "What do you think?" is banned. The closing question must have two defensible answers that make people argue.
10. **A human signs every video.** The scorecard in `docs/04-production-pipeline.md` must score ≥ 42/60 with zero hard fails. The pipeline enforces the presence and threshold of `review.yaml`.

## Platform rules we build around (TikTok originality and retention)

1. **No third-party footage, ever.** Not podcast clips, not film scenes, not stock B-roll, not
   other creators' videos, cropped or not. TikTok's originality violations disqualify a video
   from Creator Rewards and three of them end monetisation for the account. Every frame in our
   videos is generated from our own prompts or shot by us; music is licensed; typography is ours.
   The pipeline has no input path for external video on purpose.
2. **No built-in platform voices.** Never TikTok's or CapCut's text-to-speech. The narrator is a
   locked ElevenLabs voice chosen by audition for breath, pauses and inflection
   (`docs/06-voice-and-sound.md`); a take that sounds read is regenerated after a rewrite.
3. **Nothing sits still.** No shot over five seconds (the final hold excepted, and it carries the
   question card and the stamp). Average shot three seconds. The assembler adds a hard punch-in
   on any shot of about four seconds or more, cards scale in with a tick, and every shot has a
   camera move from frame one. A pattern interrupt lands every three to four seconds by
   construction: a cut, a card, a punch-in or a sound.

## The taste test (read before approving anything)

Ask of every shot and every line: *could this only exist in this episode?* If the shot
could be dropped into any other "what if" video unchanged, it is wallpaper. Replace it
with the specific thing: not "a futuristic city" but "the Forum, 2024, with maglev
tracks laid along the Via Sacra and SPQR on the hull of a cargo drone".
