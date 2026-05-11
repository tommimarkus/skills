---
name: architecture-design
description: Use when building, extracting, reviewing, rendering, validating, or looking up ArchiMate® 3.2 architecture models as dediren packages, especially dediren package source, SVG render quality, optional OEF export, readiness review, drift detection, or reverse lookup from code, UI, API, or workflows to Business Processes.
---

# Architecture Design

## Purpose

Build, extract, review, validate, render, and look up ArchiMate® architecture
models stored as dediren packages. The skill answers what the enterprise,
solution, or application architecture consists of: capabilities, services,
components, technology nodes, relationships, motivation, process ownership, and
the views that communicate those concerns.

The canonical modeling reference is
[../../docs/architecture-reference/architecture.md](../../docs/architecture-reference/architecture.md).
This file is the operational router. Load the referenced procedure files only
when their conditions apply.

## Artifact Contract

The canonical source is a package directory:

```
docs/architecture/<feature>.dediren/
  project.json
  model.json
  render-policy.json
  render-metadata.json
  export-policy.json        # optional; required only for OEF export
  generated/                # ignored output; recreate from source
```

Agents edit package source and policy files. `generated/` is tool output and is
ignored by default. SVG is the primary visual proof for review. OEF is an
optional compatibility export, not the source of truth.

`project.json` lists only actual views. Do not add placeholder view entries for
diagram kinds that are not modeled yet; report missing kinds in the output
footer instead.

## Ownership Boundary

Owns:

- ArchiMate® 3.2 notation decisions and architecture model quality.
- Dediren package source, render policies, SVG render evidence, and optional
  OEF export evidence.
- Build, Extract, Review, Render, Validate, Drift, and Lookup workflows for
  architecture packages.
- Finding namespaces `ARCH-M-*`, `ARCH-V-*`, `ARCH-L-*`, `ARCH-R-*`,
  `ARCH-X-*`, `ARCH-E-*`, and `ARCH-Q-*`.

Does not own:

- C4, UML, BPMN, TOGAF content metamodel, xAF, Archi-native `.archimate`, live
  cloud-resource observation, approval-board governance, or project
  documentation packaging unless the user explicitly asks for that package.
- Business, Motivation, Strategy, or Physical layer extraction from source or
  IaC. These are architect-owned except for explicit process candidates lifted
  from supported workflow sources.

Sibling handoffs:

- `app-design`, `api-design`, and `infra-design` own app, API, and
  infrastructure design; this skill models those surfaces and reviews paired
  `docs/architecture/<feature>.dediren/` packages for architecture drift.
- `devsecops-audit` audits security posture; this skill only models controls
  and workflows as architecture elements.

## When To Use

Use for requests that mention ArchiMate, dediren, architecture package
build/extract/review/render/validation, architecture drift, SVG render quality,
optional OEF export, or reverse lookup from code/UI/API/workflow artifacts to
Business Processes.

Assume Build when the user asks to design architecture without supplying an
existing package. Assume Extract when they supply code/IaC/workflows without a
package. Assume Review when they supply a package or ask whether a model is
well-formed, professional, renderable, review-ready, or drifted. Assume Lookup
for a narrow factual ArchiMate or package question.

Ask before continuing only when the mode, feature, diagram kind, destructive
overwrite, unsupported target, or quality target is genuinely ambiguous.

## When Not To Use

Do not use this skill for UI implementation, HTTP API design, security audits,
test quality, repo release packaging, live cloud drift, or non-ArchiMate
notation work. Refer to the owning sibling skill or explain the boundary.

Refuse Extract when the requested scope is entirely forward-only
(Business/Motivation/Strategy/Physical from source or IaC). Suggest Build with
architect intent instead.

## Modes

- **Build**: create or edit a dediren package from architect intent.
- **Extract**: lift extractable layers from source, IaC, and workflows into a
  dediren package while marking architect-owned content.
- **Review**: assess source validity, view readability, SVG render quality,
  optional export evidence, and drift.
- **Lookup**: answer a bounded notation, package, domain-discovery, or reverse
  lookup question without mutating the package.

## Dediren Runtime Self-Check

Use the tool directly. Select the first executable that exists:

1. `souroldgeezer-architecture/tools/dediren-linux/bin/dediren`
2. `souroldgeezer-architecture/tools/dediren-macos/bin/dediren`

Run `--version` and inspect the adjacent `bundle.json` before claiming runtime
evidence. If neither bundle exists, disclose `not run (missing dediren bundle)`
and cap quality at `source-valid` unless the user only asked for Lookup. There
is no fallback runtime.

