# Software Design Reference

## 1. Purpose And Non-Goals

`software-design` shapes code-level and module-level design before and during implementation. The goal is the smallest coherent design that solves the known problem, localizes likely change, avoids semantic fragmentation, and preserves future refactoring options without building imagined futures.

The reference sits between implementation tactics and architecture notation:

- Below `architecture-design`: no ArchiMate models, OEF XML, enterprise viewpoints, or architecture drift checks.
- Above specialist runtime skills: no responsive UI rules, HTTP API contracts,
  API runtime guidance, infrastructure/IaC topology, security posture audit, or
  test-quality audit.
- Inside software design: boundaries, responsibilities, dependency direction, state/data ownership, vocabulary, coupling, cohesion, quality tradeoffs, and safe evolution.

## 2. Source Basis

Rules cite source families rather than copying source prose.

- Lean value and waste discipline: Mary and Tom Poppendieck, *Implementing Lean Software Development: From Concept to Cash*, Pearson, https://www.pearson.com/en-us/subject-catalog/p/implementing-lean-software-development-from-concept-to-cash/P200000009108/9780321437389
- Information hiding and change-isolating modularity: David L. Parnas, "On the criteria to be used in decomposing systems into modules," Communications of the ACM, https://cacm.acm.org/research/on-the-criteria-to-be-used-in-decomposing-systems-into-modules/
- Domain terminology and DDD vocabulary: Eric Evans / Domain Language DDD Reference, https://www.domainlanguage.com/ddd/reference/
- Quality-attribute tradeoff discipline: SEI Architecture Tradeoff Analysis Method, https://www.sei.cmu.edu/library/the-architecture-tradeoff-analysis-method/
- Socio-technical fit and maintainability: DORA loosely coupled teams and code maintainability capabilities, https://dora.dev/capabilities/loosely-coupled-teams/ and https://dora.dev/devops-capabilities/technical/code-maintainability/
- Coupling and propagation-cost calibration: MacCormack and Sturtevant, Journal of Systems and Software study page, https://www.hbs.edu/faculty/Pages/item.aspx?num=51343
- Code smells/refactoring calibration: Lacerda, Petrillo, Pimenta, and Gueheneuc, tertiary systematic review, https://www.sciencedirect.com/science/article/pii/S0164121220300881
- DDD empirical calibration: systematic literature review, https://www.sciencedirect.com/science/article/pii/S0164121225002055

Source roles:

- Principle authorities define rules.
- Empirical calibration sources tune severity and confidence.
- Runtime/platform authorities define extension-specific facts.

Discovery sources such as blogs, vendor summaries, conference slides, and AI summaries can help search, but they do not anchor reference rules when primary or official sources are available.

## 3. Principles

### 3.1 Value And Waste Discipline

Design starts from current value and explicit uncertainty. Avoid building optionality that is not demanded by the known change, validated product direction, or measured operational force.

Default: do less, name what is deferred, and make the next decision cheap.

### 3.2 Information Hiding And Change Isolation

Module boundaries should hide design decisions likely to change. A good boundary localizes the effect of changing storage, protocol, policy, vendor, workflow, or domain rule.

Default: place a boundary around volatility, not around a folder type.

### 3.3 Semantic Coherence

A concept should have one meaning inside a boundary. When the same word means two things, split or qualify it. When two words mean the same thing, converge or explicitly translate.

DDD terms are tools, not a default architecture. Use bounded context, aggregate, anti-corruption layer, or shared kernel only when domain complexity and collaboration patterns justify them.

### 3.4 Coupling, Cohesion, And Propagation Cost

Design health is judged by how far a change spreads. Cycles, unstable shared cores, fan-out hotspots, hidden global state, and bidirectional dependencies increase propagation cost even when the code compiles.

Default: choose the shape that makes the next likely change touch fewer concepts and fewer owners.

### 3.5 Evolutionary Design And Refactoring Safety

Prefer a design that can evolve through small behavior-preserving steps. Refactor toward the needed boundary when evidence exists; do not perform a broad redesign to satisfy an aesthetic target.

Default: make the next safe move, then reassess.

### 3.6 Lightweight Quality-Attribute Tradeoffs

Software design choices balance modifiability, performance, reliability, security, operability, cost, and cognitive load. The skill borrows ATAM's discipline of making forces explicit, but it does not run an architecture-board analysis.

Default: state the force and the local tactic. Do not pretend one design optimizes all qualities.

### 3.7 Socio-Technical Fit

Boundaries are not only technical. Ownership, cognitive load, and coordination cost are design signals. A boundary that repeatedly forces unrelated teams to coordinate is suspect.

Default: align code boundaries with stable ownership where that does not weaken semantic coherence.

## 4. Decision Defaults

1. Start with one concrete use case before adding extension mechanisms.
2. Prefer deletion or narrowing over adding indirection.
3. Hide volatile decisions behind the owning module.
4. Keep domain policy close to the state and invariants it governs.
5. Translate across boundaries explicitly. Do not share a model merely to avoid mapping.
6. Depend inward toward stable policy and outward toward adapters, not the reverse.
7. Use shared code for stable, boring mechanics; avoid shared domain cores unless ownership and vocabulary are genuinely shared.
8. Record rejected abstractions when a familiar pattern is intentionally skipped.
9. Treat performance, security, reliability, and operability as forces that may change the design, then delegate specialist detail to sibling skills when needed.
10. Prefer a reversible local change when evidence is weak.

## 5. Design Primitives

