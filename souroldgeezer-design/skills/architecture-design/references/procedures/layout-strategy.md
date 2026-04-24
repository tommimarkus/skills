# Layout strategy — banded grid for OEF XML views

Procedure for producing `<view>` node placements that are readable, diff-stable, and round-trippable through ArchiMate® conformant tools. Invoked by Build (always) and Extract (when an existing diagram has no prior view placements for the elements being added). Review uses the same rules — restated as checks — to flag `AD-L*` smells.

The reference is [../../../../docs/architecture-reference/architecture.md](../../../../docs/architecture-reference/architecture.md); the structural rules this procedure operationalises live in §6.4a *Layout strategy*. Layout smell codes are defined in [../smell-catalog.md](../smell-catalog.md) (`AD-L1..AD-L8`).

**Determinism is the point.** Given the same element set, relationship set, diagram kind, and layer scope, the procedure must produce the same `x`, `y`, `w`, `h` values every run. Re-extracts don't churn coordinates; git diffs on `.oef.xml` stay narrow; architect hand-edits survive because identifiers are preserved (reference §6.6) and layout is recomputed only for elements without an architect-chosen position.

## Why deterministic banded grid

Three design choices drive everything else in this procedure:

1. **Banded grid over free placement.** Every element lands in a fixed cell derived from `(layer, aspect)`. Free placement under a loose prompt is how real-world diagrams end up with overlaps, cut-off labels, and crossing soup.
2. **Coordinates in the XML, not a layout hint.** An alternative is to emit no coordinates and let a tool's auto-layout engine (e.g. Archi's ELK-based plugin) place nodes at render time. That produces empty-coord views that other tools render at `(0, 0)`, loses git-diff readability, and breaks tools that don't ship an auto-layout engine. Explicit coordinates are the portable choice.
3. **Nest instead of drawing Composition / Aggregation / Realization edges where the parent–child relation is visually natural.** Matches Archi's Automatic Relationship Management convention (the implementation tool most architects use) and is the single biggest crossing-reduction lever per the ArchiMate Cookbook (Hosiaisluoma §2.3.2, §2.3.5).

## Inputs

1. The element set for the view (already assigned to their ArchiMate layer via `xsi:type`, per reference §3–§4).
2. The relationship set (already validated against Appendix B, per reference §5).
3. The diagram kind (one of the six supported in reference §9).
4. Any prior view at the canonical path, parsed for architect-chosen placements (reference §6.4; project-assimilation rule).

## The banded grid

All coordinates are pixels, origin top-left, positive down — per OEF XML convention (reference §6.4). All values are integer multiples of the grid.

**Grid.** 10 px. Every `x`, `y`, `w`, `h` is a multiple of 10. Matches Archi's default snap-to-grid granularity; architects who open the file see pixel-perfect alignment without re-snapping.

**Canvas columns (aspects — left to right).** Five fixed columns, 240 px wide, 20 px gutters:

| Column | `x` start | `x` end | Used by |
|---|---:|---:|---|
| Motivation | 40 | 280 | Stakeholder, Driver, Assessment, Goal, Outcome, Principle, Requirement, Constraint, Value, Meaning |
| Active structure | 300 | 540 | Actor, Role, Component, Node, Device, System Software, Interface, Collaboration |
| Behaviour | 560 | 800 | Process, Function, Interaction, Service, Event |
| Passive structure | 820 | 1060 | Business Object, Data Object, Artifact, Contract, Product |
| Implementation & Migration | 1080 | 1320 | Work Package, Deliverable, Implementation Event, Plateau, Gap |

**Canvas rows (layers — top to bottom).** Five fixed rows, 200 px tall, 40 px gutters; matches the canonical ArchiMate Framework arrangement (Strategy top, Physical bottom) and the Cookbook's Layered View convention (top-down by layer):

| Row | `y` start | `y` end | Used by |
|---|---:|---:|---|
| Strategy | 40 | 240 | Resource, Capability, Value Stream, Course of Action |
| Business | 280 | 480 | Business-layer elements |
| Application | 520 | 720 | Application-layer elements |
| Technology | 760 | 960 | Technology-layer elements |
| Physical | 1000 | 1200 | Physical-layer elements |

Motivation and Implementation & Migration columns span all five rows — they are not per-layer. Their elements are placed by row = the layer their Realisation target belongs to (reference §2.4, Core-vs-extension rule).

A cell is one `(column, row)` intersection. A diagram with only Application Cooperation (reference §9.2) uses one cell (Application × Active / Behaviour / Passive) and the others are empty.

## Default element sizes

Every element placed by this procedure carries explicit `w` and `h`. Sizes are minimums — when a `<name>` is long enough that the default would truncate, enlarge `w` in 20-px steps until it fits (assume 7 px per character at the default font; architects can override after import).

