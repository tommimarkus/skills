---
name: software-design
description: Use when building, extracting, reviewing, or looking up sustainable software design for code changes, modules, libraries, services, refactors, or existing codebases, especially when the task needs boundary placement, dependency direction, responsibility assignment, semantic coherence, coupling control, evolutionary design, or .NET™ project/design guidance without duplicating UI, API, architecture-model, security, or test-quality specialist skills.
---

# Software Design

## Overview

Shape software so the current change is coherent, small enough to validate, and cheap to change later. The skill applies the bundled reference at [../../docs/software-reference/software-design.md](../../docs/software-reference/software-design.md) and cites the smell catalog in [references/smell-catalog.md](references/smell-catalog.md).

This is the design companion one layer closer to code than `architecture-design` and one layer more general than `responsive-design` or `serverless-api-design`. It does not produce architecture diagrams, API contracts, UI responsive behavior, security audits, or test-quality classifications.

## Modes

### Build Mode

Use for a new feature, module, workflow, library seam, refactor target, or code change before implementation.

Output a compact design brief:

```text
Mode: Build
Scope:
Forces:
Recommended design:
Boundaries:
Dependency direction:
State / data ownership:
Deferred decisions:
Rejected abstractions:
Validation step:
Delegations:
Footer:
```

### Extract Mode

Use when adapting to an existing codebase or when the user asks what design is already present.

Output a software-design baseline:

```text
Mode: Extract
Scope:
Signals inspected:
Current design map:
Boundary candidates:
Coupling hotspots:
Semantic drift:
Design debt:
Preserve:
Next smallest move:
Delegations:
Footer:
```

### Review Mode

Use for code, pull requests, design proposals, planned implementations, or "is this design good?" questions.

Per finding:

```text
[SD-<family>-<n>] <file>:<line>
  bucket:   waste | boundary | coupling | semantic | evolution | tradeoff | socio-technical
  layer:    static | graph | history | runtime | human
  severity: block | warn | info
  evidence: <short snippet or observed structure>
  action:   <smallest useful design correction>
  ref:      software-design.md section <n.m> + smell code or extension code
```

Block only when the design likely forces expensive fragmentation or makes the requested change unsafe: circular project references, boundary inversion, duplicated domain models, shared mutable domain state, mandatory speculative abstractions, or a load-bearing legacy pattern that new work cannot avoid.

### Lookup Mode

Use for narrow design questions: "Should this be a service?", "Where should this responsibility live?", "Is this abstraction premature?", "How should I split this module?"

Answer in two to six lines, cite the reference section, and include a footer line.

## Default Dispatch

- Existing repo with no specific change: Extract.
- New feature or refactor request: Build.
- Existing code or proposal with review/audit/is-this-good wording: Review.
- Narrow principle or tradeoff question: Lookup.
- Ambiguous request: ask the user to choose.

## Extensions

Load extensions only when source signals match.

| Extension | Applies to | Loaded when target matches |
|---|---|---|
| [extensions/dotnet.md](extensions/dotnet.md) | .NET solution and project design | `.sln`, `.slnx`, `.csproj`, `.cs`, `Directory.Build.*`, `global.json`, `InternalsVisibleTo`, `IServiceCollection`, `DbContext`, `BackgroundService`, or package references commonly used in .NET applications |

Unknown stacks proceed with the core reference only. The .NET extension adds stack-specific evidence and smell codes in the `dotnet.SD-*` namespace; it never overrides core rules.

## Pre-Flight

Before build, extract, or review:

1. Identify mode and scope. If the user supplied files, read only the relevant slice first.
2. Identify the design question: smallest change, boundary placement, dependency direction, semantic model, refactor path, tradeoff, or ownership fit.
3. Detect stack and load matching extensions. Announce loaded extensions.
4. Read the reference sections needed for the mode:
   - Principles and defaults: reference sections 2 and 3.
   - Primitives and patterns: sections 4 and 5.
   - Smells and checklist: sections 6 and 7 plus [references/smell-catalog.md](references/smell-catalog.md).
5. State verification layers available from the current evidence: `static`, `graph`, `history`, `runtime`, `human`.
6. Delegate instead of stretching the skill when the request belongs to a sibling skill.

