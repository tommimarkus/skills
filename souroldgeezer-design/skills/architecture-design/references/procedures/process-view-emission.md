# Process-view emission contract

Rules for emitting the §9.7 Business Process Cooperation view + process-rooted
§9.3 Service Realization views from a Business Layer element set. Single source
of truth — invoked by Build mode step 3 and Extract mode step 3.

The reference is [../../../../docs/architecture-reference/architecture.md](../../../../docs/architecture-reference/architecture.md). This procedure cites §9.3 (Service Realization), §9.7 (Business Process Cooperation), §10 self-check items for `AD-B-11` / `AD-B-12` / `AD-B-13` / `AD-B-14`, and §6.4b (suppression property definitions).

## When this procedure runs

- **Build mode step 3** — when diagram kind is §9.7 or §9.3 *and* pre-flight Q5 process scope is `all-processes-in-feature` or `multi-feature` (not `single-process`). The procedure receives the architect-authored Business Layer element set as input.
- **Extract mode step 3** — when [`lifting-rules-process.md`](lifting-rules-process.md) emitted any Business Process / Event / Interaction element. The procedure receives the lifted element set as input.

The Skill tool that loaded `SKILL.md` does not auto-inject nested files — `Read` this file explicitly before invoking its rules.

## Inputs

- The set of Business Layer elements (Business Process, Business Event, Business Interaction) and their relationships (`xsi:type="Composition"`, `xsi:type="Triggering"`, `xsi:type="Flow"`) — either just-lifted (Extract) or just-authored (Build).
- Application Layer elements that realise Business Processes (Application Service, Application Component) when present — for §9.3 view contents.
- Technology Layer elements hosting the Application Components when present — for §9.3 view contents.
- Architect-authored Business Actor Assignments and Business Object Access edges if present — preserved verbatim in the §9.7 view.
- Any pre-existing `<view>` blocks at `docs/architecture/<feature>.oef.xml` — preserved per Extract step 5 (merge, not overwrite).

## Output

A complete set of `<view>` blocks under `<views>/<diagrams>` in the canonical file, conforming to the rules in §2.

### 1. View identifiers and naming

- **§9.7 cooperation view** — identifier `id-view-bpc-<feature-slug>`, `<name xml:lang="en">Business Process Cooperation — <Feature title></name>`. One per feature.
- **§9.3 service-realization view, single process** — identifier `id-view-sr-<process-slug>`, `<name xml:lang="en">Service Realization — <Process name></name>`.
- **§9.3 service-realization view, shared story** — identifier `id-view-sr-shared-<first-process-slug>-<last-process-slug>`, `<name xml:lang="en">Service Realization — Shared <Feature title> realization</name>`.

`<process-slug>` is the lowercase-hyphens normalisation of the Business Process element's `<name>` (or, if available, derived from the lifting `LIFT-CANDIDATE source=` path's basename for stable cross-extracts). For shared-story views, sort member process slugs ascending before computing the identifier.

## 2. Rules

### Rule 1 — §9.7 contents (top-level processes only)

Process A is **top-level** when no other Business Process has a Composition relationship targeting A (no `<relationship xsi:type="Composition" target="A">` from a Business Process source).

The §9.7 view contains:

- Every top-level Business Process *not* carrying `propid-coop-view-exclude=true` (§6.4b suppression).
- Each included process's **start Business Event** when one is identifiable (the Triggering source feeding the process; for Extract-lifted processes this is the orchestrator's HTTP / queue / timer / event-grid starter per [`lifting-rules-process.md`](lifting-rules-process.md) "Orchestrator entry point → Business Event").
- All `xsi:type="Triggering"` and `xsi:type="Flow"` relationships **between included top-level processes** (inter-process edges).
- Architect-authored Business Actor Assignments to included top-level processes — preserved from any prior diagram at the canonical path; never invented from code.
- Architect-authored Business Object Access edges from included top-level processes — preserved likewise.

