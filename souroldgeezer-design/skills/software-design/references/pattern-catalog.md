# Software Design Pattern Catalog

Load only for named-pattern questions or visible pattern ceremony. Use base
model knowledge for mechanics; use this file for fit/rejection.

Before accepting/rejecting a pattern, answer: Current force, simpler shape
rejected, smell prevented, smell introduced, and cheapest validation layer.
Default to no pattern when no current force exists.

## High-Impact Shortlist

Track record is supporting evidence only. Fit comes first.

| Pattern | Current force | Sustainable lift | Misuse guardrail | Track record |
|---|---|---|---|---|
| Anti-Corruption Layer / Adapter | External/legacy/vendor/generated vocabulary leaks. | Boundary translation. | Reject same-semantics wrappers. | DDD, cloud catalogs, Fowler. |
| Strategy / Policy Object | Current algorithms/rules vary. | Local policy. | Reject one implementation. | GoF, framework/domain practice. |
| Composition Root / Dependency Injection / Factory | Creation/lifetime/wiring varies. | Visible construction owner. | Keep at edge. | GoF Factory, DI guidance. |
| Facade | Subsystem is broad/noisy/unstable. | Stable caller surface. | Reject pass-through renames. | GoF, SDK boundaries. |
| State Machine | Transition/progress/failure legality matters. | Reviewable states. | Reject simple status. | GoF, workflow/protocol practice. |
| Pipes and Filters / Pipeline | Ordered transforms recur. | Step contracts and reuse. | Require schemas/failures. | POSA, EIP, cloud catalogs. |
| Publish-Subscribe / Observer / Domain Events | Multiple consumers need notification. | Producer/consumer decoupling. | Reject one direct call. | GoF, EIP, cloud catalogs. |
| Domain Model / Aggregate | Complex invariants own data and behavior. | Rules stay with model. | Reject CRUD records. | PoEAA, DDD. |
| Repository + Unit of Work | Persistence/query/transaction boundary is real. | Domain/data-map split. | Reject ORM CRUD wrappers. | PoEAA; high misuse risk. |
| Strangler Fig / Branch by Abstraction | Replace behavior while shipping. | Incremental migration. | Require Exit condition. | Fowler, AWS guidance. |

Pattern output: `Force`, `Fit`, `Avoid case`, `Smell prevented`, `Smell
introduced`, `Validation`. Reject pattern shopping, imagined future variation,
pass-through wrappers, exitless migrations, and event layers that hide a direct
call without clarifying consistency/failure/ownership.
