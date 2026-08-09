---
name: architecture-design
description: Use when building, extracting, reviewing, rendering, validating, or looking up architecture models and diagrams as ArchiMate® or UML® dediren packages, SVG/OEF/XMI evidence, shareable HTML gallery, drift, cross-notation handoff links, or code/IaC/API/UI/workflow reverse lookup — including plain-language requests for an architecture diagram or model kept and maintained in the repo, even without dediren, ArchiMate®, or UML® vocabulary. Not for diagrams the user wants kept in another format (Mermaid, PlantUML, draw.io), one-off or maintained; UI component hierarchies belong to app-design, code/module structure sketches to software-design.
---

# Architecture Design

Build, Extract, Review, and Lookup ArchiMate® and UML® dediren packages. This is
the router; load references only when their conditions apply.

## Package

Canonical source is `docs/architecture/<feature>.dediren/`: edit source and
policies, recreate generated output, use SVG as proof, treat OEF/XMI as optional
compatibility export, and list only actual views in `package.json`. Elements
shared across packages and the optional `landscape.dediren/` portfolio rollup
follow the cross-package identity convention (architecture §15).

## Boundary

Owns ArchiMate® and UML® notation when the artifact is a dediren
architecture/design package, package source/policies, SVG/OEF/XMI evidence,
drift, cross-package identity and landscape rollup, cross-notation
`properties.uml.architecture_context` handoff links, and
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

- **Build**: create/edit package source from architect intent; close with the
  build readiness disclosure
  ([implementation-readiness-review](references/procedures/implementation-readiness-review.md)
  § Build Readiness Disclosure).
- **Extract**: lift evidenced code/IaC/API/UI/workflow facts; mark
  architect-owned content. Put source-backed groups in `model.json` under
  `plugins.generic-graph.views[].groups`, not `package.json`.
- **Review**: assess validity, readability, SVG, optional export, and drift;
  lead with findings. `dediren_verify` is the artifact-freshness drift gate and
  `dediren_diff` compares two model revisions (architecture §9).
- **Lookup**: answer bounded notation/package/reverse-lookup questions only,
  including structural queries (dependents / orphans / view-coverage) via
  `dediren_query` (architecture §9).

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
   - **Lookup**: only the section the question cites (a structural-query Lookup
     cites §9 for `dediren_query`).
   - Any mode adds §15 cross-package identity when more than one
     `docs/architecture/*.dediren/` package exists and the task touches a
     shared element or the landscape package.

   This map is a floor, not a cap: pull §10 OEF, §11 profile, §14 pitfalls, or
   any other section the moment the task reaches it, and escalate a Lookup to
   the fuller Build/Extract/Review set (or ask) when a bounded answer no longer
   covers the work. Read the
   [operational workflow](references/procedures/architecture-operational-workflow.md)
   before running Build/Extract/Review operational steps; a Lookup that makes no
   runtime claim may skip it.
2. Before any runtime claim, run
   [self-check](references/procedures/self-check.md). The plugin supplies
   Claude Code, Codex, and Copilot MCP adapters, but Dediren itself is the
   host-managed current `dediren` executable (`PATH` or `DEDIREN_COMMAND`) and
   is never bundled or pinned by this plugin. A migration fallback may reuse the
   newest executable already present in the former verified release cache, but
   never downloads one. The router discovers that
   executable's live tool catalog and adds a required absolute `workspaceRoot`
   to every tool call. Drive it through its tools — `dediren_validate`,
   `dediren_build`, `dediren_guide`, plus the four read-only tools `dediren_diff` /
   `dediren_query` / `dediren_verify` / `dediren_status` (architecture §9, wired per
   mode above) — prefer MCP over the CLI. Extract, Review, and Lookup need only the
   read-only tool subset; Build also needs `dediren_build`. When the `dediren_*`
   tools are absent, an internal CLI fallback may drive the same host-managed
   executable; self-check § Server availability owns the availability check and
   exact `source-valid` cap condition. Never auto-install, download, or downgrade
   Dediren from the plugin. Defer
   the format guide (`dediren_guide`) until authoring source JSON, a command
   handoff, or a repair loop is imminent — a notation Lookup or a mechanical edit
   that reaches no runtime command never loads it. Lookup may skip self-check
   entirely when the answer makes no runtime claim.
   The skill's own bundled helper scripts (`build-gallery.py`,
   `svg-accessible-name.py`) live under `${CLAUDE_SKILL_DIR}/references/scripts/`.
   Claude Code™ expands `${CLAUDE_SKILL_DIR}` to the skill's absolute path in this
   SKILL.md body (resolving the installed-plugin cache and this source repo alike);
   the reference procedures (self-check, architecture §9) are read raw and reuse that
   same resolved value. For Codex, resolve `<skill-dir>` once from the loaded
   skill's source path and use `<skill-dir>/references/scripts/`; in this source
   repo that fallback is `souroldgeezer-architecture/skills/architecture-design`.
   Carry the runtime-appropriate resolved path into raw reference procedures.
