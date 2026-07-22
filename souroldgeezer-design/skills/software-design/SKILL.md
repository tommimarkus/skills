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

## Load Map

For Build/Extract/Review, load the whole core reference
[../../docs/software-reference/software-design.md](../../docs/software-reference/software-design.md).
For findings, load [references/smell-catalog.md](references/smell-catalog.md)
and [references/smell-cards.jsonl](references/smell-cards.jsonl).
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
2. Prefer `rg`; inspect inputs, detect stack, announce extensions.
3. Assimilate modules/imports, adapters, shared code, terms, models, state
   owners, principle claims, pattern ceremony, seams, and debt; apply project
   assimilation before choosing reuse, migration, or legacy-debt treatment.
4. Check for a paired `docs/architecture/<feature>.dediren/` package when
   module, boundary, or dependency-direction changes may affect a code-lifted
   architecture view.
5. Separate fact from inference, choose the smallest coherent move, validate,
   then emit contract/footer.
6. For Build implementation, record the design decision, implement
   the smallest coherent move, review diff against the design decision,
   validate, then classify adjacent audit triggers: use/request devsecops-audit
   Quick for security-sensitive edits and test-quality-audit Quick for
   test/fixture/assertion/coverage edits or test-dependent confidence;
   disclose unavailable or not applicable with reason.

## Outputs

Build outputs forces, principle/pattern decision, responsibilities, deps, state
owner, validation, and delegations. Extract outputs modules, boundaries, deps,
hotspots, debt, and next move. Review outputs findings only: block the
`Default blocks:` classes in
[references/smell-catalog.md](references/smell-catalog.md); warn risks; info
notes. Lookup gives rule, exception, citation, delegation, and footer.

Answers report mode, extensions, reference path, layers (`static`,
`graph`, `history`, `runtime`, `human`), assimilation, architecture pairing,
delegations, and limits.
Findings use `[SD-<family>-<n>] <file>:<line>` with bucket, layer, severity,
evidence, action, and citation; extension findings cite only that extension's
defined key codes, never its family globs. Principle/pattern decisions name
force, fit/rule, avoid case, smell reduced/introduced, cheapest validation
layer.

## Stop Conditions
<!-- lean-audit:sync-intentional -->

Stop when source/scope is missing, sibling ownership dominates, runtime/human
facts are absent, debt has no smaller safe move, extension validation is
unavailable, or a principle/pattern claim lacks current force.