| Element class | Default `w` | Default `h` | Rationale |
|---|---:|---:|---|
| Structure (Component, Node, Device, System Software, Actor, Role, Interface, Artifact) | 140 | 60 | Fits 18–20 characters; the commonest case |
| Behaviour (Process, Function, Interaction, Service, Event) | 160 | 60 | Verb-noun labels run longer ("Place Order", "Process Payment") |
| Motivation (Goal, Requirement, Constraint, Principle, Driver, Assessment, Stakeholder, Outcome, Value, Meaning) | 180 | 60 | Longer labels plus the layer's icon |
| Strategy (Capability, Value Stream, Resource, Course of Action) | 180 | 60 | Same as Motivation |
| Passive (Business Object, Data Object, Contract, Product) | 140 | 60 | Short noun labels |
| Implementation & Migration (Work Package, Deliverable, Implementation Event, Plateau, Gap) | 160 | 60 | Plateau labels are often environment names ("Production") |
| Grouping (container for logical cluster) | computed | computed | `w = max(child.w) + 40`, `h = sum(child.h) + 20 × (n+1)`, min `200 × 120` |
| Junction | 14 | 14 | ArchiMate convention |

**Minimum size enforcement.** `w ≥ 120`, `h ≥ 55`. Below either, the label truncates in Archi's default figure — triggers `AD-L3` in Review.

## Placement algorithm

Run once per view.

### Step 1 — Preserve architect positions

If a prior view exists at the canonical path and contains a `<node>` for this element (matched by `elementRef`), reuse its `x`, `y`, `w`, `h` verbatim. Do not recompute. The architect's hand-edit is authoritative.

Record the set of *new* elements (present in this run, absent from the prior view) — only these get algorithmic placement.

### Step 2 — Assign each new element to a cell

Compute `cell(e) = (column(e), row(e))`:

- `column(e)` from the element's aspect per reference §2.3:
  - Motivation / Strategy layers → Motivation column
  - Active structure → Active structure column
  - Behaviour → Behaviour column
  - Passive structure → Passive structure column
  - Implementation & Migration → Implementation & Migration column
- `row(e)` from the element's layer:
  - Strategy layer → Strategy row
  - Business layer → Business row
  - Application layer → Application row
  - Technology layer → Technology row
  - Physical layer → Physical row
  - Motivation / Implementation & Migration elements → row of the element they Realise (or the row of their Realisation target); if none, default to Application row

### Step 3 — Order elements within each cell

Sort by:

1. In-degree + out-degree descending (hub elements up).
2. Identifier ascending (stable tiebreaker).

Record the ordered list `cell_elements[c, r]`.

### Step 4 — One pass of barycentric reordering (crossing minimisation)

For each adjacent pair of non-empty columns `(c, c+1)` — left to right — reorder elements in column `c+1` by the barycentre of their connected neighbours in column `c`:

- For each element `e` in column `c+1`, compute `bary(e) = mean(index(n) for n in neighbours(e) where n in column c)`.
- Re-sort `cell_elements[c+1, *]` by `bary(e)` ascending (elements with no cross-column neighbour keep their Step 3 order).

One pass is enough — this is the coarse version of ELK's `LAYER_SWEEP`. A full sweep is out of scope; the determinism requirement forbids iterating until convergence.

### Step 5 — Nest children into parents

For every Composition, Aggregation, or Realization relationship `(parent, child)` where **both endpoints land in the same cell** (same column, same row):

- Place `child` as a nested `<node>` inside `parent`'s placement. Child `x = parent.x + 20`, `y = parent.y + 40 + Σ prior_children.h + 20 × prior_count`. Child `w ≤ parent.w − 40`, `h` unchanged.
- Mark the relationship edge as implicit: add `<properties>` with `<property propertyDefinitionRef="propid-archi-arm"><value xml:lang="en">hide</value></property>` to the relationship, and **do not** emit a `<connection>` for it in this view. Archi's ARM will render the nesting as-is; tools without ARM still read the relationship in the model.
- Grow the parent's `w`/`h` if needed to contain children: `parent.w = max(parent.w, max_child.x + max_child.w + 20 − parent.x)`, `parent.h = max(parent.h, last_child.y + last_child.h + 20 − parent.y)`.

Rules:

- Only nest when both endpoints are in the same cell — cross-cell nesting crosses layer or aspect bands and violates reference §2.1 / §2.3.
- A child may be nested in at most one parent per view. If a child has two valid parents, nest in the one whose relationship is Composition; fall back to the first parent in identifier order.
- Nesting depth is capped at 2 (parent → child → grandchild). Deeper chains render correctly but exceed the view budget quickly — flag as `AD-L4` risk.

### Step 6 — Compute concrete coordinates

For each non-nested element in `cell_elements[c, r]` in order:

- `x = column(c).x_start + (column.width − element.w) / 2` rounded to the nearest 10. This centres the element in its column.
- `y = row(r).y_start + 20 + Σ prior_elements.h + 20 × prior_count`. This stacks elements vertically inside the row, 20-px gutter between.

If the stack overflows the row (`y + h > row.y_end`), flag `AD-L4` (view-density over budget) and bleed into the next row by 40 px — do not overlap the next row's own elements.

### Step 7 — Route edges

Every `<connection>` that wasn't hidden by Step 5:

