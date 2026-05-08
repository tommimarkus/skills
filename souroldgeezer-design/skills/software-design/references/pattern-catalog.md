# Software Design Pattern Catalog

Load this catalog only when the user asks about design patterns, proposes a
named pattern, or source shows pattern ceremony whose fit must be judged. This
is a compact decision aid; rely on the base model for generic pattern mechanics
and on the core reference for design-health rules.

## Lean Selection Gate

Before recommending, accepting, or rejecting a pattern, answer:

1. What current value or change force is present now?
2. What volatility, semantic boundary, or propagation cost does the pattern
   reduce?
3. What simpler shape was rejected, and why is it insufficient?
4. Which smell family does the pattern reduce, and which might it introduce?
5. What is the cheapest evidence layer that can validate the decision?

Default to no named pattern when direct code, deletion, or narrowing solves the
known problem with less propagation cost. Pattern names are tradeoff vocabulary,
not authority.

## Force Matrix

| Force | Candidate patterns | Use when | Avoid when | Reduces | May introduce | Cheapest evidence |
|---|---|---|---|---|---|---|
| Boundary and translation | Adapter, Facade, Anti-Corruption Boundary, Mapper | External, legacy, transport, vendor, or partner vocabulary must not leak into the owning module. | A wrapper only renames calls or both sides are one owned concept. | `SD-B-*`, `SD-S-*`, `SD-C-*` | pass-through layer, mapping drift, hidden coupling | `[static]` vocabulary and dependency inspection; `[human]` for domain meaning |
| Variation and policy selection | Strategy, Policy Object, Specification | Multiple current algorithms, policies, or predicates vary behind one stable decision point. | There is one implementation, a small readable conditional, or imagined future variation only. | `SD-B-*`, `SD-C-*`, `SD-S-*` | class proliferation, tiny-object ceremony, storage leakage | `[static]` implementations and call sites; `[history]` for churn |
| Workflow and orchestration | Pipeline, Chain of Responsibility, State Machine, Saga / Process Manager | Workflow order, handoff contracts, transitions, fallback, compensation, or cross-boundary progress ownership are real design forces. | Direct sequence, dispatch table, status enum, or local transaction is clearer. | `SD-B-*`, `SD-C-*`, `SD-E-*` | hidden order, swallowed failures, distributed state complexity | `[static]` contracts and stop semantics; `[runtime]` for delivery/retry claims |
| Creation and composition | Factory Method, Abstract Factory, Builder, Composition Root | Creation varies, product families vary together, object construction hides invariants, or wiring needs one explicit edge. | Direct construction is stable or the abstraction exists for tests/future variation only. | `SD-C-*`, `SD-B-*`, `SD-S-*` | hierarchy ceremony, mutable half-built state, hidden dependencies | `[static]` creation sites and dependency resolution |
| Collaboration and events | Observer, Domain Events, Message Bus | Multiple current consumers or modules need decoupled notification with explicit contracts. | One direct local call satisfies the current force. | `SD-C-*`, `SD-B-*`, `SD-E-*` | temporal coupling, schema drift, operational complexity | `[static]` contract ownership; `[runtime]` for async delivery claims |
| Persistence and domain shape | Repository, Unit Of Work, Aggregate, Shared Kernel | Persistence, transactions, invariants, or shared vocabulary are real owned boundaries. | The layer repeats ORM CRUD, groups tables/screens, or creates shared code without ownership protocol. | `SD-C-*`, `SD-S-*`, `SD-B-*`, `SD-T-*` | pass-through ceremony, oversized aggregates, shared-core gravity | `[static]` leakage/invariants; `[human]` for shared ownership |
| Evolution | Strangler, Branch By Abstraction, Plugin / Extension Point | Replacement, temporary compatibility, or independent external implementers already exist. | Old/new paths have no removal condition or extension points predict imaginary implementers. | `SD-E-*`, `SD-C-*`, `SD-T-*` | permanent dual path, versioning burden, hidden runtime failures | `[static]` routing/removal path; `[history]` for migration progress |

## Pattern Review Output

For each named-pattern decision, report:

- `Force`: current evidence, not a forecast.
- `Fit`: why the pattern is cheaper than simpler code.
- `Avoid case`: when this exact pattern would be waste here.
- `Smell prevented`: one or two `SD-*` families.
- `Smell introduced`: one or two `SD-*` families.
- `Validation`: cheapest layer needed before treating it as justified.

## Fast Rejections

Reject or downgrade pattern ceremony when any of these are true:

- one implementation exists and no current boundary or volatility force is
  present;
- a generic interface/base/repository/bus/mediator/shared-kernel/plugin layer
  only predicts future needs;
- a wrapper passes data through without translation, protection, or ownership;
- a migration pattern lacks an exit condition;
- an event/message pattern hides a direct local call without clarifying
  consistency, failure, or ownership.
