# Architecture Design Reference

This reference defines the modeling rules for the `architecture-design` skill.
The skill uses ArchiMate® 3.2 concepts and stores agent-editable architecture
source as dediren packages.

## 1. Operating Contract

The canonical source for a feature architecture is:

```
docs/architecture/<feature>.dediren/
  project.json
  model.json
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

`project.json` lists only actual views. Missing supported diagram kinds are
reported in the footer; they are not added as placeholders.

## 2. Quality Levels

- `source-valid`: `model.json` passes schema validation, ids are unique,
  relationships resolve, and the assessed ArchiMate relationships have passed
  schema validation plus ArchiMate semantic validation with
  `dediren validate --plugin generic-graph --profile archimate`.
- `view-readable`: source-valid plus every actual view in `project.json`
  projects, lays out, and layout-validates. This proves layout validity, not
  visual cleanliness.
- `render-ready`: view-readable plus SVG render evidence exists for changed or
  requested views, the artifact is nonblank, framed, carries dediren node/edge
  markers, and visual-readiness has been inspected for density, framing, label
  risk, and audience fit.
- `review-ready`: render-ready plus no blocking `ARCH-*` finding remains for
  the audience, diagram kind, and change scope.

The package rollup is the weakest applicable level across actual views.

## 3. Dediren Package Source

`model.json` contains nodes, relationships, source evidence, and plugin-owned
metadata. A node needs a stable id, ArchiMate type, human label, and enough
properties or documentation to explain why it belongs in the package. A
relationship needs a stable id, type, source id, target id, and optional label
or documentation.

Stable ids matter. Preserve existing ids unless they are duplicate, misleading,
or tied to removed source evidence. Labels can be human-friendly; id and label
must not contradict each other semantically.

`project.json` binds actual views to projection, per-view render metadata,
layout, render, and optional export policy. A view must answer a clear
architecture question and should carry the smallest set of elements and
relationships needed to answer it.

`render-policy.json` and `render-metadata.json` control SVG style and semantic
markers. Render metadata must let reviewers map visible SVG nodes and edges back
to source ids.

`export-policy.json` is required only when OEF export is requested. When export
fails, fix package source or export policy first, then recreate output.

For ArchiMate SVG policy with generated per-view render metadata, set
`plugins.generic-graph.semantic_profile` to `archimate` in `model.json`. With
the bundled dediren 0.9.0 runtime, generated ArchiMate render metadata no
longer depends on the `archimate-oef` export plugin.

### Package JSON Generation

Start clean-slate packages from the fixture under
`skills/architecture-design/references/fixtures/dediren/basic/`, then replace
ids, labels, model content, view definitions, and policies with the project
architecture.

For ArchiMate packages that render with generated per-view metadata and an
ArchiMate SVG policy, include `generic-graph` in `model.json.required_plugins`
and set `plugins.generic-graph.semantic_profile` to `archimate`. Add
`archimate-oef` only when the package needs OEF export.

Treat these files as hand-authored and checked in: `model.json`,
`project.json`, `render-policy.json`, package-level `render-metadata.json` when
the package intentionally keeps one shared semantic metadata file, and optional
`export-policy.json`. Treat `generated/` as reproducible output: projections,
per-view render metadata, layout results, SVG, and optional OEF intermediates
stay ignored unless the owning repository deliberately commits selected render
evidence elsewhere.

For each actual view in `project.json`, define the projection target for
layout, the render-metadata target, the layout output, and the render output:

```json
{
  "id": "main",
  "projection": { "plugin": "generic-graph", "target": "layout-request" },
  "metadata": {
    "plugin": "generic-graph",
    "target": "render-metadata",
    "output": "generated/render-metadata/main.json"
  },
  "layout": { "plugin": "elk-layout", "output": "generated/layout/main.json" },
  "render": {
    "plugin": "svg-render",
    "policy": "render-policy.json",
    "metadata": "generated/render-metadata/main.json",
    "output": "generated/svg/main.svg"
  }
}
```

Use the package-level `render-metadata.json` only when a repository chooses a
checked-in shared metadata policy/cache and can keep it synchronized with the
views. Otherwise render with the generated per-view metadata declared in the
view's `metadata.output`, after confirming the generated metadata profile
matches the render policy profile.

## 4. ArchiMate Layers And Aspects

ArchiMate separates architecture content by layer and aspect. Do not collapse
these distinctions for convenience.

Primary layers:

- **Strategy**: Capability, Resource, Course of Action, Value Stream.
- **Business**: Actor, Role, Collaboration, Interface, Process, Function,
  Interaction, Event, Service, Object, Contract, Representation, Product.
- **Application**: Component, Collaboration, Interface, Function, Interaction,
  Process, Event, Service, Data Object.
- **Technology**: Node, Device, System Software, Technology Collaboration,
  Technology Interface, Technology Function, Technology Process, Technology
  Interaction, Technology Event, Technology Service, Artifact, Communication
  Network, Path.
- **Physical**: Equipment, Facility, Distribution Network, Material.
- **Motivation**: Stakeholder, Driver, Assessment, Goal, Outcome, Principle,
  Requirement, Constraint, Meaning, Value.
- **Implementation & Migration**: Work Package, Deliverable, Implementation
  Event, Plateau, Gap.

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

- **Composition**: whole/part with lifecycle-strength ownership.
- **Aggregation**: whole/part with weaker ownership.
- **Assignment**: active structure performs behavior, or behavior uses active
  structure as its performer.
- **Realization**: concrete element fulfills a more abstract service,
  requirement, capability, or deliverable.
- **Serving**: source provides behavior or service used by target.
- **Access**: behavior reads, writes, or otherwise accesses passive structure.
- **Influence**: Motivation element affects another Motivation or architecture
  element.
- **Triggering**: temporal or causal start of another behavior.
- **Flow**: transfer of information, goods, or value between behaviors or
  active structures.
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

Endpoint legality belongs to `validate --plugin generic-graph --profile
archimate`, not local guesswork. If validation accepts Application Component to
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
the resulting view as an actual view in `project.json`; do not create empty
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
- `ARCH-R-3` for labels, icons, or markers that obscure the primary message;
- `ARCH-Q-2` for hub fanout, mixed audience concerns, or multiple viewpoint
  concerns in one diagram.

Prefer splitting dense views into narrower concerns. Process views should stay
linear when the story is linear. Service-realization views should keep the
realization path easy to follow. Technology-usage views should split hosting,
data, identity/security, and observability when one view cannot carry all of
them. Migration views should prefer stages or lanes over a generic wide graph
when the work sequence is the message.

## 8. Extraction And Source Evidence

Extract only facts that source can support.

Common extractable sources:

- .NET projects, references, public clients, hosted services, and durable
  orchestrators;
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
workflow sources only as candidates with source path, symbol/workflow name,
confidence, and unresolved questions. Missing evidence is `ARCH-X-2`.

Extracted views should use source-backed groups when source structure supports
ownership, hosting, trust, environment, dependency, system responsibility, or
orchestration boundaries. In dediren source, put groups in `model.json` under
`plugins.generic-graph.views[].groups`, not `project.json`: each group needs a
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

## 9. Runtime Evidence

The skill uses the repo-bundled dediren executable directly. Select the first
available bundle:

1. `souroldgeezer-architecture/tools/dediren-linux/bin/dediren`
2. `souroldgeezer-architecture/tools/dediren-macos/bin/dediren`

The bundled dediren 0.9.0 runtime is the current evidence baseline. Its
ArchiMate® render and export paths enforce ArchiMate® 3.2 relationship endpoint
legality, use the technology element name `Node`, not `TechnologyNode`, and
layout validation can report route detours plus close parallel route channels.
It also supports explicit `generic-graph` semantic profiles for generated
ArchiMate render metadata without requiring `archimate-oef`, semantic-backed
group projection/export, improved grouped cross-route validation, and parallel
per-view ELK layout. Keep serial rerun only as a diagnostic fallback when a
parallel batch produces an error envelope or other parallel-only failure.

The packaged bundle under `souroldgeezer-architecture/tools/dediren-linux/` is
an imported upstream Dediren distribution artifact. Do not patch bundled
schemas, plugin manifests, binaries, Java helpers, fixtures, or `bundle.json`
in this repository to fix tool behavior. When the runtime, schema, layout,
render, export, or helper behavior appears wrong, report it under `Dediren tool
issues` with the bundle version, command, input summary, error envelope,
expected behavior, and minimal repro evidence. Change only repo-owned skill,
fixture, or documentation guidance unless the task is explicitly to import a
new upstream Dediren release bundle; issue-filing mechanics belong in
agent-local configuration.

Evidence gates:

- Source schema: `validate`
- Source semantics: `validate --plugin generic-graph --profile archimate`
- View projection: `project`
- Per-view render metadata: `project --target render-metadata`
- Layout: `layout`
- Layout validation: `validate-layout`
- SVG render: `render`
- Optional OEF export: `export`

Each command returns an envelope. Error envelopes are findings and cap the
quality level at the highest stage already proven. Plain `dediren validate` is
schema validation only; use `validate --plugin generic-graph --profile
archimate` before claiming ArchiMate semantic source validity. Projection,
layout, render, and optional export remain downstream evidence gates.

For ArchiMate SVG render policy, treat a generated render-metadata profile
mismatch as a package or policy defect until proven otherwise. Check
`plugins.generic-graph.semantic_profile`, the generated metadata
`semantic_profile`, and `render-policy.json` before reporting a runtime issue.

Per-view `layout --plugin elk-layout` commands may run in parallel with the
bundled dediren 0.9.0 runtime. If a parallel batch fails, rerun the exact
failing layout inputs serially before reporting `ARCH-L-1`; disclose repeated
parallel-only failures under `Dediren tool issues` with repro evidence and
reference the historical regression tracked in skills issue `#47`.

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

