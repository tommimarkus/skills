# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local issue-ops workflow and provider-extension contract. They do not copy
issue text, tracker payloads, review comments, branch names from real work, or
external provider documentation.

- Source: `../SKILL.md`.
  Handling: local public-skill workflow; eval prompts are original synthetic
  scenarios for trigger precision, queue limits, provider selection, and
  issue-to-PR handoff.
- Source: `extensions/github.md` and `extensions/README.md`.
  Handling: local provider extension mechanics; eval cases mention provider
  state and lifecycle markers without copying live tracker content.
