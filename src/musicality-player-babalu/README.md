# Musicality Breakdown — Working Clone

A from-scratch reproduction of emusicality.co.uk's song breakdown player,
using the exact same data format as the original.

## What's here
```
index.html                         ← the player (single file, no build step)
assets/songs/babalu/
    breakdown.json                 ← section/phrase/track metadata
    cover.jpg                      ← album art
    track0.trk … track7.trk        ← 8 audio stems (M4A/AAC, renamed)
```

## How to run

CORS blocks `fetch()` on `file://` URLs, so you need any local web server:

```bash
cd this-folder
python3 -m http.server 8000
# then open http://localhost:8000
```

Or with Node: `npx http-server -p 8000`

## What you'll see

- Click ▶ and all 8 stems start playing in sync via Web Audio API
- Each section block lights up + fills with a progress bar as it plays
- Framework (Derecho/Majao) updates mid-section for choruses
- The 8-count beat indicator pulses in time with the 132 BPM
- Toggle any instrument to mute/unmute just that stem
- Click any section block to jump to it

## How sync works

All 8 stems are decoded to `AudioBuffer`s up front. On play, we create 8
`AudioBufferSourceNode`s and call `.start(0, offset)` on them in the same
JS tick — the Web Audio API schedules them sample-accurately. Mute/unmute
is done by setting `gainNode.gain.value` without touching the sources.

The UI uses `audioCtx.currentTime` as the clock, so sync is perfect.

## Adding another song

1. Create `assets/songs/<slug>/` with `breakdown.json`, `cover.jpg`, and
   `track0.trk`…`trackN.trk`.
2. Edit the `SONG_SLUG` + `SONG_META` constants at the top of `index.html`.
3. Reload. Done.

## The breakdown.json schema

```json
{
  "trim": 0.09,                  // global audio offset (seconds)
  "beatsPerMeasure": 8,          // beats per phrase (bachata uses 8-count)
  "tracks": [
    "Vocals",                     // simple string = track name, no groups
    {
      "title": "Bongo & Güira",
      "groups": ["Percussion", "Rhythm"]   // for UI group toggles
    },
    ...
  ],
  "sections": [
    { "title": "Intro", "phrases": [4] },                     // 4 phrases × 8 beats = 32 beats
    { "title": "Verse", "phrases": [4, 4] },                  // two groups of 4 phrases (32 + 32 = 64 beats)
    {
      "title": "Chorus",
      "phrases": [
        ["Derecho", 8, 8, 8],     // explicit-beat phrases with framework label:
        ["Majao",   8, 8, 8]      // each = 4 phrases × 8 beats = 32 beats
      ]
    },
    {
      "title": "Verse",
      "structure": "Derecho",     // default framework for this section
      "phrases": [4, 4]
    }
  ]
}
```

**`phrases` reading rules** (matches the original emusicality.co.uk player):

- A bare **number `N`** means *N phrases of `beatsPerMeasure` beats each*. So `[4]` at `beatsPerMeasure: 8` is 32 beats, not 4 bars.
- An **array** lists phrases item-by-item:
  - A **number** is the explicit beat count of that phrase.
  - A **string** sets the framework label (e.g. `"Derecho"`, `"Majao"`) *and* adds one phrase of `beatsPerMeasure` beats with that label.
- Section length is the sum of all its phrase beats. Seconds = `beats × 60 / bpm`.