Render-ready requires inspecting SVG for:

- nonblank content;
- coherent `viewBox`;
- expected `data-dediren-node-id` markers for visible nodes;
- expected `data-dediren-edge-id` markers for visible relationships;
- labels and markers that do not obscure the main architecture path;
- density, fanout, route span, group balance, and viewpoint focus that are
  acceptable for the audience.

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
- `ARCH-X-*`: extraction and drift evidence.
- `ARCH-E-*`: optional OEF export and downstream validation evidence.
- `ARCH-Q-*`: readiness, audience, and quality claims.

Use the narrowest code from
[../../skills/architecture-design/references/smell-catalog.md](../../skills/architecture-design/references/smell-catalog.md).
Do not claim `review-ready` while any blocking finding remains.

## 13. Package Review Checklist

For each package:

1. Confirm `project.json` points to existing source, policies, metadata, and
   actual views.
2. Confirm every view has a clear architecture question.
3. Validate `model.json`.
4. Project each actual view through its configured plugin and target.
5. Project render metadata for each actual view when the render step depends
   on semantic node or edge metadata; verify the generated metadata
   `semantic_profile` matches the render policy.
6. Run ELK layout for changed or requested views; parallel per-view layout is
   allowed with dediren 0.9.0, but rerun any parallel failure serially before
   reporting it as a layout defect.
7. Render SVG for changed or requested views.
8. Inspect SVG for nonblank, marker-rich, visually readable output.
9. Run optional export only when requested.
10. Run drift detection only when source comparison is requested.
11. Report quality level, export readiness, evidence, missing diagram kinds,
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
