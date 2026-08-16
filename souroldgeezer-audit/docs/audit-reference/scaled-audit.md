# Scaled Audit (shared procedure)

How a Deep/in-depth audit keeps its evidence intact when the subject is large.
Earlier rung than sampling-projection.md: enumerate durably first, sample only
when even that is not enough.

## §1 Rungs

Apply in order, and state which rung was used:

a. **Inline**, with the §2 durability floor.
b. **Delegated** slices per §3, when the host offers delegation.
c. **Sampled** per sampling-projection.md, when the subject still exceeds capacity.

A rung is not a preference. Dropping to (c) while (a) or (b) was still available
understates coverage that was actually reachable.

## §2 Durability floor (always)

Record each per-item finding in its bounded field shape AS IT GOES; do not carry
raw sources, fixtures, or captured output forward to the rollup. The rollup needs
the records, not the material they were derived from.

This generalizes the rule already applied to suite health — bounded distribution
evidence "without retaining failure bodies or captured output" — to the per-item
lane, which is the lane whose evidence scales with subject size. Use the skill's
own per-item field set (e.g. test-quality-audit
`references/procedures/per-test-output-fields.md`), or audit-craft.md §3's 5 C's
where a skill defines none. Do not invent a second shape.

Unbounded accumulation does not fail loudly. It degrades the evidence the §4
population lanes later depend on, and the output looks unchanged.

## §3 Delegation protocol

**Preconditions**, all four: Deep/in-depth mode; the host offers delegation; this
run is not itself a delegated worker; the subject exceeds comfortable inline
enumeration. Any one unmet → rung (a). Host delegation is a conditional capability
in the same way MCP probes are (audit-craft.md §5) — probe and disclose, never
assume.

**Parent, before dispatch.** Establish the population, run the risk survey, build
the tier map (materiality.md), and compute the slice plan. Never delegate these:
every slice depends on them.

**Slice unit and size.** Use the §4 unit for the skill. Size each slice so the
WORKER's own context holds it comfortably — a compacted worker reproduces this
same defect one level down, where the parent cannot see it.

**Worker brief.** Give each worker: the skill, its Load Map slice for that
stack/rubric/scope, the parent's tier map, the explicit item list, and the §2
return shape. A worker must not re-derive the population, re-run the risk survey,
sample, or emit a gate, verdict, rollup, or footer — those are parent-only (§4).

**Worker return.** The §2 bounded records only; never raw content, file dumps, or
transcripts. Returning material instead of records relocates the parent's context
problem rather than solving it.

**Parent, after collection.** Reconcile coverage FIRST: every dispatched slice
returned, and their union equals the declared population. A missing, truncated, or
non-conforming slice is an evidence gap — disclose it (§5), never drop it
silently, and never relabel it as a sample. Only then compute the population
lanes, worklist, verdict, and footer.

**Degradation.** No delegation available → rung (a), then (c) if still needed,
disclosed as such. Never reduce scope silently because delegation was unavailable.

## §4 Divisible and parent-only lanes

A lane is **divisible** when each item's finding is determined by that item plus
the loaded criteria alone. A lane is **parent-only** when its output is a
statistic, comparison, ranking, or selection OVER THE POPULATION. Dividing a
parent-only lane produces confident statistics computed from a partial view.

| Skill | Divisible — slice unit | Parent-only |
|---|---|---|
| `test-quality-audit` | per-test findings (step 4) — module or directory | risk pass and tier map (3a); suite-management pass (3b); rollup (step 5) |
| `devsecops-audit` | per-file / per-config smell application — directory or component | threat model; supply-chain and release posture; rollup |
| `ip-hygiene` | per-surface criteria application — one publication surface | surface enumeration and exclusions; risk survey; in-depth verdict |
| `lean-audit` | **not divisible by file** — a clone pair is kept when *either* path is in scope, so slicing by file makes pairs vanish with no error; only scope-complete units | duplication and clone detection; per-use closure; rollup |

## §5 Disclosure

The footer (audit-craft.md §5) records: the rung used; delegation availability and
slice count when rung (b) applied; the coverage reconciliation result; and, when
evidence was compacted, truncated, or otherwise degraded before rollup, that the
population lanes are limited. This is an evidence-limits entry, not a new footer
slot.

A divided run must never present as undivided, and a degraded run must never
present as intact.