- Boundary: a line that controls vocabulary, dependencies, state ownership, and change propagation.
- Responsibility: a reason for code to change. Mixed reasons become boundary candidates.
- Policy: domain or product decision that should be isolated from transport, storage, and framework mechanics.
- Adapter: code that translates between a boundary and an external mechanism.
- Seam: an existing place where change can be isolated without broad churn.
- Translation: explicit mapping between two concepts or models that should not be treated as the same.
- Invariant: a rule that must stay true around state transitions.
- Volatility point: a likely future change in rule, storage, protocol, dependency, scale, ownership, or compliance.
- Design debt: a structural choice that raises the cost of future change.

## 6. Patterns

Patterns are tactics for forces, not goals. Apply the Lean value and waste
discipline from section 3.1 before reaching for a named pattern: start from a
current use case, identify the volatility or propagation cost, prefer the
smallest coherent move, and record the simpler design that was rejected.

Load the compact decision aid at
[../../skills/software-design/references/pattern-catalog.md](../../skills/software-design/references/pattern-catalog.md)
when a user asks about patterns, proposes a named pattern, or the source shows
pattern ceremony whose fit must be judged. Do not expand this reference into a
generic pattern tutorial; rely on the base model for mechanics and keep bundled
guidance focused on Lean selection, smell mapping, evidence layers, and
delegation.

Every pattern recommendation must state:

1. The current force it addresses.
2. Where the responsibility and dependency boundary sits.
3. When to avoid the pattern.
4. Which `SD-*` smell family it can reduce.
5. Which `SD-*` smell family it may introduce.
6. The cheapest evidence layer needed before treating the pattern as justified.

Core pattern families:

- Boundary and translation: Adapter, Facade, Anti-Corruption Boundary, Mapper.
- Variation and policy selection: Strategy, Policy Object, Specification.
- Workflow and orchestration: Pipeline, Chain of Responsibility, State Machine,
  Saga / Process Manager.
- Creation and composition: Factory Method, Abstract Factory, Builder,
  Composition Root.
- Collaboration and events: Observer, Domain Events, Message Bus.
- Persistence and domain shape: Repository, Unit of Work, Aggregate,
  Shared Kernel.
- Evolution: Strangler, Branch by Abstraction, Plugin / Extension Point.

Default: recommend no pattern when direct code, deletion, or narrowing solves
the known problem with less propagation cost. Transitional patterns need an exit
condition; extension points need current implementers or an explicit ownership
force.

## 7. Design Smells

Smell codes live in [../../skills/software-design/references/smell-catalog.md](../../skills/software-design/references/smell-catalog.md). Core families:

- `SD-W-*`: waste and unnecessary design.
- `SD-B-*`: boundary and responsibility.
- `SD-C-*`: coupling and dependency direction.
- `SD-S-*`: semantic coherence.
- `SD-E-*`: evolution and refactoring safety.
- `SD-Q-*`: quality-attribute tradeoff.
- `SD-T-*`: socio-technical fit.

Smells are evidence prompts, not automatic verdicts. False positives are acceptable when the output names the evidence needed to decide.

## 8. Extract And Review Checklist

Verification layers:

- `[static]`: source-readable from files alone.
- `[graph]`: requires dependency graph or import/reference analysis.
- `[history]`: requires git history, churn, or branch evidence.
- `[runtime]`: requires telemetry, profiling, logs, or production/load data.
- `[human]`: requires product, domain, or team input.

Checklist:

1. `[static]` Scope is explicit; non-goals are named.
2. `[static]` New code does not introduce speculative abstractions.
3. `[static]` Responsibilities have one clear reason to change.
4. `[graph]` Dependencies point toward stable policy, not toward framework or storage details.
5. `[graph]` No cycles or bidirectional project/module references exist in the changed scope.
6. `[static]` Domain concepts have consistent names inside a boundary.
7. `[static]` Cross-boundary models are translated explicitly.
8. `[static]` Shared modules are stable, owned, and boring.
9. `[static]` State and invariants have one owning boundary.
10. `[history]` Churn hotspots are not made more central without cause.
11. `[runtime]` Runtime quality claims are backed by measurements, not static inference.
12. `[human]` Team ownership and domain meaning are not asserted without input.
13. `[static]` Legacy debt is not extended silently.
14. `[static]` The next refactor is small enough to validate.
15. `[static]` Delegations to sibling skills are made when scope crosses their domain.

## 9. Delegation Map

- `app-design`: web frontend application structure, component architecture,
  route/screen design, frontend state/data behavior, browser runtime behavior,
  responsive behavior, accessibility, internationalization, visual behavior,
  and Core Web Vitals. `software-design` supports app-design from the
  engineering side for decomposition, dependency direction, helper/library
  extraction, state-machine shape, adapter boundaries, and coupling risks
  underneath frontend features.
- `api-design`: HTTP API contract, auth, runtime reliability, data-service patterns, API observability.
- `infra-design`: infrastructure/IaC topology, cloud resources, environment and
  state boundaries, rollout/rollback, operations handoff.
- `architecture-design`: ArchiMate models, OEF XML, enterprise/solution views, architecture drift.
- `devsecops-audit`: application and IaC security posture, workflows, release
  artifacts, secrets, pipeline controls.
- `test-quality-audit`: test quality, characterization/specification classification, integration/E2E scope, mutation-testing worklists.

## 10. Output Contracts

Build, Extract, Review, and Lookup outputs are defined in the skill workflow. All modes must report mode, extensions loaded, reference path, verification layers used, project assimilation, delegations, and limits.
