# Software Design Pattern Catalog

Load this catalog when the user asks about design patterns, proposes a named
pattern, or code shows pattern ceremony whose fit must be judged. Use it as
on-demand support for `software-design`; it does not replace the core reference
or stack extensions.

## Lean Selection Rules

1. Start from current value and one concrete change force.
2. Prefer deletion, narrowing, or direct code when a pattern does not localize a
   real volatility point.
3. Use a pattern to hide a likely-changing decision, translate across a real
   boundary, or constrain propagation cost.
4. Reject pattern use that only predicts imagined variation.
5. State the exit condition for transitional patterns such as strangler, branch
   by abstraction, or compatibility adapters.
6. Treat pattern names as vocabulary for tradeoffs, not authority.

For every pattern recommendation, report the force, fit, avoid case, likely
smell prevented, likely smell introduced, and cheapest validation layer.

## Boundary And Translation

### Adapter

- Use when: an external API, library, transport, file format, or partner model
  must not define the owning module's vocabulary.
- Avoid when: the wrapper only renames calls without hiding volatility or
  translating semantics.
- Responsibilities: adapter owns translation and external mechanics; policy
  stays inside the owning boundary.
- Dependencies: policy may depend on a narrow port or stable contract; adapter
  depends outward on the external mechanism.
- Smells prevented: `SD-B-*` boundary leakage, `SD-S-*` semantic drift,
  `SD-C-*` outward policy dependency.
- Smells introduced: pass-through wrapper waste, duplicated model drift, hidden
  error semantics.
- Validation: `[static]` call graph and model vocabulary; `[runtime]` only for
  claims about external failure behavior or latency.

### Facade

- Use when: several lower-level subsystems need one stable operation boundary
  for callers.
- Avoid when: the facade becomes a miscellaneous service that collects
  unrelated policy.
- Responsibilities: facade owns orchestration over a coherent capability; lower
  modules own their specialized decisions.
- Dependencies: callers depend on the facade; the facade depends on lower-level
  modules, not back upward.
- Smells prevented: `SD-C-*` fan-out at call sites, `SD-B-*` mixed caller
  responsibilities.
- Smells introduced: service-object gravity, hidden coupling, god facade.
- Validation: `[static]` responsibility and dependency inspection; `[history]`
  if churn is the reason for introducing the facade.

### Anti-Corruption Boundary

- Use when: a legacy system, vendor model, or partner vocabulary would distort
  internal concepts if allowed to leak.
- Avoid when: a local adapter function is enough and the integration does not
  create semantic pressure.
- Responsibilities: boundary owns translation, compatibility rules, and
  protection of internal vocabulary.
- Dependencies: internal policy depends on internal concepts; the boundary
  depends on both internal and external representations.
- Smells prevented: `SD-S-*` vocabulary collision, `SD-C-*` vendor coupling,
  `SD-E-*` migration risk.
- Smells introduced: duplicated rules, mapping drift, long-lived compatibility
  code without an owner.
- Validation: `[static]` model comparison; `[human]` for domain meaning;
  `[runtime]` for integration behavior.

### Mapper

- Use when: two boundaries need explicit data translation without sharing a
  model.
- Avoid when: both sides are owned, changed, and understood together and mapping
  only repeats field names.
- Responsibilities: mapper owns representation conversion, not policy.
- Dependencies: mapper sits at the boundary; domain policy should not depend on
  transport or persistence models.
- Smells prevented: `SD-S-*` duplicate concept confusion, `SD-B-*` DTO/entity
  leakage.
- Smells introduced: boilerplate drift, hidden validation, policy leaking into
  mapping code.
- Validation: `[static]` type and field usage; delegate to
  `test-quality-audit` when mapping tests are the key concern.

## Variation And Policy Selection

### Strategy

- Use when: multiple current algorithms or policies must vary behind one stable
  decision point.
- Avoid when: there is one implementation or a small conditional with no proven
  volatility.
- Responsibilities: strategy owns the varying algorithm; caller owns selection
  context.
- Dependencies: caller depends on a stable strategy contract; concrete
  strategies avoid depending on caller internals.
- Smells prevented: `SD-B-*` mixed policy, `SD-C-*` change spread across
  callers.
- Smells introduced: class proliferation, indirect control flow, imagined
  extension points.
- Validation: `[static]` current implementations and selection logic;
  `[history]` if churn justifies extraction.

