---
name: software-design
description: >-
  Use when designing, reviewing, extracting, or looking up code/module boundaries, deps, ownership, coupling, evolution, non-functional/quality requirements, principle/pattern tradeoffs, or C# / .NET™, Java™, Rust®, JavaScript/TypeScript, shell, Python®. Defer UI, API, infra, architecture, security, tests.
---

# Software Design

## Contract

Own Build/Extract/Review/Lookup for code boundaries, dependencies, ownership,
semantics, coupling, evolution, principle/pattern tradeoffs, and debt. Inputs:
files or proposals, intent, and evidence. If the request is ambiguous, inputs
are missing, or scope is uncertain, ask the user; otherwise continue. Also ask
before destructive work or when a sibling owns it without a safe default.
Also own an early-return File Edit lane for bounded non-code changes needing no
software-design judgment; it is not a fifth design mode.
Delegate UI/API/IaC/architecture/security/tests to `app-design`, `api-design`,
`infra-design`, `architecture-design`, `devsecops-audit`, and
`test-quality-audit`. `lean-audit` owns mechanical `LA-CODE-DUP-*` scans;
semantic duplication/DRY stays here (`SD-S-2`).

## Load Map

Before selecting a design mode, use File Edit for a wholly bounded non-code
Markdown, text, JSON/JSONL, YAML, TOML, XML, CSV, INI/properties, or similar
edit needing no code/module design or sibling decision. Load only
[references/procedures/file-edit-lane.md](references/procedures/file-edit-lane.md),
validate, report its narrow result, and return without normal design references,
extensions, procedures, or Outputs.
When cache state is relevant, execute `references/scripts/tool_state.py` without
loading its source; use its `--help` plus `gc` and the selected bounded command.

For Build/Extract/Review, load the whole core reference
[../../docs/software-reference/software-design.md](../../docs/software-reference/software-design.md).
For findings, load [references/smell-catalog.md](references/smell-catalog.md)
and [references/smell-cards.jsonl](references/smell-cards.jsonl).
When changed-code preconditions or adjacent-change risk materially apply, load
[references/procedures/fragility-review.md](references/procedures/fragility-review.md)
and start the material output with its purpose. When configured evidence from a
project-owned tool exists, a relevant tool is `detected-not-run`, or a relevant
optional suggestion is offered, load
[references/procedures/native-tool-evidence.md](references/procedures/native-tool-evidence.md).
For Lookup, skip core: answer from the matched catalog below, cite its named
core section, and name that catalog in the footer. Escalate to Review/Build or
ask when code evidence, cross-section tradeoffs, or an unmatched question is
needed.
Load [references/principles-catalog.md](references/principles-catalog.md) for
principle questions/claims and [references/pattern-catalog.md](references/pattern-catalog.md) for
pattern questions.
Load [references/nfr-catalog.md](references/nfr-catalog.md) for NFRs, quality
attributes, SLAs/SLOs, or latency/availability/throughput targets.
Load
[references/procedures/project-assimilation.md](references/procedures/project-assimilation.md)
for existing source, diffs, manifests, generated clients, shared code, adapters,
state owners, domain vocabulary, or module boundaries.
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
Unknown stacks use core only. Python module/package design stays here; web/ASGI
HTTP contracts delegate `api-design`, and UI delegates `app-design`.

When editing extensions, read
[references/procedures/extension-authoring.md](references/procedures/extension-authoring.md).
Before changing workflow/selection/grounding/evals/scope, load
[references/evals](references/evals) and
[references/source-grounding.md](references/source-grounding.md).

## Workflow

The File Edit lane returns before this workflow.

1. Select and scope Build (new), Extract (existing, unchanged), Review
   (review/audit/check), or Lookup (narrow principle/pattern/status); ask if
   ambiguous.
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
6. Assimilate modules, adapters, terms, models, state owners, seams, and debt
   before choosing reuse, migration, or legacy treatment.
7. Check paired `docs/architecture/<feature>.dediren/` when boundaries or
   dependency direction may affect its code-lifted view.
8. Separate fact from inference; choose the smallest coherent move, validate,
   and emit the contract/footer.
9. For Build implementation, record the design decision, implement
   the smallest coherent move, review diff against the design decision,
   validate, then classify adjacent audit triggers: use/request devsecops-audit
   Quick for security-sensitive edits and test-quality-audit Quick for
   test/fixture/assertion/coverage edits or test-dependent confidence;
   disclose unavailable or not applicable with reason.

## Outputs

Build outputs forces, decisions, responsibilities, deps, state owner,
validation, and delegations. Extract outputs boundaries, deps, hotspots, debt,
and next move. Review outputs findings only: block the
`Default blocks:` classes in
[references/smell-catalog.md](references/smell-catalog.md); warn risks; info
notes. Lookup gives rule, exception, citation, delegation, and footer.

Answers report mode, extensions, reference, layers (`static`, `graph`,
`history`, `runtime`, `human`), assimilation, pairing, delegations, and limits.
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
