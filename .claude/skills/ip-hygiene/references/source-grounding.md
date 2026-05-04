# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the internal IP hygiene workflow and reference. They do not copy legal source
text, vendor policies, issue text, examples, schemas, tables, or external docs.

- Source: `.claude/skills/ip-hygiene/SKILL.md`.
  Handling: local repo-authored workflow; eval prompts exercise the triage
  contract, false-positive rejection, false-negative rejection, and stop
  conditions.
- Source: `.claude/skills/ip-hygiene/references/ip-hygiene-reference.md`.
  Handling: local reference material; eval prompts paraphrase local decision
  categories and do not reproduce legal authority text.
