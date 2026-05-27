# Software Design Pattern Catalog

Load only for named-pattern questions or visible pattern ceremony. Use base
model knowledge for generic mechanics; use this file for the decision contract.

Before accepting/rejecting a pattern, answer: current force, volatility or
propagation cost reduced, simpler shape rejected, smell reduced/introduced, and
cheapest validation layer. Default to direct code, deletion, or narrower
boundaries when no current force exists.

| Force | Candidate patterns | Use when | Avoid when |
|---|---|---|---|
| Boundary/translation | Adapter, Facade, Anti-Corruption Boundary, Mapper | external/legacy/transport/vendor vocabulary must not leak | wrapper only renames calls |
| Variation/policy | Strategy, Policy Object, Specification | multiple current algorithms or predicates vary behind one decision | one implementation or small conditional |
| Workflow | Pipeline, Chain, State Machine, Saga | order, handoff, fallback, compensation, or progress ownership matters | direct sequence/status enum is clearer |
| Creation | Factory, Builder, Composition Root | creation varies or wiring needs one edge | direct construction is stable |
| Collaboration | Observer, Domain Events, Message Bus | multiple current consumers need explicit notification contracts | one direct local call works |
| Persistence/domain | Repository, Unit Of Work, Aggregate, Shared Kernel | transactions, invariants, or shared vocabulary are owned boundaries | CRUD wrapper or ownerless shared code |
| Evolution | Strangler, Branch By Abstraction, Plugin Point | replacement, compatibility, or external implementers already exist | no removal condition/current implementer |

Pattern output: `Force`, `Fit`, `Avoid case`, `Smell prevented`,
`Smell introduced`, `Validation`. Reject ceremony for one implementation,
imagined future variation, pass-through wrappers, exitless migrations, or event
layers that hide a direct call without clarifying consistency/failure/ownership.
