# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local test-quality workflow, bundled quality references, and existing
golden-corpus maintenance process. They do not copy external prompt text, code,
examples, fixtures, schemas, diagrams, logos, or screenshots.

- Source: `../../../docs/quality-reference/unit-testing.md`,
  `../../../docs/quality-reference/integration-testing.md`,
  `../../../docs/quality-reference/e2e-testing.md`, and
  `../../../references/test-quality-audit-*`.
  Handling: local bundled references owned by this repo; eval prompts are
  original synthetic scenarios for rubric selection, scope, and evidence limits.
- Source: `references/golden-corpus/index.md` and
  `references/golden-corpus/test-quality-audit-cases.jsonl`.
  Handling: local maintenance evidence; behavioral evals are separate synthetic
  cases and do not copy corpus prompts or expected outputs.
