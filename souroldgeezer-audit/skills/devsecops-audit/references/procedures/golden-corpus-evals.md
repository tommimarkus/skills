# Golden-Corpus Evals

**When this runs:** after changing `devsecops-audit` rubric wording, smell
catalog, output contract, extension files, or examples. Empirical accuracy
guardrail realizing [audit-craft.md §8](../../../../docs/audit-reference/audit-craft.md); complements
`scripts/skill-architecture-report.sh .` (marketplace source-repo tooling; structure, not accuracy).

## Inputs
- Seed corpus: [../golden-corpus/devsecops-audit-cases.jsonl](../golden-corpus/devsecops-audit-cases.jsonl)
- Current `SKILL.md`, rubric, smell catalog, affected extensions.

## Stable eval prompt (quick-mode cases)
Start a fresh audit context; provide only `target`, `config_snippet`, and any
`supporting_context`. Withhold all `expected_*` and `ground_truth` fields.
```text
Use devsecops-audit in quick mode on the supplied artifact only. Report finding
codes, positive-signal codes, severity, risk tier, and recommended action. Do
not restate rubric prose.
```

## Stable eval prompt (deep-mode cases)
For `mode: deep` cases, also report the presence-vs-efficacy verdict
(`enforcing` | `partial` | `decorative`) and, for `known-cve` cases, whether the
defect was surfaced as reachable/exploitable.

## Scoring (against the corpus entry)
- **Recall (objective):** every `expected_codes` code appears; for `ground_truth`
  `seeded-secret`/`known-cve` cases the planted defect is surfaced. A miss is a
  false negative (regression unless the rubric intentionally retired the code).
- **False-positive:** no `forbidden_codes` code appears; any extra code must be
  justified by the snippet.
- **Severity / verdict / risk-tier:** match `expected_severity`,
  `expected_verdict`, `expected_risk_tier` when present.

## Output
Record in the change discussion:
```markdown
### DevSecOps golden-corpus eval
- Cases run: <N>
- Recall (expected_codes): <passed>/<N>
- Objective ground-truth surfaced: <passed>/<seeded+kev count>
- False positives: <ids/codes or none>
- Severity/verdict/risk-tier: <passed>/<N>
```

## Updating the corpus
Add cases one at a time; keep snippets minimal and original; keep ≥1 positive per
family; false-positive-prone families also keep a clean negative (to pin false
positives); detection-recall families may be positive-only; use `forbidden_codes`
to pin known false positives.
