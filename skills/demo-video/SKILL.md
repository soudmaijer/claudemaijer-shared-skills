---
name: demo-video
description: Make a narrated demo video of a running web application for viewers who are new to it, with intro slides, film-style subtitles, a cursor, spotlights and zooms on what is being explained, and smooth transitions. Everything runs locally (offline text-to-speech, Playwright recording, ffmpeg). Use this when someone asks for a demo video, screen recording, walkthrough, product tour or explainer of an app. For a short video that proves a finished ticket works, use the implementation-video skill, which reuses this skill's scripts.
compatibility: Requires the subtitles skill from this package. Install both together.
metadata:
  version: "1.1.0"
---

# Making a demo video

The goal is a video that someone with no knowledge of the domain can watch and understand: what the product is for, what each screen does, and what is still to come. Talk to the person in their language; the video uses the language of the project documentation unless they ask otherwise.

The scripts, theme and rules in this skill are shared with the `implementation-video` skill. Sections marked **(shared)** apply to both kinds of video.

## What it rests on (shared)

- **The story comes from the project documentation**, for example functional flows, a glossary and a roadmap. Ask where it is if you cannot find it. Never invent a feature, term or explanation. A term the documentation does not explain is left out of the video.
- **The app shows what is built.** Narrate only what the app actually does. If the app and the documentation disagree, do not narrate either version as fact: report the difference to the person afterwards, and offer to update the documentation.
- **The code may be read** (read only) to find screens, routes and mock data, and to name things correctly.
- **"Not built yet"** is said only for what the app does not show, and with the roadmap phase it is planned in.

## What the video contains

0. **A title slide, always first**: the product and what exactly this video is about, in one sentence of narration. **Then a separate agenda slide** listing the sections the viewer will see, its entries appearing one by one. Never put the agenda on the title slide.
1. **Opening slides** (2 or 3) that explain the domain from scratch: the key terms and the chain the product sits in, as a simple diagram.
2. **Per screen or step:** a short intro slide (3 to 6 s) saying what this step is and why it exists, then the screen itself.
3. **On the screen, point at what is explained** (see "Visual cues").
4. **Closing:** a timeline slide of the plan ahead (per phase: period, what is built, the go-live as the milestone), with entries appearing in time with the narration, then an end slide. Only what the roadmap says, and "not built yet" only for what the app does not show. Leave the timeline out if there is no roadmap.

## Slide content (shared)

- **Slides are conceptual:** short statements and simple diagrams. No shell commands, file names, ports or step lists on a slide. The details live in the document or page the video belongs to; the narration points there.
- **Narration in plain language:** short sentences, one idea per sentence.
- **A transition sentence opens every scene after the title.** It links the scene to the previous one ("Now you know why this matters. But where does the data come from?"). Without it the video jumps from topic to topic.
- **Context sits at the top**, as a subtitle line under the slide title, because people read top to bottom. A takeaway is a light line of text, never a heavy coloured band at the bottom of the slide.
- **Progressive reveal:** a slide element appears when the narration mentions it, like a presenter who builds up a slide, not all at once. Elements named in the same sentence appear together; the title and the context line are visible from the start. See "Slides and theme" for the markup.
- **Keep the bottom free for subtitles:** about 150 px of a 1440x900 slide (180 px at 1080p). Put a footer or logo at the top.
- **Match the page the video belongs to:** its agenda, its rules and its wording. Check before building.

## Visual cues (shared)

Every sentence that names an element has a visual cue on it: an animated cursor moving there before a click, a spotlight that dims the rest, an outline or pulse around the element. Zoom only to highlight something small, then zoom back out before the next sentence. No zoom when the element is readable at full view, and never start a scene zoomed in: the viewer first sees the whole screen.

## Subtitles and transitions (shared)

- **Subtitles:** follow the `subtitles` skill in this plugin (`../subtitles/SKILL.md`) for the style, cue length, line breaks, timing and spelling. Do not restate or change its rules here. Subtitles are burned in over the full frame (no strip reserved for them), also embedded as a switchable track and kept as `.srt`. `assemble.py` uses `../subtitles/scripts/captions.py`; if the `subtitles` skill is not installed next to this one, stop and tell the person to install it.
- **Transitions:** crossfades between scenes (0.6 s), a fade in at the start and a fade out at the end. No music.

