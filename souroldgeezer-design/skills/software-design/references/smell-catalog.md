# Software Design Smell Catalog

Use with [../../../docs/software-reference/software-design.md](../../../docs/software-reference/software-design.md).
Findings cite code, evidence, smallest action, verification layer, and
reference section. Raise severity for new/load-bearing code; lower it when
evidence is partial or a local rule explains the tradeoff.

| Family | Codes | Signal |
|---|---|---|
| Waste | `SD-W-1..6` | speculative interfaces/frameworks/hooks, pass-through layers, repeated models, ceremony over current change |
| Boundary | `SD-B-1..6` | responsibility drift, folder-type boundaries, internals leakage, hidden mutable state, misplaced policy, adapter-owned workflow |
| Coupling | `SD-C-1..6` | cycles, boundary inversion, shared-core gravity, fan-out hotspots, service locators, event/config backchannels |
| Semantics | `SD-S-1..5` | vocabulary splits/homonyms, aggregate leakage, unowned shared kernels, missing external-to-internal translation |
| Evolution | `SD-E-1..4` | shotgun change, unsafe refactor jumps, flag pile-up, permanent strangle paths |
| Tradeoff | `SD-Q-1..3` | unstated quality tradeoff, unmeasured local optimization, specialist concern absorbed instead of delegated |
| Socio-technical | `SD-T-1..3` | ownership mismatch, cognitive load cliff, orphaned shared code |

## Core Code Cards

Each card is a review prompt, not an automatic verdict. Cite the code only when
the evidence fits the signal and the false-positive guard does not apply.

### `SD-W-1` - Speculative abstraction

**Signal:** Interface, base class, framework hook, plugin point, or extension
slot exists for imagined variation rather than current use, confirmed churn, or
external isolation.
**Evidence layer:** `static`; raise with `history` when repeated changes avoid
the abstraction.
**False-positive guard:** Do not flag an abstraction that protects a current
external boundary, public compatibility contract, or measured variation point.
**Smallest action:** Inline, delete, or defer the abstraction; keep a note about
the condition that would justify reintroducing it.
**Default severity:** Warn; block when new code mandates the abstraction across
unrelated callers.

### `SD-W-2` - Pass-through layer

**Signal:** Wrapper, facade, repository, mediator, or service method forwards
calls without owning vocabulary, policy, lifetime, error shape, or dependency
translation.
**Evidence layer:** `static`.
**False-positive guard:** Do not flag a thin layer that owns compatibility,
logging, retry, transaction, or external-vocabulary translation as an explicit
boundary.
**Smallest action:** Remove the layer or move the owned policy/translation into
it so the boundary pays for itself.
**Default severity:** Warn; block when the layer hides the real owner or forces
new callers through pointless ceremony.

### `SD-B-1` - Responsibility drift

**Signal:** A module changes for multiple unrelated reasons such as parsing,
policy, persistence, rendering, orchestration, and platform setup.
**Evidence layer:** `static`; raise with `history` when unrelated changes churn
through the same file.
**False-positive guard:** Do not flag cohesive orchestration that only sequences
owned collaborators and does not absorb their decisions.
**Smallest action:** Name the owned responsibility, move one drifting decision
to its owner, and keep the calling boundary narrow.
**Default severity:** Warn; block when new code puts policy inside a mechanism
that should remain an adapter.

### `SD-B-3` - Internals leakage

**Signal:** Callers depend on private structure, generated shapes, storage
entities, framework types, or module-local state that should be hidden behind
the owning boundary.
**Evidence layer:** `static` or `graph`.
**False-positive guard:** Public extension points and stable DTO contracts are
not leakage when they are intentionally owned and documented.
**Smallest action:** Introduce a translator, query, command, or public method
that exposes the needed meaning instead of the internal structure.
**Default severity:** Block for new public/friend/exported leakage; warn for
legacy leakage with a contained migration path.

### `SD-C-1` - Dependency cycle

**Signal:** Modules, packages, projects, or layers depend on each other in both
directions, directly or through a shared helper.
**Evidence layer:** `graph`; `static` is enough when imports/references show the
cycle.
**False-positive guard:** Runtime callbacks or event subscriptions are not
cycles unless compile-time or ownership dependencies point both ways.
**Smallest action:** Move the shared policy inward, invert the adapter
dependency, or split the shared type into owned contracts.
**Default severity:** Block for new cycles; warn for legacy cycles only when
the change reduces rather than extends the cycle.

