# Process Lifting Rules

Use when Extract sees workflows, orchestrators, queue processors, or UI/API
flows that imply process candidates. Load `../source-weighting.md` for
ambiguous source-to-ArchiMate choices.

## Candidate Rules

| Source evidence | Prefer | Avoid |
|---|---|---|
| UI/API sequence with application-owned outcome | UI/API sequence can be Application Process by default | Business Process without business ownership/outcome confirmation |
| Source-backed workflow with participant, business outcome, or stakeholder confirmation | Business Process stays candidate until confirmed | Final Business Process from method names alone |
| Timers, callbacks, messages, webhooks, deploy/release occurrences | Timers, callbacks, messages, and deploy/release occurrences are events | Process if the evidence only proves a state change |
| Queue/orchestrator/service responsibility | Source-backed groups for participant, system responsibility, trust, or orchestration boundaries | Inferred human role names from technical labels |
| Small linear process | A small linear process should remain ungrouped unless participant, responsibility, trust, or orchestration boundaries change the reading | Decorative grouping |

Business Actor, Role, Object, Contract, Product, Service, Function, Motivation,
Strategy, and Physical remain architect-owned unless supplied.

## Evidence

Record source path, symbol/workflow, trigger/entrypoint, outcome, confidence,
and unresolved architect questions. Missing evidence is `ARCH-X-2`.

Use source-backed groups for shared participant, orchestrator, queue, service
boundary, or system responsibility. Inferred human themes stay architect-owned.

Do not add groups to small linear process views unless a participant, system
responsibility, trust boundary, or orchestration boundary changes the
architectural reading.
