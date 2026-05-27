# Software Design Smell Catalog

Use with [../../../docs/software-reference/software-design.md](../../../docs/software-reference/software-design.md). Cite code/evidence/action/layer/source.

| Family | Codes | Signal |
|---|---|---|
| Waste | `SD-W-1..6` | hooks, pass-through |
| Boundary | `SD-B-1..6` | drift, leakage |
| Coupling | `SD-C-1..6` | cycles, shared core |
| Semantics | `SD-S-1..5` | split terms, leakage |
| Evolution | `SD-E-1..4` | shotgun change, flags |
| Tradeoff | `SD-Q-1..3` | tradeoff, optimization |
| Socio-technical | `SD-T-1..3` | ownership, cognition |

## Core Code Cards

### `SD-W-1` - Speculative abstraction

**Signal:** Imagined variation.
**Evidence layer:** `static`; `history`.
**False-positive guard:** Real boundary/compatibility/variation.
**Smallest action:** Inline, delete, or defer.
**Default severity:** Warn; block framework mandate.

### `SD-W-2` - Pass-through layer

**Signal:** Meaningless forwarding.
**Evidence layer:** `static`.
**False-positive guard:** Compat/logging/retry/transaction/translation.
**Smallest action:** Remove or own.
**Default severity:** Warn; block hidden owner.

### `SD-B-1` - Responsibility drift

**Signal:** Unrelated decisions share owner.
**Evidence layer:** `static`; `history`.
**False-positive guard:** Sequencing.
**Smallest action:** Move one decision.
**Default severity:** Warn; block adapter policy.

### `SD-B-3` - Internals leakage

**Signal:** Callers depend on internals.
**Evidence layer:** `static` or `graph`.
**False-positive guard:** Owned extension or stable DTO.
**Smallest action:** Expose owned API.
**Default severity:** Block new leakage; warn contained legacy.

### `SD-C-1` - Dependency cycle

**Signal:** Dependency both ways.
**Evidence layer:** `graph`; `static` for imports.
**False-positive guard:** Runtime callback.
**Smallest action:** Move policy, invert adapter, split contract.
**Default severity:** Block new cycles; warn reducing legacy.

### `SD-C-3` - Shared-core gravity

**Signal:** Shared core absorbs volatile policy.
**Evidence layer:** `static`; `history`.
**False-positive guard:** Stable utility.
**Smallest action:** Move policy home.
**Default severity:** Warn; block cross-context owner.

### `SD-S-1` - Vocabulary split

**Signal:** Conflicting term/synonym.
**Evidence layer:** `static`; `human`.
**False-positive guard:** Context with translation.
**Smallest action:** Rename, qualify, or translate.
**Default severity:** Warn; block invariant/contract blur.

### `SD-S-4` - External model collapse

**Signal:** External shape is internal state.
**Evidence layer:** `static`.
**False-positive guard:** Stable CRUD meaning.
**Smallest action:** Add edge translation.
**Default severity:** Warn; block churn/invariant mismatch.

### `SD-E-1` - Shotgun change

**Signal:** One rule, scattered edits.
**Evidence layer:** `history`; `static`.
**False-positive guard:** Migration with exit.
**Smallest action:** Add rule owner.
**Default severity:** Warn; block multiplied sites.

### `SD-E-3` - Flag pile-up

**Signal:** Flags lack owner/expiry/return.
**Evidence layer:** `static`; `history`.
**False-positive guard:** Short rollout with owner/trigger.
**Smallest action:** Add removal/collapse.
**Default severity:** Warn; block permanent flags.

### `SD-Q-1` - Unstated quality tradeoff

**Signal:** Quality claim lacks proof.
**Evidence layer:** `static`; `runtime`/`human`/sibling.
**False-positive guard:** No quality claim.
**Smallest action:** State force/tradeoff/validation/delegation.
**Default severity:** Info/warn; block unsupported design.

### `SD-T-1` - Ownership mismatch

**Signal:** Boundary crosses owner.
**Evidence layer:** `human`; `static`/`history`.
**False-positive guard:** Shared owner or small project.
**Smallest action:** Align owner or state contract.
**Default severity:** Warn known; info uncertain.

Default blocks: new dependency cycles/inversions, new internals leakage, hidden mutable state, invariant leakage, mandatory speculative framework, specialist-scope absorption. Default warns: rest unless advisory.