3. Select notation from `plugins.generic-graph.semantic_profile`, view kinds,
   export request, or prompt. Load
   [`references/notations/archimate.md`](references/notations/archimate.md) for
   ArchiMate. For UML, load
   [`references/notations/uml.md`](references/notations/uml.md) (hub) plus only
   the per-kind file under `references/notations/uml/` for the kind in play:
   `class`, `data`, `activity`, `sequence`, `state-machine`, `use-case`,
   `component`, or `deployment`. For mixed packages, load both notation files
   and bind one single-notation model per notation in `package.json`
   (`models[]`, per-view `model`, `exports[]`; the notation itself rides on each
   `model.json`'s own `semantic_profile`; architecture.md §3, fixture
   `references/fixtures/dediren/mixed/`).
4. Preserve ids, labels, source evidence, policies, architect-owned intent, and
   explicit cross-notation links.
5. Load task references below. In Extract mode, load
   [`references/source-weighting.md`](references/source-weighting.md)
   before selecting ArchiMate element,
   relationship, or view types unless the task is a purely mechanical update to
   an existing package. Keep a compact rationale for every non-obvious
   source-to-ArchiMate choice. Build/Extract may mutate source; Review/Lookup
   do not mutate by default.
6. Validate before quality claims — call the Dediren MCP server's
   `dediren_validate` tool (pass absolute `workspaceRoot` plus the model's
   relative path and `profile`) so `source-valid` covers
   schema plus semantic-profile validation. When a run (re)generates package
   output, build it through the MCP server following self-check § Building a package
   (one `dediren_build` call with `workspaceRoot` and the `package` argument;
   the host-managed `dediren build --package` command is the CLI fallback when
   the server is unavailable). Then complete each rendered SVG's
   accessible name. Return
   [output](references/output-format.md).
7. Whenever this run (re)generates a view's SVG output, rebuild the package
   gallery as the next action:
   `${CLAUDE_SKILL_DIR}/references/scripts/build-gallery.py <package>` (Codex:
   `<skill-dir>/references/scripts/build-gallery.py <package>`). This is
   mode-agnostic (any run that re-renders rebuilds; a Lookup or a read-only Review
   that renders nothing does not). On a read-only pass, run
   `${CLAUDE_SKILL_DIR}/references/scripts/build-gallery.py --check <package>`
   (Codex: `<skill-dir>/references/scripts/build-gallery.py --check <package>`) when a
   committed gallery may have drifted; `dediren_status` indexes package/workspace
   freshness alongside it (architecture §9, non-gating). Disclose the outcome in the
   footer `Gallery:` line. [`references/gallery.md`](references/gallery.md) owns what the gallery is,
   its full input set, and when it goes stale.
8. Stop when required evidence is missing, a dediren MCP tool returns an error
   envelope (or the server is unavailable), the notation is unsupported, or a
   blocking finding prevents requested readiness.

## References

