# EPISODE YAML SCHEMA (what `pipeline write` must return)

```yaml
id: epNNN-slug                      # lowercase, hyphens
series: never-fell | tomorrow-morning | early-arrival | the-hinge
series_number: 1
pillar: <same as series>
title: "Rome Never Fell"
hook_title: "WHAT IF ROME NEVER FELL"   # 3-6 words, caps, the cover title
file_number: "FILE B-0001"
target_duration: 76                  # 61-90
stamp_text: "UNHAPPENED"
voice: {direction: "calm dry archivist, British-leaning, unhurried, lets facts land", voice_type: preset, voice_id: "<locked id>"}
music: {mood: "low strings, slow pulse", cue: "assets/music/never-fell-01.mp3"}
look_key_prompt: "empty establishing frame of the episode's world, era-correct, named materials, light and weather"
research:
  hinge: "one sentence: the real divergence, dated"
  hinge_date: "275 AD"
  sources: ["Author, Title (year)", "..."]      # >= 2
  facts: ["each with a number or a name", "..."]  # 5-8
  era_sheet: {architecture: "...", clothing: "...", vehicles: "...", street: "...", light: "...", palette: "...", forbidden: "..."}
  cost: "what this timeline loses; this is the turn"
beats:                               # exactly these seven ids, in order
  - {id: hook, vo: "What if ... (first sentence <= 8 words, then an open loop; >= 12 words total)", card: {text: "WHAT IF ...", style: title}}
  - {id: hinge, vo: "...", card: {text: "275 AD", style: date}}
  - {id: phase1, vo: "... because ...", card: {text: "YEAR ONE", style: phase}}
  - {id: phase2, vo: "...", card: {text: "YEAR FIFTY", style: phase}}
  - {id: phase3, vo: "...", card: {text: "TODAY", style: phase}}
  - {id: turn, vo: "[exhale] But ...", card: null}
  - {id: dilemma, vo: "That timeline never happened. Ours did. <question>?", card: {text: "<question>", style: question}}
shots:                               # ~22-26; sizes rotate; each phase has a CLOSE/POV/DETAIL
  - {beat: hook, size: WIDE, location: "...", prompt: "subject doing one action in setting with two era details, light", motion: "slow dolly forward, ...", dur: 2.5, mode: video, sfx: "jets pass", hero_object: true}
dilemma: "<the question>"
pinned_comment: "<takes a side with one fact>"
metadata: {cover_time: 1.2, second_comment: "<other side with one fact>", hashtags: ["#...", "#..."]}
```
Rules: numbers spelled out in vo; no digits; no banned phrases or prompt tokens; no text in images; hook opens with "What if".
