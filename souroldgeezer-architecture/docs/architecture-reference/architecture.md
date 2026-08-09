# Architecture Design Reference

This reference defines the modeling rules for the `architecture-design` skill.
The skill uses ArchiMate® 3.2 concepts and stores agent-editable architecture
source as dediren packages.

## 1. Operating Contract

The canonical source for a feature architecture is:

```
docs/architecture/<feature>.dediren/
  package.json               # dediren-native build manifest (package.schema.v1),
                             # the only authored manifest; its package-level
                             # presentation declares lang / dir once
  model.json
  model-<notation>.json      # per-notation model(s) in a mixed package (§3)
  render-policy.json
  render-metadata.json       # optional checked-in shared semantic metadata
  export-policy.json        # optional compatibility export policy
  generated/                # reproducible per-view output, ignored by default
```

Agents edit package source and policies. Generated layout, SVG, and optional
export files can be recreated from the package. SVG render output is the primary
visual proof for review. OEF export is optional compatibility output for
conformant tools and is not the source of truth.

This plugin is an ArchiMate-aware modeling skill and package workflow. It is
not a certified or complete conforming ArchiMate tool. Its quality levels are
workflow evidence claims about the package, views, render output, and optional
export evidence that were checked in the current task.

`package.json` lists only actual views. Missing supported diagram kinds are
reported in the footer; they are not added as placeholders.

## 2. Quality Levels

- `source-valid`: `model.json` passes schema validation, ids are unique,
  relationships resolve, and the assessed ArchiMate relationships have passed
  schema validation plus ArchiMate semantic validation via
  `dediren_validate {workspaceRoot, source, profile: "archimate"}`.
- `view-readable`: source-valid plus every actual view in `package.json`
  projects, lays out, and layout-validates (inside `dediren_build`). This proves
  layout validity, not visual cleanliness.
- `render-ready`: view-readable plus SVG render evidence exists for changed or
  requested views, the artifact is nonblank, framed, carries dediren node/edge
  markers, and visual-readiness has been inspected for density, framing, label
  risk, and audience fit.
- `review-ready`: render-ready plus no blocking `ARCH-*` finding remains for
  the audience, diagram kind, and change scope.

The package rollup is the weakest applicable level across actual views.

### Implementation-Readiness Review

An implementation-readiness review asks whether the architecture package is
enough to guide implementation. This is separate from `source-valid`,
`view-readable`, `render-ready`, and `review-ready`: a package can validate and
render while still lacking product intent, confirmed business process semantics,
data lifecycle, trust boundaries, environment responsibility, or operational
acceptance gates.

For implementation-readiness review, split findings into
architecture-documentation findings and other source material findings.
Architecture-documentation findings need ArchiMate equivalence and an
implementation impact. Other source material findings should be routed to API,
app, infra, security, test, or software-design sources rather than duplicated
inside the architecture package.

## 3. Dediren Package Source

`model.json` contains nodes, relationships, source evidence, and plugin-owned
metadata. A node needs a stable id, ArchiMate type, human label, and enough
`properties` to explain why it belongs in the package. A relationship needs a
stable id, type, source id, target id, and an optional label. The model schema
sets `additionalProperties: false` on nodes and relationships and rejects a
`documentation` field on either; the schema-legal home for prose and evidence is
the free-form `properties` object, through the canonical keys below. Bounded
structural questions over the model — a node's dependents, orphaned
relationships or nodes, per-view node coverage — are answered read-only by
`dediren_query` (§9), without editing source.

Canonical `properties` keys keep prose and evidence machine-readable, so Review,
drift detection, and cross-package queries can rely on them instead of a
per-extraction dialect:

- `rationale` — prose explaining why the element belongs or what it represents
  (the schema-legal home for the rejected node-level `documentation` text);
- `evidence` — the §8 evidence label (`source-backed`, `candidate-from-source`,
  `architect-owned`, `weak-evidence`, or `overlay-only`);
- `source` — source path plus symbol or workflow name backing the claim;
- `confidence` — confidence in the claim;
- `open_question` — an unresolved question about the element.
- `identity` — repo-stable cross-package identity slug asserting that elements
  in different packages model the same real-world thing (§15).

Set `rationale` on any non-obvious node or relationship. Add the four evidence
keys in Extract mode whenever a claim could be mistaken for extracted truth
(§8). Notation-specific keys stay namespaced (for example `properties.uml.node`,
`properties.uml.architecture_context`).

Stable ids matter. Preserve existing ids unless they are duplicate, misleading,
or tied to removed source evidence. Labels can be human-friendly; id and label
must not contradict each other semantically.

`package.json` binds actual views to a render policy, presentation, declared
outputs, and optional export lanes. A view must answer a clear
architecture question and should carry the smallest set of elements and
relationships needed to answer it.

`render-policy.json` and `render-metadata.json` control SVG style and semantic
markers. Render metadata must let reviewers map visible SVG nodes and edges back
to source ids.

`export-policy.json` is required only when OEF export is requested. When export
fails, fix package source or export policy first, then recreate output.

For ArchiMate SVG policy with generated per-view render metadata, set
`plugins.generic-graph.semantic_profile` to `archimate` in `model.json`. With
the supported Dediren runtime, generated ArchiMate render metadata no
longer depends on the `archimate-oef` export plugin.

### Package JSON Generation

Start clean-slate packages from the fixture under
`skills/architecture-design/references/fixtures/dediren/basic/`, then replace
ids, labels, model content, view definitions, and policies with the project
architecture.

For ArchiMate packages that render with generated per-view metadata and an
ArchiMate SVG policy, include `generic-graph` in `model.json.required_plugins`
and set `plugins.generic-graph.semantic_profile` to `archimate`. Add
`archimate-oef` only when the package needs OEF export. As of the current
release, `required_plugins` is informational only — it names the engines a
package expects, for human readers; the in-memory registry no longer enforces
it. Keep listing the engines the package uses (a truthful manifest), but a
`required_plugins` mismatch is not a runtime gate.

For UML packages, set `plugins.generic-graph.semantic_profile` to `uml` and
start from a matching UML source fixture exposed by the selected host runtime that
matches the kind in play (see the UML notation hub at
`skills/architecture-design/references/notations/uml.md` for the current kind
list).

Treat these files as hand-authored and checked in: `model.json`,
`package.json`, `render-policy.json`, package-level `render-metadata.json` when
the package intentionally keeps one shared semantic metadata file, and optional
`export-policy.json`. Treat `generated/` as reproducible output: projections,
per-view render metadata, layout results, SVG, and optional OEF intermediates
stay ignored unless the owning repository deliberately commits selected render
evidence elsewhere.

