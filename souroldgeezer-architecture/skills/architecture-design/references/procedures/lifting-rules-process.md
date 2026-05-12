# Process Lifting Rules

Use when Extract sees workflows, orchestrators, queue processors, or UI/API
flows that imply Business Process candidates.

## Candidate Rules

- Lift Business Process/Event/Interaction only as evidenced candidates.
- Business Actor, Role, Object, Contract, Product, Service, Function,
  Motivation, Strategy, and Physical remain architect-owned unless supplied.
- Do not turn every method or endpoint into a Business Process.

## Evidence

Record source path, symbol/workflow, trigger/entrypoint, outcome, confidence,
and unresolved architect questions. Missing evidence is `ARCH-X-2`.

Use source-backed groups for shared participant, orchestrator, queue, service
boundary, or system responsibility. Inferred human themes stay architect-owned.

Do not add groups to small linear process views unless a participant, system
responsibility, trust boundary, or orchestration boundary changes the
architectural reading.
