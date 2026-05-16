# Process View Emission

Use when Build or Extract needs Business Process Cooperation, Application
Process, or Service Realization views.

## Decision Table

| Evidence | Emit | Reject |
|---|---|---|
| UI/API sequence with application-owned outcome and no business actor | Keep Application Process | Business Process Cooperation |
| At least two process/event/interaction elements or a process plus meaningful participant/object context | Emit Business Process Cooperation | Flat endpoint inventory |
| Business service or process needs traceability to app, technology, data, or identity controls | Emit Service Realization | Service name without realization chain |
| Several process drill-downs have the same app/tech/data/security/UI story | Consolidate duplicate process drill-downs | Near-duplicate views |
| Small linear process has no participant, responsibility, trust, or orchestration boundary change | Keep it ungrouped | Decorative groups |

## Business Process Cooperation

Show Triggering or Flow and handoff responsibilities. Keep source-lifted
business process content `candidate-from-source` until architect or stakeholder
confirmation exists.

## Service Realization

Show the primary realization chain from service to behavior, component, and
technology/data/identity controls when those controls are the concern.

## Findings

- Missing trigger/flow or participant context: `ARCH-V-2`.
- Missing realization chain: `ARCH-V-2`.
- Duplicate or over-dense process views: `ARCH-Q-2`.
