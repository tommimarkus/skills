---
name: architecture-design
description: Use when building, extracting, reviewing, rendering, validating, or looking up ArchiMate® dediren packages, SVG/OEF evidence, drift, or code/IaC/API/UI/workflow reverse lookup.
---

# Architecture Design

Build, Extract, Review, and Lookup ArchiMate® dediren packages. This is the
router; load references only when their conditions apply.

## Package

Canonical source is `docs/architecture/<feature>.dediren/`: edit source and
policies, recreate generated output, use SVG as proof, treat OEF as optional,
and list only actual views in `project.json`.

## Boundary

Owns ArchiMate notation, package source/policies, SVG/OEF evidence, drift, and
`ARCH-*` findings. Delegate UI, API, infra, security, test-quality,
non-ArchiMate notation, and live cloud observation.

## Inputs

Pre-flight: inspect prompt, target package/source paths, existing dediren source,
rendered SVG/OEF evidence, validation logs, requested mode, quality target, and
export need. Infer only the default mode. If target/evidence/scope is missing or
ambiguous, ask the user before edits/findings.

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

1. Read [architecture](../../docs/architecture-reference/architecture.md) and
   [workflow](references/procedures/architecture-operational-workflow.md).
2. Run [self-check](references/procedures/self-check.md) before runtime claims.
3. Preserve ids, labels, source evidence, policies, and architect-owned intent.
4. Load task references below. For ambiguous Build/Extract choices, load
   `references/source-weighting.md` and keep a short rationale. Build/Extract
   may mutate source; Review/Lookup do not mutate by default.
5. Validate before quality claims; return [output](references/output-format.md).
6. Stop when required evidence is missing, dediren returns an error envelope,
   the target is unsupported, or a blocking finding prevents requested readiness.

## References

| Need | Use |
|---|---|
| Review/readiness | `references/smell-catalog.md`, `references/red-flags.md`, `references/procedures/professional-readiness.md` |
| implementation-readiness review | `references/procedures/implementation-readiness-review.md` |
| Source-weighted element/relation selection | `references/source-weighting.md`; details in `../../docs/architecture-reference/source-weighting.md` |
| Drift | `references/procedures/drift-detection.md` |
| OEF/downstream validation | `references/procedures/external-validation-handoff.md` |
| .NET extraction | `references/procedures/lifting-rules-dotnet.md` |
| Bicep extraction | `references/procedures/lifting-rules-bicep.md` |
| GitHub Actions extraction | `references/procedures/lifting-rules-gha.md` |
| Process extraction | `references/procedures/lifting-rules-process.md`, `references/procedures/process-view-emission.md`, `references/procedures/seed-views.md` |
| Examples/smoke tests | `references/fixtures/dediren/basic/` |
| Skill maintenance | `references/evals`, `references/source-grounding.md` |
