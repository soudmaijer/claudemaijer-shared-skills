# claudemaijer-shared-skills

Shared agent skills for Claude Code and other agent tools.

| Skill | Purpose |
|---|---|
| [demo-video](skills/demo-video/README.md) | Makes a narrated demo video of a running web app, with slides, subtitles, a cursor and spotlights. Runs fully offline. |
| [implementation-video](skills/implementation-video/README.md) | Makes a short proof-of-work video that shows finished tickets working and how they were validated. Uses the demo-video scripts. |
| [video-process-extraction](skills/video-process-extraction/README.md) | Extracts the process, workflow and requirements from a screen recording. On request it also writes an English user journey for a vendor, compares the result with docs, code or release notes, or drafts mails to the recorder. |

## Installation

### Claude Code plugin (recommended)

In Claude Code:

```
/plugin install claudemaijer-shared-skills --marketplace soudmaijer/claudemaijer-shared-skills
```

Or in two steps:

```
/plugin marketplace add soudmaijer/claudemaijer-shared-skills
/plugin install claudemaijer-shared-skills@claudemaijer-shared-skills
```

The skills are then available as `/claudemaijer-shared-skills:<skill>`, for example `/claudemaijer-shared-skills:video-process-extraction`. Updates arrive through `/plugin marketplace update`.

### APM (Agent Package Manager)

```bash
apm install soudmaijer/claudemaijer-shared-skills
```

APM deploys the skills to the agent tools you target (for example Claude Code or GitHub Copilot).

### Manual copy

Copy or link a skill folder to `~/.claude/skills/` (all projects) or to `<project>/.claude/skills/` (one project).

macOS / Linux:

```bash
ln -s "$PWD/skills/video-process-extraction" ~/.claude/skills/video-process-extraction
```

Windows (PowerShell):

```powershell
Copy-Item -Recurse .\skills\video-process-extraction "$env:USERPROFILE\.claude\skills\"
```

## After installation

Some skills need a one-time setup, for example Python packages. See the README of each skill.

## Repository layout

| Path | Purpose |
|---|---|
| `skills/<name>/` | One folder per skill, with `SKILL.md` and a README |
| `.claude-plugin/plugin.json` | Claude Code plugin manifest |
| `.claude-plugin/marketplace.json` | Claude Code marketplace that lists this plugin |
| `apm.yml` | APM package manifest |
| `CODEOWNERS` | Owners of the repository |
| `AGENTS.md` | Rules for agents and contributors, including: no customer, company or personal information |
| `LICENSE` | MIT licence |

When you change a skill, raise `version` in both `plugin.json` and `apm.yml`. Users stay on the old version until it changes.

## Contributing

Read [AGENTS.md](AGENTS.md) before you add or change a skill. Never add customer, company or personal information.

## Licence

MIT. The skills are provided as is, without warranty or liability. See [LICENSE](LICENSE).
