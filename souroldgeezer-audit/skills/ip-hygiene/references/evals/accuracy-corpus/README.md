# Accuracy Corpus (audit-of-the-audit)

Synthetic planted-defect cases scoring the skill's recall and
false-positive rate (audit-craft §8). Rerun after any rubric, gate,
bucket, or output-contract change: run the skill in-depth over `cases/`,
compare emitted findings to `expected.jsonl` (match on case id + bucket),
and report recall (expected found / expected) and false positives
(unexpected findings). For the bounded triage-gate check, run each case
change-scoped and compare its `triage_gate` value. Every file here is
repo-authored; nothing is copied from any third-party source.
`cases/c6-clean-control` MUST stay finding-free — it is the false-positive
control. `c7-unclear-redistribution` preserves ambiguity without inventing a
blocker; `c8-symbol-convention` proves an ordinary convention finding remains
nonblocking. A `stopped:` output line whose question names a case's planted
issue counts as a recall hit for that case; its bucket matches when the stop
reason concerns that bucket's subject matter.
