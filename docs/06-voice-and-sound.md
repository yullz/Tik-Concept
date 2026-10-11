# 06 · Voice & Sound

## The casting brief for the Archivist

Male or female is open; the pick below is male because the two strongest available
candidates are. What matters is the register:

- Low-mid pitch, calm, unhurried, dry. Documentary authority without news-anchor punch.
- British or neutral transatlantic. A slight gravel, no breathiness.
- Reads numbers slowly, lands facts, lets a pause sit. Zero "YouTuber" energy.
- Must survive 2.3 words per second without sounding rushed or slurred.

## Important: ElevenLabs default voices are going away

ElevenLabs' classic *Default* voices (Adam, Brian, Daniel, George and the rest) are only
available to accounts created before March 2026 and expire on **31 December 2026**
(ElevenLabs help centre, "What are Default voices?"). A season-one voice chosen from that
set would have to be recast mid-season, which is exactly the consistency break the charter
forbids. So the lock is made from voices that stay available.

## The route: ElevenLabs API, Eleven v4 (direct, not through Higgsfield)

We call ElevenLabs ourselves with the channel's own key. Eleven v4 (released late September 2026,
with a lower-latency v4 Turbo) is the most expressive model and uses bracketed natural-language
audio tags; SSML `<break>` tags are disabled on v4, so pauses are written as punctuation and
ellipses, and emotion as short tags. The exact `model_id` used by the API is confirmed from your
account with `python3 -m pipeline audition --list-models` (third-party gateways expose it as
`eleven_v4`; the pipeline default is that string and is overridable in `.env`).

| Setting | Value | Note |
|---|---|---|
| `model_id` | `eleven_v4` (confirm via `--list-models`) | v4 Turbo only for drafts; the master uses full v4 |
| stability | 0.50 | lower drifts between takes, higher goes flat |
| similarity_boost | 0.75 | |
| style / speed | n/a | not available on Eleven v3/v4 (v2 models only); pace comes from the script, punctuation and `[pause]` tags, never from post |
| use_speaker_boost | true | |
| `apply_text_normalization` | `on` | we still spell numbers out |
| output | `mp3_44100_192` (Creator tier or above; the code falls back to `mp3_44100_128`, or set `ELEVENLABS_OUTPUT_FORMAT`) | the assembler normalises to −16 LUFS |
| timestamps | `/with-timestamps` first; if the model or plan refuses, plain synthesis then `/v1/forced-alignment` with the exact script; then faster-whisper | word timings drive every cut and caption |

## Casting: pick by audition, lock by id

Arthur (the Higgsfield preset) is demoted to a reference take. The Archivist is chosen from the
ElevenLabs Voice Library by ear, never by name alone, and locked by `voice_id` in every episode
(`voice.elevenlabs_voice_id`). Run the audition with your key:

```
python3 -m pipeline audition --list-models --search "documentary narrator" --gender male
python3 -m pipeline audition "Frederick Surrey" "Haseeb - British Documentary" <any voice_id> --gender male
python3 -m pipeline audition --search "documentary" --gender female
```

The command resolves Voice Library names through the API (adding the voice to the account),
synthesises the audition script with each candidate, measures words per second and the longest
internal pause, and writes `renders/_audition/README.md` with the files to listen to blind on a
phone. Candidates to start with (from the Library's documentary category; confirm on the live
page): **Frederick Surrey** (calm, well-spoken British narrator for history and science
documentaries; closest to the brief), **Haseeb - British Documentary** (soothing, engaging), and
two or three female voices from the same search for comparison. Pick one, set its id in all ten
episodes, and never change it mid-season.

## The audition script (read by every candidate, compare blind)

The text is `AUDITION_SCRIPT` in `pipeline/tts.py` (the command reads it from there):

> What if Rome never fell. Not in four seventy-six. Not ever. Tonight, the Senate votes on the Moon. One autumn night, two seventy-five. Aurelian, the emperor who stitched the broken empire back together in five years, is murdered by his officers. Here, the plot fails. This is how it happens. [exhale] But an empire with no rivals has no reason to invent. Printing, banking, steam, all came from states fighting to survive. That timeline never happened. Ours did. So, honestly: would you trade the internet for Rome?

Scoring: clarity of "two seventy-five", the weight of "This is how it happens", whether the bracketed exhale sounds human, whether the last line darkens without slowing to a crawl.

## How narration is written for the synthesiser (what `pipeline lint` enforces)

- One continuous read per episode, in beats. The timeline snaps cuts to the first word of each beat, so no per-shot audio juggling.
- 2.2–2.8 words per second measured on the result (`pipeline tts` prints it). Slower: add a fact. Faster: cut a modifier. Never `atempo`.
- Numbers as words. Dates as words ("the eleventh of December, twelve forty-one").
- Punctuation is pacing: a full stop costs ~0.6 s, a comma ~0.4 s, an ellipsis ~0.8 s. Short sentences for the hook and the turn, one flowing sentence per mechanism.
- Performed non-verbals in square brackets, at most two per episode: `[exhale]` before the turn, `[quiet]` on the sign-off. Round brackets are direction and are stripped before synthesis.
- Delivery direction is written once per episode in `voice.direction` and sent as a short bracketed tag at the start of the request (v4 reads bracketed natural-language direction as an audio tag).

## Sound design (the layer that most separates us from slop)

Three layers under the voice, mixed by `pipeline assemble`:

| Layer | Source | Level | Rules |
|---|---|---|---|
| Voice | ElevenLabs | normalised to −16 LUFS integrated, −1 dBTP | always first; everything else ducks under it |
| Music bed | **licensed library** (Epidemic Sound or Artlist), instrumental, chosen per episode mood from `music.mood` | −28 LUFS under speech, −22 in the 1.5 s gaps, sidechain ducked by the voice | one cue per episode, a second cue allowed at the turn; no AI music in season one |
| SFX | library (freesound CC0 or the music library's SFX) and the clips' own audio when a model generated it | peaks ≈ −20 dBFS, ducked under voice | **minimum six cues per episode**, one per phase at least: jets, crowd, wind, oven, sea, paper; placed from `sfx:` cues in the YAML |

Music moods by pillar: Never Fell → low strings and a slow pulse; Tomorrow Morning → sparse piano and sub bass; Early Arrival → clockwork percussion and cello; The Hinge → a single sustained note that resolves at the turn.

Loudness targets are platform-safe: TikTok and YouTube both normalise toward −14 to −16 LUFS; a −16 master with −1 dBTP survives both without pumping.
