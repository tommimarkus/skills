---
name: software-design
description: >-
  Use when building, extracting, reviewing, or looking up code/module/service/refactor design: boundaries, dependencies, responsibilities, semantics, coupling, evolution, and .NET™, shell, or Python® tooling. Defer app/UI, API, infra, architecture, security, and test-quality work.
---

# Software Design

## Purpose

Shape code-, script-, and module-level design so changes stay coherent. Use
[../../docs/software-reference/software-design.md](../../docs/software-reference/software-design.md)
and [references/smell-catalog.md](references/smell-catalog.md).

## Contract

Own Build, Extract, Review, and Lookup for boundaries, dependencies,
responsibilities, state/data ownership, semantics, coupling, evolution, and debt.
Delegate app/UI, API, infra/IaC, ArchiMate/OEF, security, and test quality to
`app-design`, `api-design`, `infra-design`, `architecture-design`,
`devsecops-audit`, and `test-quality-audit`.

Inputs: files, diffs/proposals, intent, and provided history/runtime/human
evidence. Do not infer non-static facts from static source. If the request is
ambiguous, ask the user when mode, scope, source, evidence cost, destructive
edits, or sibling ownership lack a safe default; otherwise continue.

Modes: Build new/refactored design; Extract existing design; Review code, PRs,
proposals, or plans; Lookup narrow principles/tradeoffs.

## Load Map

Load what applies: core reference sections 2-7 and 9;
[references/smell-catalog.md](references/smell-catalog.md) for `SD-*` findings;
[extensions/dotnet.md](extensions/dotnet.md) for .NET solution/project signals;
[extensions/shell-script.md](extensions/shell-script.md) for shell or portability
signals; [extensions/python.md](extensions/python.md) for repo-internal Python
tooling signals; and [extensions/README.md](extensions/README.md) only when
editing extensions. Skip Python web/ASGI apps and delegate app/API concerns.

Before changing trigger metadata, workflow, extension selection, grounding, or
evals, load [references/evals](references/evals) and
[references/source-grounding.md](references/source-grounding.md); keep evals
synthetic/paraphrased. Unknown stacks use core only.

## Workflow

1. Select mode, scope, and design question.
2. Prefer `rg`; inspect inputs, detect stack, and announce extensions.
3. Assimilate modules, refs/imports, adapters, shared code, terms, duplicated
   models, state owners, seams, and debt.
4. Separate fact from inference, choose the smallest coherent move, include
   available mandatory extension validation, then emit contract/footer.

## Mode Outputs

- Build: scope/forces, pattern, responsibilities, dependencies, state owner,
  deferred decisions, rejected abstractions, validation, delegations.
- Extract: modules, boundaries, ownership, dependencies, clusters, hotspots,
  seams, debt, next move.
- Review: actionable findings only; `block` fragmentation, unsafe path, cycle,
  inversion, duplicate model, shared state, speculation, or load-bearing legacy;
  `warn` risk, `info` note/deferred check.
- Lookup: direct rule, exception, citation, delegation, one-line footer.

Every final answer reports mode, extensions, reference path, verification layers
(`static`, `graph`, `history`, `runtime`, `human`), assimilation, delegations,
and limits. Findings use `[SD-<family>-<n>] <file>:<line>` with bucket, layer,
severity, evidence, action, and citation. If none, say so with limits.

## Stop Conditions

Stop when source/scope is missing, sibling ownership dominates, required
non-static facts are absent, load-bearing debt has no smaller safe move,
extension validation is unavailable, or a generic interface/base/repository/bus/
mediator/shared-kernel/plugin/framework layer lacks current evidence.
