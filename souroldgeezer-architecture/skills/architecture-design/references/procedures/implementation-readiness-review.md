# Implementation-Readiness Review

Use this in Review mode when the user asks whether architecture docs are enough
as an implementation handoff, whether findings should be expected in
architecture docs, or whether a package can guide implementation without the
rest of the source material.

## Review Contract

Report:

- implementation-readiness verdict;
- evidence inventory for package source, actual views, validation, SVG render,
  optional export, and linked source evidence;
- architecture-documentation findings;
- other source material findings;
- skill/package issue classification: `Yes`, `Maybe`, or `No`;
- ArchiMate equivalence for each architecture-documentation finding;
- Implementation impact for each finding;
- recommendation that architecture docs link to implementation contracts instead
  of duplicating them.

Do not treat architecture docs as a complete implementation specification.
runtime/package readiness claims are separate from implementation-handoff
completeness claims.

## Finding Shape

For architecture-documentation findings, use this field order:

```text
Finding: KKW-ARCH-001 Product intent and stakeholder drivers are missing
Expected in architecture docs: This belongs in architecture because it defines product outcomes and stakeholder concerns.
Expected form: Capability Map, Motivation view, Strategy view, ADRs, and an open decision log.
ArchiMate equivalence: Direct for Capability, Stakeholder, Driver, Goal, Outcome, Requirement, Constraint, Principle, Resource, Course of Action, and Value Stream; ADRs and open decisions are companion text.
Architecture-design skill issue: No for source-only extract; Maybe for Review if the package claims implementation-handoff sufficiency without disclosing the gap.
Implementation impact: Implementers can copy structure but cannot know which outcomes the structure is meant to optimize.
```

## Architecture-Documentation Findings

Use these finding classes when implementation readiness is the question.

- Product intent and stakeholder drivers: Capability Map, Motivation, Strategy,
  stakeholders, drivers, goals, outcomes, requirements, constraints, principles,
  capabilities, resources, courses of action, and value streams are modelable.
  ADRs and open decision logs are companion text.
- Confirmed business process semantics: Business Actor, Business Role,
  Business Event, Business Process, Business Object, Outcome, Triggering, and
  Flow are modelable. Keep source-lifted process content as
  `candidate-from-source` until architect or stakeholder confirmation exists.
- Architecture-level API surface: Application Interface, Application Service,
  Application Component, external Application Service, Serving, Realization,
  and Flow are modelable. Full wire contracts, auth matrices, and OpenAPI
  details are companion material.
- Data ownership and lifecycle architecture: Data Object, Artifact,
  Application Service, Technology Node, Technology Service, Grouping, Access,
  Serving, Requirement, and Constraint are modelable. Retention, classification,
  cache cadence, and storage placement matrices are companion material.
- Security, identity, and trust boundaries: Application Interface, Application
  Service, Application Component, Technology Service, Node, Artifact, Serving,
  Access, Requirement, and Constraint are modelable. Trust boundaries are
  represented with Grouping, environment/location grouping, labels, or view
  grouping rather than a dedicated ArchiMate element.
- Deployable environment architecture: Technology Usage, Deployment, Node,
  System Software, Technology Service, Artifact, Communication Network,
  Location, Plateau, Work Package, Serving, Assignment, Access, and Triggering
  cover topology and environment shape. SKU, region, lock, diagnostic, and
  workflow variable details are companion material.
- Operational architecture and acceptance gates: Work Package, Deliverable,
  Implementation Event, Plateau, Gap, Technology Service, Application Service,
  Triggering, Realization, Serving, and Access can represent release and
  operational shape. Runbook procedures, exact commands, and evidence-source
  tables are companion operational documentation.

## Other Source Material

Route these out of architecture-design findings unless the package claimed to
contain the implementation detail:

- exact API request, response, status, and problem shapes;
- persistence schemas, indexes, TTL, partition keys, and queries;
- concrete UI layout, component composition, browser states, copy,
  accessibility, localization, and performance behavior;
- OAuth callback code, cookie/token/session mechanics, retries, CORS, and
  framework integration;
- Bicep parameter names, GitHub variables, workflow expressions, and
  deploy-time values;
- exact verification commands, fixtures, test data, and CI job mechanics;
- class design, dependency injection, repository abstractions, mappers,
  algorithms, caching, and retry internals.

## Code Routing

- Use `ARCH-Q-3` when implementation-readiness claims exceed evidence.
- Use `ARCH-X-2` when required architecture evidence is absent.
- Use `ARCH-V-4` when a supported diagram kind is intentionally absent and
  should be disclosed rather than stubbed.
- Use `ARCH-V-3` or `ARCH-Q-2` when a view mixes concerns or cannot answer the
  handoff question.
- Use `ARCH-M-4` when architect-owned content is presented as extracted fact.

Do not report source-material gaps as architecture-design defects unless the
architecture package claimed to contain that implementation detail.
