# Software Design Smell Catalog

Use with [software-design.md](../../../docs/software-reference/software-design.md). This index maps core smell codes to families. Load matching records from [smell-cards.jsonl](smell-cards.jsonl) for signal, layer, guard, action, and severity.

| Family | Codes | Signal |
|---|---|---|
| Waste | `SD-W-1`, `SD-W-2` | speculation, pass-through |
| Boundary | `SD-B-1`, `SD-B-2`, `SD-B-3`, `SD-B-4` | drift, state owner, leakage, adapter policy |
| Coupling | `SD-C-1`, `SD-C-2`, `SD-C-3`, `SD-C-4`, `SD-C-5` | cycle, inversion, shared core, hidden state, version divergence |
| Semantics | `SD-S-1`, `SD-S-2`, `SD-S-4` | vocabulary, duplicate concepts, external model collapse |
| Evolution | `SD-E-1`, `SD-E-2`, `SD-E-3`, `SD-E-4`, `SD-E-5` | shotgun, migration exit, flag lifecycle, deprecation lifecycle, dependency currency |
| Tradeoff | `SD-Q-1`, `SD-Q-2`, `SD-Q-3` | unsupported claim/NFR, unmeasured tactic, unallocated NFR |
| Socio-technical | `SD-T-1` | owner/cognition mismatch |

## Core Code Cards

### `SD-W-1` - Speculative abstraction
### `SD-W-2` - Pass-through layer
### `SD-B-1` - Responsibility drift
### `SD-B-2` - State owner blur
### `SD-B-3` - Internals leakage
### `SD-B-4` - Adapter owns policy
### `SD-C-1` - Dependency cycle
### `SD-C-2` - Policy-to-adapter dependency
### `SD-C-3` - Shared-core gravity
### `SD-C-4` - Hidden mutable state
### `SD-C-5` - Version or implementation divergence
### `SD-S-1` - Vocabulary split
### `SD-S-2` - Duplicate concept drift
### `SD-S-4` - External model collapse
### `SD-E-1` - Shotgun change
### `SD-E-2` - Migration without exit
### `SD-E-3` - Flag pile-up
### `SD-E-4` - Deprecation without lifecycle
### `SD-E-5` - Stale-dependency or big-bang-upgrade debt
### `SD-Q-1` - Unstated quality tradeoff
### `SD-Q-2` - Unmeasured quality tactic
### `SD-Q-3` - Unallocated NFR
### `SD-T-1` - Ownership mismatch

Default blocks: new dependency cycles/inversions, internals/invariant leakage, hidden mutable state, mandatory speculative framework, specialist-scope absorption, unbounded divergence of a shared concern.
