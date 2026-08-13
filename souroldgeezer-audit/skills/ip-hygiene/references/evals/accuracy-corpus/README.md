# Accuracy Corpus (audit-of-the-audit)

Thirty-two synthetic adversarial cases cover `IP-SRC`, `IP-COPY`, `IP-DB`,
`IP-LIC`, and `IP-MARK`, including ambiguity, every counsel-required stop, and
clean controls. All names and facts are repo-authored fictional material. Each
blind prompt provides distinct material, source/provenance, intended act and
distribution context, the explicitly requested lane, plus the ambiguity or
counsel-trigger fact relevant to that scenario. Blind records use opaque
`case-NNN` identifiers and omit scorer-only criterion-family labels. They do not
disclose an expected record, criterion code, authority classification, or
outcome.

## Blind evaluation

Build the allowlisted evaluator bundle and give the evaluator only that bundle:

```text
python references/scripts/build_ip_hygiene_blind_bundle.py --repo-root <repo-root> --output <empty-bundle-dir>
```

The bundle contains raw cases, the public workflow, directly required local
references, evaluator instructions, and the actual-record validator. It omits
expected outcomes, the parent scorer, source grounding, repository tests, Git
metadata/history, prior diagnoses, and evaluator caches. The evaluator writes
one JSONL record per case in the validator's closed schema, and validates
structure and exact assigned-case coverage only. The required invocation is
`validate_ip_hygiene_actual.py --cases cases.jsonl --actual <actual.jsonl>`;
positional or coverage-free validation is rejected. The actual result schema
uses a per-case `findings` array whose
entries carry criterion code, severity, authority class, and fact status, plus
the lane outcome, counsel outcome, and literal-false clearance disclosure. It
must read only its assigned bundle: any outside read or
expected-outcome exposure is `blocked:contaminated`, with no produced or revised
results. Parent-only evaluation privately scores behavioral accuracy.
The bundle manifest exposes `cases.jsonl` and `validate_ip_hygiene_actual.py`
at its root so the evaluator's assigned acceptance command is self-contained.

After receiving uncontaminated actual records, the parent scores results
deterministically:

```text
python references/scripts/score_ip_hygiene_eval.py --expected references/evals/accuracy-corpus/expected.jsonl --actual /path/to/actual.jsonl --families IP-MARK,IP-COPY,IP-DB
```

Parent-held expected records retain the family selector and declare
`required_codes`, explicit allowed codes,
per-code classifications, lane outcome, counsel outcome, and any substantiated
designated blocker. The scorer fails for a missing required code, an unsupported
extra code, a clean-control finding, a wrong classification or lane/counsel
outcome, an unexpected case ID, or a legal-clearance overclaim. Structural validation is not model recall:
the child validator proves record shape and case coverage; only the
parent scorer measures behavioral accuracy. The focused contract test also
rejects duplicate, placeholder, or under-specified prompts; it checks fixture
quality, not an evaluator's answer.
