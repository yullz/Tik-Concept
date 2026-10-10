# 01 · Channel Bible

## Three original names (pick one, then never change it)

| Name | Why it is ownable | Handle | Sign-off | End stamp |
|---|---|---|---|---|
| **UNHAPPENED** (recommended) | A coined word: nobody ranks for it, it says the whole premise, and it *is* the end stamp. Searchable, pronounceable in every market, works dubbed. | `@unhappened` | "That timeline never happened. Ours did." | **UNHAPPENED** |
| **ELSEWHEN** | "Else-when": another time. Evocative, rare, reads as a place you visit. Slight sci-fi flavour that suits the physics pillar. | `@elsewhen` | "Filed under Elsewhen." | **ELSEWHEN** |
| **TIMELINE B** | The clearest: everyone understands "the other timeline" instantly; file numbers become B-0001. Less unique as a word, strongest as a format label. | `@timelineb` | "This was Timeline B." | **FILE CLOSED** |

Avoid anything with "What If" or "Alt History" in it: those are crowded, generic, and read as copies.
Check all three handles on TikTok, YouTube and Instagram the same day. The repository uses
"Counterfact" as a placeholder style name (`styles/counterfact-v1.yaml`); only the channel
name, the stamp text (`stamp_text` in each episode) and the sign-off change.

Tagline for any of the three: **"History, rewritten one decision at a time."**

## The promise (one sentence, printed on the channel page)

In seventy-five seconds you will see a world that almost existed, understand exactly why it didn't, and leave with a question you'll argue about in the comments.

## Who it is for

| Segment | Why they watch | Where they live |
|---|---|---|
| Core: 18–34, history and geopolitics curious, strategy-game players (Civilization, Europa Universalis, Hearts of Iron, Crusader Kings) | They already run counterfactuals for fun. They argue about them. | TikTok edutainment, YouTube Shorts history, r/HistoryWhatIf, r/AlternateHistory |
| Second: "what would happen if" physics audience (ocean dries up, moon vanishes) | Pure curiosity, high share rate, kid-safe | TikTok science, Shorts science |
| Third: students and teachers | Memorable framing of real causality | Shorts search, saves |

Comments are the product. The audience is people who *correct* you. Design for them: a precise hinge, one defensible mechanism per phase, and an ending that forces a side.

## Four content pillars (each pillar is a recurring series with its own accent colour)

| Pillar | Series name | Example premises | Accent |
|---|---|---|---|
| Empires that never fell | **Never Fell** | Rome never collapses; Byzantium holds Constantinople in 1453; the Mongols take Vienna | Imperial gold `#C9A227` |
| Tomorrow-morning physics | **Tomorrow Morning** | The ocean dries up overnight; the Moon disappears; all oil vanishes; gravity drops 10% | Deep cyan `#2BB3C0` |
| Technology arrives early | **Early Arrival** | Steam engines in 100 AD Rome; the internet in 1950; antibiotics in 1300; printing press in Athens | Amber `#E8872B` |
| One decision reversed | **The Hinge** | Columbus turns back; the Library of Alexandria survives; the Marshall Plan is rejected; Apollo never lands | Crimson `#B8322F` |

Rule: at least one episode from each pillar every week. Pillars one and four are the comment engines; pillar two is the share engine; pillar three is the save engine.

## The character of the channel (why every video is unmistakably ours)

TikTok and YouTube both require original content and both reward a recognisable format. The
channel's character is built from six devices that cost nothing in generation and appear in
every episode, so a viewer knows it is ours within one second and a platform never reads it
as recycled:

1. **The file number.** Every episode is a case file: `FILE B-0001`, faint, top right, the whole
   video. The description repeats it. Reply episodes are `B-0001 / R1`.
2. **The sonic logo.** A two-note bowed-string figure (low, then a fifth up, 0.8 s) under the
   first frame, before the narrator speaks. Same file every episode (`assets/sfx/sonic-logo.wav`).
3. **The "WHAT IF" sigil** in the pillar colour, bottom left, always.
4. **The hinge line.** A thin bar that splits in two when the divergence is named. Our one graphic.
5. **The stamp.** The last second: a red stamp slams onto the frame (UNHAPPENED / ELSEWHEN /
   FILE CLOSED) with a dry thud. It is the visual sign-off and the thing people imitate.
