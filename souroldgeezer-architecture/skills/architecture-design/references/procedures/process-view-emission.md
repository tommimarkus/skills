# Process View Emission

Use when Build or Extract needs Business Process Cooperation or Service
Realization views.

## Business Process Cooperation

Create an actual view only when there are at least two process/event/interaction
elements or a process plus meaningful participant/object context. Show the
trigger or flow chain and the responsibilities needed to understand handoff.

## Service Realization

Create an actual view when a Business Process or Service needs traceability to
Application Services, Application Components, Technology services/nodes, data,
or identity controls. The view must show the primary realization chain.

## Consolidation

Avoid one near-duplicate drill-down per process when the application,
technology, data, security, deployment, and UI-entry story is the same. Reuse a
single view and document the covered process set.

## Findings

- Missing trigger/flow or participant context: `ARCH-V-2`.
- Missing realization chain: `ARCH-V-2`.
- Duplicate or over-dense process views: `ARCH-Q-2`.
