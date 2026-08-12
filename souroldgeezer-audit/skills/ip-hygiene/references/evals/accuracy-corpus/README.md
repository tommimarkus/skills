# Accuracy Corpus (audit-of-the-audit)

Thirty-two synthetic adversarial cases cover `IP-SRC`, `IP-COPY`, `IP-DB`,
`IP-LIC`, and `IP-MARK`, including ambiguity, every counsel-required stop, and
clean controls. All names and facts are repo-authored fictional material.

## Blind evaluation

Give an evaluator `cases.jsonl`, not `expected.jsonl`. It writes one JSONL
record per case using this actual result schema: `case`, `codes` (array),
`severity`, `triage_gate`, `in_depth_verdict`, `authority_class`,
`fact_status`, `counsel_outcome`, and optional `legal_clearance` (which must
never be true). A no-finding control uses an empty `codes` array. Do not copy
the expected codes into the prompt.
Expected records use `required_codes` and `forbidden_codes` alongside the
required outcome fields; they remain scorer input, not evaluator guidance.

Score results deterministically:

```text
python references/scripts/score_ip_hygiene_eval.py --expected references/evals/accuracy-corpus/expected.jsonl --actual /path/to/actual.jsonl --families IP-MARK,IP-COPY,IP-DB
```

The scorer fails for a missed designated blocker, a forbidden clean-control
finding, a wrong lane gate or in-depth verdict, or a legal-clearance overclaim.
It also checks authority, fact/inference status, severity, and counsel outcome.
Structural validation is not model recall: the corpus schema only proves that
the test inventory is well formed; blind evaluation measures the model result.