`assemble.py` implements these rules.

## Slides and theme (shared)

Slides are HTML pages of 1440x900 in the example's `slides/` folder style. They link `theme.css` and may use `logo.svg`; `record.js` copies every file of the theme folder next to the slides. The default theme in `theme/` is neutral. For a house style, make a theme folder with the same file names (and any fonts or images it needs) and pass `--theme <dir>`. Ask the person whether they have a house style before you design slides.

Slide markup rules: the content sits in `<div id="root">`; elements with class `a` fade in when recording starts, delayed by the CSS variable `--d` (for example `style="--d:1.2s"`). This is the progressive reveal: set `--d` of an element to the `start` of the cue (in `<id>.cues.json`) of the sentence that mentions it. A hidden element keeps its place (opacity, not `display:none`), so the layout does not jump when it appears.

**Re-record a slide after every text change.** A stale clip once shipped old slide text. Before assembling, check that every slide clip (`<id>.mp4`) is newer than its slide HTML, and re-run `record.js` and `mux` for any that is not.

## One-time setup (shared)

Everything runs locally; no text or audio leaves the machine. **Always run `scripts/setup.sh` first** (Windows: `scripts/setup.ps1`, untested). It is idempotent: it checks ffmpeg, node, a suitable Python (3.12 to 3.14; 3.15 or newer is refused because onnxruntime has no wheels for it yet), a virtual environment with Kokoro, the two Kokoro model files (about 340 MB), Playwright with Chromium, and runs a voice smoke test. It installs what is missing, prints `OK` at the end and exits non-zero otherwise.

Tools and models go to `$DEMO_VIDEO_HOME` (default `~/.local/share/demo-video-tts`). Set the variable to reuse an existing install. Run the Python scripts with `$DEMO_VIDEO_HOME/venv/bin/python` (Windows: `venv\Scripts\python`).

## How to build it (shared)

**Build in clips, in parallel, and assemble last.** That is much faster than one long recording, and a single scene can be redone on its own.

1. **Explore** the app and, if needed, the code. Make a scene list: per scene, the screen or slide, the narration, and the element to highlight per sentence. Write it to a working folder that is not committed (for example `local/demo/<name>-script.md`; check that `local/` is in `.gitignore`).
2. **Narration per scene** with `scene.py narrate`: local Kokoro voice (default `af_heart`, change with `--voice`), one audio part per sentence so subtitles can be timed exactly. The audio length sets the length of the scene.
   - **Voice:** Kokoro, an open-source model, with voice `af_heart` sounds natural; the built-in text-to-speech of the operating system was rejected as robotic. When the voice is not agreed yet, narrate one scene with 2 or 3 voices and let the person choose before you narrate everything.
   - **Pronunciation map** (`pronunciation.json`, `{"written": "spoken"}`): subtitles and slides keep the term as written; only the voice uses the spoken form. Use it for words in another language than the voice, for abbreviations that should be spoken in full (only where the documentation gives the full name), and for names that the voice says wrong. Typical entries: acronyms spelled out (`"API": "A P I"`, `"AI": "A I"`, `"CPUs": "C P U s"`), `"p99": "p ninety-nine"`, units (`"GB": "gigabytes"`), and numbers and paths written out as words. Try terms as written first; add an entry only when a term comes out wrong. Pick a spelling by ear: narrate one sample sentence with numbered variants, play it and let the person choose. Terms are replaced longest first, so `CPUs` wins over `CPU`.
3. **Record every scene as its own clip, concurrently**, with `record.js`, after the narration, so each cue lands on its own sentence.
   - **A slow live answer** (for example a chat with an AI model) varies per run: measure it once, write narration that covers the wait, and point at the answer only in a sentence that starts after it. Send a message with `"fill"` plus `"press": "Enter"` rather than clicking a send button.
   - **A scene that needs data another scene creates** is recorded after that scene, not in parallel.
   - **Links that open a new tab** are followed with `"goto": true`.
   - Role names match as a substring: use `"exact": true` or a scoped CSS selector when several elements have similar names.
   - **A login**: save a Playwright storage state once and pass `--storage <file>`. Never commit it.
