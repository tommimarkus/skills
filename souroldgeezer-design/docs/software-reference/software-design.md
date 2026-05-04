# Software Design Reference

## 1. Purpose And Non-Goals

`software-design` shapes code-level and module-level design before and during implementation. The goal is the smallest coherent design that solves the known problem, localizes likely change, avoids semantic fragmentation, and preserves future refactoring options without building imagined futures.

The reference sits between implementation tactics and architecture notation:

- Below `architecture-design`: no ArchiMate models, OEF XML, enterprise viewpoints, or architecture drift checks.
- Above specialist runtime skills: no responsive UI rules, HTTP API contracts, API runtime guidance, security posture audit, or test-quality audit.
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

### 6.1 Thin Adapter, Stable Policy

Use when framework, transport, persistence, or vendor details are likely to change independently from domain policy. Keep adapters replaceable and policy testable without the external mechanism.

Avoid when the app is a simple script or the adapter/policy split creates more moving parts than the known change requires.

### 6.2 Explicit Boundary Translation

Use when two modules use different meanings, lifecycles, or ownership for similar data. Mapping is cheaper than letting one model leak everywhere.

Avoid when the boundary is artificial and both sides are owned, changed, and understood together.

### 6.3 Vertical Slice With Local Policy

Use when a feature owns its request, workflow, validation, and local persistence behavior without broad reuse pressure. This reduces cross-layer edits for feature changes.

Avoid when independent features genuinely share complex domain policy that needs one authoritative home.

### 6.4 Layered Core With Inward Dependencies

Use when shared domain policy is stable enough to justify a core and adapters are clearly outside it.

Avoid when layers merely mirror folder names and every change still crosses all layers.

### 6.5 Anti-Corruption Boundary

Use when integrating with an external system, legacy model, or partner vocabulary that must not define internal concepts.

Avoid when the integration is small and a local adapter function is sufficient.

### 6.6 Shared Kernel With Ownership Contract

Use only when multiple teams or modules truly share stable concepts and can coordinate changes.

Avoid when "shared" means "convenient place to put code no one owns."

### 6.7 Strangler Refactor

Use when replacing a design incrementally while keeping behavior stable.

Avoid when the new and old designs would run indefinitely without a retirement path.

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

- `responsive-design`: responsive UI, accessibility, internationalization, visual behavior, Core Web Vitals.
- `api-design`: HTTP API contract, auth, runtime reliability, data-service patterns, API observability.
- `architecture-design`: ArchiMate models, OEF XML, enterprise/solution views, architecture drift.
- `devsecops-audit`: security posture, IaC, workflows, release artifacts, secrets, pipeline controls.
- `test-quality-audit`: test quality, characterization/specification classification, integration/E2E scope, mutation-testing worklists.

## 10. Output Contracts

Build, Extract, Review, and Lookup outputs are defined in the skill workflow. All modes must report mode, extensions loaded, reference path, verification layers used, project assimilation, delegations, and limits.
