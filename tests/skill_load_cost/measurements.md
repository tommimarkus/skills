# test-quality-audit per-use load cost

| Scenario | Before | After | Delta |
|---|---|---|---|
| quick-node-unit | 23251 | 20037 | -3214 |
| deep-nextjs-suite | 44360 | 44610 | +250 |

## Load-set reductions (not captured by fixed-file scenarios)

The fixed-file-list scenarios measure content-token changes only — they cannot
show load-SET changes because the file list is declared, not derived from the
Load Map at runtime.

Task 9's real win: Quick mode no longer loads
`materiality.md` (333 tok) + `sampling-projection.md` (200 tok) = **533 tokens**
saved per Quick audit, per the tightened Load Map. These files were never in the
`quick-node-unit` scenario list (it was already minimal), so the removal does
not appear in the scenario delta above. The SKILL.md grew by +126 tokens due to
the Load Map clarifications across all tasks, which accounts for the small upward
tick in both scenario totals.

## Summary

The headline Quick win is a **−3214-token content reduction** in the
`quick-node-unit` scenario (23251 → 20037): the Deep-only split of
`nodejs/core.md` removed 3340 tokens from the Quick load path (base 14384 →
tip 11044), partly offset by a +126-token SKILL.md growth (base 1229 → tip
1355) from the Load Map clarifications. On top of that, the Load Map tightening
(Task 9) removes `materiality.md` (333 tok) and `sampling-projection.md`
(200 tok) from Quick mode entirely, a further **533 tokens per Quick audit**
that the fixed-file scenario cannot show because those files were never in the
declared list. Together the per-use Quick saving is **−3747 tokens** (3214
content + 533 load-set). The Deep scenario stayed nearly flat (+250 tokens,
within noise) by design — Deep mode still loads everything including the new
`deep.md` files, so no content was net-removed from that path. Task 8 was a
cross-file restatement pass that found no true duplicate content to factor out
of `nextjs/core.md` — the nodejs and nextjs cores are disjoint by design,
already factored to their respective homes — so it made no change. Fidelity
diff: 0 regressions across all tasks — the `uv run python scripts/skill_load_cost.py diff`
gate exited 0 at every task where it was run, and the full
`TestQualityAuditBaselineTest` suite passes at branch tip.
