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
structure only. It must read only its assigned bundle: any outside read or
expected-outcome exposure is `blocked:contaminated`, with no produced or revised
results. Parent-only evaluation privately scores behavioral accuracy.

After receiving uncontaminated actual records, the parent scores results
deterministically:

```text
python references/scripts/score_ip_hygiene_eval.py --expected references/evals/accuracy-corpus/expected.jsonl --actual /path/to/actual.jsonl --families IP-MARK,IP-COPY,IP-DB
```

The scorer fails for a missed designated blocker, a forbidden clean-control
finding, a wrong lane gate or in-depth verdict, or a legal-clearance overclaim.
It also checks authority, fact/inference status, severity, and counsel outcome.
Structural validation is not behavioral scoring: the child validator only
proves record shape; the parent scorer measures the model result. The focused
contract test also rejects duplicate, placeholder, or under-specified prompts;
it checks fixture quality, not an evaluator's answer.
