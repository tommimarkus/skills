# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the original internal IP hygiene workflow and references. They do not copy
legal source text, vendor policies, issue text, examples, schemas, tables, or
external docs.

- Source: `souroldgeezer-audit/skills/ip-hygiene/SKILL.md`.
  Handling: local repo-authored workflow; eval prompts exercise the triage
  contract, false-positive rejection, false-negative rejection, configurable
  conventions, focused scope, and stop conditions.
- Source: `souroldgeezer-audit/skills/ip-hygiene/references/{copyright,trademark,licence-assets,drive-by}.md`.
  Handling: local operational rules; eval prompts paraphrase decision
  categories and do not reproduce legal authority text.
- Source: `souroldgeezer-audit/skills/ip-hygiene/references/authority-index.md`.
  Handling: URL-level source notes only; eval prompts do not copy legal source
  language or vendor policy text.
- Source: `souroldgeezer-audit/docs/audit-reference/audit-craft.md` and
  `souroldgeezer-audit/docs/audit-reference/materiality.md`.
  Handling: local bundled references owned by this repo; eval cases exercise
  audit craft and materiality output contracts and do not reproduce rubric prose.
- Source: `souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus/`.
  Handling: repo-authored planted-defect fixtures scoring recall and
  false-positive rate. Thirty-two cases cover each coded criterion family,
  ambiguity, all counsel-required stops, and clean controls. Expected records
  are withheld from blind evaluators and the deterministic scorer checks codes,
  severity, lane/verdict, authority, fact status, counsel, and clearance
  overclaim. Structural completeness is not evidence of model recall. No
  content is copied from a real source.
