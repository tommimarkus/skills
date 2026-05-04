# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local pr-ops workflow and provider-extension contract. They do not copy pull
request text, review comments, check logs, tracker payloads, or external
provider documentation.

- Source: `../SKILL.md`.
  Handling: local public-skill workflow; eval prompts are original synthetic
  scenarios for trigger precision, full-cycle monitoring, review-only mode,
  feedback remediation, and merge safety.
- Source: `extensions/github.md` and `extensions/README.md`.
  Handling: local provider extension mechanics; eval cases mention PR state and
  checks without copying live provider content.
