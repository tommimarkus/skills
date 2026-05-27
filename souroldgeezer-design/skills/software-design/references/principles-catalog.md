# Software Design Principle Catalog

Load only for named-principle/slogan questions. Require `Force`, `Rule`,
`Avoid`, `Smell +/-`, `Validation`; otherwise reject.

Acronyms: SOLID = responsibility, variation, contract, dependency. DRY =
knowledge. KISS/YAGNI = simple.

| Principle | Force -> rule | Avoid | Smell/evidence |
|---|---|---|---|
| Information hiding | Volatile detail leaks -> owner boundary. | Empty wrappers. | `SD-B/C/E` down, `SD-W` risk. |
| Coupling/cohesion | Change fans out -> fewer concepts/modules. | Incoherent splits. | `SD-C/B/E` down, `SD-T` risk. |
| Value/waste | Speculative hooks/frameworks -> smallest coherent move. | Ignoring known volatility. | `SD-W` down, `SD-E/Q` risk. |
| Semantic coherence | Duplicate/external models -> one meaning plus translation. | Default DDD ceremony. | `SD-S/B` down, `SD-W` risk. |
| Stable policy | Mechanism owns policy -> depend toward policy. | Interface-per-class. | `SD-C/B` down, `SD-W` risk. |
| DRY ownership | Rule/invariant drifts -> one owner/source. | Shared core for unrelated contexts. | `SD-S/E/W` down, `SD-C/T` risk. |
| Evolution/tradeoff fit | Migration/quality force -> step, exit, tactic, delegation. | Permanent flags or "improves everything." | `SD-E/Q` down, `SD-W` risk. |
