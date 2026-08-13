# Accuracy Corpus (audit-of-the-audit)

Fifty-two synthetic adversarial cases cover `IP-SRC`, `IP-COPY`, `IP-DB`,
`IP-LIC`, and `IP-MARK`, including ambiguity, every counsel-required stop, and
clean controls. Cases `case-043` through `case-052` carry the source-code lane
across its four comment classes — notices and headers, attribution comments,
copied doc-comment prose, and marks in code — plus generated and derived
material and a clean source-file control. The five prospective cases cover every
prospective-decision
outcome; the in-depth cases cover `blocked`, `qualified`, and
`no-blocker-identified`; criterion-level cases cover every code including
referential use, software/interfaces, consumer-practice claims, notice
survival, and generated material. Counsel
records cover `not-triggered`, non-mandatory `recommended`, and mandatory
`required`. All names and
facts are repo-authored fictional material. Each
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
entries carry the bounded public finding basis: criterion/classification,
condition/location, provenance, act, audience, applicability, confidence and
evidence, cause, consequence, recommendation, risk tier, and counsel outcome.
Every lane also records reviewed surface, exclusions, case-grounded evidence,
limits, independence, exact assurance level, its outcome, and literal-false
clearance disclosure; prospective records additionally name decision controls.
These fields preserve the basis of a result instead of treating an outcome
label as clearance. It
must read only its assigned bundle: any outside read or
expected-outcome exposure is `blocked:contaminated`, with no produced or revised
results. Parent-only evaluation privately scores behavioral accuracy.
The bundle manifest exposes `cases.jsonl` and `validate_ip_hygiene_actual.py`
at its root so the evaluator's assigned acceptance command is self-contained.

After receiving uncontaminated actual records, the parent scores results
deterministically:

```text
python references/scripts/score_ip_hygiene_eval.py --cases references/evals/accuracy-corpus/cases.jsonl --expected references/evals/accuracy-corpus/expected.jsonl --actual /path/to/actual.jsonl --families IP-MARK,IP-COPY,IP-DB
```

Parent-held expected records retain the family selector and declare
`required_code_groups`, explicit allowed codes and case-grounding evidence anchors,
per-code classifications, lane outcome, counsel outcome, and any substantiated
designated blocker. Each group requires one supported code; codes within the
same group are accepted alternatives only for the same proposition. When a case
has independently required propositions, `required_proposition_grounding`
binds each exact code group to its own accepted condition/location anchors, so
a source-indicator finding cannot borrow a logo/endorsement condition (or vice
versa). Codes from distinct proposition entries are not interchangeable.

When one code permits both factual and inferential formulations,
`fact_proposition_anchors` names the directly observed content, provenance,
evidence, or explicit conservative repository-policy proposition that may be
labelled `fact`. The scorer fails closed if a mixed code lacks that private
allowlist; fact-only codes remain condition-grounded in their case anchors. It
separately treats propositions that apply legal protection or another legal
category, an exception, likelihood, infringement, or disputed merits as
inference-only even when the record also contains an observed factual anchor.
This preserves factual source and repository-policy findings without letting a
legal-merits conclusion inherit their label. Authority classifications distinguish a directive or other
EU harmonization source from an operative national binding-law proposition. The
scorer rejects unknown or zero-coverage family selectors and fails for a missing required code group, an unsupported
extra code, a clean-control finding, a wrong classification or lane/counsel
outcome, missing distinctive lane or per-finding grounding, swapped proposition
grounding, an expected/assigned case mismatch, or a
legal-clearance overclaim. Malformed or cross-field-incoherent expected records
fail closed. Structural validation is not model recall:
the child validator proves record shape and case coverage; only the
parent scorer measures behavioral accuracy. The focused contract test also
rejects duplicate, placeholder, or under-specified prompts; it checks fixture
quality, not an evaluator's answer.

## Reading a score against the baseline

A raw score is not interpretable on its own. The evaluator is stochastic, so the
same corpus and the same bundled guidance produce different results run to run,
and a bare issue count cannot tell a regression from noise. `baseline.json`
records what that noise actually looks like.

It holds two runs over one pinned bundle — same corpus bytes, same references,
one evaluator each, unsharded — with the corpus SHA-256, date, harness shape and
model recorded beside them. Both runs failed 14 cases, but they were not the
same 14: 11 cases failed in both, 6 in exactly one, and the issue count ranged
21 to 26. Failing-set agreement was 65%.

So, when scoring a change:

- A case in `envelope.stable_failures` that keeps failing is **not** news, and a
  change that fixes one **is**.
- A case in `envelope.variable_failures`, or a fresh single-run failure, is
  within noise. One run cannot convict it; run again before believing it.
- An issue count inside `envelope.issues_range` is unremarkable. Movement well
  outside that range is the signal worth chasing.

Two constraints keep the comparison honest. Change **one** variable per scored
run: altering bundled guidance and the harness shape together produces a delta
that cannot be attributed to either. And compare only against a baseline built
from the same bundled guidance — a baseline recorded before a `SKILL.md` edit
does not describe the skill after it.

Refresh the baseline deliberately, by re-running and committing, whenever
bundled guidance or the corpus changes materially. It is not re-measured by the
suite: unlike the deterministic `tests/skill_load_cost/cost-snapshot.json`, an
evaluator score cannot be re-derived in-process, so a stale baseline is caught
by reading its provenance, not by a gate.
