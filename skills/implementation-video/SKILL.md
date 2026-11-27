---
name: implementation-video
description: Make a short narrated implementation video (proof of work) that shows one or more finished tickets working in the running app and how the work was validated, for an audience that already knows the product. Reuses the scripts, theme and rules of the demo-video skill (offline voice, Playwright recording, film-style subtitles, cursor and spotlights). Use this when someone asks for an implementation video, proof of work, a video of a change, a ticket demo or a sprint review clip.
metadata:
  version: "1.0.1"
---

# Making an implementation video

An implementation video shows that one or more tickets are built and work. Its audience knows the product, so it skips the domain explanation and spends the time on the change and the evidence. Aim for about 2 to 2.5 minutes.

This skill uses the `demo-video` skill in the same plugin. Read its `SKILL.md` (`../demo-video/SKILL.md`) and follow every section marked **(shared)**: what the video rests on, visual cues, subtitles and transitions, slides and theme, setup, how to build it, reuse, scripts, where it goes and afterwards. Run the scripts from `../demo-video/scripts/` and copy `../demo-video/examples/sample/` as the starting point. Subtitles follow the `subtitles` skill (`../subtitles/SKILL.md`), which `assemble.py` uses. If the `demo-video` or `subtitles` skill is not installed, stop and tell the person to install it.

## Inputs

Ask for these one at a time if they are missing:

1. **The ticket keys**, and access to the ticket text (requirements and acceptance criteria). If you cannot read the tickets, ask the person to paste the text.
2. **The running app** (URL, and a login if needed) on a version that contains the change.
3. **The change itself**: a branch, pull request or commit range, so you can read the diff.
4. **The validation evidence**: which tests ran and their results, and what was checked by hand.

## Structure

1. **Title slide:** the ticket keys and one short sentence about the change. Nothing else: no list of screens or requirements, because the next slides cover them.
2. **Ticket slide:** say that these are tickets from the team's tracker, and give their scope briefly: the requirements and the acceptance criteria, taken from the tickets. A decision the team made that is not in a ticket is labelled as a team decision.
3. **Per changed screen:** a short screen-name card (2 to 3 s) with the screen name and its place in the flow, then the screen itself. Show each requirement working, with the visual cues from the demo-video skill.
4. **Technical changes slide:** briefly, what changed under the hood. Before you write it, ask the person which technical changes to cover. Propose a short list from the diff to choose from (for example API contract changes such as new parameters, values and error codes, the main design choice, and shared code that was added), and use only what they pick. Keep it to a few entries.
5. **Validation slide:** how the work was validated, with concrete evidence from the actual runs: which test suites ran and how many tests passed, what was checked by hand or in the browser and against which environment, and the known limits (for example "no automated integration tests yet"). State only results that were really observed. Never invent a test result.
6. **End slide**, short.

Leave out the agenda, the domain opening slides and the roadmap timeline of a demo video.

## Naming

Name the files after the tickets, for example `local/demo/proj-123-filter-sort.mp4`, in a folder that git ignores.

## Afterwards

Open the video for the person. Report in a few lines: the duration, which requirements were shown, which could not be shown and why, and any difference between the tickets and what the app does.