### Policy Object

- Use when: a named rule set should travel as data or configuration while
  keeping policy explicit.
- Avoid when: the policy object is a property bag with no invariant or decision
  ownership.
- Responsibilities: policy object owns rule parameters and invariant checks;
  workflow owns when to apply it.
- Dependencies: consumers depend on the policy contract, not on scattered
  config keys.
- Smells prevented: `SD-S-*` rule ambiguity, `SD-B-*` scattered decisions.
- Smells introduced: anemic configuration object, duplicated validation,
  hidden default behavior.
- Validation: `[static]` rule ownership and call-site spread; `[human]` when
  business meaning is uncertain.

### Specification

- Use when: composable predicates are shared policy and need names, reuse, or
  persistence translation.
- Avoid when: a one-off simple predicate is easier to read inline.
- Responsibilities: specification owns predicate semantics; repositories or
  query adapters own translation to storage.
- Dependencies: policy should not depend on storage-specific query machinery
  unless the boundary explicitly owns that tradeoff.
- Smells prevented: `SD-S-*` unnamed rule drift, `SD-B-*` predicate scattering.
- Smells introduced: tiny-object ceremony, storage leakage, unreadable
  predicate composition.
- Validation: `[static]` reuse and translation boundary; `[runtime]` only for
  query performance claims.

## Workflow And Orchestration

### Pipeline

- Use when: a workflow has ordered stages with stable handoff contracts and
  independently testable transformations.
- Avoid when: the sequence is short, fixed, and clearer as direct code.
- Responsibilities: pipeline owns stage order and handoff; stages own local
  transformation or validation.
- Dependencies: stages depend on the handoff contract, not on neighboring stage
  internals.
- Smells prevented: `SD-B-*` mixed workflow responsibilities, `SD-C-*` stage
  fan-out.
- Smells introduced: opaque stage ordering, hidden shared context, premature
  plugin architecture.
- Validation: `[static]` stage contracts and error flow; `[runtime]` for
  throughput or latency claims.

### Chain Of Responsibility

- Use when: multiple handlers may process a request and handler order or
  fallback is an explicit policy.
- Avoid when: direct dispatch or a table of handlers is clearer.
- Responsibilities: chain owns traversal and stop/fallback semantics; handlers
  own one decision.
- Dependencies: handlers share a narrow request/result contract.
- Smells prevented: `SD-B-*` tangled conditional dispatch, `SD-C-*` caller
  knowledge of every handler.
- Smells introduced: invisible order dependency, swallowed failures, handler
  side effects.
- Validation: `[static]` chain construction and stop semantics; delegate to
  `test-quality-audit` when behavior coverage is the concern.

### State Machine

- Use when: valid transitions, invalid transitions, and state-dependent behavior
  are central to correctness.
- Avoid when: a status enum has no transition rules.
- Responsibilities: state machine owns transition rules and state behavior;
  adapters own persistence and presentation.
- Dependencies: callers request transitions through one contract instead of
  mutating state directly.
- Smells prevented: `SD-S-*` status meaning drift, `SD-B-*` scattered
  invariant enforcement.
- Smells introduced: over-modeled lifecycle, transition table hidden from
  domain owners, storage coupling.
- Validation: `[static]` transition ownership; `[human]` for lifecycle meaning;
  delegate to `test-quality-audit` when transition coverage is the concern.

### Saga / Process Manager

- Use when: a long-running workflow crosses boundaries and needs explicit
  compensation, retries, or progress ownership.
- Avoid when: the workflow is one local transaction or one synchronous call.
- Responsibilities: process manager owns orchestration state and compensation;
  participants own local actions.
- Dependencies: process manager depends on participant contracts and event or
  command channels, not participant internals.
- Smells prevented: `SD-B-*` cross-boundary workflow leakage, `SD-E-*`
  recovery ambiguity.
- Smells introduced: distributed state complexity, unclear ownership, hidden
  retry side effects.
- Validation: `[static]` ownership and compensation path; `[runtime]` for
  delivery, ordering, and retry behavior; delegate API or infra details.

## Creation And Composition

### Factory Method

- Use when: creation choice varies and the creator has the context needed to
  select the implementation.
- Avoid when: direct construction is stable and readable.
- Responsibilities: factory method owns creation variation; created object owns
  behavior.
- Dependencies: callers depend on the created contract, not concrete selection
  details.
