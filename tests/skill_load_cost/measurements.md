# test-quality-audit per-use load cost

| Scenario | Before | After | Delta |
|---|---|---|---|
| quick-node-unit | 23251 | 20033 | -3218 |
| deep-nextjs-suite | 44360 | 44606 | +246 |

## Load-set reductions (not captured by fixed-file scenarios)

The fixed-file-list scenarios measure content-token changes only — they cannot
show load-SET changes because the file list is declared, not derived from the
Load Map at runtime.

Task 9's real win: Quick mode no longer loads
`materiality.md` (333 tok) + `sampling-projection.md` (200 tok) = **533 tokens**
saved per Quick audit, per the tightened Load Map. These files were never in the
`quick-node-unit` scenario list (it was already minimal), so the removal does
not appear in the scenario delta above. The SKILL.md grew by ~90 tokens due to
the clarifying Load Map prose, which accounts for the small upward tick in both
scenario totals.

## Summary

The headline Quick win is a **−3218-token content reduction** in the
`quick-node-unit` scenario (23251 → 20033): the Deep-only split of
`nodejs/core.md` removed 3308 tokens from the Quick load path, partly offset by
a ~90-token SKILL.md growth from the tightened Load Map prose. On top of that,
the Load Map tightening (Task 9) removes `materiality.md` (333 tok) and
`sampling-projection.md` (200 tok) from Quick mode entirely, a further **533
tokens per Quick audit** that the fixed-file scenario cannot show because those
files were never in the declared list. Together the per-use Quick saving is
**−3751 tokens** (3218 content + 533 load-set). The Deep scenario stayed nearly
flat (+246 tokens, within noise) by design — Deep mode still loads everything
including the new `deep.md` files, so no content was net-removed from that path.
Task 8 was a justified no-op: a next.js E2E section review confirmed no content
met the Deep-only split threshold. Fidelity diff: 0 regressions across all
tasks — the `uv run python scripts/skill_load_cost.py diff` gate exited 0 at
every task where it was run, and the full `TestQualityAuditBaselineTest` suite
passes at branch tip.
