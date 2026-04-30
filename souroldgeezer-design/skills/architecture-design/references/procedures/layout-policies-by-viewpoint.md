# Layout policies by viewpoint

Viewpoint-specific visual grammar for architecture-design OEF views. Use this
after semantic model selection and before selecting a geometry backend or
fallback layout.

The goal is to answer the architecture question each viewpoint is meant to
answer. Generic layered layout is only a fallback for small directed stories,
not the default for every view.

| Viewpoint | Preferred policy | Avoid |
|---|---|---|
| Capability Map | Capability tile/decomposition map | Generic layered layout as primary policy |
| Application Cooperation | Cluster, hub, integration lanes | Random force-directed layout unless cluster story is explicit |
| Service Realization | Layered realization spine | Hiding the main realization chain |
| Technology Usage | Hosting/deployment stack | Generic layer/aspect rows when hosting is the point |
| Migration | Plateau/timeline layout | Treating dev/stage/prod topology as migration without intent |
| Motivation | Influence/traceability tree | Layer/aspect grid as default |
| Business Process Cooperation | Process-flow lanes, swimlanes, handoffs | Generic dependency layout |

## Capability Map

Question: What capabilities exist, how do they decompose, and where is
realization or investment relevant?

Policy:

- Use a tile/decomposition map.
- Place top-level Capabilities as uniform tiles in a row-major grid.
- Nest sub-Capabilities through Composition when the part-whole semantics are
  clear.
- Place Course of Action, Resource, or Business Service elements to the side
  only when they support the capability question.

Routing:

- Capability Composition/Aggregation edges may be represented by nesting.
- Realization edges from services, functions, resources, or courses of action
  remain visible when they are the view's realization evidence.

Acceptance:

- The view reads as a capability map, not an application inventory.
- Top-level capability boundaries are visually obvious.

## Application Cooperation

Question: How do application components, services, interfaces, and integration
boundaries cooperate?

Policy:

- Use clustered dependency or integration-lane layout.
- Use hub-and-spoke only when one Application Component dominates by degree
  (`degree(in)+degree(out)` materially exceeds peers).
- Put external components inside an external trust-boundary Grouping when
  present.
- Keep Application Services and Interfaces near the Components that expose or
  consume them.

Routing:

- Serving and Realization edges that explain cooperation stay visible.
- Composition edges used only for grouping may be hidden by nesting.
- Parallel integration lanes need explicit port/lane separation.

Acceptance:

- Collaboration boundaries, integration paths, and responsibility split are
  clear without verbal explanation.

## Service Realization

Question: What realizes the business or application service?

Policy:

- Use a layered realization spine.
- Keep the main Realization chain visible.
- Prefer top-down or left-to-right flow.
- Business service/process sits at the top or left.
- Application service/function/component sits in the middle.
- Technology nodes/artifacts sit below or right only when needed.
- Process-rooted modality includes the UI Application Component and Application
  Interface at the entry point when the paired process is user-driven.

Edge priority:

- Realization spine: `100`.
- Serving edges directly supporting the spine: `80`.
- Assignment/hosting edges: `60`.
- Associations and secondary context: `20`.

Do not hide:

- Main Realization edges.

May hide:

- Redundant Composition/Aggregation edges represented by valid nesting, if the
  visual story remains auditable.

Acceptance:

- A reviewer can audit the realization chain from business concern to
  application implementation, and to technology when in scope.

## Technology Usage

Question: What technology hosts or enables the application?

Policy:

- Use a hosting stack/tower.
- Preserve Application Component -> Technology Node hosting alignment.
- Place Application Components directly above their hosting Technology Nodes
  when possible.
- Route hosting Assignment vertically where possible.
- Put data-plane and observability resources in adjacent columns.
- Communication Network / Path elements may become horizontal bars when they
  explain connectivity.

Do not:

- Use generic layer rows when the hosting relationship is the point of the
  diagram.
- Hide data-plane or identity paths that carry the technology argument.

Acceptance:

- Hosting, runtime, data-plane, observability, and network/resource boundaries
  are visually distinguishable.

## Migration

Question: What changes from baseline through transition to target?

Policy:

- Use Plateau/timeline columns.
- Place Baseline, Transition, and Target Plateaus left to right.
- Place Gaps between Plateaus.
- Place Work Packages and Deliverables under the Plateau or transition they
  affect.
- Deployment Topology views use sibling environment Plateaus in a row or compact
  grid without Plateau-to-Plateau Triggering unless explicit migration intent
  exists.

Routing:

- True migration Gap/Triggering paths run horizontally between chronological
  Plateaus.
- Deployment topology Work Package Realization edges route into sibling
  Plateaus without implying one environment becomes another.

Acceptance:

- A planning reviewer can distinguish migration sequence from parallel
  deployment environments.

## Motivation

Question: Which stakeholders, drivers, goals, requirements, and constraints
influence the architecture?

Policy:

- Use an influence/traceability tree.
- Place Stakeholders and Drivers at the top.
- Cascade Goals, Outcomes, Requirements, Constraints, and Principles by
  Realization/Influence depth.
- Keep cross-cutting Influence edges visible but lower-priority than the main
  traceability chain.

Routing:

- Realization and Influence edges follow the tree direction.
- Association edges remain secondary.

Acceptance:

- Decisions and requirements trace back to motivation rather than floating as
  disconnected labels.

## Business Process Cooperation

Question: How do business processes, events, actors, and passive objects
cooperate over time?

Policy:

- Use flow, swimlane, or handoff layout.
- Behaviour elements flow left-to-right by Triggering / Flow.
- Active structure sits above the Behaviour lane.
- Passive structure sits below the Behaviour lane.
- Place actors/roles above the process they are assigned to.
- Place business objects below the process that accesses them.

Routing:

- Triggering / Flow edges use the process direction and should be straight when
  adjacent.
- Assignment and Access edges use short vertical routes.
- Handoffs and exceptions get separate lanes instead of crossing the main
  process chain.

Acceptance:

- The view shows trigger/flow, responsibilities, passive objects accessed, and
  terminal value outcome.

## Split-view triggers

Split a view instead of forcing layout when:

- the view exceeds `AD-L4` budget and no grouping preserves the question;
- two realization stories share little application, data, technology, security,
  deployment, UI-entry, or business semantics;
- process exceptions dominate the happy path;
- a capability tile map starts carrying application implementation details; or
- technology hosting and migration sequencing are both present but answer
  different reviewer questions.