- Smells prevented: `SD-C-*` scattered constructor knowledge, `SD-B-*` mixed
  creation and workflow policy.
- Smells introduced: needless indirection, hidden dependencies, test-only
  abstractions.
- Validation: `[static]` creation call sites and variation evidence.

### Abstract Factory

- Use when: families of related objects must vary together under one product or
  platform boundary.
- Avoid when: only one object varies or family consistency is not a real force.
- Responsibilities: factory owns family consistency; products own behavior.
- Dependencies: consumers depend on family contracts and receive a coherent
  set of products.
- Smells prevented: `SD-S-*` incompatible family mixing, `SD-C-*` platform
  selection spread.
- Smells introduced: abstract hierarchy ceremony, hidden product coupling.
- Validation: `[static]` product family variation; `[history]` if platform churn
  is the justification.

### Builder

- Use when: constructing a valid object requires staged decisions, named
  defaults, or invariants that direct constructors obscure.
- Avoid when: the object has a small stable constructor or the builder allows
  invalid partial state.
- Responsibilities: builder owns construction sequence and defaults; target
  object owns invariants after creation.
- Dependencies: callers depend on builder methods, not on target internals.
- Smells prevented: `SD-S-*` argument meaning ambiguity, `SD-B-*` scattered
  setup.
- Smells introduced: mutable half-built state, fluent ceremony, duplicated
  validation.
- Validation: `[static]` constructor complexity and invariant ownership.

### Composition Root

- Use when: object graph assembly, dependency injection, or runtime adapter
  selection needs one explicit edge.
- Avoid when: arbitrary modules resolve dependencies or composition is trivial
  direct construction.
- Responsibilities: composition root owns wiring; modules own behavior and
  declare dependencies.
- Dependencies: composition root may depend outward on adapters; policy modules
  should not depend on the container.
- Smells prevented: `SD-C-*` service locator coupling, `SD-B-*` hidden wiring.
- Smells introduced: oversized startup module, container-specific domain code.
- Validation: `[static]` dependency resolution sites and direction.

## Collaboration And Events

### Observer

- Use when: one subject needs to notify multiple current consumers without
  knowing their concrete types.
- Avoid when: there is one consumer or direct calls are clearer.
- Responsibilities: subject owns notification contract; observers own reactions.
- Dependencies: subject depends on a narrow observer contract or event
  mechanism.
- Smells prevented: `SD-C-*` fan-out from subject to concrete consumers.
- Smells introduced: hidden execution order, side-effect coupling, difficult
  error handling.
- Validation: `[static]` observer count and failure semantics; `[runtime]` for
  asynchronous delivery claims.

### Domain Events

- Use when: a domain-significant fact should trigger reactions without placing
  reaction policy inside the aggregate or originator.
- Avoid when: events only hide a direct local call or make transaction
  boundaries unclear.
- Responsibilities: originator owns event creation; handlers own follow-up
  policy; event contract owns stable meaning.
- Dependencies: handlers depend on event contracts, not originator internals.
- Smells prevented: `SD-B-*` aggregate doing unrelated work, `SD-C-*`
  bidirectional module coupling.
- Smells introduced: temporal coupling, unclear consistency, event vocabulary
  drift.
- Validation: `[static]` event meaning and handler ownership; `[human]` for
  domain vocabulary; delegate API/infra delivery concerns.

### Message Bus

- Use when: modules or services need asynchronous decoupling with explicit
  message contracts and delivery ownership.
- Avoid when: an in-process direct call satisfies the current force.
- Responsibilities: bus adapter owns transport mechanics; publishers and
  consumers own message semantics and local policy.
- Dependencies: modules depend on message contracts and bus port, not concrete
  transport internals.
- Smells prevented: `SD-C-*` direct cross-boundary coupling, `SD-E-*` evolution
  blockage.
- Smells introduced: distributed debugging cost, schema drift, operational
  coupling hidden by abstraction.
- Validation: `[static]` contract ownership; `[runtime]` for delivery,
  ordering, retry, or scale claims; delegate infra/security specifics.

## Persistence And Domain Shape

### Repository

- Use when: persistence access is a real boundary and callers need a domain
  collection contract rather than storage mechanics.
- Avoid when: the repository is pass-through CRUD over an ORM with no boundary
  force.
- Responsibilities: repository owns persistence translation and collection-like
  access; domain policy owns invariants.
