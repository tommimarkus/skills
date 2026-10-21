# IP Hygiene Eval Maintenance

Parent-facing procedure for maintaining this skill's evals and verifying edits
to the skill or its references; the blind evaluator does not load it.

## Eval Changes

When changing trigger, workflow, gates, source, or eval behavior, inspect
`references/evals/`, its accuracy corpus, and
[source-grounding.md](../source-grounding.md). Keep evals synthetic or
originally paraphrased. Build a blind evaluator bundle, then give the evaluator
only that bundle:

`${CLAUDE_SKILL_DIR}/references/scripts/build_ip_hygiene_blind_bundle.py --repo-root <repo-root> --output <empty-bundle-dir>`

In Codex, replace `${CLAUDE_SKILL_DIR}` with the absolute `<skill-dir>` reported
for this loaded `SKILL.md`. The evaluator reads only its assigned bundle and
must structurally validate its actual records with:

`${CLAUDE_SKILL_DIR}/references/scripts/validate_ip_hygiene_actual.py --cases <bundle-dir>/cases.jsonl --actual <actual.jsonl>`

In Codex, replace `${CLAUDE_SKILL_DIR}` with the absolute `<skill-dir>` reported
for this loaded `SKILL.md`. An outside read or expected-outcome exposure is
`blocked:contaminated`, with no results produced or revised. The parent alone
privately scores behavior after receiving actual records:

`${CLAUDE_SKILL_DIR}/references/scripts/score_ip_hygiene_eval.py --cases ${CLAUDE_SKILL_DIR}/references/evals/accuracy-corpus/cases.jsonl --expected ${CLAUDE_SKILL_DIR}/references/evals/accuracy-corpus/expected.jsonl --actual <actual.jsonl> --families <comma-separated-families>`

In Codex, replace `${CLAUDE_SKILL_DIR}` with the absolute `<skill-dir>` reported
for this loaded `SKILL.md`. Structural corpus checks do not establish model
recall; this command compares the separately produced blind results.

## Edit Verification

After editing this skill or references in the marketplace source repo, run its
focused tests and `scripts/skill-architecture-report.sh .` from the clean task
worktree. When editing `authority-index.md`, spot-check affected primary-source
links and report verification limits.
