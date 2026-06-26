# Source Grounding

This internal skill's behavioral evals are synthetic, repo-authored cases
derived from the local issue lifecycle overlay and public operations skills.
They do not copy issue text, review comments, tracker payloads, command logs, or
external documentation.

- Source: `.claude/skills/github-issue-lifecycle/SKILL.md`.
  Handling: local repo-authored overlay; eval prompts are original synthetic
  cases for trigger precision, repo-local gates, direct-main safety, and PR
  handoff.
- Source: `souroldgeezer-ops/skills/issue-ops/SKILL.md` and
  `souroldgeezer-ops/skills/issue-ops/extensions/github.md`.
  Handling: local public-skill workflow and provider mechanics; eval cases
  mention the handoff shape without reproducing tracker data.
