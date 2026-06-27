# undecided/

Staging area for skills not yet assigned to a published plugin. Contents here
are **NOT** registered in `.claude-plugin/marketplace.json` and **NOT**
production-ready; do not reference them from other skills.

Layout mirrors a plugin's skill dir:

- `agents/<name>.md` — matching Claude Code subagent for a parked skill
- `<skill-name>/` — same shape as a plugin's `skills/<skill>/`

When a skill graduates, move it (and its `agents/<name>.md`) into the target
plugin per CLAUDE.md → "Directory layout". This directory is intentionally
near-empty when nothing is parked.
