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
- Software-design principle taxonomy: IEEE Computer Society, SWEBOK Guide v4, https://www.computer.org/education/bodies-of-knowledge/software-engineering/v4
- Domain terminology and DDD vocabulary: Eric Evans / Domain Language DDD Reference, https://www.domainlanguage.com/ddd/reference/
- Quality-attribute tradeoff discipline: SEI Architecture Tradeoff Analysis Method, https://www.sei.cmu.edu/library/the-architecture-tradeoff-analysis-method-2/
- Quality-attribute taxonomy: ISO/IEC 25010 (SQuaRE) product quality model, https://www.iso.org/standard/78176.html
- Socio-technical fit and maintainability: DORA loosely coupled teams and code maintainability capabilities, https://dora.dev/capabilities/loosely-coupled-teams/ and https://dora.dev/capabilities/code-maintainability/
- Coupling and propagation-cost calibration: MacCormack and Sturtevant, Journal of Systems and Software study page, https://www.hbs.edu/faculty/Pages/item.aspx?num=51343
- DRY as knowledge-ownership discipline: Hunt and Thomas, *The Pragmatic Programmer*, https://pragprog.com/titles/tpp20/the-pragmatic-programmer-20th-anniversary-edition/
- Code smells/refactoring calibration: Lacerda, Petrillo, Pimenta, and Gueheneuc, tertiary systematic review, https://www.sciencedirect.com/science/article/pii/S0164121220300881
- DDD empirical calibration: systematic literature review, https://www.sciencedirect.com/science/article/pii/S0164121225002055
- Software maintenance lifecycle and maintenance-type taxonomy: ISO/IEC/IEEE 14764:2022 on ISO/IEC/IEEE 12207:2017, https://www.iso.org/standard/80710.html and https://www.iso.org/standard/63712.html
- Version-as-compatibility-contract schemes: Semantic Versioning 2.0.0, https://semver.org/ and Calendar Versioning, https://calver.org/
- Dependency management, deprecation, and single-version convergence: Titus Winters, Tom Manshreck, and Hyrum Wright, *Software Engineering at Google*, https://abseil.io/resources/swe-book
- Observable-behavior coupling calibration: Hyrum's Law, https://www.hyrumslaw.com/
- Dependency freshness measurement: Cox, Bouwers, van Eekelen, and Visser, "Measuring Dependency Freshness in Software Systems," ICSE 2015, https://ericbouwers.github.io/papers/icse15.pdf
- Safe backward-incompatible interface change: Parallel Change (expand/contract), Joshua Kerievsky via Martin Fowler, https://martinfowler.com/bliki/ParallelChange.html
- Change-history communication for consumers: Keep a Changelog, https://keepachangelog.com/
- Concurrency ownership and failure-contract design as reliability quality attributes: ISO/IEC 25010 reliability characteristics (fault tolerance, recoverability), https://www.iso.org/standard/78176.html, applied through the SEI quality-attribute tradeoff discipline above, with detached concurrency treated as a coupling concern per the propagation-cost calibration above.

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

Balance modifiability, performance, reliability, security, operability, cost,
and cognitive load by making forces explicit, not by running an architecture
board. For each in-scope NFR, name its quality, write a measurable scenario
(stimulus, response, measure), and allocate an owning boundary; missing measure is
`SD-Q-1`, missing owner `SD-Q-3`. Load the
[NFR catalog](../../skills/software-design/references/nfr-catalog.md) for NFRs,
SLAs/SLOs, or targets. State the force and local tactic; data paths use
operation/size/semantics before measuring gains, caches, or tuning.

### 3.7 Socio-Technical Fit

Ownership, cognitive load, and coordination cost are boundary signals; align
code with stable ownership unless that weakens semantic coherence. Load the
[principles catalog](../../skills/software-design/references/principles-catalog.md)
for a named or source-visible principle (including SOLID, DRY, KISS, YAGNI,
information hiding, dependency inversion, or ubiquitous language). A
recommendation or rejection states its force, concrete rule, avoid case,
reduced and introduced `SD-*` families, and cheapest justified evidence layer.