For each actual view in `package.json`, declare the render policy, the
presentation, and the diagram / render-metadata / layout outputs:

```json
{
  "id": "main",
  "model": "orders",
  "render_policy": "render-policy.json",
  "presentation": {
    "title": "Orders - Application Cooperation",
    "question": "Which application components cooperate to deliver orders?",
    "diagram_kind": "Application Cooperation"
  },
  "outputs": {
    "diagram": "generated/svg/main.svg",
    "render_metadata": "generated/render-metadata/main.json",
    "layout": "generated/layout/main.json"
  }
}
```

Projection, layout and the render stage are the runtime's business — the package
declares *what* each view is and *where* its artifacts go, never the per-stage
plugin chain. `presentation.title` / `question` double as that view's SVG
accessible name, per view even under a shared render policy — which is why a
render policy shared by several views must **not** carry its own `accessibility`
block: a policy-level `title` / `description` overrides the per-view text and
stamps one view's name onto every view sharing that policy.

A package-level `"presentation": {"lang": "fi", "dir": "rtl"}` beside `models` /
`views` tags all of the package's authored text at once: a BCP 47 language and an
`ltr` / `rtl` base direction. The runtime pushes the pair down into each view's
render policy (an explicit value in a view's own policy overrides it) and writes
it onto every emitted SVG root as `xml:lang` / `direction`; the gallery reuses the
same pair for `<html lang dir>`. Screen readers then pronounce each `<title>` /
`<desc>` in the right language, right-to-left text is laid out in the direction it
is read, and the page cannot contradict the diagrams it inlines. Tag any package
written in something other than the language its audience defaults to, or in a
right-to-left script. Neither key has a default — leave both out and the artifacts
are byte-for-byte what an undeclared package has always produced. `package.json`
is the only authored manifest; the feature name is the package directory's own,
under the canonical `docs/architecture/<feature>.dediren/` path.

Use the package-level `render-metadata.json` only when a repository chooses a
checked-in shared metadata policy/cache and can keep it synchronized with the
views. Otherwise render with the generated per-view metadata declared in the
view's `metadata.output`, after confirming the generated metadata profile
matches the render policy profile.

The `render` plugin emits the SVG artifact that remains the canonical proof. It
no longer produces PNG: Dediren dropped native raster rendering in 2026.07.13,
retiring the `raster` render-policy block and the `png` `artifact_kind` so that
only `svg` is returned. SVG stays the evidence of
record. When a consumer needs a bitmap, generate it downstream as a separate
step by running the emitted SVG through any general-purpose SVG converter —
librsvg's `rsvg-convert`, `resvg`, ImageMagick, and Inkscape each handle this.

Renders are static SVG only. Dediren retired the interactive render policy
(render-policy schema v3, 2026.07.18): the `interactive` field and the
`style.interaction` block no longer exist, and there is no scripted-SVG or
HTML-wrapper output. Still verify the mode from the emitted artifact, not the
policy (§9 render-mode check): a `<script>` element is a defect — runtimes
≤ 2026.07.0 embedded a click-to-highlight script regardless of policy — reported
as `ARCH-R-5` plus a `Dediren tool issues` entry, never disclosed as intended
output. Current Dediren distributions expose `rich-svg` (richer-styled) and
`dark-svg` (dark canvas, light labels) render-policy fixtures as starting
points. A dark policy is still held to the same WCAG 2.2 SC 1.4.11 non-text and
label-text contrast bars as a light one — verify contrast from the emitted
artifact, not from the fixture's presence. Static SVG stays the default and the
evidence of record; keep the `data-dediren-node-id` / `data-dediren-edge-id`
markers required by §9.

Beyond the per-view SVG, the skill can emit a package-level
**shareable gallery** — one self-contained `gallery.html` inside the package that
inlines every view's SVG as an inert `<template>`, with a notation-grouped
register, zoom, light/dark theme, deep-linking, and keyboard navigation. The
diagram sheet is derived per view from each SVG's own background (so a dark
render policy is not framed by a white card), and an optional
`gallery-theme.json` beside `package.json` overrides the gallery palette per
package. It is built by the bundled `references/scripts/build-gallery.py` from
the package's own sources (`package.json`, `generated/svg/*.svg`,
`generated/render-metadata/*.json`, and the optional `gallery-theme.json`) and
is a pure function of them, so it is rebuilt whenever SVG output is
(re)generated (mode-agnostic). It is an outer viewer over the static SVGs and
does not alter or substitute for the per-view render mode or the §9 render-mode
check; a committed gallery that has drifted from its SVGs (`build-gallery.py
--check`) is `ARCH-R-2`. Design system and tuning: `references/gallery.md`.

The render policy may also carry an optional `accessibility` block (`title`,
`description`, plus `lang` / `dir`) that names the emitted SVG for assistive
technology: the root element gets `role="img"` with a `<title>` and a `<desc>`
when a description is supplied. Leave `title` / `description` out — the per-view
`presentation.title` / `question` above supply them per view, and a policy-level
block **overrides** that, stamping one view's text onto every view sharing the
policy. Reach for the block only for a genuinely policy-wide fact; `lang` / `dir`
are better declared once at package level (§ package `presentation`), which is
where a whole package's authored language belongs.

### Mixed-Notation Packages

One dediren model carries a single `plugins.generic-graph.semantic_profile`, and
validation is profile-global: the runtime rejects foreign-profile element types
(`DEDIREN_ARCHIMATE_ELEMENT_TYPE_UNSUPPORTED` /
`DEDIREN_UML_ELEMENT_TYPE_UNSUPPORTED`), so one model cannot hold both ArchiMate
and UML content. A package that spans notations therefore keeps **one
single-notation model per notation** — `model.json` for ArchiMate plus
`model-<notation>.json` (for example `model-uml.json`) for UML — each validated,
projected, rendered, and exported with its own `--profile`.

`package.json` binds these models: a `models[]` registry (`{ id, source }`), a
`model` reference on every view (optional when the package declares one model),
and an `exports[]` array where each entry targets **exactly one** of a `view`
(one focused file) or a whole `model` (the aggregate lane). The notation is not
declared here — it rides on each `model.json`'s own
`plugins.generic-graph.semantic_profile`, the single authority. Each view
carries the same `render_policy` / `presentation` / `outputs` shape shown above.

The `uml-xmi` aggregate is class-family only. Scope that export to a `model` and
it gathers the model's `uml-class` and `uml-data` views; every other kind needs a
`view`-scoped export of its own, and a model offering no class-family view has
nothing to aggregate.

