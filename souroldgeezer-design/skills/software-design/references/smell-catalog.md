# Software Design Smell Catalog

Use with [software-design.md](../../../docs/software-reference/software-design.md). This index maps core smell codes to families. Load matching records from [smell-cards.jsonl](smell-cards.jsonl) for signal, layer, guard, action, and severity.

| Family | Codes | Signal |
|---|---|---|
| Waste | `SD-W-1`, `SD-W-2` | speculation, pass-through |
| Boundary | `SD-B-1`, `SD-B-2`, `SD-B-3`, `SD-B-4` | drift, state owner, leakage, adapter policy |
| Coupling | `SD-C-1`, `SD-C-2`, `SD-C-3`, `SD-C-4`, `SD-C-5`, `SD-C-6` | cycle, inversion, shared core, hidden state, version divergence, unowned concurrency |
| Semantics | `SD-S-1`, `SD-S-2`, `SD-S-4`, `SD-S-5` | vocabulary, duplicate concepts, external model collapse, error-contract collapse |
| Evolution | `SD-E-1`, `SD-E-2`, `SD-E-3`, `SD-E-4`, `SD-E-5` | shotgun, migration exit, flag lifecycle, deprecation lifecycle, dependency currency |
| Tradeoff | `SD-Q-1`, `SD-Q-2`, `SD-Q-3`, `SD-Q-4` | unsupported claim/NFR, unmeasured tactic, unallocated NFR, stacked failure handling |
| Socio-technical | `SD-T-1` | owner/cognition mismatch |

Core `SD-S-3` is intentionally retired and stays reserved: do not emit it or map findings to it. The extension code `shell.SD-S-3` is unrelated and remains valid.

Default blocks: new dependency cycles/inversions, internals/invariant leakage, duplicate-model invariant mismatch, hidden mutable state, unowned detached concurrency, swallowed failures on state-changing paths, stacked retries on non-idempotent operations, mandatory speculative framework, unsafe boundary fragmentation, silent extension of load-bearing legacy, specialist-scope absorption, unbounded divergence of a shared concern.
