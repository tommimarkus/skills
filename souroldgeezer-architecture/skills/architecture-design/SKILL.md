---
name: architecture-design
description: Use when building, extracting, reviewing, rendering, validating, or looking up architecture models and diagrams as ArchiMate® or UML® dediren packages, SVG/OEF/XMI evidence, drift, cross-notation handoff links, or code/IaC/API/UI/workflow reverse lookup.
---

# Architecture Design

Build, Extract, Review, and Lookup ArchiMate® and UML® dediren packages. This is
the router; load references only when their conditions apply.

## Package

Canonical source is `docs/architecture/<feature>.dediren/`: edit source and
policies, recreate generated output, use SVG as proof, treat OEF/XMI as optional
compatibility export, and list only actual views in `project.json`.

## Boundary

Owns ArchiMate® and UML® notation when the artifact is a dediren
architecture/design package, package source/policies, SVG/OEF/XMI evidence,
drift, cross-notation `properties.uml.architecture_context` handoff links, and
`ARCH-*` findings. Delegate UI, API, infra, security, test-quality, live cloud
observation, and implementation details that are not being modeled as package
handoff facts.

## Inputs

Pre-flight: inspect prompt, target package/source paths, existing dediren source,
selected notation/profile, rendered SVG/OEF/XMI evidence, validation logs,
requested mode, quality target, and export need. Infer only the default mode. If
target/evidence/scope is missing or ambiguous, ask the user before
edits/findings.

## Modes

- **Build**: create/edit package source from architect intent.
- **Extract**: lift evidenced code/IaC/API/UI/workflow facts; mark
  architect-owned content. Put source-backed groups in `model.json` under
  `plugins.generic-graph.views[].groups`, not `project.json`.
- **Review**: assess validity, readability, SVG, optional export, and drift;
  lead with findings.
- **Lookup**: answer bounded notation/package/reverse-lookup questions only.

Default: architect intent -> Build; source without package -> Extract; supplied
package/readiness/drift -> Review; narrow fact -> Lookup. Refuse forward-only
Business, Motivation, Strategy, or Physical extraction from source; suggest
Build.

## Workflow

1. Load only the [architecture](../../docs/architecture-reference/architecture.md)
   sections the mode needs; do not read it whole. By mode:
   - **Build / Extract**: §1 operating contract, §2 quality levels, §3 package
     source, §5 relationship discipline, §7 view rules, §9 runtime evidence; add
     §4 layers/aspects and §6 diagram kinds when choosing element or view types;
     Extract also loads §8 source evidence.
   - **Review**: §1 operating contract, §2 quality levels, §7 view rules, §9
     runtime evidence, §12 finding taxonomy, §13 review checklist; add §5
     relationship discipline and §4 layers/aspects when auditing element or
     relationship legality.
   - **Lookup**: only the section the question cites.

   This map is a floor, not a cap: pull §10 OEF, §11 profile, §14 pitfalls, or
   any other section the moment the task reaches it, and escalate a Lookup to
   the fuller Build/Extract/Review set (or ask) when a bounded answer no longer
   covers the work. Read the
   [operational workflow](references/procedures/architecture-operational-workflow.md)
   before running Build/Extract/Review operational steps; a Lookup that makes no
   runtime claim may skip it.
2. Before any runtime claim, run
   [self-check](references/procedures/self-check.md); it uses
   [dediren-release.sh](references/scripts/dediren-release.sh) to resolve the
   pinned GitHub™ release bundle. Defer the bundle agent guide
   (`dediren-release.sh --agent-guide`) until authoring source JSON, a command
   handoff, or a repair loop is imminent — a notation Lookup or a mechanical
   edit that reaches no runtime command never loads it. Lookup may skip
   self-check entirely when the answer makes no runtime claim.
3. Select notation from `plugins.generic-graph.semantic_profile`, view kinds,
   export request, or prompt. Load `references/notations/archimate.md` for
   ArchiMate. For UML, load `references/notations/uml.md` (hub) plus only the
   per-kind file under `references/notations/uml/` for the kind in play:
   `class`, `data`, `activity`, `sequence`, `state-machine`, `use-case`,
   `component`, or `deployment`. For mixed packages, load both notation files
   and bind one single-notation model per notation with the `project.json`
   multi-model `v2` layout (`models[]`, per-view `model`, `exports[]`;
   architecture.md §3, fixture `references/fixtures/dediren/mixed/`).
4. Preserve ids, labels, source evidence, policies, architect-owned intent, and
   explicit cross-notation links.
5. Load task references below. In Extract mode, load
   `references/source-weighting.md` before selecting ArchiMate element,
   relationship, or view types unless the task is a purely mechanical update to
   an existing package. Keep a compact rationale for every non-obvious
   source-to-ArchiMate choice. Build/Extract may mutate source; Review/Lookup
   do not mutate by default.
6. Validate before quality claims; return [output](references/output-format.md).
7. Stop when required evidence is missing, dediren returns an error envelope,
   the notation is unsupported, or a blocking finding prevents requested
   readiness.

## References

| Need | Use |
|---|---|
| ArchiMate notation/profile | `references/notations/archimate.md` |
| UML® notation/profile and ArchiMate handoff links | `references/notations/uml.md` |
| Review/readiness | `references/smell-catalog.md`, `references/red-flags.md`, `references/procedures/professional-readiness.md` |
| implementation-readiness review | `references/procedures/implementation-readiness-review.md` |
| Source-weighted ArchiMate element/relation selection | `references/source-weighting.md`; details in `../../docs/architecture-reference/source-weighting.md` |
| Drift | `references/procedures/drift-detection.md` |
| OEF/downstream validation | `references/procedures/external-validation-handoff.md` |
| Dediren release resolver | `references/scripts/dediren-release.sh`; use through self-check before runtime claims, and run `bash -n references/scripts/dediren-release.sh` when editing the resolver |
| SVG accessible name | `references/scripts/svg-accessible-name.sh`; run per rendered view (title = view label, desc = the view's architecture question) before render-ready claims; `--check` verifies (§9) |
| .NET extraction | `references/procedures/lifting-rules-dotnet.md` |
| Java extraction | `references/procedures/lifting-rules-java.md` |
| Bicep extraction | `references/procedures/lifting-rules-bicep.md` |
| GitHub Actions extraction | `references/procedures/lifting-rules-gha.md` |
| Process extraction | `references/procedures/lifting-rules-process.md`, `references/procedures/process-view-emission.md`, `references/procedures/seed-views.md` |
| Examples/smoke tests | `references/fixtures/dediren/basic/` |
| Skill maintenance | `references/evals`, `references/source-grounding.md` |
