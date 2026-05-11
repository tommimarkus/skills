# Process Lifting Rules

Use when Extract sees backend workflows, orchestrators, Logic Apps, durable
functions, queue processors, or UI/API flows that imply Business Process
candidates.

## Candidate Rules

- Business Process, Event, and Interaction may be lifted only as candidates
  with source evidence and confidence.
- Business Actor, Role, Object, Contract, Product, Service, Function,
  Motivation, Strategy, and Physical content remain architect-owned unless
  explicitly supplied by the user.
- Do not turn every method or endpoint into a Business Process. Lift only
  end-to-end behavior that a stakeholder would recognize.

## Evidence

Record:

- source path and symbol/workflow name;
- trigger or entrypoint;
- completion or outcome;
- confidence level;
- unresolved architect questions.

Missing evidence is `ARCH-X-2`.

Use source-backed groups when related process steps share a participant,
orchestrator, queue, service boundary, or system responsibility. If the group
would only name a human theme inferred by the agent, leave it as architect-owned
intent instead.