### 3.8 Version, Deprecation, And Convergence Lifecycle

Classify every externally visible change as breaking, additive, or cosmetic.
SemVer encodes that contract; CalVer carries it in changelog and deprecation
policy; live-at-HEAD requires convergence. Choose by audience, then hold the
classification discipline. A deprecation needs replacement, owner, and removal
trigger. Treat dependency currency as measurable debt, prefer small upgrades,
converge on one supported version, bound producer/consumer skew, and give
divergence an owner and exit. Before changing observable behavior, account for
Hyrum's Law with characterization evidence. Delegate HTTP versioning to
`api-design`, fleet convergence to `infra-design`, CVE/supply-chain risk to
`devsecops-audit`, and characterization tests to `test-quality-audit`.

### 3.9 Concurrency, Cancellation, And Error-Contract Ownership

Every spawned, background, or parallel path has one lifetime owner: start,
join/supervision, and caller-cancellation propagation. Detached work without it
couples timing and state (`SD-C-4`, `SD-C-6`); static evidence shows the missing
path and runtime evidence its leak, starvation, or shutdown hang. A boundary
names domain, transport, and infrastructure failures, translation/propagation,
and retryable versus terminal classes. Do not collapse or swallow meanings
(`SD-S-5`), or stack retry, timeout, or fallback outside one budget owner
(`SD-Q-4`), multiplying load or non-idempotent effects. Delegate HTTP error
shape to `api-design`, runtime SLIs/SLOs and rollout to `infra-design`,
failure-mode security to `devsecops-audit`, and characterization tests to
`test-quality-audit`.

### 3.10 Testability And Seams

Testability means collaborators can be observed and substituted at their owning
boundary. Use a parameter, port, or injected collaborator for a real IO, clock,
randomness, network, or global/singleton isolation boundary; construct the real
implementation at the composition edge. Hidden construction inside policy is
`SD-B-5`, compounded by shared mutable state (`SD-C-4`); static and graph
evidence show the hidden dependency. One implementation plus test doubles is
legitimate at a real isolation boundary. Do not add a wrapper solely for test
substitution (`SD-W-1`, `SD-W-2`): pure logic needs no seam. Delegate test
judgment to `test-quality-audit`.

### 3.11 Operation Feedback And CLI Progress

Domain code supplies operation state; an adapter presents it. A CLI or agent
operation that crosses about one second, including prefetch and housekeeping,
keeps status discoverable, acknowledges known slow work immediately, reports
completed/total only with a known total, and otherwise uses a labelled
indeterminate state. It never fabricates percentages or ETA.
Completion means the result is usable; failure, cancellation, and awaiting input
clear busy status and state the next action.

All CLI progress, including interactive TTY rendering, goes to stderr or a
separate status channel, preserving stdout and exit semantics for data
consumers. Redirected output uses bounded plain records. A detached job returns
an identifier and a status route. Quiet mode may suppress healthy routine status
only when a separate discoverable status route remains; it never hides terminal
errors. Keep background outcomes inspectable.

Each operation owns timeout, recovery, and supported cancellation. For
foreground CLI and agent work, announce known slow work, report meaningful
milestones and confirmed waiting at least every 60 seconds, prefer host
notifications, and aggregate background status instead of interrupting the user
repeatedly. Disclose when an uninterruptible host call prevents an interim
update. The one-second and 60-second limits are repository defaults, not general
standards.

## 4. Decision Defaults

