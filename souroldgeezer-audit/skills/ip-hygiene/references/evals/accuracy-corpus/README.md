# Accuracy Corpus (audit-of-the-audit)

Synthetic planted-defect cases scoring the skill's recall and
false-positive rate (audit-craft §8). Rerun after any rubric, gate,
bucket, or output-contract change: run the skill in-depth over `cases/`,
compare emitted findings to `expected.jsonl` (match on case id + bucket),
and report recall (expected found / expected) and false positives
(unexpected findings). Every file here is repo-authored; nothing is copied
from any third-party source. `cases/c6-clean-control` MUST stay
finding-free — it is the false-positive control.
