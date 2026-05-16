# Seed Views

Use when Build or Extract needs an initial package shape.

Seed diagram kinds are starter coverage, not the full ArchiMate viewpoint
mechanism. Add only actual views to `project.json`; missing kinds are footer
disclosure.

| Seed view | Concern | Typical elements | Typical relationships | Split trigger |
|---|---|---|---|---|
| Application Cooperation | Application collaboration and service/data dependencies | Application Component, Interface, Service, Data Object | Serving, Access, Composition, Realization, Flow | Hosting, identity, or data flow dominates |
| Technology Usage | Runtime and platform support for applications | Application Component, Node, System Software, Technology Service, Artifact | Serving, Assignment, Realization, Access | Hosting, data, identity/security, and observability compete |
| Service Realization | How a service is implemented | Service, Function, Process, Component, Node, Artifact | Realization, Assignment, Serving | Primary realization chain is hidden |
| Business Process Cooperation | Process handoff and participant context | Business Process candidate, Event, Interaction, Actor/Role when evidenced | Triggering, Flow, Assignment, Access | Single process has no handoff or participant context |
| Motivation | Why a change matters | Stakeholder, Driver, Goal, Outcome, Requirement, Constraint | Influence, Realization, Association | Source-code names are the only evidence |
| Migration | How work changes the landscape | Work Package, Deliverable, Implementation Event, Plateau, Gap | Triggering, Flow, Realization | Parallel environments lack state-transition evidence |
| Capability Map | Business capability context | Capability, Resource, Course of Action, Value Stream | Composition, Aggregation, Realization, Serving | Capability evidence is absent or only code naming |

Custom viewpoint path: define stakeholder concern, allowed element types,
allowed relationship types, audience, and quality target before editing source.
Each seed or custom view needs a clear question, necessary elements, primary
relationship path, and projection/layout/validation/SVG evidence before
`render-ready`.