1. Start with one concrete use case before adding extension mechanisms.
2. Prefer deletion or narrowing over adding indirection.
3. Hide volatile decisions behind the owning module.
4. Keep domain policy close to the state and invariants it governs.
5. Translate across boundaries explicitly. Do not share a model merely to avoid mapping.
6. Depend inward toward stable policy and outward toward adapters, not the reverse.
7. Use shared code for stable, boring mechanics; avoid shared domain cores unless ownership and vocabulary are genuinely shared.
8. Record rejected abstractions when a familiar pattern is intentionally skipped.
9. Treat performance, security, reliability, and operability as forces that may change the design; name in-scope non-functional requirements from the quality taxonomy, express them as measurable scenarios, and allocate each to an owning boundary, then delegate specialist detail to sibling skills when needed.
10. Prefer a reversible local change when evidence is weak.
11. Make each release's compatibility contract explicit and classify every externally-visible change as breaking, additive, or cosmetic — independent of scheme (SemVer, CalVer, or live-at-HEAD). Treat a deprecation as a staged lifecycle with a replacement, an owner, and a removal trigger, not a permanent marker.
12. Keep dependencies and internal consumers converging on one supported version; prefer incremental upgrades over a big-bang, and give any divergence a convergence owner and exit.
13. A library or module owns emitting diagnostics through injected or standard logging/tracing interfaces; it does not configure logging — root logger, sinks, levels — or own trace-context transport (the application entrypoint or composition root is the one place that configures). Treat trace/correlation context crossing a boundary as part of the boundary contract. Delegate API observability to `api-design` and ops/runtime observability to `infra-design`.
14. Keep operation state at the owning boundary and presentation at the CLI,
    UI, or agent adapter. Emit honest, channel-appropriate feedback for work
    that outlasts immediate response; a quick completed operation, quiet mode
    with a separate discoverable status route, or a supervised job with a
    discoverable status route is not `SD-Q-6`.

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
13. `[human]` In-scope NFRs are named from the quality taxonomy, expressed as measurable scenarios, and allocated to an owning boundary.
14. `[static]` Legacy debt is not extended silently.
15. `[static]` The next refactor is small enough to validate.
16. `[static]` Delegations to sibling skills are made when scope crosses their domain.
17. `[static]` Externally-visible changes are classified breaking/additive/cosmetic and the compatibility contract is explicit.
18. `[static]` Deprecations name a replacement, an owner, and a removal trigger.
19. `[history]` Dependency currency is treated as debt with an upgrade cadence; security risk is delegated to `devsecops-audit`.
20. `[graph]`/`[human]` Divergent versions or forks of a shared concern have a named convergence owner and bounded internal skew.

## 9. Delegation Map

- `app-design`: web frontend application structure, component architecture,
  route/screen design, frontend state/data behavior, browser runtime behavior,
  responsive behavior, accessibility, internationalization, visual behavior,
  and Core Web Vitals. `software-design` supports app-design from the
  engineering side for decomposition, dependency direction, helper/library
  extraction, state-machine shape, adapter boundaries, and coupling risks
  underneath frontend features.
- `api-design`: HTTP API contract, auth, runtime reliability, data-service patterns, API observability, HTTP versioning and `Sunset`/`Deprecation` headers.
- `infra-design`: infrastructure/IaC topology, cloud resources, environment and
  state boundaries, rollout/rollback, runtime config/fleet convergence, ops/runtime observability, operations handoff.
- `architecture-design`: ArchiMate models, OEF XML, enterprise/solution views, architecture drift. `architecture-design` owns the paired package at `docs/architecture/<feature>.dediren/`; when one exists, `software-design` checks it after module/boundary restructuring and dispatches drift review to `architecture-design` rather than running drift checks itself.
- `devsecops-audit`: application and IaC security posture, workflows, release
  artifacts, secrets, pipeline controls, dependency-upgrade CVE and supply-chain risk.
- `test-quality-audit`: test quality, characterization/specification classification, integration/E2E scope, mutation-testing worklists, characterization tests before converging or removing observable behavior.
- `lean-audit`: mechanical copy-paste duplication — token-window clone
  detection across source and prose (`LA-CODE-DUP-*`) — and duplication/waste
  audits of docs and skill surfaces. Semantic duplication — which boundary
  owns a duplicated concept and where its one meaning lives (`SD-S-2`, the
  DRY principle) — stays with `software-design`.

## 10. Output Contracts

Build, Extract, Review, and Lookup outputs are defined in the skill workflow. All modes must report mode, extensions loaded, reference path, verification layers used, project assimilation, delegations, and limits.
