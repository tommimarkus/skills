# Code Clone Adjudication (LA-CODE-DUP-*)

Load when the code lens nominates `LA-CODE-DUP-*` candidates (codes in
[`../smell-catalog.md`](../smell-catalog.md)). The lens only nominates; this
procedure decides whether each candidate is reported or cleared. It is auditor
inference (audit-craft §2): name the compared copies and the evidence.

## Rules

1. **Parameters are not contracts.** In a clone, messages, limits, names and constants are
   parameters: two copies that differ only there are one routine with different
   arguments, so the candidate stands.
2. **Clear narrowly.** Clear a candidate only for genuinely different contracts
   (the copies must change for different reasons) or for idioms too small to
   extract without costing more than the copy. Record the reason for each clear.
3. **Compare against the canonical sibling.** Before claiming no divergence or
   naming a canonical target, compare the copies with any canonical sibling they
   cite (a comment, import, or docstring naming the original) and make that
   sibling the target. If a copy has drifted from the canonical sibling, report
   the drift as condition evidence on the finding and hand the correctness
   defect to `software-design`; this lens does not judge which behaviour is right.
4. **One criterion.** Apply one criterion to every candidate in the run, so two
   near-identical pairs never receive opposite verdicts.

## Output

For each candidate give the verdict (report or clear), the copies compared, the
canonical target, and any pair-versus-canonical drift with its hand-off. Semantic
DRY ownership stays with `software-design`.