The §9.7 view does **not** contain sub-processes (those are Composition-nested under a top-level process and appear inside that top-level process's §9.3 drill-down view as nested boxes).

If after applying suppression the §9.7 view would contain zero or one Business Process, omit emission entirely (zero) or emit but accept that `AD-B-11` will fire on Review (one). Do **not** silently fabricate processes to pad the view.

### Rule 2 — §9.3 contents (one per distinct realization story)

For every Business Process X that is **orchestrator-level** (= top-level OR Composition-nested under another Business Process) and not carrying `propid-drilldown-exclude=true` (§6.4b suppression), assign X to a realization-story group before emitting §9.3 views.

Two or more processes share the same realization story when their materialized
§9.3 drill-down would have the same fingerprint:

- same Application Service set realising the process group;
- same Application Component set realising those services;
- same UI-entry posture (all user-driven with the same UI Application Component
  + Application Interface pattern, or all system-driven with no UI entry point);
- same Technology Node / System Software / Artifact hosting chain when
  Technology is in scope;
- same data-plane, managed-identity / RBAC, external trust-boundary, and
  deployment-environment elements when those are present in the model; and
- no process-specific Business Object, Actor Assignment, Triggering / Flow
  handoff, security boundary, deployment path, or view documentation that would
  change the architecture question the §9.3 view answers.

Emit one §9.3 view per distinct fingerprint. For a singleton group, root the
view on X. For a shared group, root the view on the sorted set of Business
Processes and show those processes together at the top of the realization
spine, then draw the shared Application / Technology chain once. Do not emit
near-identical per-process copies.

Each §9.3 view contains:

- The Business Process X at the top for a singleton view, or the grouped
  Business Processes at the top for a shared-story view.
- The Application Service that Realises X or the process group (if any in the model). Multiple Application Services possible.
- The Application Component(s) Realising those Application Service(s).
- The Technology Node(s) the Application Component(s) are Assigned to.
- For **user-driven** processes (carrying a Business Actor Assignment per reference §4.1) — the architect-authored UI Application Component and Application Interface at the entry point (per existing reference §9.3 Process-rooted UI-aware modality and `AD-B-10`).
- Composition-nested sub-processes of X appear *inside* the view as nested boxes per existing §9.3 layout (the sub-process also has its own singleton or shared §9.3 view unless suppressed; the two representations together give the architect both the parent's drill-down view and a navigable sub-process drill-down).

Layout follows the existing Tier 2 §9.3 specialisation in [`layout-strategy.md`](layout-strategy.md) — vertical realisation stack, no change.

**Review smell.** If an existing model contains two or more §9.3 Service
Realization views with identical fingerprints and no material process-specific
difference, Review emits `AD-B-14` and recommends consolidation. Separate views
are justified when the process changes application, data, technology, security,
deployment, UI-entry, or business semantics materially.

### Rule 3 — Cross-reference back-pointers in `<documentation>`

Every emitted §9.3 view's `<documentation>` block carries the back-pointer block at the top. Shared-story views also list their member processes:

```
Parent process: id-bp-<parent-slug>     [omit when this process is top-level]
Cooperation view: id-view-bpc-<feature-slug>
Member processes: id-bp-<slug-a>, id-bp-<slug-b>     [shared-story views only]
```

Reverse Lookup ([SKILL.md](../../SKILL.md) "Lookup mode workflow" step 1c reverse-lookup-backend-path) uses these back-pointers to walk a Composition hierarchy in one parse instead of file-globbing.

If the architect has authored a `<documentation>` block on the view, append the back-pointer block at the end (preserve architect prose).

### Rule 4 — Layout invocation

Each emitted §9.7 / §9.3 view runs the existing [`layout-strategy.md`](layout-strategy.md) Tier 2 specialisation matching its `viewpoint=` attribute. No change to the layout engine — multi-process §9.7 views were already supported by the 3-lane process-flow specialisation; singleton and shared-story §9.3 views use the vertical realisation stack specialisation.

### Rule 5 — Existing model preservation

If the canonical file already contains §9.7 or §9.3 views:

- Existing view identifiers, names, properties, and `<node>` placements are preserved verbatim.
- Architect-edited view contents (extra Actors / Objects added by hand) are preserved.
- Top-level processes missing from an existing §9.7 view are added; processes removed from the model are removed from the view (drift surface — listed in the footer).
- §9.3 views are added when missing for an orchestrator-level process story (and not suppressed via `propid-drilldown-exclude`); near-identical per-process copies are consolidated when their fingerprint matches; removed when their root process group is removed from the model.

### Rule 6 — Budget cap, no auto-split

If a §9.7 view would exceed the `AD-L4` budget (>20 elements or >30 relationships), emit it anyway and surface `AD-L4` as a finding in the footer with text *"feature has too many top-level processes; consider splitting the feature."* The procedure does not invent feature boundaries.

### Rule 7 — Determinism

A re-Extract of the same code produces byte-identical output: same view identifiers (per Rule 1's slug rule), same view contents, same Tier 0 architect-position preservation (per [`layout-strategy.md`](layout-strategy.md)).

### Rule 8 — Suppression properties

Architect-set `<property>` instances on Business Process elements:

- `<property propertyDefinitionRef="propid-coop-view-exclude"><value xml:lang="en">true</value></property>` — exclude this process from §9.7 emission. Suppresses `AD-B-13` for this process.
- `<property propertyDefinitionRef="propid-drilldown-exclude"><value xml:lang="en">true</value></property>` — suppress emission of this process's own §9.3 drill-down. Suppresses `AD-B-12`.

Both are defined in reference §6.4b. The two `<propertyDefinition>` declarations are emitted once per model under `<propertyDefinitions>` only when at least one element carries a corresponding `<property>` instance — never auto-injected on a legacy file.

## 3. Output shape

### Example A — small feature, 2 top-level processes, 1 sub-process

A feature `checkout` with two top-level orchestrators (`PlaceOrder`, `CancelOrder`) and one sub-orchestrator (`ValidateOrder`, Composition-nested under `PlaceOrder`). Expected emission when all three have materially different realization stories: 1 × §9.7 + 3 × §9.3.

```xml
<views>
  <diagrams>
    <view identifier="id-view-bpc-checkout" xsi:type="Diagram" viewpoint="Business Process Cooperation">
      <name xml:lang="en">Business Process Cooperation — Checkout</name>
      <node identifier="id-node-bpc-place-order" xsi:type="Element" elementRef="id-bp-place-order" x="40" y="200" w="180" h="64"/>
      <node identifier="id-node-bpc-cancel-order" xsi:type="Element" elementRef="id-bp-cancel-order" x="280" y="200" w="180" h="64"/>
      <!-- start events + actor assignments + object access edges as applicable -->
    </view>

    <view identifier="id-view-sr-place-order" xsi:type="Diagram" viewpoint="Service Realization">
      <name xml:lang="en">Service Realization — Place Order</name>
      <documentation>Cooperation view: id-view-bpc-checkout</documentation>
      <!-- node placements per Tier 2 §9.3 vertical realisation stack -->
    </view>

    <view identifier="id-view-sr-cancel-order" xsi:type="Diagram" viewpoint="Service Realization">
      <name xml:lang="en">Service Realization — Cancel Order</name>
      <documentation>Cooperation view: id-view-bpc-checkout</documentation>
      <!-- ... -->
    </view>

    <view identifier="id-view-sr-validate-order" xsi:type="Diagram" viewpoint="Service Realization">
      <name xml:lang="en">Service Realization — Validate Order</name>
      <documentation>Parent process: id-bp-place-order
Cooperation view: id-view-bpc-checkout</documentation>
      <!-- ... -->
    </view>
  </diagrams>
</views>
```

The §9.7 view contains the two top-level processes (`PlaceOrder`, `CancelOrder`) but **not** the sub-process (`ValidateOrder`). The sub-process appears nested inside `id-view-sr-place-order` (its parent's §9.3) and as the root of its own §9.3 view (`id-view-sr-validate-order`) — reachable from both directions.

### Example A2 — shared realization story

Two top-level processes (`PlaceOrder`, `CancelOrder`) both realise the same
Application Service through the same Application Component, hosting chain,
data-plane resources, trust boundary, deployment environment, and UI-entry
posture. Expected emission: 1 × §9.7 + 1 × shared §9.3 view. The shared view
lists both Business Processes at the top and draws the common Application /
Technology chain once.

### Example B — single-process suppression

Two top-level processes; one is tagged `propid-coop-view-exclude=true` because it is deprecated.

```xml
<propertyDefinitions>
  <propertyDefinition identifier="propid-coop-view-exclude" type="string">
    <name xml:lang="en">coop-view-exclude</name>
  </propertyDefinition>
</propertyDefinitions>

<elements>
  <element identifier="id-bp-place-order" xsi:type="BusinessProcess">
    <name xml:lang="en">Place Order</name>
  </element>
  <element identifier="id-bp-legacy-place-order" xsi:type="BusinessProcess">
    <name xml:lang="en">Legacy Place Order (deprecated)</name>
    <properties>
      <property propertyDefinitionRef="propid-coop-view-exclude">
        <value xml:lang="en">true</value>
      </property>
    </properties>
  </element>
</elements>
```

The §9.7 view contains only `id-bp-place-order`. The legacy process still has its own §9.3 drill-down view (suppression is orthogonal — `propid-coop-view-exclude` does not imply `propid-drilldown-exclude`).

## 4. What this procedure does not do

- **Lift Business Layer elements.** Element lifting lives in [`lifting-rules-process.md`](lifting-rules-process.md). This procedure consumes the lifted set; it doesn't produce it.
- **Author Business Actor / Role / Object content.** Forward-only per reference §7.2; architect-authored. The procedure preserves architect-authored Actor Assignments and Object Access edges in the §9.7 view but never invents them.
- **Emit UI Application Components for §9.3.** Hand-authored per existing reference §9.3 Process-rooted modality (UI route lifting deferred in v1).
- **Auto-split a feature when its §9.7 overflows AD-L4.** Surface AD-L4 as a finding; architect splits.
- **Apply layout.** Delegated to [`layout-strategy.md`](layout-strategy.md). This procedure produces the view skeleton (identifier, name, content references); the layout procedure applies coordinates.
- **Invent consolidation across materially different process stories.** If
  security, data, deployment, UI-entry, technology, or business semantics
  differ, emit separate §9.3 views and explain why they were kept separate.

## Sources

Paraphrased guidance; no code samples copied from sources.

- The Open Group, *ArchiMate® 3.2 Specification* (C226, March 2023). The notation anchor for the §9.7 Business Process Cooperation viewpoint, the §9.3 Service Realization viewpoint, the Composition relationship between Business Processes, and the Triggering / Flow relationships.
- The Open Group, *ArchiMate® 3.2 Reference Cards* (N221, Copyright © 2022 The Open Group). Verbatim definitions of Composition (*"Represents that an element consists of one or more other concepts."*) and Triggering (*"Represents a temporal or causal relationship between elements."*). Publicly downloadable from www.opengroup.org.
- The Open Group, *ArchiMate® Model Exchange File Format 3.2* (Appendix E of C226). The OEF XML serialisation the procedure emits.