- `routing` attribute omitted (OEF has no such attribute); rendering tools decide. Emit bend points as `<bendpoint x="..." y="..."/>` child elements, all coordinates on the 10-px grid.
- Orthogonal routing only: from source midpoint, one horizontal-then-vertical (or vertical-then-horizontal) path to target midpoint. Choose the path that introduces fewer crossings with existing edges; tiebreak by path-length.
- Parallel edges in the same lane space 20 px apart.
- Connection source/target connect to the side of the element that faces the other endpoint (left, right, top, bottom midpoint). Do not connect to corners.

## View budget

| Limit | Threshold | Smell |
|---|---:|---|
| Elements per view | 20 | `AD-L4` warn |
| Relationships per view | 30 | `AD-L4` warn |
| Nesting depth | 2 | `AD-L4` info |
| Elements per cell | 4 | split the view or promote a cluster to Grouping |
| Edge crossings per view | `node_count / 4` | `AD-L5` info |

Over budget → prefer one of: split into two views (by feature or by aspect), promote a cluster to a Grouping element (reference §4.8; logical cluster, never a layer container), or move peripheral elements to a separate Motivation / Migration view.

## Colour and stroke

Do not emit `<style>` children on `<node>` placements. Leaving style undeclared lets each rendering tool apply its layer-idiomatic colours (yellow Business / turquoise Application / green Technology in Archi's default theme). Declaring custom colours on elements overrides the tool's theme without signal.

Exception: a Grouping used for a logical cluster may carry a fill for visual distinction. Use a single neutral fill for every Grouping in the same view.

## Worked placement

Suppose an Application Cooperation view (reference §9.2) with three Application Components and one Application Service:

- `C1` = Orders API (ApplicationComponent, out-degree 2)
- `C2` = Payments API (ApplicationComponent, out-degree 1)
- `C3` = Orders Core (ApplicationComponent, in-degree 2; Composition parent of C1 and C2)
- `S1` = Place Order (ApplicationService; realised by C1)

Cells: `C1, C2, C3 → (Active structure, Application)`, `S1 → (Behaviour, Application)`.

Step 5 nests `C1` and `C2` inside `C3` (Composition, same cell).

Step 6 on the non-nested elements:

- `C3` at `x = 300 + (240 − 200) / 2 = 320`, `y = 520 + 20 = 540`, `w = 200` (grown to contain children), `h = 200` (grown).
- `S1` at `x = 560 + (240 − 160) / 2 = 600`, `y = 520 + 20 = 540`, `w = 160`, `h = 60`.

Nested children inside `C3`:

- `C1` at `x = 320 + 20 = 340`, `y = 540 + 40 = 580`, `w = 140`, `h = 60`.
- `C2` at `x = 340`, `y = 580 + 60 + 20 = 660`, `w = 140`, `h = 60`.

Edges:

- `C1 → S1` (Realization): orthogonal, out the right midpoint of C1 (`x=480, y=610`), right to `x=600`, up to `y=570` (right midpoint of S1 is `y=570`). Bend point `(600, 610)`.
- Composition edges `C3 → C1` and `C3 → C2`: hidden by ARM marker (Step 5).

Result: one view, four elements, one visible connection, zero crossings.

## What this procedure does not solve

- **Views with > 30 relationships** produce crossings even after Step 4 — the one-pass barycentric sweep cannot match a full iterative solver. Beyond the view budget, split the view; that is the correct answer.
- **Non-tree nesting.** If two parents both want to contain the same child (e.g., Orders API is Composed by *both* Orders Core and Checkout Service), nesting picks one and the other Composition is drawn as an explicit edge. Pick the parent with higher out-degree in the current view; tiebreak by identifier.
- **Hand-drawn aesthetic.** The grid is deliberately regular; architects who want organic placement should hand-edit after import. The procedure preserves hand edits on re-run (Step 1).
- **Diagram kinds outside reference §9.** Product Map, Information Structure, Physical views are expressible in OEF but outside the skill's supported set in v1 — the procedure is not tuned for them.

## Sources

Paraphrased guidance; no prose, figures, or samples copied.

- The Open Group ArchiMate® 3.2 Specification (C226, March 2023) — the ArchiMate Framework (horizontal layers, Motivation left of Core, Implementation & Migration right of Core) and Appendix B well-formedness are the structural anchors for cell assignment and the nest-in-same-cell rule. <https://publications.opengroup.org/c226>
- Eero Hosiaisluoma, *ArchiMate® Cookbook — Patterns & Examples* — the Layered View convention (top-down by layer), the nesting-over-explicit-edge preference for Composition / Aggregation, and the "compact and readable" principle that drives the view budget. <http://www.hosiaisluoma.fi/ArchiMate-Cookbook.pdf>
- Phillip Beauvoir, *Archi User Guide* — Container Elements and Automatic Relationship Management as the implementation-tool idiom that the nest + hide rule emits for. <https://www.archimatetool.com/downloads/archi/Archi%20User%20Guide.pdf>
- Eclipse Layout Kernel, *Layered algorithm* — Sugiyama-style layered placement, orthogonal edge routing, and `LAYER_SWEEP` crossing minimisation inform the one-pass barycentric step and the default routing style. <https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html>
