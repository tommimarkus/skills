---
name: software-design
description: >-
  Use when designing, reviewing, extracting, or looking up code/module boundaries, deps, algorithms, data structures, data-access efficiency, ownership, coupling, evolution, library compatibility/versioning, non-functional/quality requirements, principle/pattern tradeoffs, or C# / .NET™, Java™, Rust®, JavaScript/TypeScript, shell, Python®, or making bounded non-code text/data edits needing no design decision. Defer UI, API, infra, architecture, security, tests.
---

# Software Design

## Contract

Own Build/Extract/Review/Lookup for code boundaries, dependencies, ownership,
semantics, coupling, evolution, principle/pattern tradeoffs, and debt. Inputs:
files or proposals, intent, and evidence. Continue with safe, task-relevant
judgment within existing authority. Ask the user for a material missing decision or
authority; uncertainty that does not affect the next safe step is not a stop.
Also own an early-return File Edit lane for bounded non-code changes needing no
software-design judgment; it is not a fifth design mode.
Delegate UI/API/IaC/architecture/security/test adequacy to `app-design`,
`api-design`, `infra-design`, `architecture-design`, `devsecops-audit`, and
`test-quality-audit`. `lean-audit` owns mechanical `LA-CODE-DUP-*` scans;
semantic duplication/DRY stays here (`SD-S-2`).

## Load Map

Before selecting a design mode, use File Edit for a wholly bounded non-code
Markdown, text, JSON/JSONL, YAML, TOML, XML, CSV, INI/properties, or similar
edit needing no code/module design or sibling decision. Load only
[references/procedures/file-edit-lane.md](references/procedures/file-edit-lane.md),
validate, report its narrow result, and return without normal design references,
extensions, procedures, or Outputs.
The cache helper is optional; use command help or maintenance only when needed,
without loading its source. From consumer repository, Claude uses
`python3 "${CLAUDE_SKILL_DIR}/references/scripts/tool_state.py" --repo-root "<consumer-repository>"`;
Codex uses `python3 "<absolute-loaded-skill-dir>/references/scripts/tool_state.py" --repo-root "<consumer-repository>"`.
Carry it into raw procedures; never enter the installed skill directory.

Writing or restructuring tests, fixtures, or test helpers, or a `tdd-policy`
handoff, loads only the matched test-code file:
[csharp](extensions/csharp/test-code.md), [java](extensions/java/test-code.md),
[python](extensions/python/test-code.md), [rust](extensions/rust/test-code.md),
[shell](extensions/shell-script/test-code.md),
[typescript](extensions/typescript/test-code.md); not core or `<stack>.md`
unless it also makes production-design claims, then escalate to Build/Review.

For every mode, select relevant sections of the core reference
[../../docs/software-reference/software-design.md](../../docs/software-reference/software-design.md).
Scale reading to the changed behavior and decision; expand when source evidence,
uncertainty, dependencies, or material risk requires it.
For findings, load [references/smell-catalog.md](references/smell-catalog.md)
and [references/smell-cards.jsonl](references/smell-cards.jsonl).
When changed-code preconditions or adjacent-change risk materially apply, load
[references/procedures/fragility-review.md](references/procedures/fragility-review.md)
and start the material output with its purpose. When configured evidence from a
project-owned tool exists, a relevant tool is `detected-not-run`, or a relevant
optional suggestion is offered, load
[references/procedures/native-tool-evidence.md](references/procedures/native-tool-evidence.md).
For Lookup, start from the matched catalog below or core section and read
additional relevant excerpts when needed. Consulting code, multiple sections,
or stacks does not itself require a mode change or approval. Missing runtime
or human evidence limits only the conclusion that depends on it.
Load [references/principles-catalog.md](references/principles-catalog.md) for
principle questions/claims and [references/pattern-catalog.md](references/pattern-catalog.md) for
pattern questions.
Load [references/nfr-catalog.md](references/nfr-catalog.md) for NFRs, quality
attributes, SLAs/SLOs, or latency/availability/throughput targets.
For interactive CLI, background-job, or agent-operation design, load the core
reference's operation-feedback default before judging status ownership, progress
output, cancellation, or detached-job recovery. UI feedback itself remains with
`app-design`.
For Build/Review data paths or explicit debt Extract, load
[data-efficiency](../../docs/design-reference/data-efficiency.md).
Factual Extract skips it; relevant Lookup reads its matched section; File Edit returns.
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
Before stack-specific claims, read relevant sections of matching extensions:
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
   (review/audit/check), or Lookup (narrow principle/pattern/status). Infer the
   useful route from the authorized outcome; ask only for a material ambiguity.
2. Prefer `rg` for repository text; inspect relevant inputs and detect stack.
   Run bounded discovery of repository-configured commands,
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
   and report the useful result and material limits.
9. For Build implementation, record the design decision, implement
   the smallest coherent move, review diff against the design decision,
   validate, and use specialist guidance when a material security or test-quality
   question needs it. A routine test edit does not automatically require a
   separate devsecops-audit Quick or test-quality-audit Quick workflow; retain
   relevant safety and test adequacy checks within the authorized task.

## Outputs

Lead with the result, relevant changes or findings, validation, and material
limits. Build explains consequential decisions; Extract separates observed
structure from judgment; Review gives actionable evidence; Lookup answers the
question directly. Omit routine mode, extension, assimilation, pairing, and
negative inventories unless requested or useful to an actual consumer.

For a requested formal review, findings may use `[SD-<family>-<n>] <file>:<line>`
with severity, evidence, consequence, action, and citation. Extension findings
use defined key codes, never family globs. Explain force, fit, and cheapest
sufficient validation when a principle or pattern materially shapes a decision.

## Stop Conditions
<!-- lean-audit:sync-intentional -->

Stop the affected action when authority or essential evidence is missing, or
when it would introduce a concrete unsafe or incompatible change. Ask for the
material decision, disclose the limited conclusion, and continue independent
source-grounded work. A reference difference, sibling boundary, or absent
optional tool does not by itself halt the task.
