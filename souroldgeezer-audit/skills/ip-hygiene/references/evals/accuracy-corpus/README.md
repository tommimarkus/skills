# Accuracy Corpus (audit-of-the-audit)

Thirty-two synthetic adversarial cases cover `IP-SRC`, `IP-COPY`, `IP-DB`,
`IP-LIC`, and `IP-MARK`, including ambiguity, every counsel-required stop, and
clean controls. All names and facts are repo-authored fictional material. Each
blind prompt provides distinct material, source/provenance, intended act and
distribution context, plus the ambiguity or counsel-trigger fact relevant to
that scenario. It does not disclose its expected record or criterion code.

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
structure only. The actual result schema uses a per-case `findings` array whose
entries carry criterion code, severity, authority class, and fact status, plus
the lane outcome, counsel outcome, and literal-false clearance disclosure. It
must read only its assigned bundle: any outside read or
expected-outcome exposure is `blocked:contaminated`, with no produced or revised
results. Parent-only evaluation privately scores behavioral accuracy.

After receiving uncontaminated actual records, the parent scores results
deterministically:

```text
python references/scripts/score_ip_hygiene_eval.py --expected references/evals/accuracy-corpus/expected.jsonl --actual /path/to/actual.jsonl --families IP-MARK,IP-COPY,IP-DB
```

Parent-held expected records declare `required_codes`, explicit allowed codes,
per-code classifications, lane outcome, counsel outcome, and any substantiated
designated blocker. The scorer fails for a missing required code, an unsupported
extra code, a clean-control finding, a wrong classification or lane/counsel
outcome, or a legal-clearance overclaim. Structural validation is not model recall:
the child validator proves record shape and case coverage; only the
parent scorer measures behavioral accuracy. The focused contract test also
rejects duplicate, placeholder, or under-specified prompts; it checks fixture
quality, not an evaluator's answer.
