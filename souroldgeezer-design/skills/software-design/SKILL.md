---
name: software-design
description: >-
  Use when designing, reviewing, extracting, or looking up code/module boundaries, deps, ownership, coupling, evolution, non-functional/quality requirements, principle/pattern tradeoffs, or C# / .NET™, Java™, Rust®, TypeScript, shell, Python®. Defer UI, API, infra, architecture, security, tests.
---

# Software Design

## Contract

Own Build/Extract/Review/Lookup for code/module boundaries, deps, ownership,
semantics, coupling, evolution, principle/pattern tradeoffs, and debt. Inputs:
files, diffs/proposals, intent, evidence. If request is ambiguous,
scope/evidence is missing, destructive, or sibling-owned with no safe default,
ask the user; otherwise continue.
Delegate UI/API/infra/IaC/architecture/security/tests to `app-design`,
`api-design`, `infra-design`, `architecture-design`, `devsecops-audit`, and
`test-quality-audit`; delegate mechanical copy-paste duplication scans
(token-window clones, `LA-CODE-DUP-*`) to `lean-audit` — semantic
duplication/DRY ownership stays here (`SD-S-2`).
When fragility materially applies: Fragility review checks whether code that
works today introduces hidden assumptions or scatters one design decision across
places that a nearby future change could miss, causing regressions or repeated
refactoring. It is not style review, speculative abstraction, analyzer
enforcement, or development-method enforcement.

## Load Map

For Build/Extract/Review, load the whole core reference
[../../docs/software-reference/software-design.md](../../docs/software-reference/software-design.md).
For findings, load [references/smell-catalog.md](references/smell-catalog.md)
and [references/smell-cards.jsonl](references/smell-cards.jsonl).
Load [references/procedures/fragility-review.md](references/procedures/fragility-review.md)
when Review assesses changed code for hidden preconditions or whether a nearby
change could miss a volatile design decision. Load
[references/procedures/native-tool-evidence.md](references/procedures/native-tool-evidence.md)
only when a repository-configured native tool supplied evidence, a relevant
tool was detected without a repository-owned invocation, or a demonstrated
evidence gap makes one optional suggestion relevant.
For Lookup, do not load the core reference: answer from the matched catalog
below and cite the core-reference section it names for Lookup (a `Cite` column
or a cite sentence). If the lookup needs code evidence, cross-section
tradeoffs, or no catalog row matches, escalate to Review/Build or ask — do not
under-answer from a catalog row.
Lookup footers name the catalog as the loaded reference path.
Load [references/principles-catalog.md](references/principles-catalog.md) for
principle questions/claims and [references/pattern-catalog.md](references/pattern-catalog.md) for
pattern questions.
Load [references/nfr-catalog.md](references/nfr-catalog.md) when
non-functional/quality requirements, SLAs/SLOs, latency/availability/throughput
targets, or quality attributes are in scope.
Load
[references/procedures/project-assimilation.md](references/procedures/project-assimilation.md)
when existing source, diffs, manifests, generated clients, shared libraries,
adapters, state owners, domain vocabulary, or module boundaries are in scope.
Load
[references/procedures/architecture-pairing.md](references/procedures/architecture-pairing.md)
(mechanics canonical in
[../../docs/design-reference/architecture-pairing-core.md](../../docs/design-reference/architecture-pairing-core.md))
when a paired `docs/architecture/<feature>.dediren/` package exists and module,
boundary, or dependency-direction restructuring may affect a code-lifted
architecture view, or the user asks to update architecture after
software-design work.
Before stack claims, load matching extensions:
[csharp](extensions/csharp.md), [java](extensions/java.md), [rust](extensions/rust.md),
[typescript](extensions/typescript.md), [shell](extensions/shell-script.md),
[python](extensions/python.md).
Unknown stacks use core only; Python module/package/application/library
design is owned here — only Python web/ASGI HTTP contracts delegate
`api-design`, and UI delegates `app-design`.

When editing extensions, read
[references/procedures/extension-authoring.md](references/procedures/extension-authoring.md).
Before changing workflow/selection/grounding/evals/scope, load
[references/evals](references/evals) and
[references/source-grounding.md](references/source-grounding.md).

## Workflow

1. Select Build, Extract, Review, or Lookup; name scope/question. Existing
   code with no requested change defaults to Extract; a new
   module/feature/component defaults to Build; review/audit/check wording
   defaults to Review; a narrow principle/pattern/status question defaults
   to Lookup; if still ambiguous, ask.
2. Prefer `rg` for repository text; inspect inputs, detect stack, and announce
   extensions. Run bounded discovery of repository-configured commands,
   host-exposed integrations, and plausible task-relevant installed tools;
   never perform an exhaustive machine crawl.
3. Select tools by task fit, repository convention, authoritative data,
   structured output, failure and side-effect behavior, and maintainability.
   There is no universal MCP, CLI, or script ranking. Prefer an existing
   suitable tool over an ad hoc script or brittle parsing of human-oriented
   output.
4. When Context7 MCP is already exposed by the host and current third-party
   library, API, or tool documentation could affect the work, resolve the
   library and query its documentation before inventing usage. Context7 informs
   capabilities and APIs; local project configuration, installed versions, and
   actual tool output remain authoritative for availability and behavior.
5. If Context7 MCP is absent or insufficient, continue through project
   documentation, local help, official sources, or the smallest validated
   fallback. Do not install Context7, invoke its CLI, or alter MCP configuration.
6. Assimilate modules/imports, adapters, shared code, terms, models, state
   owners, principle claims, pattern ceremony, seams, and debt; apply project
   assimilation before choosing reuse, migration, or legacy-debt treatment.
7. Check for a paired `docs/architecture/<feature>.dediren/` package when
   module, boundary, or dependency-direction changes may affect a code-lifted
   architecture view.
8. Separate fact from inference, choose the smallest coherent move, validate,
   then emit contract/footer.
9. In Review, when fragility materially applies, run the adjacent-change probe
   and the calibrated completion gate from `fragility-review.md`; treat tool
   findings as evidence candidates, not conclusions.
10. For Build implementation, record the design decision, implement
   the smallest coherent move, review diff against the design decision,
   validate, then classify adjacent audit triggers: use/request devsecops-audit
   Quick for security-sensitive edits and test-quality-audit Quick for
   test/fixture/assertion/coverage edits or test-dependent confidence;
   disclose unavailable or not applicable with reason.

## Outputs

Build outputs forces, principle/pattern decision, responsibilities, deps, state
owner, validation, and delegations. Extract outputs modules, boundaries, deps,
hotspots, debt, and next move. Review outputs findings only, with a fragility
completion of `pass`, `warn`, `block`, or `not-assessed` when that review
materially applies: block the
`Default blocks:` classes in
[references/smell-catalog.md](references/smell-catalog.md); warn risks; info
notes. Lookup gives rule, exception, citation, delegation, and footer.

Answers report mode, extensions, reference path, layers (`static`,
`graph`, `history`, `runtime`, `human`), assimilation, architecture pairing,
delegations, and limits.
Findings use a plain-language title and `[SD-<family>-<n>] <file>:<line>` with
bucket, layer, severity, evidence, action, and citation; extension findings
cite only that extension's defined key codes, never its family globs. Principle/pattern decisions name
force, fit/rule, avoid case, smell reduced/introduced, cheapest validation
layer.

## Stop Conditions
<!-- lean-audit:sync-intentional -->

Stop when source/scope is missing, sibling ownership dominates, runtime/human
facts are absent, debt has no smaller safe move, extension validation is
unavailable, or a principle/pattern claim lacks current force.
