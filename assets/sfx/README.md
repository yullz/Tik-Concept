# Sound effects (licensed or CC0, not in git)

The assembler places a file at each shot's start when `assets/sfx/<slug>.wav` exists, where the slug
is the shot's `sfx` text lower-cased with hyphens (`"jets pass"` → `jets-pass.wav`). Two fixed files:

- `sonic-logo.wav`  two-note bowed-string figure, 0.8 s, under the first frame (set `sfx: sonic logo` on shot 1 to use it)
- `card.wav`        a short dry tick placed automatically on every phase, date and stat card

Minimum six cues per episode. Sources: freesound.org (CC0) or the music library's SFX catalogue.
