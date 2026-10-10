# 05 · Visual Style & Prompt Library

## The Unhappened look (locked for season one)

| Element | Spec | Why |
|---|---|---|
| Format | 9:16, keyframes at 2K (Nano Banana Pro), clips at 1080×1920 | vertical native, headroom for reframes |
| Lens | 35 mm anamorphic, shallow depth of field on closes, deep focus on wides, mild oval bokeh | the "film" tell that reads as deliberate |
| Camera | eye level or slightly low on people; high and slow on cities; handheld micro-shake only on POV | authored coverage, not drone wallpaper |
| Film | Kodak 5219 negative, 2383 print emulation, fine grain, soft highlight roll-off | kills the plastic digital sheen |
| Light | natural key (sun, overcast, dusk) plus practicals (torches, sodium lamps, screens); volumetric haze allowed, **no glow, no bloom, no lens flare** | glow and flare are the two biggest slop tells |
| Palette | desaturated earth base, one pillar accent colour per episode in props and light (gold / cyan / amber / crimson) | consistency across the series |
| Materials | named, era-correct: travertine, bronze, tufa, linen, oak, cast iron, Bakelite, carbon fibre | specificity beats adjectives |
| People | real faces in wides and mediums only; closes are hands, objects, backs of heads, silhouettes; never a close-up likeness of a historical figure | avoids uncanny faces and identity issues |
| Text | none generated in frame; signage described as "weathered inscription, illegible at this distance" | AI text is always wrong |
| Motion | camera-driven (dolly, push, track, crane, pan); subjects do small, physical things (walk, turn, lift, pour); nothing transforms | morphing is the clip-level tell |

## Prompt grammar (every keyframe prompt is built from these slots, in this order)

```
[SIZE] [SUBJECT doing one physical ACTION] [in SETTING with two era-correct DETAILS],
[LIGHT and WEATHER and TIME], [LENS], [FILM], [ACCENT], [NEGATIVE]
```

`pipeline promptsheet` assembles the prompt from the shot's `prompt` field (SUBJECT, ACTION,
SETTING, DETAILS) plus the style bible in `styles/counterfact-v1.yaml` (LENS, FILM,
NEGATIVE) and the episode's accent. Writers only write the middle; the house look is appended.

**Example, Never Fell · 01, shot 1 (the hook):**
> WIDE low angle, three delta-wing jet fighters in tight formation banking over the Colosseum, the Colosseum intact and in use with a modern retractable roof of bronze-coloured louvres, SPQR and a gilded eagle painted on each tail fin, Rome at dusk, sodium street lamps just lit, haze over the Tiber, 35 mm anamorphic, Kodak 5219 with 2383 print emulation, fine grain, soft highlights, imperial gold accents, no text, no watermark, no lens flare, no glow

**Example, same episode, shot 9 (human scale):**
> CLOSE, a baker's hands sliding flat bread into a brick oven, a battered aluminium tray stamped with a small eagle, a wall-mounted induction panel beside the oven, Trastevere morning, cool north light from a window, 35 mm anamorphic, Kodak 5219 with 2383 print emulation, fine grain, no text, no watermark, no glow

## Motion prompt grammar (image-to-video, 5 s, used at 2.5–3.5 s)

```
[CAMERA MOVE at SPEED], [one SUBJECT micro-motion], [one ATMOSPHERE motion], subject keeps its shape, no new objects appear, no text
```

Examples:
- "slow dolly forward, the jets drift left across the frame and bank gently, haze moves with the wind, buildings stay rigid, no new objects appear, no text"
- "static tripod with a slow push-in, hands slide the tray into the oven and withdraw, heat shimmer above the oven mouth, no new objects appear, no text"

Camera vocabulary that works on Kling 3.0: `slow dolly forward`, `slow dolly back`, `lateral track left/right`, `crane up/down`, `slow pan`, `handheld micro-shake`, `orbit a few degrees`. Avoid: `zoom` (produces warping), `fast`, `whip`, `spin`, `transform`, `morph`, `time-lapse`.

## Banned tokens (the linter rejects a prompt containing any of these)

`8k`, `4k`, `hyper-detailed`, `ultra-detailed`, `masterpiece`, `trending on artstation`, `award-winning`, `epic`, `cinematic masterpiece`, `lens flare`, `glowing`, `glow`, `bloom`, `neon` (unless the era sheet calls for it), `particles`, `sparkles`, `hologram`, `holographic`, `futuristic city` (name the city and the change instead), `beautiful`, `stunning`, `breathtaking`, `hyperrealistic`, `octane`, `unreal engine`, `dramatic lighting` (say which light), `volumetric lighting` (say "haze" and the light source).

## Shot-size tags and what they mean for the prompt

| Tag | Prompt opener | Use |
|---|---|---|
| `AERIAL` | "AERIAL, high and slow," | one per episode max, never the opener twice in a row |
| `WIDE` | "WIDE," | establishing a phase |
| `MEDIUM` | "MEDIUM, waist-up," | people doing things |
| `CLOSE` | "CLOSE," | hands, objects, textures; the human scale |
| `DETAIL` | "DETAIL, macro," | the hinge object, inscriptions (illegible), mechanisms |
| `POV` | "POV, handheld," | the viewer inside the timeline |
| `MAP` | "MAP, top-down," | a physical map on a table or wall, never a glowing UI map |

## Era sheet template (filled in each episode's `research.era_sheet`)

```
period/timeline: ...
architecture: (three named materials, one named building type)
clothing/uniforms: (two named garments, colours, fabrics)
vehicles/machines: (what exists, what the premise adds, and how it is built: materials, power source)
street furniture/signage: (lamps, paving, awnings, inscription style — always illegible)
light: (latitude, season, time of day the episode favours)
palette anchor: (two colours from the real place)
forbidden anachronisms: (list)
```

## Continuity devices

- **Look key** (one per episode) passed as the image reference for every keyframe.
- **Hero object**: one physical object that recurs in at least four shots and changes state (the through-line in `docs/02-format-beat-sheet.md`): an eagle standard that gets older, a tide line that drops, a map that fills.
- **Location budget**: no more than two consecutive shots in one location; each phase moves at least once.
- **Human scale**: at least one `CLOSE` or `POV` per phase.

## Reject list (Gate A and B reasons, fixed vocabulary)

Stills: `anachronism`, `anatomy`, `text`, `warped-architecture`, `generic`, `wrong-size`, `off-palette`, `duplicate-of-another-shot`.
Clips: `morph`, `limb`, `flicker`, `static-start`, `text`, `wrong-camera`, `too-fast`.

The reasons are counted per prompt pattern in `renders/*/selections.yaml` so the prompt library improves each week.
