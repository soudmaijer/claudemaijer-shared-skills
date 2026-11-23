---
name: video-process-extraction
description: Extract the business process, workflow and requirements from a screen recording of someone doing their work (for example a Teams recording of a user walking through an application). Transcribes the speech locally, samples frames on screen changes, combines what is said with what is on screen, and writes an evidence-based process analysis with steps, inputs, systems, business rules, pain points, requirements and open questions. On request it also writes an English user journey for a vendor (with a "must keep working" list), compares the result with docs, code or release notes, or drafts mails to the recorder. Trigger phrases: "analyse this video", "extract the process from this recording", "what does the user do in this screen recording", "requirements from a video", "transcribe and analyse the recording", "document the user journey", "check the journey against a release", "ask a user to record their work".
---

# Video process extraction

Turn a screen recording into a traceable process description. Every statement must point to a timestamp in the video (speech or frame). Never guess.

The core is steps 1 to 5: video in, `analysis.md` out. The optional extras run only after the user agrees.

The person who made the recording (the recorder) is often not the person who runs this skill. Do not treat the user's answers as evidence about the recorded work, unless they say they know it first-hand. List questions about the work as open questions for the recorder.

## Inputs

Ask for these one at a time if they are missing:

1. **Video path** (mp4, mkv, mov, webm).
2. **Spoken language** (default `nl`).
3. **Domain terms file** (optional). A plain text file with system names, screen codes and jargon. It improves speech recognition. Offer to create one from a docs folder.

## Step 1: Check the environment

Run from this skill folder:

```
python scripts/prepare_video.py --check
```

If something is missing, tell the user to run `python -m pip install -r requirements.txt`. Use Python 3.10 to 3.14 (3.15 has no `av` wheels yet). Recommend a virtual environment. Do not install packages without the user's consent.

## Step 2: Transcribe and sample frames

```
python scripts/prepare_video.py VIDEO --out OUTDIR --lang nl --vocab TERMS.txt
```

Frames use change detection: a frame is saved when at least 1% of the pixels change (`--threshold 0.01`), at most every 2 s (`--min-gap`) and at least every 15 s (`--max-gap`). `--threshold 0` gives a fixed frame every `--max-gap` seconds. Small changes such as a status-bar message can stay below the threshold; lower it (for example 0.003) if such moments matter. A moving webcam tile can cause many frames; raise `--min-gap` then. Model: `large-v3-turbo` (`--model`; use `small` on a slow laptop). The first run downloads the model (about 1.6 GB). On a CPU, expect roughly 1/4 to 1x the video length.

Output in OUTDIR:
- `transcript.srt`: raw speech with timestamps.
- `transcript.txt`: one line per segment, `[hh:mm:ss] text`.
- `frames/f_NNN.jpg` and `frames/index.tsv` (frame name, timestamp, reason: start / change / max-gap).

## Step 3: Read speech and frames together

1. Read `transcript.txt` fully.
2. View the frames in order. For long videos, delegate frame viewing to a subagent per block of about 20 frames. Ask it to report per frame: screen/window title, environment (test/production), visible field names and values, menus, dialogs, files, messages. Keep its report as text, not images.
3. If a step happens between two frames and matters, rerun with `--skip-transcript --out OTHERDIR` and a lower `--threshold` or `--max-gap`.
4. Correct speech-recognition errors with what is on screen (for example "a b c one two three" spoken, ABC123 visible). List every correction.
5. Mark text you cannot verify with `[?]`. Do not fix it by guessing. Flag Whisper artefacts (repeated sentences, hallucinated text during silence) as artefacts, not content.

## Step 4: Write the analysis

Write `OUTDIR/analysis.md` with `templates/analysis-template.md`. Rules:

- Write in the language of the video unless the user asks otherwise.
- Each step row: time range, what the user says, what is on screen. Keep these two columns separate.
- Separate **observed** (said or visible) from **interpreted**. Label every interpretation.
- Requirements come only from observed behaviour, stated rules or stated pain points. Each requirement cites the timestamp(s) it comes from. Do not invent requirements the user did not show or say.
- List open questions for the recorder instead of filling gaps.
- Note sensitive data (names, personal data, customer data) that is visible, so the user can decide what to share.

## Step 5: Report

Give the user: the output folder, the number of steps, requirements, pain points and open questions, and the speech corrections. For several videos of the same process, also write `OUTDIR/../summary.md` that merges the steps into one end-to-end workflow, with references to each video's analysis. Then ask the user which optional extras they want, if any. Suggest the one that fits the situation (for example the review mail when there are open questions for the recorder). Run nothing extra without a yes.

## Optional extras

Run these only when the user asks or agrees. The user can also do any of these outside the skill (for example write the mails themselves); do not insist.

### User journey for a vendor

Write `OUTDIR/user-journey.md` with `templates/user-journey-template.md`. This document goes to people outside the team (for example a SaaS vendor), so:

- Write in English, whatever the language of the video.
- Explain internal terms and abbreviations the first time, or list them under Open questions if their meaning is not evidenced.
- Use the role, not the person's name. Leave out personal data.
- "Must keep working" lists only behaviour the user relies on, as shown or said in the recording. Each item cites a timestamp and names the journey steps it covers.
- Keep current behaviour, pain points and wishes in separate sections. A wish is not a requirement.
- Advise the user to have the recorder approve the journey before it is shared.

### Compare with docs or code

Write `OUTDIR/comparison.md` with `templates/comparison-template.md`.

- One row per observation. Status: **COVERED** (docs/code describe it), **MISSING** (not found), **CONTRADICTION** (docs/code say something else).
- COVERED and CONTRADICTION rows need a `file:line` citation. MISSING rows state where you searched.
- Put anything you cannot decide under "Unclear". Show contradictions with both citations; do not pick a side.
- Give totals per status.
- Do not change the docs or code. Propose doc changes and wait for the user's approval.

### Check a journey against a release

Input: release notes, or a recording of the new version. Write `OUTDIR/release-check.md` with `templates/release-check-template.md`. Check every journey step and every "must keep working" item: UNCHANGED, CHANGED, REMOVED or UNKNOWN (not covered by the release information). Cite the release evidence per row. Put CHANGED and REMOVED must-keep items first.

### Mails to the recorder

Fill the template in the recorder's language. Show the draft. Do not send it; the user sends it.

- **Recording request** (`templates/recording-request-mail.md`): before there is a recording. Needs the recorder's name, the application, the task, who processes the video and the share folder.
- **Review request** (`templates/review-request-mail.md`): after the analysis or journey. Needs the recorder's name, the task, the open questions (with timestamps) and who will receive the result. When answers come back, update the documents and mark each answered question with its source ("recorder, mail of <date>").
