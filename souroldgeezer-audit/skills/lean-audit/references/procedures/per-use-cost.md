# Per-Use Cost Lens (LA-PUC-1 / LA-PUC-2 / LA-PUC-3)

Load when running lean-audit against a skill surface. These three codes are
inference — the engine cannot decide them — and MUST be disclosed as such (see
[`../../../../docs/audit-reference/audit-craft.md`](../../../../docs/audit-reference/audit-craft.md)
§2). Cite codes from [`../smell-catalog.md`](../smell-catalog.md); do not
restate catalog prose. Harness subcommands (`resolve_closure`, `measure`,
`baseline`, `diff`) live in
[`../scripts/skill_load_cost.py`](../scripts/skill_load_cost.py) (`snapshot` is
the guard's cost-warn input — see [`../hook-recipe.md`](../hook-recipe.md), not
this advisor run).

## When this lens runs

Gate: the scope must contain at least one entry artifact — a `SKILL.md`, an
`agents/*.md` subagent, or a `commands/**/*.md` file. If no entry
artifact is in scope, this lens is silent — emit nothing.

## Resolve the closure

For each entry artifact in scope, run:

```
skill_load_cost.py resolve_closure <entry>
```

The closure is the transitive set of `.md` files reachable via Load-Map links
from that entry, including out-of-directory references such as
`docs/<kind>-reference/*.md`. The **closure**, not the entry file itself, is
what gets measured and where per-use findings are raised.

When multiple entry artifacts share the same SKILL.md root, merge their
closures — duplicate paths count once.

## Model per-mode load sets

Read the SKILL.md `## Load Map` section and the skill's mode list (e.g. Quick /
Deep, or Build / Extract / Review / Lookup). For each mode, trace which Load-Map
lines are conditional on that mode (explicit "only in Deep", "only for Lookup",
or equivalent guard) versus unconditional (loaded on every invocation).

Output: a table — `mode × file` — marking each closure file as `always`,
`conditional:<mode>`, or `not loaded`. This table is the evidence substrate for
all three PUC checks.

## Find LA-PUC-1/2/3

### LA-PUC-1 — mode loads a file it does not need

Trigger: a closure file is loaded in mode A, but its content is exclusively
relevant to mode B (or the file is detection-loaded regardless of mode when it
is only needed in a subset).

Evidence shape: the `mode × file` table shows the file as `always` or
`conditional:A`, yet every section inside it is labelled for or logically
scoped to mode B.

