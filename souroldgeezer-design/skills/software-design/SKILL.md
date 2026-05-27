---
name: software-design
description: >-
  Use when designing/reviewing code/module boundaries, deps, ownership, coupling, evolution, pattern tradeoffs, or .NET™, Java™, Rust®, TypeScript, shell, Python® tooling. Defer UI, API, infra, architecture, security, tests.
---

# Software Design

## Contract

Own Build, Extract, Review, and Lookup for code/module boundaries, deps,
ownership, semantics, coupling, evolution, pattern tradeoffs, and debt. Inputs
are files, diffs/proposals, intent, and evidence. If request is ambiguous,
scope/evidence is missing, destructive, or sibling-owned with no safe default,
ask the user; otherwise continue. Delegate UI, API, infra/IaC, architecture,
security, and tests to `app-design`,
`api-design`, `infra-design`, `architecture-design`, `devsecops-audit`, and
`test-quality-audit`.

## Load Map

Load core reference [../../docs/software-reference/software-design.md](../../docs/software-reference/software-design.md)
§§2-7,9. Load [references/smell-catalog.md](references/smell-catalog.md) for
findings and [references/pattern-catalog.md](references/pattern-catalog.md) for
pattern questions. Before stack claims, load matching extensions:
[dotnet](extensions/dotnet.md), [java](extensions/java.md),
[rust](extensions/rust.md), [typescript](extensions/typescript.md),
[shell](extensions/shell-script.md), [python](extensions/python.md).
Unknown stacks use core only; Python web/ASGI delegates app/API.

When editing extensions, load
[references/procedures/extension-authoring.md](references/procedures/extension-authoring.md).
Before changing workflow, selection, grounding, evals, or scope, load
[references/evals](references/evals) and
[references/source-grounding.md](references/source-grounding.md).

## Workflow

1. Select Build, Extract, Review, or Lookup; name scope/question.
2. Prefer `rg`; inspect inputs, detect stack, announce extensions.
3. Assimilate modules/imports, adapters, shared code, terms, models, state
   owners, pattern ceremony, seams, and debt.
4. Separate fact from inference, choose the smallest coherent move, add
   mandatory validation when available, then emit contract/footer.

## Outputs

Build outputs forces, pattern decision, responsibilities, deps, state owner,
validation, and delegations. Extract outputs modules, boundaries, ownership,
deps, hotspots, debt, and next move. Review outputs actionable findings only:
block unsafe fragmentation/cycles/inversions/duplicate models/shared
state/speculation/load-bearing legacy; warn risks; info notes. Lookup gives the
direct rule, exception, citation, delegation, and footer.

Every answer reports mode, extensions, reference path, layers (`static`,
`graph`, `history`, `runtime`, `human`), assimilation, delegations, and limits.
Findings use `[SD-<family>-<n>] <file>:<line>` with bucket, layer, severity,
evidence, action, and citation. Pattern decisions must name force, fit, avoid
case, smell reduced/introduced, and cheapest validation layer.

## Stop Conditions

Stop when source/scope is missing, sibling ownership dominates, required
runtime/human facts are absent, debt has no smaller safe move, extension
validation is unavailable, or a pattern cannot name its current force.
