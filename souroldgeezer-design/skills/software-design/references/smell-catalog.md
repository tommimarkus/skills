# Software Design Smell Catalog

Use with [../../../docs/software-reference/software-design.md](../../../docs/software-reference/software-design.md). Cite code, evidence, action, layer, source.

| Family | Codes | Signal |
|---|---|---|
| Waste | `SD-W-1..6` | speculative hooks, pass-through, ceremony |
| Boundary | `SD-B-1..6` | drift, type folders, leakage, hidden state |
| Coupling | `SD-C-1..6` | cycles, inversion, shared-core gravity, hotspots |
| Semantics | `SD-S-1..5` | vocabulary split, leakage, missing translation |
| Evolution | `SD-E-1..4` | shotgun change, unsafe jump, flag pile-up |
| Tradeoff | `SD-Q-1..3` | unstated tradeoff, unmeasured optimization, specialist-scope absorption |
| Socio-technical | `SD-T-1..3` | ownership mismatch, cognitive cliff, orphaned shared code |

## Core Code Cards

### `SD-W-1` - Speculative abstraction

**Signal:** Imagined variation hook.
**Evidence layer:** `static`; `history` for bypass churn.
**False-positive guard:** Real boundary, compatibility, or measured variation.
**Smallest action:** Inline, delete, or defer.
**Default severity:** Warn; block mandatory framework.

### `SD-W-2` - Pass-through layer

**Signal:** Wrapper forwards without owned meaning.
**Evidence layer:** `static`.
**False-positive guard:** Compatibility, logging, retry, transaction, translation.
**Smallest action:** Remove or own policy.
**Default severity:** Warn; block hidden ownership.

### `SD-B-1` - Responsibility drift

**Signal:** One module owns unrelated decisions.
**Evidence layer:** `static`; `history` for joined churn.
**False-positive guard:** Pure sequencing.
**Smallest action:** Move one decision.
**Default severity:** Warn; block policy in adapter.

### `SD-B-3` - Internals leakage

**Signal:** Callers depend on private shape, type, or state.
**Evidence layer:** `static` or `graph`.
**False-positive guard:** Owned extension point or stable DTO contract.
**Smallest action:** Expose meaning through owned API.
**Default severity:** Block new exported leakage; warn contained legacy.

### `SD-C-1` - Dependency cycle

**Signal:** Dependency points both ways.
**Evidence layer:** `graph`; `static` for imports.
**False-positive guard:** Runtime callback only.
**Smallest action:** Move policy, invert adapter, or split contract.
**Default severity:** Block new cycles; warn cycle-reducing legacy.

### `SD-C-3` - Shared-core gravity

**Signal:** Shared core attracts volatile policy.
**Evidence layer:** `static`; `history` for churn.
**False-positive guard:** Stable mechanical utility.
**Smallest action:** Move policy home.
**Default severity:** Warn; block cross-context ownership.

### `SD-S-1` - Vocabulary split

**Signal:** Conflicting term or synonym.
**Evidence layer:** `static`; `human` for meaning.
**False-positive guard:** Bounded context with translation.
**Smallest action:** Rename, qualify, or translate.
**Default severity:** Warn; block invariant/contract ambiguity.

### `SD-S-4` - External model collapse

**Signal:** External shape becomes internal state.
**Evidence layer:** `static`.
**False-positive guard:** Stable CRUD with one meaning.
**Smallest action:** Add edge translation.
**Default severity:** Warn; block churn or invariant mismatch.

### `SD-E-1` - Shotgun change

**Signal:** One rule needs scattered edits.
**Evidence layer:** `history`; `static` for patch proof.
**False-positive guard:** Owned migration with exit.
**Smallest action:** Add one rule owner.
**Default severity:** Warn; block multiplied edit sites.

### `SD-E-3` - Flag pile-up

**Signal:** Flags lack owner, expiry, return path.
**Evidence layer:** `static`; `history` for persistence.
**False-positive guard:** Short rollout flag with owner and trigger.
**Smallest action:** Add removal or collapse path.
**Default severity:** Warn; block permanent flags.

### `SD-Q-1` - Unstated quality tradeoff

**Signal:** Quality claim lacks tradeoff or evidence.
**Evidence layer:** `static`; `runtime`/`human`/sibling for proof.
**False-positive guard:** No quality claim.
**Smallest action:** State force, tradeoff, validation, delegation.
**Default severity:** Info/warn; block unsupported broad design.

### `SD-T-1` - Ownership mismatch

**Signal:** Boundary crosses decision owner.
**Evidence layer:** `human`; `static`/`history` for coordination.
**False-positive guard:** Shared ownership or small project.
**Smallest action:** Align owner or state contract.
**Default severity:** Warn when known; info when uncertain.

Default blocks: new dependency cycles/inversions, new internals leakage, hidden mutable state, invariant leakage, mandatory speculative framework, and specialist-scope absorption that misroutes work. Default warns: everything else unless advisory.