- Dependencies: policy depends on repository contract only when persistence is
  outside the policy boundary; repository depends on storage adapter.
- Smells prevented: `SD-C-*` storage leakage, `SD-S-*` persistence model
  confusion.
- Smells introduced: pass-through ceremony, query capability hiding, duplicated
  unit-of-work semantics.
- Validation: `[static]` storage leakage and caller needs; `[runtime]` only for
  performance claims.

### Unit Of Work

- Use when: several repository operations must share one explicit transactional
  boundary.
- Avoid when: the platform already supplies a clear transaction boundary and a
  wrapper only repeats it.
- Responsibilities: unit of work owns commit/rollback scope; repositories own
  access; domain owns invariants.
- Dependencies: application workflow coordinates the unit; domain objects do
  not manage transactions.
- Smells prevented: `SD-E-*` partial persistence risk, `SD-B-*` transaction
  scattering.
- Smells introduced: hidden lifetime coupling, nested transaction confusion,
  redundant ORM wrapper.
- Validation: `[static]` transaction scope; `[runtime]` for concurrency or
  isolation claims.

### Aggregate

- Use when: a cluster of state has invariants that must be enforced together.
- Avoid when: the object grouping is only a table join or screen shape.
- Responsibilities: aggregate owns invariants and state transitions inside its
  boundary.
- Dependencies: callers request operations; they do not mutate internal state
  directly.
- Smells prevented: `SD-S-*` invariant drift, `SD-B-*` scattered state policy.
- Smells introduced: oversized aggregate, unrelated lifecycle coupling,
  persistence-driven design.
- Validation: `[static]` invariant ownership; `[human]` for domain meaning.

### Shared Kernel

- Use when: multiple modules or teams truly share stable concepts and have an
  ownership contract for changes.
- Avoid when: shared means convenient dumping ground for code no one owns.
- Responsibilities: kernel owns stable shared vocabulary; consumers own local
  policy around it.
- Dependencies: consumers depend on the kernel deliberately; kernel avoids
  depending back on consumers.
- Smells prevented: `SD-S-*` duplicate concept drift, `SD-T-*` coordination
  ambiguity when sharing is real.
- Smells introduced: shared-core gravity, cross-team bottleneck, broad
  propagation cost.
- Validation: `[static]` dependency spread; `[human]` for ownership contract.

## Evolution

### Strangler

- Use when: replacing a design incrementally while preserving behavior and
  routing traffic or calls safely between old and new paths.
- Avoid when: the old and new designs would coexist indefinitely without a
  retirement path.
- Responsibilities: strangler boundary owns routing and compatibility; new
  implementation owns target behavior; old path has a removal condition.
- Dependencies: callers move toward the strangler boundary rather than calling
  both designs directly.
- Smells prevented: `SD-E-*` risky big-bang rewrite, `SD-C-*` unmanaged
  migration coupling.
- Smells introduced: permanent dual path, behavior drift, unclear cutover owner.
- Validation: `[static]` routing and removal path; `[runtime]` for traffic,
  performance, or failure claims.

### Branch By Abstraction

- Use when: a behavior-preserving replacement needs a temporary abstraction to
  switch implementations safely.
- Avoid when: the abstraction has no planned removal or the change can be made
  directly.
- Responsibilities: abstraction owns temporary compatibility; implementations
  own old and new behavior; plan owns removal.
- Dependencies: callers depend on the abstraction during transition only.
- Smells prevented: `SD-E-*` large unsafe refactor, `SD-C-*` migration spread.
- Smells introduced: permanent indirection, lowest-common-denominator contract,
  hidden divergence.
- Validation: `[static]` switch points and removal condition; `[history]` for
  migration progress.

### Plugin / Extension Point

- Use when: independent implementations are already expected, externally owned,
  or released on different cadences.
- Avoid when: the plugin point exists only for imagined future variation.
- Responsibilities: host owns lifecycle and contract; plugins own isolated
  behavior; compatibility policy is explicit.
- Dependencies: plugins depend on host contract; host avoids depending on
  plugin internals.
- Smells prevented: `SD-C-*` host-to-implementation coupling, `SD-T-*`
  ownership mismatch when extension ownership is real.
- Smells introduced: unused extension point, versioning burden, hidden runtime
  loading failures.
- Validation: `[static]` current implementers and contract; `[runtime]` for
  loading, isolation, and compatibility claims.
