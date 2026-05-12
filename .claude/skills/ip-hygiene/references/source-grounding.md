# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the internal IP hygiene workflow and references. They do not copy legal source
text, vendor policies, issue text, examples, schemas, tables, or external docs.

- Source: `.claude/skills/ip-hygiene/SKILL.md`.
  Handling: local repo-authored workflow; eval prompts exercise the triage
  contract, false-positive rejection, false-negative rejection, and stop
  conditions.
- Source: `.claude/skills/ip-hygiene/references/{copyright,trademark,licence-assets,drive-by}.md`.
  Handling: local operational rules; eval prompts paraphrase decision categories
  and do not reproduce legal authority text.
- Source: `.claude/skills/ip-hygiene/references/authority-index.md`.
  Handling: URL-level source notes only; eval prompts do not copy legal source
  language or vendor policy text.
