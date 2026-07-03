# Software Design Principle Catalog

Load only for named-principle/slogan questions. Require `Force`, `Rule`,
`Avoid`, `Smell +/-`, `Validation`; otherwise reject. In Lookup, cite the
row's `Cite` section of the core reference.

Acronyms: SOLID = responsibility, variation, contract, dependency. DRY =
knowledge. KISS/YAGNI = simple.

| Principle | Force -> rule | Avoid | Smell/evidence | Cite |
|---|---|---|---|---|
| Information hiding | Volatile detail leaks -> owner boundary. | Empty wrappers. | `SD-B/C/E` down, `SD-W` risk. | §3.2 |
| Coupling/cohesion | Change fans out -> fewer concepts/modules. | Incoherent splits. | `SD-C/B/E` down, `SD-T` risk. | §3.4 |
| Value/waste | Speculative hooks/frameworks -> smallest coherent move. | Ignoring known volatility. | `SD-W` down, `SD-E/Q` risk. | §3.1 |
| Semantic coherence | Duplicate/external models -> one meaning plus translation. | Default DDD ceremony. | `SD-S/B` down, `SD-W` risk. | §3.3 |
| Stable policy | Mechanism owns policy -> depend toward policy. | Interface-per-class. | `SD-C/B` down, `SD-W` risk. | §4 |
| DRY ownership | Rule/invariant drifts -> one owner/source. | Shared core for unrelated contexts. | `SD-S/E/W` down, `SD-C/T` risk. | §3.3, §4 |
| Evolution/tradeoff fit | Migration/quality force -> step, exit, tactic, delegation. | Permanent flags or "improves everything." | `SD-E/Q` down, `SD-W` risk. | §3.5, §3.6 |
