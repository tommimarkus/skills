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
  render-metadata.json
  export-policy.json        # optional compatibility export policy
  generated/                # reproducible output, ignored by default
```

Agents edit package source and policies. Generated layout, SVG, and optional
export files can be recreated from the package. SVG render output is the primary
visual proof for review. OEF export is optional compatibility output for
conformant tools and is not the source of truth.

`project.json` lists only actual views. Missing supported diagram kinds are
reported in the footer; they are not added as placeholders.

## 2. Quality Levels

- `source-valid`: `model.json` validates, ids are unique, relationships resolve,
  and relationship types are legal for their source and target element types.
- `view-readable`: source-valid plus every actual view in `project.json`
  projects, lays out, and layout-validates.
- `render-ready`: view-readable plus SVG render evidence exists for changed or
  requested views and the artifact is nonblank, framed, and carries dediren
  node/edge markers.
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

`project.json` binds actual views to projection, layout, render, and optional
export policy. A view must answer a clear architecture question and should carry
the smallest set of elements and relationships needed to answer it.

`render-policy.json` and `render-metadata.json` control SVG style and semantic
markers. Render metadata must let reviewers map visible SVG nodes and edges back
to source ids.

`export-policy.json` is required only when OEF export is requested. When export
fails, fix package source or export policy first, then recreate output.

## 4. ArchiMate Layers And Aspects

ArchiMate separates architecture content by layer and aspect. Do not collapse
these distinctions for convenience.

Primary layers:

- **Strategy**: Capability, Resource, Course of Action, Value Stream.
- **Business**: Actor, Role, Collaboration, Interface, Process, Function,
  Interaction, Event, Service, Object, Contract, Product.
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

Application Components must not realize Application Interfaces. In ArchiMate
3.2, an Application Component provides an Application Interface through
Composition. If a target modeling profile or future export consumer does not
support Composition, use Aggregation for the component-interface whole/part
relationship and disclose the profile decision in the footer.

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

The skill reports coverage for seven diagram kinds. The package may contain any
subset; missing kinds are disclosed, not stubbed.

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

Drift review compares source evidence in the package with current repo state.
When source and package disagree, report whether the likely action is to update
the package or update the source.

## 9. Runtime Evidence

The skill uses the repo-bundled dediren executable directly. Select the first
available bundle:

1. `souroldgeezer-architecture/tools/dediren-linux/bin/dediren`
2. `souroldgeezer-architecture/tools/dediren-macos/bin/dediren`

The bundled dediren 0.2.0 runtime is the current evidence baseline. Its
ArchiMate® render and export paths enforce ArchiMate® 3.2 relationship endpoint
legality, use the technology element name `Node`, not `TechnologyNode`, and
layout validation can report route detours plus close parallel route channels.

Evidence gates:

- Source: `validate`
- View projection: `project`
- Layout: `layout`
- Layout validation: `validate-layout`
- SVG render: `render`
- Optional OEF export: `export`

Each command returns an envelope. Error envelopes are findings and cap the
quality level at the highest stage already proven.

Dediren runtime validation is evidence, not the full ArchiMate review. If the
tool accepts a relationship type, source/target combination, export shape, or
layout artifact that the architecture review still rejects, report the
architecture finding normally and list the validator or renderer gap under
`Dediren tool issues` in the footer.

If grouped layout validation reports connector-through-node, invalid route, or
group-boundary warnings, rerun the same view without groups. If the ungrouped
layout validates cleaner, keep source-backed groups in `model.json`, use the
cleaner layout as evidence and report the grouped-layout regression with both
validation counts.

Render-ready requires inspecting SVG for:

- nonblank content;
- coherent `viewBox`;
- expected `data-dediren-node-id` markers for visible nodes;
- expected `data-dediren-edge-id` markers for visible relationships;
- labels and markers that do not obscure the main architecture path.

## 10. Optional OEF Export

OEF export exists for tool compatibility and external validation. It is useful
when the architect needs to import the model into a conformant ArchiMate tool or
when downstream validation evidence is part of the review.

Rules:

- Do not require export for normal source or SVG review.
- If export is requested, require `export-policy.json`.
- Treat export failure as `ARCH-E-1`.
- Treat unresolved downstream validation evidence as `ARCH-E-2` unless a
  narrower model, view, layout, render, or quality code applies.
- Fix source and policy, then recreate export output.

## 11. Finding Taxonomy

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

## 12. Package Review Checklist

For each package:

1. Confirm `project.json` points to existing source, policies, metadata, and
   actual views.
2. Confirm every view has a clear architecture question.
3. Validate `model.json`.
4. Project each actual view through its configured plugin and target.
5. Run layout and layout validation for changed or requested views.
6. Render SVG for changed or requested views.
7. Inspect SVG for nonblank, marker-rich, readable output.
8. Run optional export only when requested.
9. Run drift detection only when source comparison is requested.
10. Report quality level, export readiness, evidence, missing diagram kinds,
    and findings.

## 13. Modeling Pitfalls

- Layer soup: mixing Business, Application, Technology, Motivation, and
  Strategy without one view concern.
- Inventory view: listing discovered components without an architecture
  question.
- Missing realization chain: service names without the elements that realize
  them.
- API or GUI access surface modeled as an Application Service instead of an
  Application Interface.
- Application Component realizes an Application Interface instead of using the
  component-interface whole/part relationship.
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