### `SD-C-3` - Shared-core gravity

**Signal:** A shared module attracts domain policy, cross-context models,
configuration, helpers, or state because it is convenient rather than stable
and boring.
**Evidence layer:** `static`; raise with `history` when many features churn
inside the shared core.
**False-positive guard:** Stable mechanical utilities with clear ownership and
no domain vocabulary are acceptable shared code.
**Smallest action:** Move volatile policy back to the owning context and leave
only stable mechanics or explicit translation contracts shared.
**Default severity:** Warn; block when new shared code creates cross-context
domain ownership.

### `SD-S-1` - Vocabulary split

**Signal:** The same term means different things across a boundary, or multiple
terms describe the same concept without an explicit translation rule.
**Evidence layer:** `static`; `human` may be needed for domain meaning.
**False-positive guard:** Different terms across truly separate bounded
contexts are acceptable when translation is explicit.
**Smallest action:** Rename inside one boundary, qualify terms, or add a
translator that makes the semantic difference visible.
**Default severity:** Warn; block when ambiguity can corrupt invariants or
external contracts.

### `SD-S-4` - External model collapse

**Signal:** Vendor DTOs, generated API types, database entities, transport
payloads, or framework request models become the internal domain/workflow model.
**Evidence layer:** `static`.
**False-positive guard:** Simple CRUD or stable mechanical data transfer can use
one shape when there is no separate internal meaning or volatility.
**Smallest action:** Add an edge translator and keep internal code using the
owned vocabulary.
**Default severity:** Warn; block when known external churn or internal
invariants already differ.

### `SD-E-1` - Shotgun change

**Signal:** One behavior change requires scattered edits across many modules
because the decision is duplicated or no boundary owns it.
**Evidence layer:** `history` when available; `static` when the duplication and
required edits are evident in the patch.
**False-positive guard:** Cross-cutting migrations with an explicit owner and
exit condition are not this smell by themselves.
**Smallest action:** Put the rule behind one owner, then update callers through
that owner in a behavior-preserving step.
**Default severity:** Warn; block when new code knowingly multiplies required
edit sites for the same rule.

### `SD-E-3` - Flag pile-up

**Signal:** Feature flags, mode flags, compatibility switches, or migration
branches accumulate without owners, expiry, or a path back to one behavior.
**Evidence layer:** `static`; raise with `history` when flags persist across
releases.
**False-positive guard:** Short-lived rollout flags with owner, removal trigger,
and validation path are acceptable.
**Smallest action:** Add an owner and removal condition, collapse expired paths,
or split genuinely separate modes behind explicit strategies.
**Default severity:** Warn; block when a new permanent flag multiplies core
workflow semantics.

### `SD-Q-1` - Unstated quality tradeoff

**Signal:** A design claims better performance, reliability, operability,
security, cost, or modifiability without naming the sacrificed quality or the
evidence layer that supports the claim.
**Evidence layer:** `static` for the claim; `runtime` or `human` may be needed
for proof, and specialist evidence should be delegated to the owning sibling
skill.
**False-positive guard:** Small local decisions do not need ceremony when no
quality claim is being made.
**Smallest action:** State the force, local tactic, tradeoff, validation layer,
and sibling delegation if specialist evidence is needed.
**Default severity:** Info or warn; block when an unsupported quality claim
drives a broad or irreversible design.

### `SD-T-1` - Ownership mismatch

**Signal:** Code boundaries require one team or maintainer to change another
owner's policy, vocabulary, release unit, or operational decision.
**Evidence layer:** `human` for team ownership; `static` or `history` can show
the coordination pressure.
**False-positive guard:** Shared ownership or small single-maintainer projects
can tolerate boundaries that would be wrong in larger organizations.
**Smallest action:** Align the boundary with the owner of the decision, or make
the cross-owner contract explicit.
**Default severity:** Warn when ownership is known; info when ownership must be
confirmed.

Default blocks: new dependency cycles/inversions, new internals leakage,
hidden mutable state, invariant leakage, mandatory speculative framework, and
specialist-scope absorption that would misroute the work. Default warns:
everything else unless evidence is advisory only.