4. **Mux** each clip with its audio (`scene.py mux`), in the background in parallel. Always run ffmpeg with `-nostdin`.
5. **Assemble** with `assemble.py`: crossfades, burned-in subtitles, fades, `.srt`.
6. **Check before showing it:** extract one frame from every scene (slides, highlights, zooms, subtitles) and look at each one, or let a subagent do it. Fix anything clipped, blank, overlapping, or with subtitles over important UI.

## Reuse as much as possible (shared)

A new version starts from what exists, never from scratch.

- Start from the latest scenes, slides and narration of the previous version.
- **Redo only the scenes that change.** A text or pronunciation change means narrating and re-recording that scene only. A change in subtitle style or transitions needs only a new assemble.
- Keep audio, video and subtitles separate until the final assemble.
- **Make a short sample first** (two or three scenes) for any change in look or voice, and iterate until the person is happy; only then roll it out to the full video.

## Scripts (shared)

All in `scripts/`. Order: setup once, then narrate, record, mux per scene, assemble.

| Script | Arguments | What it does |
|---|---|---|
| `setup.sh` / `setup.ps1` | none | Prerequisite check and install. |
| `scene.py narrate` | `<scenes.json> --out <clips> [--map pronunciation.json] [--voice af_heart] [--lang en-us] [id ...]` | Audio per scene: `<id>.wav` and `<id>.cues.json`. The map defaults to `pronunciation.json` next to `scenes.json`. |
| `record.js` | `--scenes <scenes.json> --clips <clips> --id <id> [--slides <dir>] [--theme <dir>] [--base <url>] [--storage <file>]` | Records a slide (`<slides>/<id>.html`, default `slides/` next to `scenes.json`) or an app screen with cursor, spotlight and zoom, timed to the cues. Writes `<id>.webm` and `<id>.offset`. Run with `node`. |
| `scene.py mux` | `<id> <clips>/<id>.webm $(cat <clips>/<id>.offset) --out <clips>` | Trims the recording to the narration and adds the audio: `<id>.mp4`. |
| `assemble.py` | `--clips <clips> <out.mp4> <id> [<id> ...]` | Joins the scenes, burns in subtitles, fades in and out, writes `<out>.srt` and embeds it. |

`scenes.json` is a list of `{"id", "kind", "sents": [...]}`. Slide scenes use any kind other than `app`. App scenes are `{"kind": "app", "url", "ready", "sents": [{"text", "act": [{"target", "z", "click", "fill", "press", "goto"}]}]}`; the header of `record.js` has the full format. A `url` starting with `/` is appended to `--base`.

`examples/sample/` is the template for a new video: `scenes.json`, `pronunciation.json`, `slides/` and a small local `app/` page. Copy it, then replace the content. Run it from this skill folder:

```
V=$DEMO_VIDEO_HOME/venv/bin/python; E=examples/sample; C=local/demo/clips
$V scripts/scene.py narrate $E/scenes.json --out $C
for i in t1 t2 a1 e1; do
  (node scripts/record.js --scenes $E/scenes.json --clips $C --id $i --base "file://$PWD/$E/app" &&
   $V scripts/scene.py mux $i $C/$i.webm $(cat $C/$i.offset) --out $C) &
done; wait
$V scripts/assemble.py --clips $C local/demo/sample.mp4 t1 t2 a1 e1
```

## Where it goes, and what is kept (shared)

- The video, the `.srt`, the script and the clips go in a folder that git ignores (for example `local/demo/`). A video never ends up in the repository.
- A new version gets a new name (`-v2`, `-v3`) and its own clips folder; the earlier one stays.
- **Never delete clips, slides, audio or intermediate renders until the person says they are satisfied.** Feedback usually concerns one or two scenes, and the rest can be reused. Once they are satisfied, ask before cleaning up.

## Afterwards (shared)

**Show the video and get approval before you publish it anywhere.** When you publish to a wiki page that already holds media, fetch the page fresh right before you update it, and keep every existing attachment and embed; an update built from an older copy drops them.

Open the video for them (`open` on macOS, `start` on Windows, `xdg-open` on Linux). Report in a few lines: the duration, the scenes, what could not be shown and why, and where the app differs from the documentation.
