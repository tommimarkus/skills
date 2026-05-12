# Process View Emission

Use when Build or Extract needs Business Process Cooperation or Service
Realization views.

## Business Process Cooperation

Create only when there are at least two process/event/interaction elements or a
process plus meaningful participant/object context. Show trigger/flow and
handoff responsibilities.

## Service Realization

Create when a Business Process or Service needs traceability to application,
technology, data, or identity controls. Show the primary realization chain.

## Consolidation

Avoid near-duplicate drill-downs; reuse one view when app/tech/data/security/UI
story is the same and document the covered process set.

## Findings

- Missing trigger/flow or participant context: `ARCH-V-2`.
- Missing realization chain: `ARCH-V-2`.
- Duplicate or over-dense process views: `ARCH-Q-2`.
