# implementation-video

Makes a short narrated video (about 2 to 2.5 minutes) that proves one or more finished tickets work. The audience already knows the product, so the video skips the domain explanation and shows the change and the evidence.

This skill reuses the scripts, theme and rules of [demo-video](../demo-video/README.md). Install both; the plugin and the APM package do that for you.

## What the video contains

1. **Title slide:** the ticket keys and one sentence about the change.
2. **Ticket slide:** the requirements and acceptance criteria from the tickets. Team decisions that are not in a ticket are labelled as such.
3. **Per changed screen:** a short screen-name card, then the screen with each requirement shown working.
4. **Technical changes:** a few points from the diff. Claude proposes a list and you choose.
5. **Validation:** which tests ran and their results, what was checked by hand, and the known limits. Only results that were really observed.
6. **End slide.**

## What Claude needs

- The ticket keys and the ticket text (requirements and acceptance criteria).
- The running app on a version that contains the change.
- The change: a branch, pull request or commit range.
- The validation evidence: test results and manual checks.

## Setup

The same as [demo-video](../demo-video/README.md#one-time-setup). If you have set up demo-video, you are ready.

## Usage

Example prompts for Claude Code:

- "Make an implementation video for PROJ-123, the app runs at `http://localhost:3000`."
- "Make an implementation video for the tickets in this pull request."

The video is named after the tickets and goes to `local/demo/`. Make sure that folder is ignored by git.
