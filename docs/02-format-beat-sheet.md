# 02 · Format & Beat Sheet (1:01–1:30, target 1:12–1:18)

Why this length: both platforms now reward watch time, YouTube Shorts accepts up to three minutes, and TikTok's "over one minute" bucket unlocks longer-form distribution and (where eligible) Creator Rewards. We target 72–78 seconds: long enough for three phases, short enough to hold 60 % average view.

## The seven beats

| # | Beat | Time | Narration (word budget at 2.5 w/s) | Visuals | On screen |
|---|---|---|---|---|---|
| 1 | **Cold open, two stages** | 0:00–0:06 | Stage one (0–2.5 s): first sentence ≤ 8 words, stated flat: "What if Rome never fell." Stage two (2.5–6 s): the open loop, one impossible specific that promises the video: "Tonight, the Senate votes on the Moon." ≥ 12 words total. | Two shots: the single most specific, impossible image of the episode (motion from frame one), then a second image that escalates it. The cut lands at ~2.5 s so there is new information exactly where thumbs decide. | sonic logo, "WHAT IF" sigil, title in 3–5 words, file number |
| 2 | **Hinge** | 0:06–0:18 | ~30 words. The one real divergence point, with a date and a name. "This is how it happens." | 3–4 shots, 2–3 s each: the real moment, then the first visible change | Hinge line splits; date card |
| 3 | **Phase one** | 0:15–0:30 | ~36 words. The first mechanism: *because* X, Y. One number. | 4–5 shots, 2.5–3.5 s: WIDE → DETAIL → MEDIUM → POV | Phase card: "YEAR ONE" (or real year) |
| 4 | **Phase two** | 0:30–0:45 | ~36 words. Escalation: the consequence of the consequence. Bigger, weirder, more specific. | 4–5 shots, rotate sizes; move location | Phase card |
| 5 | **Phase three** | 0:45–1:00 | ~36 words. The present day of the other timeline. The viewer's own life, changed. | 4–5 shots; at least one shot of ordinary people, not monuments | Phase card: "TODAY" |
| 6 | **The turn** | 1:00–1:10 | ~24 words. The cost. What this timeline lost, or what it never discovered. Counterintuitive. | 2–3 shots, slower (3.5–4 s), the tone darkens | Hinge line returns |
| 7 | **The dilemma** | 1:10–1:16 | ~14 words. "That timeline never happened. Ours did." + the question. | 1 held shot (4–5 s), end card over it | Question in large type; next-episode tease |

Totals: ~180 words, ~24 shots, 74–78 seconds. The linter (`pipeline lint`) checks the word budget against the target duration and the shot budget against the beats.

## The five-second rule (why the hook is two stages)

A view only counts once the viewer passes five seconds. So the hook is not one shot and one
line; it is a flat impossible statement (0–2.5 s) and then a *second* impossible specific
(2.5–6 s) that opens a loop the rest of the video closes. The validator refuses a hook under
twelve words, under two shots, or under five seconds of shots. The second stage must be a
concrete promise (a vote, a date, a number, an object), never "and this is how it happened".

## The shot cadence rules (enforced in `pipeline validate`)

- Average shot length 3.0 s; hook shots ≤ 2.5 s; no shot longer than 5 s except the final hold.
- Shot sizes must rotate: never more than two consecutive shots with the same size tag (`WIDE`, `MEDIUM`, `CLOSE`, `DETAIL`, `POV`, `AERIAL`).
- Every beat starts on a cut that lands on the first word of its narration (the timeline builder snaps cuts to word timestamps).
- Max two consecutive shots in the same location.
- Every phase has at least one human-scale shot (a hand, a street, a kitchen). Monuments alone are wallpaper.
- Motion from frame one: every clip is generated with a camera move; stills that must be used get a parallax or push, never a static hold.

## Hook grammar (ten patterns that work for this format)

1. **Flat impossible fact.** "What if the ocean dried up tonight."
2. **Date collision.** "Rome, nineteen sixty-nine. The eagle lands on the Moon."
3. **Object out of time.** "A steam engine. Alexandria. Year one hundred."
4. **The small decision.** "One letter. Sent a week later. No America."
5. **The number first.** "Four billion people. All speaking Latin."
6. **Reversal of the known.** "The Library of Alexandria never burned."
7. **The viewer's morning.** "You wake up. The Moon is gone."
8. **The map.** "Here is Europe in this timeline." (map shot)
9. **The denial.** "They told you the Mongols stopped. They didn't."
10. **The question with a cost.** "Would you trade the internet for Rome?"

The first sentence is the cover-frame title. If it does not work as five words on a thumbnail, rewrite it.

## Dilemma grammar (the ending must split the room)

Banned: "What do you think?", "Let me know in the comments", "Which would you choose?" without stakes.

Templates:
- **Trade.** "Would you take [the gain] if it cost [the loss]?"
- **Blame.** "So who actually ended Rome: the Goths, or the Romans?"
- **Prediction.** "Does this timeline reach the Moon before or after ours?"
- **Identity.** "In that timeline, is your country still a country?"
- **Correction bait (used sparingly, honestly).** "Historians say this is where I'm wrong. Prove it."

Then the fixed sign-off: "That timeline never happened. Ours did." The pinned comment restates the dilemma and takes a side, so the first reply has something to disagree with.

## Retention devices (what keeps a faceless video watched)

Faceless formats hold attention with the picture, the type and the rhythm, not a presenter.
The four we use, every episode:

1. **Cinematic B-roll plus minimalist kinetic type.** Every shot is a deliberate, moody,
   photoreal image with camera motion; captions are large (84 px on a 1080-wide frame),
   two to four words, timed to the word. Nothing else is on screen except the devices below.
2. **Stat cards.** When the voice says a number ("eighty thousand kilometres of road"), the
   screen shows the digits, big, with a two-word label, scaling in for a quarter second. At
   least one per phase. Digits on screen, words in the voice: the eye and the ear get the
   fact twice without the narrator sounding robotic. YAML: `card: {text: "80,000 KM\nOF PAVED ROAD", style: stat}` on the shot.
3. **The map moment.** One `MAP` shot per episode: a physical map (relief, parchment,
   a floor map in a hall), never a glowing UI. The camera moves over it while the narration
   names places. It is the alternate-history equivalent of the whiteboard diagram, and it is
   the shot most saved and screenshotted.
4. **Pattern interrupts every six to nine seconds.** A size change, a card, a sound, a new
   location. The validator's rotation rules and the per-phase card requirement enforce the
   floor; the edit should never go nine seconds without one.

Script rhythm: short sentences. The linter warns above twenty-two words and refuses above
thirty. Mechanisms get one flowing sentence; hooks, turns and sign-offs get fragments.
Read every line aloud before it is voiced; if you need a breath mid-sentence, cut it in two.

## Text system

- Captions: kinetic keyword captions, 2–4 words per card, timed to the word, lower-middle third, within platform safe zones (TikTok: keep 220 px clear at the bottom, 120 px at the top, 140 px at the right edge). One font, white, subtle shadow, no outlines, no emoji.
- Phase cards and the end card use the pillar accent colour.
- No generated text in any AI image. Ever. The pipeline burns all typography.

## Length variants

- **Standard** 72–78 s (default).
- **Extended** 85–90 s for two-hinge premises (two divergences, two phases each). Never beyond 90 s.
- **Reply episode** 61–65 s: cold open on the comment (as on-screen text), one phase, turn, question.
