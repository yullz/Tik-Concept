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

## The pick

**Launch voice: "Arthur" through Higgsfield's ElevenLabs engine.**

| Field | Value |
|---|---|
| Backend | Higgsfield `text2speech_v2`, `variant: elevenlabs` |
| `voice_type` | `preset` |
| `voice_id` | `30fc8796-ceb6-4a66-b3a7-4a145ef7f346` |
| Measured cost | 0.6 credits per ~35 words (≈ 4 credits per episode) |
| Why | Higgsfield's own history-channel recommendation; measured, dry, British-leaning; available on this account today; no expiry |

Audition alternates (same backend, same audition script, pick by ear, then never change):
- **Cillian** `d8ba9f14-8a24-44db-932b-99e16c45bd32` (Higgsfield's pinned narrator default; warmer, a touch younger).
- **Callum** (search `list_voices`; intense, gravelly; better for the darker Hinge pillar, risk of sounding like a trailer).

**Direct ElevenLabs API route** (for the dubbing accounts and when we want word timestamps
straight from the synthesiser): pick one voice from the ElevenLabs **Voice Library**
(not a Default voice), filter `Narrative & Story` → `Documentary`, male, 40s, British, and
audition the same script. Save its `voice_id` into `.env` as `ELEVENLABS_VOICE_ID`, add it
to the account's library, and never resolve by name again. Settings to start from:

| Setting | Value | Note |
|---|---|---|
| `model_id` | `eleven_v3` | most expressive; supports performed tags like `[sighs]`, `[whispers]` |
| fallback `model_id` | `eleven_multilingual_v2` | when `with-timestamps` is required and v3 alignment is unavailable on the account |
| stability | 0.50 | "natural" range; lower drifts, higher goes flat |
| similarity_boost | 0.75 | |
| style | 0.15 | keep low, the script carries the emotion |
| speed | 0.95 | slightly slower than default; we never time-stretch in post |
| `apply_text_normalization` | `on` | but we spell numbers out anyway |
| output | `mp3_44100_128` for review, `pcm_44100` for the master | |

## The audition script (read by every candidate, compare blind)

> What if Rome never fell. In the year two thousand twenty-four, the Senate still meets. The eagle flies over four continents, and Latin is the language of the internet. This is how it happens. [exhale] But a timeline that keeps its empire has to pay for it, and the bill arrives in the fifteenth century.

Scoring: clarity of "two thousand twenty-four", the weight of "This is how it happens", whether the bracketed exhale sounds human, whether the sentence after it darkens without slowing to a crawl.

## How narration is written for the synthesiser (what `pipeline lint` enforces)

- One continuous read per episode, in beats. The timeline snaps cuts to the first word of each beat, so no per-shot audio juggling.
- 2.2–2.8 words per second measured on the result (`pipeline tts` prints it). Slower: add a fact. Faster: cut a modifier. Never `atempo`.
- Numbers as words. Dates as words ("the eleventh of December, twelve forty-one").
- Punctuation is pacing: a full stop costs ~0.6 s, a comma ~0.4 s, an ellipsis ~0.8 s. Short sentences for the hook and the turn, one flowing sentence per mechanism.
- Performed non-verbals in square brackets, at most two per episode: `[exhale]` before the turn, `[quiet]` on the sign-off. Round brackets are direction and are stripped before synthesis.
- Delivery direction is written once per episode in `voice.direction` and prepended to the request (on the Higgsfield route it is the bracketed prefix their engine expects; on the direct route it is sent as the v3 context tag).

## Sound design (the layer that most separates us from slop)

Three layers under the voice, mixed by `pipeline assemble`:

| Layer | Source | Level | Rules |
|---|---|---|---|
| Voice | ElevenLabs | normalised to −16 LUFS integrated, −1 dBTP | always first; everything else ducks under it |
| Music bed | **licensed library** (Epidemic Sound or Artlist), instrumental, chosen per episode mood from `music.mood` | −28 LUFS under speech, −22 in the 1.5 s gaps, sidechain ducked by the voice | one cue per episode, a second cue allowed at the turn; no AI music in season one |
| SFX | library (freesound CC0 or the music library's SFX) and the clips' own audio when a model generated it | peaks ≈ −20 dBFS, ducked under voice | **minimum six cues per episode**, one per phase at least: jets, crowd, wind, oven, sea, paper; placed from `sfx:` cues in the YAML |

Music moods by pillar: Never Fell → low strings and a slow pulse; Tomorrow Morning → sparse piano and sub bass; Early Arrival → clockwork percussion and cello; The Hinge → a single sustained note that resolves at the turn.

Loudness targets are platform-safe: TikTok and YouTube both normalise toward −14 to −16 LUFS; a −16 master with −1 dBTP survives both without pumping.
