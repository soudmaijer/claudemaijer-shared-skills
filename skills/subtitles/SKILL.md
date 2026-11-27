---
name: subtitles
description: House style and code for subtitles and captions on any video, burned in plus a matching .srt, in a short-cue streaming style (balanced lines, light box, bottom centre). Use whenever a video gets subtitles or captions; the other video skills in this plugin refer to this one.
metadata:
  version: "1.0.0"
---

# Subtitles

`scripts/captions.py` implements every rule below (`Captions.split_cue`, `hold_until_next`, `lines`, `png`, `write_srt`, `overlay_filter`). Import it or run it from the command line. Do not re-implement the rules, and do not restate them in another skill: refer to this one.

## Rules

- **Burn them in.** Most players and wikis ignore a sidecar `.srt`. Also write the `.srt`, with the same cues and the same line breaks.
- **Short cues.** Little text per cue, so cues change often. At most about 60 characters per cue. A new sentence always starts a new cue. A longer sentence is split at clause boundaries (`,` `;` `:`) first, and on words last. Each chunk gets its share of the spoken sentence's time, by character count.
- **Timing follows the narration.** A cue stays on screen until the next one starts, so captions do not flicker in the short pauses between sentences.
- **At most two lines of about 42 characters, balanced.** A cue that does not fit one line is split at the word boundary that makes the two lines closest in rendered width. Never a long first line with one word below it.
- **Font:** a bold sans-serif (Helvetica Bold on macOS, Arial Bold on Windows, DejaVu Sans Bold on Linux; override with `--font` or `CAPTIONS_FONT`), 44 px at 1080p, white with a 1 px black stroke. Sizes scale with the frame height.
- **Background:** a tight box per line, not one panel for the cue, black at about 30% opacity (alpha 80 of 255). It reads as light grey on a white slide. A darker box was rejected as too heavy; the bold font with the stroke stays readable on the light box.
- **Position:** bottom centre, about 44 px from the bottom at 1080p. Keep the bottom ~180 px of the picture (1080p) free of content, so a caption never covers anything. Tell whoever designs the slides or frames.
- **Spelling:** captions use the normal written form of every word (product names, `API`, `CPUs`). The pronunciation spellings used for text-to-speech (`A P I`) never reach the captions.

## Burning in with ffmpeg

Many ffmpeg builds lack libass, so the `subtitles` and `ass` filters are not available. Do not depend on them. Render each cue as a transparent full-frame PNG (`Captions.png`) and overlay it for its time range:

```
[prev][k:v]overlay=0:0:enable='between(t,START,END)'[next]
```

`Captions.overlay_filter` builds this chain. A switchable subtitle track (`-c:s mov_text`) may be embedded as well, next to the burned-in captions.

## Command line

```
python scripts/captions.py --image frame.png --cues cues.json --out out.mp4
python scripts/captions.py --video in.mp4 --cues cues.json --out out.mp4 [--srt out.srt] [--font <path>]
```

`cues.json` is a list of `{"start", "end", "text"}`, typically one entry per spoken sentence; the script splits it into short cues.

## Verify

Extract a frame in the middle of several cues (`ffmpeg -ss <t> -i out.mp4 -frames:v 1 f.png`) and look at each: balanced lines, readable on the background, nothing covered, normal spelling. Compare the `.srt` with the burned-in text.