```json
{
  "package_schema_version": "package.schema.v1",
  "models": [
    { "id": "arch", "source": "model.json" },
    { "id": "uml", "source": "model-uml.json" }
  ],
  "views": [
    { "id": "app-cooperation", "model": "arch", "render_policy": "render-policy.json",
      "presentation": { "title": "Application Cooperation", "diagram_kind": "Application Cooperation" },
      "outputs": { "diagram": "generated/svg/app-cooperation.svg",
                   "render_metadata": "generated/render-metadata/app-cooperation.json",
                   "layout": "generated/layout/app-cooperation.json" } },
    { "id": "domain-class", "model": "uml", "render_policy": "render-policy-uml.json",
      "presentation": { "title": "Domain Class View", "diagram_kind": "UML Class" },
      "outputs": { "diagram": "generated/svg/domain-class.svg",
                   "render_metadata": "generated/render-metadata/domain-class.json",
                   "layout": "generated/layout/domain-class.json" } }
  ],
  "exports": [
    { "id": "arch-oef", "view": "app-cooperation", "lane": "archimate-oef", "policy": "export-policy.json", "output": "generated/export/orders.oef.xml" },
    { "id": "uml-xmi", "model": "uml", "lane": "uml-xmi", "policy": "export-policy-uml.json", "output": "generated/export/orders.uml.xmi" }
  ]
}
```

Cross-notation handoff stays one-directional through
`properties.uml.architecture_context` on the UML side, pointing at an id in the
package's ArchiMate model (see `references/notations/uml.md`). The bundled
example is `references/fixtures/dediren/mixed/` — an ArchiMate Application
Cooperation model plus a UML class model whose `pkg-fulfilment` package
elaborates the ArchiMate `svc-orders` component; its per-view pipeline and both
exports
resolve on the compatibility baseline. Do not invent a single mixed model, a different
`model-<notation>.json` split, or an ad-hoc `exports[]` dialect outside this
layout.

## 4. ArchiMate Layers And Aspects

ArchiMate separates architecture content by layer and aspect. Do not collapse
these distinctions for convenience.

Primary layers:

- **Strategy**: Capability, Resource, Course of Action, Value Stream.
- **Business**: Actor, Role, Collaboration, Interface, Process, Function,
  Interaction, Event, Service, Object, Contract, Representation, Product.
- **Application**: Component, Collaboration, Interface, Function, Interaction, Process, Event, Service, Data Object.
- **Technology**: Node, Device, System Software, and related Technology* elements, Artifact, Communication Network, Path.
- **Physical**: Equipment, Facility, Distribution Network, Material.
- **Motivation**: Stakeholder, Driver, Assessment, Goal, Outcome, Principle, Requirement, Constraint, Meaning, Value.
- **Implementation & Migration**: Work Package, Deliverable, Implementation Event, Plateau, Gap.

Primary aspects:

- **Active structure** performs behavior: actors, roles, components, nodes,
  devices, collaborations, interfaces.
- **Behavior** is what happens: processes, functions, interactions, events,
  services.
- **Passive structure** is acted on: business objects, contracts, products, data
  objects, artifacts, material.

Do not model one thing as both active structure and behavior. Do not connect
active structure directly to passive structure when a behavior element is the
real architectural claim.

## 5. Relationship Discipline

Use the narrowest valid relationship type that represents the claim.

Core relationship families:

- **Composition**: whole/part, lifecycle-strength ownership.
- **Aggregation**: whole/part, weaker ownership.
- **Assignment**: active structure performs behavior (or vice versa).
- **Realization**: concrete element fulfills a more abstract service,
  requirement, capability, or deliverable.
- **Serving**: source behavior/service used by target.
- **Access**: behavior reads, writes, or accesses passive structure.
- **Influence**: Motivation element affects another element.
- **Triggering**: causal or temporal start of another behavior.
- **Flow**: transfer of information, goods, or value.
- **Specialization**: source is a specialization of target.
- **Association**: weakest allowed relationship; use sparingly.

Every relationship must be valid for its source and target ArchiMate element
types. Invalid type/source/target combinations are `ARCH-M-1`.

### Application Interfaces, APIs, And GUIs

APIs and GUIs are Application Interfaces: they are access points where
application behavior is made available to users, application components, or
nodes. Application Services model the functionality exposed through an
interface. Name services for the exposed behavior or capability, not for the
transport surface, unless the source label is quoted as evidence and the
architecture label resolves the role.

Endpoint legality belongs to `dediren_validate {workspaceRoot, profile: "archimate"}`, not local
guesswork. If validation accepts Application Component to
Application Interface Realization, do not report it as endpoint-illegal. Prefer
Composition or Aggregation for component-interface ownership when the
architecture claim is that a component provides or owns an access point. Use
Realization only when the model intentionally states that the component fulfills
the interface abstraction.

### Process Handoffs

Use Triggering when the architectural claim is process sequencing or one
process/event causes the next behavior to start. Use Flow when the important
claim is transfer of information, goods, or value. Reserve Serving for a stable
service dependency, not for a process handoff that is meant to show order.

Prefer explicit realization chains:

- Business Service realized by Application Service.
- Application Service realized by Application Component or Function.
- Application Component assigned to or hosted by Technology elements when the
  deployment concern is in scope.
- Requirement or Goal realized by the architecture element that actually
  satisfies it.

## 6. Supported Diagram Kinds

The skill reports coverage for seven seed diagram kinds. Seed diagram kinds are
starter coverage, not the full ArchiMate viewpoint mechanism. The package may
contain any subset; missing kinds are disclosed, not stubbed.

### Capability Map

Use for strategic capability grouping and ownership. Keep technology and
implementation details out unless they clarify capability support.

### Application Cooperation

Use for application components, services, interfaces, data objects, and external
systems. The view should show how applications collaborate and what service or
data dependency matters.

### Service Realization

Use to show how a Business or Application Service is realized by lower-level
application and technology elements. The primary realization path must be
visible; otherwise report `ARCH-V-2`.

### Technology Usage

Use for hosting, data stores, identity, queues, networks, and system software.
Show security or identity paths when they are architecture-significant.

### Migration

Use for Work Packages, Plateaus, Gaps, Deliverables, and Implementation Events.
Do not treat parallel environments as migration states unless the architecture
intent says one state becomes another.

### Motivation

Use for Stakeholders, Drivers, Assessments, Goals, Outcomes, Requirements,
Constraints, Principles, Meaning, and Value. Connect Motivation elements to the
architecture elements they influence or are realized by.

### Business Process Cooperation

Use for process handoffs, participants, business objects, events, and outcomes.
Show Triggering or Flow where the sequence matters. A single process without a
handoff or participant context rarely justifies this view.

### Custom Viewpoint Path

