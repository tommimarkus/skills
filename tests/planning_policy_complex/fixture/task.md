# Catalog export evaluation

Implement four public functions in this synthetic repository. Only `catalog.py`,
`summary.py`, `render.py`, and `export.py` may change. The coordinator owns the
plan and tests; the oracle outside this repository is immutable.

`catalog.normalize(records)` returns a fresh list of fresh dictionaries with
`id`, `label`, and `amount`. Inputs have those three keys. IDs are strings:
strip outer whitespace and use Unicode case folding. Labels are strings:
collapse whitespace to single spaces. Amounts must be nonnegative integers;
booleans are invalid. Preserve record order and never mutate caller data.

Validate records in order. Within each record reject an empty normalized ID
with `ValueError('empty id')`, then invalid amounts with
`ValueError('invalid amount')`, then a duplicate normalized ID with
`ValueError('duplicate id')`. Duplicate IDs are rejected, never merged.

`summary.totals(records)` uses the normalized records and returns a dictionary
mapping each ID's first character to its total amount, inserted in sorted key
order. `render.rows(records)` uses the same normalization and returns lines
`id|label|amount` sorted by normalized ID. Input labels contain no `|`.
`export.build(records)` returns exactly `{'totals': ..., 'rows': ...}` using
those two public functions. Empty input returns empty results.

The coordinator must prepare cohesive assignments from these requirements;
there is no supplied plan or suggested leaf count. Preserve shared interface,
validation, and nonmutation decisions in each relevant generated handoff.
Workers receive only their generated packet and named files. Use scoped
acceptance, the current planning ledger, and normal integration/cleanup.
The evaluator separately reports whether execution exercised a dependency fork
and join; grouping everything into one task cannot establish that coverage.
