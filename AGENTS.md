# AGENTS.md

Instructions for AI coding agents and contributors who work in this repository.

## Repository purpose

This repository holds reusable agent skills. Each skill lives in `skills/<name>/` with a `SKILL.md`, a `README.md` and any scripts or templates it needs. The repository is public.

## No confidential or personal information

Never add the following to a skill, a template, a script, an example, a test file, a commit message or any other file in this repository:

- **Customer information**: names of customers, customer data, orders, contracts or anything that identifies a customer.
- **Company information**: names of employers, clients or vendors, internal system names, application or screen codes, internal URLs, host names, network paths, project names, team names, organisation structures, business rules or figures from a real organisation.
- **Personal information**: names, e-mail addresses, phone numbers, user names, account IDs, addresses or other data that identifies a person.
- **Secrets**: passwords, tokens, API keys, certificates or connection strings.
- **Recordings and their output**: videos, transcripts, screenshots, frames or analyses made from real work.

Use neutral placeholders instead, for example `<application>`, `<task>`, `<name>`, `<vendor>`, `<org>/<repo>` or `ABC123F` for a screen code.

Write examples so that they are clearly invented and generic. Do not copy an example from a real project and only change a few details.

Before you commit, check the diff for these items. If you find one, remove it. If it is already in the git history, tell the repository owner, because it must also be removed from the history.

## Conventions

- Write all documentation in English.
- Keep `SKILL.md` focused on the instructions for the agent. Put human-oriented setup and usage in the skill's `README.md`.
- Scripts must work on Windows, macOS and Linux. Prefer Python over shell scripts.
- When you change a skill, raise `version` in both `.claude-plugin/plugin.json` and `apm.yml`.
- Keep the plugin and package descriptions generic. Do not describe a single skill in them.