Custom viewpoint path: when the requested concern does not fit a seed diagram
kind, define the stakeholder concern, allowed element types, allowed
relationship types, audience, and quality target before editing source. Store
the resulting view as an actual view in `package.json`; do not create empty
placeholder views for viewpoint coverage.

## 7. View Design Rules

A view should answer one architecture question. Examples:

- Which application components cooperate to deliver this capability?
- Which technology services and nodes host this application service?
- Which process handoff creates the business outcome?
- Which requirement or goal is realized by the design?
- Which work package moves the architecture from current to target state?

Before modeling, define the view concern, allowed element types, and
relationship types. Keep the view consistent with that small vocabulary. If an
out-of-set element or relationship is needed, either document why it belongs or
split the concern into a separate view.

Good views have:

- a small set of elements needed for the question;
- visible primary relationships;
- labels intended for the target audience;
- enough source-backed groups to reveal ownership, hosting, trust,
  dependency, or realization boundaries;
- render output that can be read without inspecting source.

Bad views list inventory, hide the primary relationship, mix unrelated layers,
or include implementation trivia that distracts from the architecture claim.

Visual-readiness is separate from layout validity. When a view validates but is
hard to scan, report the narrowest warning instead of claiming it is clean:

- `ARCH-L-3` for high edge count, high edge/node ratio, long cross-group
  routes, extreme aspect ratio, large empty groups, or congested route channels;
- `ARCH-R-3` for labels, icons, or markers that obscure the primary message,
  including an edge label that dissociates from its own edge — closer to a
  different edge run than to its own route;
- `ARCH-Q-2` for hub fanout, mixed audience concerns, or multiple viewpoint
  concerns in one diagram.

One sub-check is measurable and mandatory whenever a rendered view carries edge
labels: label-to-own-edge distance. Pair each edge label with its own route via
the `data-dediren-edge-id` markers, measure the distance from the label anchor
to the nearest point of that route, and compare it against the nearest point of
every other edge run in the view. Report `ARCH-R-3` when a different edge run
is closer than the label's own route, or when the own-route distance exceeds
roughly one label height. A `validate-layout` envelope reporting
`label_space_issue_count: 0` never clears this check — the runtime is known to
under-report label-edge dissociation — so measure from the rendered SVG. When
measured dissociation contradicts a zero label-space count, also record the
silent metric under `Dediren tool issues` (§9); do not patch the host runtime.

First separate a *layout* problem from a *concern* problem. Density, route
congestion, long spans, extreme aspect ratio, framing, and label displacement
are placement problems: tune the dediren layout (§9 `layout_preferences` —
`mode`, `direction`, `density`, `wrapping`, `routing`, and the ELK Layered
tuning knobs) and re-run
`validate-layout` before reporting `ARCH-L-3`. Reserve `ARCH-Q-2` and view
splitting for genuine concern problems — mixed audiences, multiple viewpoints,
an inventory dump, or unrelated layers in one diagram — or for a view that
layout tuning still cannot make scannable.

When the concern is genuinely mixed, prefer splitting into narrower concerns
over one wide graph. Process views should stay
linear when the story is linear. Service-realization views should keep the
realization path easy to follow. Technology-usage views should split hosting,
data, identity/security, and observability when one view cannot carry all of
them. Migration views should prefer stages or lanes over a generic wide graph
when the work sequence is the message.

## 8. Extraction And Source Evidence

Load `source-weighting.md` before classifying source surfaces in Extract mode
unless the task is a purely mechanical update to an existing package. Use the
source-to-ArchiMate selection matrix, relationship ladder, view recipes, and
evidence labels for non-obvious choices. Record the label — `source-backed`,
`candidate-from-source`, `architect-owned`, `weak-evidence`, or `overlay-only` —
in the element's `properties.evidence` key when a claim could be mistaken for
extracted truth, with `properties.source`, `properties.confidence`, and
`properties.open_question` alongside it (canonical keys defined in §3). Those
property keys are the schema-legal home for evidence; do not invent
per-extraction key names.

Extract only facts that source can support.

Common extractable sources:

- .NET projects, references, public clients, hosted services, and durable
  orchestrators;
- Java builds, deployable modules, public entrypoints, typed clients,
  scheduled/message handlers, and persistence/data models;
- Bicep or ARM-style IaC resources, dependencies, identities, and environment
  declarations;
- GitHub Actions workflows, jobs, environments, deployment stages, and release
  artifacts;
- OpenAPI or source-defined HTTP routes when API architecture is in scope;
- UI routes when they are architecture-significant entry points.

Architect-owned content includes Business Actor, Role, Collaboration, Object,
Contract, Product, Service, Function, Motivation, Strategy, and Physical claims
unless the user supplies explicit architecture intent or source evidence.

Business Process, Business Event, and Business Interaction may be lifted from
workflow sources only as candidates, each recording `properties.evidence`
(`candidate-from-source`), `properties.source` (path plus symbol/workflow name),
`properties.confidence`, and `properties.open_question`. Missing evidence is
`ARCH-X-2`.

Extracted views should use source-backed groups when source structure supports
ownership, hosting, trust, environment, dependency, system responsibility, or
orchestration boundaries. In dediren source, put groups in `model.json` under
`plugins.generic-graph.views[].groups`, not `package.json`: each group needs a
stable id, human label, and member ids that are also present in the view. Do
not create decorative groups just to make a flat inventory prettier. Do not add
groups to small linear process views unless a participant, system
responsibility, trust boundary, or orchestration boundary changes the
architectural reading. If the boundary comes from architect intent rather than
source evidence, label it as architect-owned.

The `plugins.generic-graph.views[].groups` field is a dediren view grouping
mechanism with explicit roles. Use `role: "layout-only"` for visual grouping
only. Use the default `semantic-boundary` role, with `semantic_source_id`
pointing at a `Grouping` node, when a view group represents a real ArchiMate
Grouping element. Layout-only groups are not ArchiMate Grouping elements, and
unbacked source groups are not enough by themselves to claim semantic Grouping.

Drift review compares source evidence in the package with current repo state.
When source and package disagree, report whether the likely action is to update
the package or update the source.

That source drift is complemented by the §9 freshness tools: `dediren_verify`
(the artifact-freshness gate — a stale artifact is a blocking drift finding),
`dediren_status` (a non-gating workspace freshness index), and `dediren_diff`
(a report-only comparison of two revisions of this package's *own* source model,
distinct from repo-source drift and raising no `ARCH-X-*`). The procedure that
applies them, with the finding codes, is
`references/procedures/drift-detection.md`.

## 9. Runtime Evidence