| Need | Use |
|---|---|
| ArchiMate notation/profile | [`references/notations/archimate.md`](references/notations/archimate.md) |
| UML® notation/profile and ArchiMate handoff links | [`references/notations/uml.md`](references/notations/uml.md) |
| Review/readiness | [`references/smell-catalog.md`](references/smell-catalog.md), [`references/red-flags.md`](references/red-flags.md), [`references/procedures/professional-readiness.md`](references/procedures/professional-readiness.md) |
| implementation-readiness review; Build closeout disclosure | [`references/procedures/implementation-readiness-review.md`](references/procedures/implementation-readiness-review.md) |
| Source-weighted ArchiMate element/relation selection | [`references/source-weighting.md`](references/source-weighting.md); details in [`../../docs/architecture-reference/source-weighting.md`](../../docs/architecture-reference/source-weighting.md) |
| Drift / cross-package consistency | [`references/procedures/drift-detection.md`](references/procedures/drift-detection.md) |
| OEF/downstream validation | [`references/procedures/external-validation-handoff.md`](references/procedures/external-validation-handoff.md) |
| Dediren MCP server (execution) | Claude Code, Codex, and Copilot adapters launch [`references/scripts/dediren-mcp.sh`](references/scripts/dediren-mcp.sh), whose router discovers the live tools of the host-managed current `dediren` executable (or an already-installed legacy-cache migration fallback) and adds required `workspaceRoot` routing. The skill requires `dediren_validate` / `dediren_build` / `dediren_guide` plus the read-only `dediren_diff` / `dediren_query` / `dediren_verify` / `dediren_status` (architecture §9); newer tools remain visible. |
| Package build (native `dediren_build {workspaceRoot, package}` lane) | The package manifest is dediren-native `package.json` (`package.schema.v1`); the single-call flow, the `package-build-result` rollup, and the host-managed `build --package` CLI fallback are owned by [`references/procedures/self-check.md`](references/procedures/self-check.md) § Building a package |
| SVG visible title band | [`references/scripts/svg-accessible-name.py`](references/scripts/svg-accessible-name.py); run per rendered view (title = view label, desc = the view's architecture question) before render-ready claims; adds the band and sets the runtime-written name, refusing an unnamed artifact (exit 4); `--check` verifies (§9) |
| .NET extraction | [`references/procedures/lifting-rules-dotnet.md`](references/procedures/lifting-rules-dotnet.md) |
| Java extraction | [`references/procedures/lifting-rules-java.md`](references/procedures/lifting-rules-java.md) |
| Bicep extraction | [`references/procedures/lifting-rules-bicep.md`](references/procedures/lifting-rules-bicep.md) |
| GitHub Actions extraction | [`references/procedures/lifting-rules-gha.md`](references/procedures/lifting-rules-gha.md) |
| Process extraction | [`references/procedures/lifting-rules-process.md`](references/procedures/lifting-rules-process.md), [`references/procedures/process-view-emission.md`](references/procedures/process-view-emission.md), [`references/procedures/seed-views.md`](references/procedures/seed-views.md) |
| Examples/smoke tests | `references/fixtures/dediren/basic/` |
| Mixed-package regression fixture (skill maintenance) | Inspect `references/fixtures/dediren/mixed/` only when changing mixed ArchiMate/UML model bindings, per-model render/export policies, or their regression coverage; do not load it for ordinary model work. |
| Skill maintenance | `references/evals`, [`references/source-grounding.md`](references/source-grounding.md); run `bash -n references/scripts/dediren-mcp.sh` and `python -m py_compile references/scripts/dediren-mcp-router.py` after editing the adapter |
| Shareable gallery build/refresh | [`references/scripts/build-gallery.py`](references/scripts/build-gallery.py) via `${CLAUDE_SKILL_DIR}/references/scripts/build-gallery.py <package>` (Claude Code) or `<skill-dir>/references/scripts/build-gallery.py <package>` (Codex); drift check `--check`; design system in [`references/gallery.md`](references/gallery.md) |
| Gallery builder fixture (tests) | `references/fixtures/dediren/rendered/` — multi-model package (package-level `presentation` lang/dir) with committed `references/fixtures/dediren/rendered/generated/svg/` and `references/fixtures/dediren/rendered/generated/render-metadata/`, built against by the gallery-builder tests |
