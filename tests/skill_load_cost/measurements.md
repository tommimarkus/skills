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