6. **The Archivist's voice.** One voice, one register, one sign-off sentence, forever.

Originality rule: no two posts share a body. Language versions are re-cut by the pipeline
(cuts follow the new narration), carry their own cards, cover and file suffix (`B-0001 / ES`).
Reply episodes are new scripts. We never re-upload a video with a different hook.

## The narrator: "The Archivist"

The voice is not a hype narrator. It is a calm, dry, precise archivist reporting from the other timeline as if it already happened and they have the files. Present tense for the alternate timeline, past tense for ours.

- Opens every episode with the words **"What if"** (it is the brand, and it is the label).
- Never says "imagine", "buckle up", "let's dive in", "crazy", "insane", "mind-blowing".
- Speaks numbers as words, slowly. Lets a fact land. One performed non-verbal per episode at most (a dry exhale before the turn).
- Sign-off formula, always: a dilemma, then "**That timeline never happened. Ours did.**" and the question.

Full voice casting and settings: `docs/06-voice-and-sound.md`.

## Visual identity

- **Look:** photoreal cinematic, anamorphic 35 mm, natural light and practicals, haze but never glow, real materials and era-correct details. Full spec and prompt grammar in `docs/05-visual-style-and-prompt-library.md`.
- **Typography:** one typeface for everything (Inter Display or Montserrat, Extra Bold caps for cards, Semi Bold for captions). No stroke outlines, no rainbow karaoke.
- **The hinge mark:** a thin horizontal line across the lower third that *splits* into two lines at the moment the narrator names the divergence. It returns at the end card. It is the only brand graphic in the body of the video.
- **Phase cards:** three on-screen cards, each with a real date or a relative time ("YEAR ONE", "YEAR FIFTY", "TODAY"), accent-coloured by pillar.
- **End card (last 4 s):** the question in large type, the "WHAT IF" sigil, the next episode's hook as a one-line tease.
- **Cover frame:** the single most specific image in the episode, with a 3–5 word title. Never a generic explosion.

## Series architecture (why people follow instead of just watch)

- Every episode stands alone, but each belongs to a series with a numbered title ("Never Fell · 03").
- Every end card teases the next episode in the same series.
- Every fourth episode is a **comment-reply episode**: the Archivist answers the best objection from the comments with a new 60-second timeline. This is the single cheapest source of views and the strongest follow driver.

## Accuracy, sensitivity and labelling policy

1. The hinge (the real divergence point) is always real and sourced. The research sheet lists sources. We never invent a real-world fact.
2. Counterfactuals are labelled: "What if" on screen in the first second, "Alternate timeline" in every description, AI-generated content flagged on both platforms.
3. No episode glorifies atrocity, and no premise is "what if [genocide/terror] succeeded". Wars are covered as logistics and consequences, not as spectacle.
4. No living politicians. No real living people as characters. Historical figures appear only in wide or medium shots, never as close-up likenesses.
5. Religious premises are handled as institutions and geography, never as theology.
6. Music is licensed from a library (Epidemic Sound or Artlist). No AI-generated music in the first season; it is the fastest tell of slop.

## Season one (first 30 episodes)

Thirty episodes, ten per week for three weeks, then a reply week. Episode list: `docs/07-topic-backlog.md` (the first ten are fully written in `episodes/`).

## KPIs (what we watch, in order)

| Metric | Target (month 1) | Why it matters |
|---|---|---|
| 5-second qualified view (watched ≥ 5 s) | ≥ 65 % | TikTok counts a view only past five seconds; the hook is built to hold the viewer through it |
| 3-second hold | ≥ 75 % | the impossible image is doing its job |
| Average watch percentage | ≥ 60 % | Pacing and script shape |
| Completion rate | ≥ 35 % | The turn and the question are working |
| Comment rate | ≥ 1.0 % of views | The dilemma is real |
| Share rate | ≥ 1.5 % | Premise strength |
| Follows per 1k views | ≥ 8 | Series architecture |

The growth plan in `docs/03-growth-plan-10M.md` turns these into a path to ten million views.
