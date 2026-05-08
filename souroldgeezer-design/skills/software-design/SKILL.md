---
name: software-design
description: >-
  Use when building, extracting, reviewing, or looking up code/module/service/refactor design: boundaries, dependencies, responsibilities, semantics, coupling, evolution, pattern tradeoffs, and .NET™, Java™, Rust®, shell, or Python® tooling. Defer app/UI, API, infra, architecture, security, and test quality.
---

# Software Design

## Contract

Own Build, Extract, Review, and Lookup for boundaries, dependencies,
responsibilities, state/data ownership, semantics, coupling, evolution, pattern
tradeoffs, and debt. Delegate app/UI, API, infra/IaC, ArchiMate/OEF, security,
and test quality to `app-design`, `api-design`, `infra-design`,
`architecture-design`, `devsecops-audit`, and `test-quality-audit`.

Inputs: files, diffs/proposals, intent, and provided evidence. Do not infer
non-static facts from static source. If ambiguous, missing, destructive, or
sibling-owned scope lacks a safe default, ask the user; otherwise continue.

Modes: Build, Extract, Review, Lookup.

## Load Map

Load what applies: core reference
[../../docs/software-reference/software-design.md](../../docs/software-reference/software-design.md)
sections 2-7 and 9; [references/smell-catalog.md](references/smell-catalog.md)
for findings; [references/pattern-catalog.md](references/pattern-catalog.md)
for pattern questions/ceremony; [extensions/dotnet.md](extensions/dotnet.md),
[extensions/java.md](extensions/java.md), [extensions/rust.md](extensions/rust.md),
[extensions/shell-script.md](extensions/shell-script.md), or
[extensions/python.md](extensions/python.md) for matching stack signals;
[extensions/README.md](extensions/README.md) only when editing extensions.
Unknown stacks use core only. Skip Python web/ASGI apps and delegate app/API.

Before changing workflow, extension selection, grounding, evals, or guidance
scope, load [references/evals](references/evals) and
[references/source-grounding.md](references/source-grounding.md). Keep evals
synthetic and require pressure evidence for generic model knowledge.

## Workflow

1. Select mode, scope, and design question.
2. Prefer `rg`; inspect inputs, detect stack, and announce extensions.
3. Assimilate modules, refs/imports, adapters, shared code, terms, duplicate
   models, state owners, pattern ceremony, seams, and debt.
4. Separate fact from inference, choose the smallest coherent move, include
   available mandatory validation, then emit contract/footer.

## Outputs

- Build: forces, justified pattern/rejection, responsibilities, dependencies,
  state owner, validation, delegations.
- Extract: modules, boundaries, ownership, dependencies, hotspots, debt, next move.
- Review: actionable findings only; `block` fragmentation, unsafe path, cycle,
  inversion, duplicate model, shared state, unjustified ceremony, speculation,
  or load-bearing legacy; `warn` risk; `info` note.
- Lookup: direct rule, exception, citation, delegation, one-line footer.

Every final answer reports mode, extensions, reference path, layers (`static`,
`graph`, `history`, `runtime`, `human`), assimilation, delegations, and limits.
Findings use `[SD-<family>-<n>] <file>:<line>` with bucket, layer, severity,
evidence, action, and citation. If none, say so with limits.

When recommending, rejecting, or reviewing a named pattern, report the current
force, fit, avoid case, likely smell prevented, likely smell introduced, and
cheapest validation layer. Treat pattern names as tradeoff vocabulary, not
authority.

## Stop Conditions

Stop when source/scope is missing, sibling ownership dominates, required
non-static facts are absent, load-bearing debt has no smaller safe move,
extension validation is unavailable, generic abstraction lacks current evidence,
or a pattern recommendation cannot name the current force it serves.