Fix: add a Load-Map mode-gate (`load only in B`) — the fix is structural-safe
(see [Classify fidelity-safety](#classify-fidelity-safety) below).

Worked example: `api-design` Lookup mode loaded the full extension set that
only Build/Review/Extract use — each extension file carried no Lookup-relevant
content.

### LA-PUC-2 — always-loaded file carries content exclusive to one rarer mode

Trigger: a file is always loaded (or loaded across many modes), but a
substantial block inside it is exclusive to a single, less frequent mode.

Evidence shape: a section heading or block marker inside the file maps to one
mode in the `mode × file` table, while the rest of the file is multi-mode.
Measure the rarer-mode block with `skill_load_cost.py measure` and compare to
the file's total to size the waste.

Fix: split the exclusive block into a separate file loaded only in that mode.
Classification is structural-safe when the split falls on a clean header
boundary; needs-adversarial-review when prose must move under a shared header
(see [Classify fidelity-safety](#classify-fidelity-safety)).

Worked example: `test-quality-audit` always loaded a file containing a large
Deep-mode-only rubric block; splitting it to a Deep-only load removed that
block from Quick-mode context.

### LA-PUC-3 — single-file extension loaded whole when each mode needs only a slice

Trigger: a single-file extension or reference file is loaded as one unit, but
each mode uses only a distinct slice of it.

Evidence shape: the extension file contains clearly demarcated per-mode sections
(e.g., `### Build`, `### Lookup`), yet the Load Map loads the whole file in all
modes. Because a single-file extension loads all-or-nothing, adding a mode gate
saves nothing — the partition is the win.

Fix: partition the file into core (loaded always) and per-mode slices (loaded
conditionally). Mark needs-adversarial-review — cross-references between
sections must be preserved across the split.

Worked example: an `api-design` extension file contained both a Lookup-relevant
smell catalog slice and a Build/Review pattern catalog; partitioning let each
mode load only its slice.

## Classify fidelity-safety

Every recommended move is one of two classes:

**structural-safe** — the move cannot change what a correct executor reads:
codes, section headings, and link pointers are unchanged and all remain
reachable from the entry. Confirming: run `skill_load_cost.py baseline` before
and after, diff the inventory; all codes and sections still present across the
updated closure.

**needs-adversarial-review** — the diff gate (`baseline` → `diff`) sees codes,
section headings, and link pointers, but it does NOT detect prose that silently
moves under a shared heading. Any restructure where prose meaning could be
altered by the split (cross-referencing sentences, prose that depends on
sibling paragraphs, sections renamed to share a header) is
needs-adversarial-review. Apply adversarial review before recommending.

Two additional method rules apply at classification time:

1. **Single-file-extension rule.** A single-file extension loads all-or-nothing
   — mode-gating its load pointer saves zero tokens. Classify such a finding as
   LA-PUC-3 (partition), not LA-PUC-1 (gate), and mark needs-adversarial-review
   because cross-references must be audited across the split.

2. **Escalation-cue rule.** Any recommendation that caps the loaded set (a mode
   gate or a partition that excludes content for some modes) MUST include an
   explicit escalation cue — the prose or pointer that tells the executor how to
   re-load the excluded content when a less common mode is triggered. Omitting
   the escalation cue turns a performance improvement into a silent
   fidelity-floor violation.

## Infer the dial

The dial is the auditor's compression tolerance for this skill — how aggressively
to recommend restructure versus flag-and-defer.

Basis for inference:

- **Plugin / skill family.** Audit skills (`lean-audit`, `devsecops-audit`,
  `test-quality-audit`, `ip-hygiene`) → structural-only dial: recommend only
  structural-safe moves; flag needs-adversarial-review findings but do not
  recommend applying them automatically, because evidence citations must survive
  intact. Design and operations skills (`api-design`, `app-design`, `issue-ops`,
  etc.) → compression-tolerant dial: flag needs-adversarial-review findings
  and note they are candidates for restructure, but never auto-recommend; always
  surface to the skill maintainer.
- **Parallel / subagent use.** If the skill is routinely invoked as a subagent
  or in parallel with siblings, per-use cost compounds; raise the priority of
  structural-safe wins.
- **Mode count and measured cost.** Run `skill_load_cost.py measure` for each
  mode scenario. A mode with low invocation frequency and high exclusive load is
  a primary target for gating; measure the projected delta before recommending.

Disclose the inferred dial in the output and allow the maintainer to override
it.

## Emit

For each LA-PUC finding, emit the following fields:

- **code** — `LA-PUC-1`, `LA-PUC-2`, or `LA-PUC-3`
- **modes** — which modes are affected (over-loaded, splitting target, or
  partition scope)
- **evidence** — the specific file(s) and section(s) from the `mode × file`
  table; cite the Load-Map line and the closure path
- **projected delta** — token reduction estimate from `skill_load_cost.py
  measure` run on the before and after scenario, or a slice-sizing estimate
  when the restructure is not yet applied
- **fidelity-safety** — `structural-safe` or `needs-adversarial-review` with
  the reason
- **consequence** — impact on executor fidelity if the finding is not addressed
  (see [`../../../../docs/audit-reference/audit-craft.md`](../../../../docs/audit-reference/audit-craft.md)
  §3 consequence field)
- **dial priority** — derived from the inferred dial and the projected delta;
  structural-safe wins on high-frequency modes are highest priority
- **recommended move** — the concrete action (add mode gate / split file /
  partition extension), including the required escalation cue if applicable

After emitting findings, capture the fidelity baseline for the executor:

```
skill_load_cost.py baseline --files <closure-files> --code-patterns <patterns>
```

This `baseline` output is the pre-restructure inventory of codes, sections, and
pointers. The executor uses it with `skill_load_cost.py diff` to confirm no
fidelity loss after applying the recommended moves. Emit it as a named block
(`baseline:`) in the finding output so the executor can run the diff gate.
