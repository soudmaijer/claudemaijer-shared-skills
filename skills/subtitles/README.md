# subtitles

House style and code for subtitles (captions) on a video. Captions are burned into the picture, and a matching `.srt` is written next to the video.

The style:
- short cues (about 60 characters), a new cue for every sentence, then split at commas and similar breaks;
- at most two balanced lines;
- bold white sans-serif with a thin black outline, on a light semi-transparent box per line;
- bottom centre, with the bottom of the picture kept free of content.

The other video skills in this plugin (`demo-video`, `implementation-video`) use it for their subtitles.

## Requirements

- Python 3 with Pillow (`python -m pip install pillow`).
- ffmpeg for the command line. libass is not needed.
- A bold sans-serif font. The script finds Helvetica Bold (macOS), Arial Bold (Windows) or DejaVu Sans Bold (Linux). Set `CAPTIONS_FONT` or pass `--font` to use another one.

## Usage

Ask Claude to add subtitles to a video, or run the script:

```bash
python scripts/captions.py --video talk.mp4 --cues cues.json --out talk-captioned.mp4
```

`cues.json` lists the spoken sentences with their times:

```json
[{"start": 0.0, "end": 2.5, "text": "Welcome to this short example."}]
```

From your own Python build script:

```python
from captions import Captions
cap = Captions(1920, 1080)
cues = cap.hold_until_next(cap.split_cue("A spoken sentence, with a clause.", 0.0, 3.0))
```

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | The rules, for Claude |
| `scripts/captions.py` | Splits text into cues, renders caption images, burns them in with ffmpeg, writes the `.srt` |
