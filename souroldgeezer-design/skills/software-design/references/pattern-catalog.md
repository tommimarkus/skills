# Software Design Pattern Catalog

Load only for named-pattern questions or visible ceremony. Output: `Force`,
`Fit`, `Avoid case`, `Smell prevented`, `Smell introduced`, `Validation`.
Reject shopping, imagined variation, pass-through wrappers, hidden ownership,
and migrations lacking an Exit condition. In Lookup, cite core reference `§6`
(Patterns).

| Pattern | Current force | Sustainable lift | Misuse guardrail | Track record |
|---|---|---|---|---|
| Anti-Corruption Layer / Adapter | Leaky external vocabulary. | Translate boundary. | Reject wrapper. | DDD; Fowler; cloud catalogs. |
| Strategy / Policy Object | Rules vary now. | Local policy. | Reject one implementation. | GoF; domain practice. |
| Composition Root / Dependency Injection / Factory | Wiring varies. | Visible owner. | Edge only. | GoF Factory; DI. |
| Facade | Noisy subsystem. | Stable surface. | Reject rename. | GoF; SDKs. |
| State Machine | Legal transitions matter. | Reviewable states. | Reject status field. | GoF; workflows. |
| Pipes and Filters / Pipeline | Recurring ordered transforms. | Step contracts. | Require schemas/failures. | POSA; EIP; cloud catalogs. |
| Publish-Subscribe / Observer / Domain Events | Multiple consumers. | Decouple producer/consumer. | Reject one call. | GoF; EIP; cloud catalogs. |
| Domain Model / Aggregate | Invariants matter. | Rules with model. | Reject CRUD record. | PoEAA; DDD. |
| Repository + Unit of Work | Real persistence/transaction boundary. | Domain/data split. | Reject ORM CRUD wrapper. | PoEAA; high misuse risk. |
| Strangler Fig / Branch by Abstraction | Replace while shipping. | Incremental migration. | Require Exit condition. | Fowler; AWS guidance. |
| Parallel Change / Expand-Contract | Backward-incompatible interface change while shipping. | Safe expand, migrate, contract. | Require the removal (Exit) step; reject a permanent dual interface. | Kerievsky; Fowler; Continuous Delivery. |