If the user has not supplied a product/domain constraint, default to the smallest coherent design that satisfies the source-readable requirement and leaves deferred decisions explicit.

## Project Assimilation

Assimilation is one-way: the project is brought up to the reference; the reference is not weakened to match local drift.

For build and review work in an existing repo, inspect these signals before recommending a design:

1. Module/project/package shape: solution files, project files, package manifests, top-level directories.
2. Dependency direction: project references, imports/usings, adapters, shared libraries.
3. Semantic boundaries: repeated domain terms, duplicated models, DTO/entity/domain leakage.
4. Change-locality evidence: recent churn if history is in scope, duplicated edits, fan-out hotspots.
5. Existing compliant seams worth preserving.
6. Legacy debt that must not be extended silently.

Reuse compliant infrastructure and names. Flag non-compliant design as legacy debt. If legacy debt is load-bearing for the requested change, halt and ask whether to expand scope or choose a smaller safe change.

## Build Workflow

1. Confirm Build mode and load extensions.
2. Frame scope as in/out. Name the design forces using reference section 3.
3. Choose the smallest design primitive or pattern from reference sections 4 and 5.
4. Define responsibilities and dependency direction. Prefer hiding volatile decisions behind the boundary that owns them.
5. Name deferred decisions and rejected abstractions. This is mandatory when common abstractions are tempting but unjustified.
6. Pick the cheapest validation step: a narrow implementation spike, characterization test, design review with a domain expert, dependency-graph check, or runtime measurement.
7. Emit the Build output contract and footer.

## Extract Workflow

1. Confirm Extract mode and load extensions.
2. Inspect source-readable structure first. Use `rg`/file reads, project manifests, import/reference graphs, and only then history/runtime/human evidence if the user supplied or approved it.
3. Separate facts from inference. Mark inferred intent explicitly.
4. Produce a current design map: modules, boundaries, ownership signals, dependency direction, semantic clusters, coupling hotspots, and preserved seams.
5. Identify the next smallest useful design move. Avoid proposing a broad redesign when one boundary correction or deletion of a speculative abstraction would unlock the work.
6. Emit the Extract output contract and footer.

## Review Workflow

1. Confirm Review mode and load extensions.
2. Walk the checklist in reference section 7 and the smell catalog.
3. Emit only actionable findings. Do not pad with generic best-practice commentary.
4. Use severity consistently:
   - `block`: likely fragmentation, unsafe change path, or mandatory new-code routing through a bad design.
   - `warn`: maintainability or evolution risk with a clear smaller correction.
   - `info`: useful design note or deferred validation.
5. Keep layer claims honest. Static review cannot prove runtime, history, or human/ownership facts.
6. Follow findings with a short rollup and footer.

## Lookup Workflow

1. Locate the relevant reference section or smell code.
2. Answer directly with the default rule and the exception boundary.
3. Recommend a sibling skill only when the question crosses into that sibling's scope.
4. Emit a one-line footer.

## Delegation Boundaries

- UI responsiveness, WCAG, i18n, visual behavior, and Core Web Vitals: `responsive-design`.
- HTTP API contract, auth, reliability, serverless runtime, API observability, and Azure data-service patterns: `serverless-api-design`.
- ArchiMate models, OEF XML, enterprise/solution architecture, and code-to-architecture drift: `architecture-design`.
- Pipeline, IaC, release, or application security posture: `devsecops-audit`.
- Unit/integration/E2E test quality or mutation-testing worklists: `test-quality-audit`.

## Footer

Every mode emits:

```text
Mode:
Extensions loaded:
Reference path: souroldgeezer-design/docs/software-reference/software-design.md
Verification layers used:
Project assimilation:
Delegations:
Limits:
```

## Red Flags

Stop and revise before delivering if output:

- Adds a generic interface, base class, repository, event bus, mediator, plugin system, shared kernel, or framework layer without current evidence.
- Moves logic only to match folder names while preserving the same coupling.
- Duplicates a domain model or vocabulary in a second boundary without naming the translation rule.
- Claims runtime performance, production operability, team ownership, or change-frequency facts from static source alone.
- Extends a legacy design violation into new code without flagging it.
- Reviews API, UI, security, test quality, or ArchiMate concerns instead of delegating.