Required commands by evidence type:

- Source validity: `dediren validate --input <package>/model.json`
- View projection: `dediren project --input <package>/model.json --plugin <plugin> --view <view> --target <target>`
- Layout: `dediren layout --plugin <plugin> --input <projection.json>`
- Layout validation: `dediren validate-layout --input <layout.json>`
- SVG render: `dediren render --plugin svg-render --policy <package>/render-policy.json --metadata <package>/render-metadata.json --input <layout.json>`
- Optional OEF export: `dediren export --plugin archimate-oef --policy <package>/export-policy.json --source <package>/model.json --layout <layout.json>`

## Minimal Workflow

1. Select the mode and read
   [references/procedures/architecture-operational-workflow.md](references/procedures/architecture-operational-workflow.md).
2. Run the runtime self-check from
   [references/procedures/self-check.md](references/procedures/self-check.md).
3. Assimilate the package from `docs/architecture/<feature>.dediren/` when it
   exists. Preserve valid identifiers, labels, documentation, source evidence,
   policies, and architect-authored intent.
4. Load only the procedure references whose conditions apply. Build and Extract
   mutate source/policy files. Review and Lookup do not mutate by default.
5. Validate before claiming quality. Use source validation, projection, layout,
   SVG render, optional export, and drift checks according to the request and
   available tooling.
6. Return the required footer from
   [references/output-format.md](references/output-format.md).

## Reference Load Map

Load only the files whose conditions apply:

- Use `../../docs/architecture-reference/architecture.md` for notation,
  relationship, package, diagram-kind, and readiness rules.
- Use `references/procedures/architecture-operational-workflow.md`,
  `references/procedures/self-check.md`, and `references/output-format.md` for
  workflow, runtime checks, and response contracts.
- Use `references/smell-catalog.md` and `references/red-flags.md` for Review
  findings and escalation cues.
- Use `references/procedures/professional-readiness.md` for every Build,
  Extract, and Review verdict.
- Use `references/procedures/external-validation-handoff.md` when the user
  supplies downstream importer, schema, or conformant-tool findings for an OEF
  export.
- Use `references/procedures/drift-detection.md` when Review compares package
  source with code, IaC, UI routes, APIs, or workflows.
- For Extract source lifting, load the matching procedure:
  [references/procedures/lifting-rules-dotnet.md](references/procedures/lifting-rules-dotnet.md),
  [references/procedures/lifting-rules-bicep.md](references/procedures/lifting-rules-bicep.md),
  [references/procedures/lifting-rules-gha.md](references/procedures/lifting-rules-gha.md), or
  [references/procedures/lifting-rules-process.md](references/procedures/lifting-rules-process.md).
- For Build or Extract process-view emission, load
  [references/procedures/process-view-emission.md](references/procedures/process-view-emission.md)
  and [references/procedures/seed-views.md](references/procedures/seed-views.md).
- Use `references/fixtures/dediren/basic/` for package fixture examples and
  runtime smoke tests.
- Use `references/evals` and `references/source-grounding.md` for trigger
  metadata, workflow behavior, and evaluation coverage.

## Output Contract

Every final answer must include selected mode, package path, runtime evidence,
quality level, export readiness, verification state, and footer fields from
[references/output-format.md](references/output-format.md).

Minimum footer fields:

- Mode, reference path, architecture package path, primary diagram kind, diagram
  kinds present/missing, and quality target.
- Dediren runtime path and version or missing-bundle disclosure.
- Views listed in `project.json`, per-view readiness, and artifact rollup.
- Source validation, projection, layout, SVG render, optional OEF export, and
  drift status.
- Findings count with `ARCH-*` codes.
- Change classification: semantic model, view membership/layout policy, render
  policy/metadata, export policy, or documentation only.

## Stop Conditions

Stop, ask, fix, or lower the claimed quality when:

- `project.json` references a missing model, policy, metadata, view, or plugin.
- `model.json` fails validation or contains dangling relationships.
- Projection, layout, layout validation, or SVG render returns an error
  envelope.
- SVG output is blank, lacks expected `data-dediren-node-id` or
  `data-dediren-edge-id` markers, or has an incoherent `viewBox`.
- OEF export was requested but `export-policy.json` is missing or export fails.
- A view cannot answer its architecture question, is too dense for the intended
  audience, or omits the primary relationship needed to understand it.
- You cannot distinguish source-derived content from architect-owned intent.