The skill drives Dediren through a shared router with native Claude Code, Codex,
and Copilot MCP adapters. The plugin bundles the adapters, not Dediren: the
router executes the current host-managed `dediren` from `DEDIREN_COMMAND` or
`PATH`, with a migration-only fallback to the newest executable already present
in the former verified release cache. It discovers that installation's live
tool catalog and adds a required absolute `workspaceRoot` to every tool schema.
It handles both legacy MCP initialization and the 2026-07-28 stateless discovery
flow, bounds upstream waits, reaps catalog-only processes, restarts a known-dead
workspace process only for the next call, never auto-retries an uncertain call,
and closes children on EOF or termination. Children set cwd; stderr errors do
not pollute JSON-RPC stdout. Call its tools before
using the same
external executable as a CLI fallback. The skill requires seven tools: three that
author, validate, and build — `dediren_validate`, `dediren_build`,
`dediren_guide` — and four read-only model-intelligence and verification tools —
`dediren_diff`, `dediren_query`, `dediren_verify`, `dediren_status` — defined
under Read-Only Model-Intelligence Tools below.
`${CLAUDE_SKILL_DIR}` is this skill's absolute directory; Claude Code
expands it in `SKILL.md` (it resolves the installed-plugin cache path and this
source repo alike, and contains the skill's `SKILL.md`), and the reference
procedures reuse that resolved value read raw. In Codex, resolve the equivalent
absolute `<skill-dir>` from the loaded skill's source path and carry it into the
raw procedures. It locates this skill's own helper scripts, not Dediren.

Read the format contract through `dediren_guide` (`{workspaceRoot}` for the topic
index, then `{workspaceRoot, topic: "source-json"}`) before authoring or repairing source JSON. It is the
fast contract for Minimal Source JSON, Artifact Map, Semantic Profiles, Command
Handoff, and Repair Rules. The plugin never downloads, pins, downgrades, or
patches Dediren. The external CLI must be executable inside the MCP sandbox and
must report version `2026.07.28` or newer before rendering. When the
`dediren_*` tools are absent, the skill's internal CLI fallback may drive that
same host-managed executable. Only when neither lane can execute do runtime
checks cap at `source-valid` (not a hard stop) and disclose
`not run (host-managed Dediren unavailable)`
(see `references/procedures/self-check.md`).

The tested Dediren runtime enforces ArchiMate® 3.2 relationship endpoint
legality, uses the technology element name `Node`, not `TechnologyNode`, and
reports close parallel route channels during layout validation. Each
`dediren_build` call walks its views through projection, layout, layout
validation, and rendering inside the server.

The host-managed Dediren installation is an upstream distribution artifact. Do
not patch its schemas, plugin manifests, binaries, Java helpers, fixtures, or
`bundle.json` to fix tool behavior. When the runtime, schema, layout, render, export, or
helper behavior appears wrong, report it under `Dediren tool issues` with the
release version, command, input summary, error envelope, expected behavior, and
minimal repro evidence. Change only repo-owned skill, fixture, or documentation
guidance unless the task is explicitly to move to a different upstream Dediren
release.

Evidence gates (all via the MCP adapter and an absolute `workspaceRoot`):

- Source schema: `dediren_validate {workspaceRoot, source}`
- Source semantics: `dediren_validate {workspaceRoot, source, profile: "archimate"}` (or `"uml"`)
- View projection, layout, layout validation, and SVG render: `dediren_build` — one
  call walks a view through all of them; the layout-validation verdict is on the
  build-result `.views[].status` / `.views[].diagnostics[]`, the mapped
  `generated/layout/<view>.json` carries the layout geometry, and
  `generated/render-metadata/<view>.json` the render metadata
- Optional OEF/XMI export: `dediren_build` with an `oef_policy` / `xmi_policy`
- Artifact freshness (the drift gate): `dediren_verify {workspaceRoot, source, artifacts}` — the
  machine check that generated output is still a pure function of source (Read-Only
  Model-Intelligence Tools below)
- Workspace freshness index (non-gating): `dediren_status {workspaceRoot, dir}` — a read-only
  index of the models and artifacts under a directory (below)

Each tool returns an envelope (`dediren_build`'s is the unwrapped build-result
document; see `self-check.md` § Reading tool results). Error envelopes are findings
and cap the quality level at the highest stage already proven. `dediren_validate`
without a `profile` is schema validation only; pass `profile` before claiming
semantic source validity. Layout, render, and optional export remain downstream
evidence gates inside the build.

### Read-Only Model-Intelligence Tools

Beyond `dediren_validate` / `dediren_build` / `dediren_guide`, the server exposes
four read-only tools that answer model questions and verify build freshness
without mutating source or regenerating output. They belong to the read-only tool
subset — launching the server `dediren mcp --read-only` withholds only
`dediren_build` and keeps these plus `dediren_validate` / `dediren_guide` (six
tools), so Extract, Review, and Lookup need only the read-only subset. The plugin
adapter stays full because Build needs `dediren_build`; the skill never passes
`--read-only`.

- **`dediren_diff {workspaceRoot, old, new}`** compares two revisions of one package's source
  model — two source paths sharing the same schema id — and returns a
  `diff-result.schema` document: `nodes` and `relationships` each as
  `{added, removed, changed}` (a `changed` entry carries field-level
  `{field, from, to}` where `field` is `type` / `label` / `source` / `target` or
  a `properties.<key>`), and `views` as `{added, removed, changed}`. It is
  report-only and deterministic (sorted output). It surfaces model-revision facts
  and is complementary to, and distinct from, the §8 source drift that compares a
  package against current repo code/IaC/API/UI/workflow source (`ARCH-X-*`): diff
  compares two revisions of the package's own source model and raises no finding
  on its own.
- **`dediren_query {workspaceRoot, source, kind, id?}`** answers a bounded structural question
  over one model and returns a `query-result.schema` document. `kind:
  "dependents"` (requires `id`) returns `{id, inbound, outbound}` with each edge
  `{relationship_id, type, node_id}` — a node's fan-in and fan-out; `kind:
  "orphans"` returns `{relationship_orphans, view_orphans}`; `kind:
  "view-coverage"` returns a `view_coverage` `{views[], model_node_count,
  model_relationship_count, uncovered_node_ids}`. An unknown `kind`, or a
  `dependents` query with no `id`, returns `DEDIREN_COMMAND_INPUT_INVALID`. These
  are Lookup facts and a Review readiness aid; they feed existing `ARCH-M-*` /
  `ARCH-V-*` judgments and are not a new finding class.
- **`dediren_verify {workspaceRoot, source, artifacts}`** verifies that built artifacts under a
  directory are a pure function of the current source, returning a
  `verify-result.schema` document `{model_sha256, artifacts: [{path, status}]}`
  with each status `current` | `stale` | `unstamped`. All `current` → `ok`; any
  `stale` → the `DEDIREN_ARTIFACT_STALE` error (exit-2 CI drift gate) — a stale
  rendered SVG or package gallery is `ARCH-R-2`, a stale OEF/XMI export is
  `ARCH-E-4`; an `unstamped` artifact → the `DEDIREN_ARTIFACT_UNSTAMPED` warning
  (non-error), a valid disclosable state, not a finding on its own.
- **`dediren_status {workspaceRoot, dir?}`** returns a read-only workspace freshness index — a
  `status-result.schema` document `{models: [{path, sha256}], artifacts:
  [{path, status, model_sha256?}]}` (omit `dir` to index the server `--root`). It
  is an index, not a gate — `dediren_verify` is the gate — and complements the
  gallery `build-gallery.py --check` freshness check (§3,
  `references/gallery.md`).

**Provenance stamps.** These freshness checks work because every `dediren_build`
artifact now carries a deterministic, timestamp-free provenance stamp: an SVG
`<metadata id="dediren-provenance">` element, and a leading
`<!-- dediren-provenance … -->` comment on OEF/XMI. The stamp holds compact JSON
— `model_schema_version`, `model_sha256`, `view_id`, one of
`render_policy_sha256` / `oef_policy_sha256` / `xmi_policy_sha256`, and
`dediren_version`. Only whole `dediren_build` output is stamped; decomposed
per-stage `--emit` outputs are unstamped. Committed rendered fixtures that predate
stamping read as `unstamped`; that is expected and disclosable — do not regenerate
fixtures to stamp them.

**MCP resources.** The server also serves read-only resources returning bundle
bytes: `dediren://schema/<file>`, `dediren://fixture/<relative-path>`,
`dediren://guide/<topic>`, and `dediren://diagnostics/catalog` (every `DEDIREN_*`
code with its repair text). Read a resource for the exact schema, fixture, guide
topic, or diagnostic repair text; the repair loop still runs through
`dediren_guide`, with the diagnostics catalog as a direct lookup.

**Migration operations.** A `DEDIREN_SCHEMA_VERSION_OUTDATED` diagnostic now
carries a machine-readable `migration` object `{from, to, operations: [{op,
pointer?, to?, value?}]}`, where `op` is `rename_field` | `remove_key` |
`set_version` | `regenerate`. Dediren never rewrites the file: apply the listed
operations in order to upgrade the outdated source or policy, then re-validate
(`self-check.md` § Migrating an outdated input).

For ArchiMate SVG render policy, treat a generated render-metadata profile
mismatch as a package or policy defect until proven otherwise. Check
`plugins.generic-graph.semantic_profile`, the generated metadata
`semantic_profile`, and `render-policy.json` before reporting a runtime issue.

Layout runs inside each `dediren_build` call; there is no separate layout command
to parallelize. If a view's build reports an `ARCH-L-1` layout failure, rebuild
that single view on its own to isolate it, and
disclose a reproducible layout-engine failure under `Dediren tool issues` with the
build-result `.views[].diagnostics[]` counts and the mapped
`generated/layout/<view-id>.json` geometry.

A view carries an optional `layout_preferences` object (set on the view in the
source model) that influences how ELK positions nodes and routes edges. It changes
presentation only and never edits source semantics, so rebuild the view after
tuning to re-run layout validation. The bundle's
`schemas/layout-request.schema.json` holds the authoritative enums:

- `mode`: `flow` runs ELK Layered when the relationships give the view a reading
  order; `packed` runs ELK Rectangle Packing when the view has only nodes and
  group boxes with no relationships to route; `auto` lets the runtime choose.
- `direction`: `right` | `left` | `down` | `up` for flow orientation and
  aspect-ratio/framing control.
- `density`: `compact` | `readable` | `spacious` to relieve a dense view.
- `wrapping`: `auto` | `off` | `multi-edge` to relieve hub fanout and parallel
  edges.
- `routing`: `style` (`orthogonal` | `polyline` | `spline`) and
  `endpoint_merging` (`off` | `local` | `auto`) to relieve route congestion and
  detours. Route density comes from the top-level `density` knob; the pinned
  runtime's `layout-request` schema rejects a `routing.profile` key with a hard
  `DEDIREN_SCHEMA_INVALID` (see source grounding), so do not author one.
- `algorithm`: `layered` selects ELK Layered explicitly (currently the only
  value; `mode: flow` already implies it) — set it alongside the layered-only
  tuning below so the intent is self-documenting.
- Layered-algorithm tuning (layered-only; ignored under `packed`):
  `cycle_breaking` picks how feedback edges are broken; `layering.strategy` and
  `placement.strategy` choose layer assignment and in-layer placement (e.g.
  `placement.strategy: network-simplex` straightens a grouped fan-out that
  staircases under the default); `crossing.strategy` / `crossing.greedy_switch`
  control crossing minimization; and `compaction`, `components` (`separate`,
  `spacing`), `high_degree_nodes`, and `thoroughness` tune whitespace,
  disconnected-component packing, hub handling, and layout effort.
- per-node placement hints (set on the node, not in `layout_preferences`):
  `layer_constraint` pins a node to an edge layer (`first` / `last` / …) and
  `partition` (integer) groups nodes into ordered bands — use sparingly to fix
  a specific misplacement, and re-validate.
- per-edge priority hints (set on the relationship, not in `layout_preferences`):
  a `priority` object with integer `resist_reversal` (bias against reversing the
  edge during cycle breaking), `keep_short` (bias toward spanning fewer layers),
  and `keep_straight` (bias toward a straight route) nudges ELK Layered edge
  routing for one edge — use sparingly to fix a specific route, and re-validate.

Tune these to resolve a placement-driven `ARCH-L-3` before splitting a view
(§7), and disclose any non-default `layout_preferences` per view in the footer.

Dediren runtime validation is evidence, not the full ArchiMate review. If the
tool accepts a relationship type, source/target combination, export shape, or
layout artifact that the architecture review still rejects, report the
architecture finding normally and list the validator or renderer gap under
`Dediren tool issues` in the footer.

If grouped layout validation still reports connector-through-node, invalid
route, or group-boundary warnings, rerun the same view without groups. If the
ungrouped layout validates cleaner, keep source-backed groups in `model.json`,
use the cleaner layout as evidence and report the grouped-layout regression
with both validation counts.

### Visible Title Band Post-Render Step

Rendered output arrives already labelled for assistive technology (WCAG 2.2
SC 1.1.1 Non-text Content). Supported Dediren writes `role="img"` on
the root together with a `<title>` and `<desc>`, sourcing their text from that
view's `presentation.title` / `question` (§3) and tagging it with the package's
`lang` / `dir` where declared. One gap remains repo-owned: the runtime renders no *visible*
title — deliberately, since visible chrome is the caller's and duplicating the
accessible name into it is an SC 1.1.1 double-labelling problem the caller must
decide — so an exported diagram is unidentifiable outside its package. Adding
that band is the repo-owned step's job. Run it on every rendered or re-rendered
view:

```bash
${CLAUDE_SKILL_DIR}/references/scripts/svg-accessible-name.py \
  --title "<view label>" --desc "<the view's architecture question>" \
  <pkg>/generated/svg/<view-id>.svg
```

In Codex, replace `${CLAUDE_SKILL_DIR}` with the resolved absolute `<skill-dir>`.

The band is what the step contributes after the external runtime. It sits above the
diagram, added by expanding the `viewBox` upward; the step keeps the root
`width`/`height` in sync with it (so browsers do not letterbox the diagram) and
paints the band with the diagram's own background colour with a contrasting
title fill (so the title stays readable on a non-light render policy), both
derived from the diagram's background `<rect>`.

The step also sets that runtime-written `<title>` to the view label and ensures a
`<desc>` carrying the view's architecture question — normally the same text
`presentation` already produced. It does **not** synthesise a name: an artifact
arriving with none is refused with **exit 4** rather than banded, because a
banded artifact that still has no accessible name looks processed while failing
SC 1.1.1 — exactly the `ARCH-R-2` case. The supported input is a render from
Dediren `2026.07.28` or newer, which self-check verifies against the external
CLI; that floor gates the *render*
side only, so render output committed in an older era can still reach the step
and is what exit 4 is for. Generated output is recreated, not maintained, so the
remedy is a re-render.

It is an XML-aware transform — it parses the rendered `<svg>` with the
Python standard library and makes structural edits rather than string surgery on
markup — so its output is canonical SVG serialization (the committed rendered
evidence is in that form, and comparing a re-render is a post-step comparison,
not a raw-byte one); any XML-declaration prolog and trailing newline are
preserved verbatim. It edits generated render output only — never the upstream
bundle — is idempotent, and offers `--check` for verification: on a supported
render that verifies the runtime's name survived the step and the band was
added. Missing accessible-name markup or
a missing visible title on rendered evidence is `ARCH-R-2`.

Render-ready requires inspecting SVG for:

- nonblank content;
- coherent `viewBox`;
- expected `data-dediren-node-id` markers for visible nodes;
- expected `data-dediren-edge-id` markers for visible relationships;
- an accessible name: `role="img"` with a nonempty `<title>`, plus `<desc>`
  when the view declares its architecture question (post-render step above);
- a visible per-view title block so the artifact stays identifiable when
  embedded outside the package;
- a static render (render-mode check): no `<script>` element — renders are
  static-only since the runtime retired the interactive render policy, so an
  embedded script is `ARCH-R-5` plus a `Dediren tool issues` entry (runtimes
  ≤ 2026.07.0 scripted every SVG regardless of policy). Read the mode from
  artifact content — the render envelope discloses only `artifact_kind` — and
  report that verified static mode, never the policy intent, in the footer
  `Layout/render options` line (a misreport is `ARCH-R-5`);
- labels and markers that do not obscure the main architecture path;
- for a UML view, authored association end adornments carried by the view's
  render metadata (edge `properties.source_role` / `target_role` /
  `source_multiplicity` / `target_multiplicity`) each appearing as a rendered
  text label at its edge end. Count rendered vs. authored adornment values
  from the SVG and qualify the quality level with that coverage
  (output-format); a missing adornment is `ARCH-R-2` plus a `Dediren tool
  issues` entry. Never infer this coverage from `ok` envelopes — dediren
  ≤ 2026.07.0 dropped every end adornment between render metadata and SVG
  while all stages reported `status: ok` with empty diagnostics (fixed in
  2026.07.1), so a developer reading the diagram lost cardinality the model
  authored with no signal;
- element type distinguishable from the rendered shape, decorator, and fill
  without reading the `data-*` metadata, and relationship notation that matches
  ArchiMate® 3.2 — each relationship family a distinct line style and endpoint
  markers, not one collapsed solid line and filled arrow — with element-group
  and trust-boundary strokes meeting WCAG 2.2 SC 1.4.11 3:1 non-text contrast.
  The bundled `render-policy.json` fixtures are the reference policy: they carry
  a decorator and layer fill for every element type used and an edge style for
  all eleven relationship families. Where the runtime has no dotted line style,
  ArchiMate Access renders dashed and is not distinguished from Influence
  (disambiguated only by Influence's `+`/`-` label); disclose that under
  `Dediren tool issues`. Collapsed notation or a sub-3:1 boundary is `ARCH-R-*`;
- density, fanout, route span, group balance, and viewpoint focus that are
  acceptable for the audience;
- kind-specific structure that a clean `validate-layout` does not prove — for
  `uml-sequence`, each lifeline in a distinct column/stem and every message
  spanning its two lifelines (per the UML sequence notation reference).
  Superimposed participants are an `ARCH-R-*` defect; inspect the SVG structure
  independently, in addition to the self-check § Layout quality verdict (a
  `warning` status on the `dediren_build` view entry and the gate counts in its
  `.views[].diagnostics[]`).

### Relationship Connectors And Junctions

ArchiMate relationship connectors and junctions are valid ArchiMate concepts.
In this skill, relationship connectors and junctions are unsupported in
dediren package source until the runtime exposes first-class source, render,
and export support. Do not replace a connector or junction with an ordinary
element without disclosing the simplification and its effect on the model.

## 10. Optional OEF Export

OEF export exists for tool compatibility and external validation. It is useful
when the architect needs to import the model into a conformant ArchiMate tool or
when downstream validation evidence is part of the review.

Rules:

- Do not require export for normal source or SVG review.
- If export is requested, require `export-policy.json`.
- If export is requested, include `archimate-oef` in the package export path.
- Treat export failure as `ARCH-E-1`.
- Treat unresolved downstream validation evidence as `ARCH-E-2` unless a
  narrower model, view, layout, render, or quality code applies.
- Fix source and policy, then recreate export output.

### Whole-Model Interchange

The per-view export lane above stays the default: one export policy binds one
view, so a source with more views declares the omission through `info`
diagnostics (`DEDIREN_OEF_VIEWS_OMITTED` / `DEDIREN_XMI_ELEMENTS_OMITTED` /
`DEDIREN_XMI_RELATIONSHIPS_OMITTED`) and coverage is disclosed as e.g. `OEF ready
(1 of 2 views)` (`references/procedures/external-validation-handoff.md`).

Alongside it, a build additionally emits one whole-model interchange document per
requested notation. `dediren_build` with an `oef_policy` also writes
`model.oef.xml` at the out-root (every built view in one OEF document);
`dediren_build` with an `xmi_policy` also writes `model.uml.xml` (one `uml:Model`
plus OMG UMLDI diagrams). These whole-model documents are complete across the
built views and carry **no** omission diagnostic — they coexist with, and do not
replace, the per-view exports. The build-result lists them under its
`model_artifacts[]` array.

The UMLDI diagram content in `model.uml.xml` is emitted only for
classifier-diagram views (`uml-class` / `uml-data`) and is **provisional** —
unverified against real UML importers — so treat that diagram interchange as
best-effort and keep the per-view `uml-xmi` export the schema-validatable
evidence (`references/procedures/external-validation-handoff.md`).

OEF and XMI export policies also gain an optional per-view identity `views` map:
OEF takes `view_identifier` / `view_name` / `viewpoint`, XMI takes
`diagram_identifier` / `diagram_name`, so an exported view can carry a stable
identifier and human name into the interchange document.

## 11. Customization Profile

Customization profile support is implementation-defined in this skill. The
profile, attribute, and specialization choices must be documented in package
properties or render/export policy before claiming customization support. If
the package uses custom properties only as local annotations, report them as
local metadata rather than as an ArchiMate customization profile.

## 12. Finding Taxonomy

The active finding namespaces are:

- `ARCH-M-*`: model/source/relationship correctness.
- `ARCH-V-*`: view projection, view membership, and diagram-kind fit.
- `ARCH-L-*`: layout command and layout validation evidence.
- `ARCH-R-*`: SVG render command and rendered artifact quality.
- `ARCH-X-*`: extraction, drift, and cross-package identity evidence.
- `ARCH-E-*`: optional OEF export and downstream validation evidence.
- `ARCH-Q-*`: readiness, audience, and quality claims.

Use the narrowest code from
[../../skills/architecture-design/references/smell-catalog.md](../../skills/architecture-design/references/smell-catalog.md).
Do not claim `review-ready` while any blocking finding remains.

## 13. Package Review Checklist

For each package:

1. Confirm `package.json` points to existing source, policies, metadata, and
   actual views.
2. Confirm every view has a clear architecture question.
3. Validate `model.json`.
4. Build the package through the MCP adapter (one `dediren_build` call with
   absolute `workspaceRoot` and relative `package`), which projects, lays out, layout-validates,
   renders, and — when requested — exports every actual view in that one call,
   writing each artifact to its declared path; verify each
   `generated/render-metadata/<view>.json` `semantic_profile` matches its render
   policy. Read the `package-build-result` per-view and per-export entries to
   isolate a failing lane.
5. Run the accessible-name post-render step (§9) on each rendered view.
6. Inspect SVG for nonblank, marker-rich, accessible-named, visually readable
   output.
7. Include the optional OEF/XMI export lane (`oef_policy` / `xmi_policy`) only
   when requested.
8. Run drift detection only when source comparison is requested.
9. Report quality level, export readiness, evidence, missing diagram kinds,
   and findings.

## 14. Modeling Pitfalls

- Layer soup: mixing Business, Application, Technology, Motivation, and
  Strategy without one view concern.
- Inventory view: listing discovered components without an architecture
  question.
- Missing realization chain: service names without the elements that realize
  them.
- API or GUI access surface modeled as an Application Service instead of an
  Application Interface.
- Application Component realizes an Application Interface when the intended
  claim is component-interface ownership.
- Process sequence shown with Serving where Triggering is the architectural
  claim.
- Unfocused view: no declared concern or inconsistent element and relationship
  vocabulary.
- Invisible identity or access path for security-sensitive data resources.
- Association overuse where a typed relationship is available.
- Process thinness: no trigger, flow, participant, object, or outcome.
- Fictitious migration: Plateaus without evidence or architect intent.
- Export-first editing: changing compatibility output instead of package
  source.
- Placeholder coverage: adding empty view definitions for missing diagram
  kinds.

Report these with `ARCH-*` findings and concrete repair actions.

## 15. Cross-Package Identity And Landscape

One package per feature keeps each model focused, but a repository with
several packages describes shared elements more than once: the same
application component, service, or node appears in multiple feature packages.
Without an identity convention those copies fragment into disconnected models.
This section is the repo-owned convention for holding them together; the
dediren runtime is per-package and enforces none of it.

### Element Identity Across Packages

Two elements in different packages are claims about the same real-world thing
only when they share an identity:

- Prefer reusing the same element id across packages when authoring a shared
  element (`svc-orders` in every package that models the orders service).
- When local ids have already diverged and renaming would churn history, set
  the canonical `properties.identity` key (§3) on each element to the same
  repo-stable slug (for example `app.orders-service`). An explicit `identity`
  value is the authoritative link and wins over id equality.
- Identity slugs are repo-scoped and stable across package renames. Never
  reuse a slug for a different real-world thing.

Matching labels or types alone assert nothing; cross-package review treats
them only as fragmentation candidates.

Linked elements must agree on the ArchiMate type (or a disclosed
specialization) and must not carry contradictory labels or evidence claims.
Feature packages may still show different subsets of a shared element's
relationships and properties; a subset is not a conflict.

### Landscape Package

When shared elements span two or more feature packages, keep the portfolio
rollup as a landscape package at:

```
docs/architecture/landscape.dediren/
```

The landscape package is an ordinary dediren package (§1, §3): same file
layout, same validation gates, same render evidence. Its views answer
portfolio questions — which applications exist, how they cooperate across
features, which technology hosts them — rather than one feature's question.
Landscape elements carry the same shared ids or `identity` slugs as their
feature-package counterparts, and their `properties.source` may cite the
member packages that elaborate them.

Landscape content is architect-owned overlay by default (§8; drift-detection
scope limits): rolling feature models up into a portfolio claim is an
architectural act, not extraction. Do not generate the landscape mechanically
from feature packages, and do not add one before at least two packages share
elements.

### Cross-Package Consistency Review

Cross-package consistency is a Review leg; the procedure lives in
[drift-detection.md § Cross-Package Consistency](../../skills/architecture-design/references/procedures/drift-detection.md#cross-package-consistency).
Run it when Review scope spans more than one package, includes the landscape
package, or edits an element shared with a sibling package. An identity
conflict is `ARCH-X-5`; an unlinked likely-duplicate or a landscape rollup gap
is `ARCH-X-6`.

A repository that deliberately models a single feature needs none of this:
one package, no shared elements. Disclose `single package` in the footer
`Cross-package identity` line and continue.
