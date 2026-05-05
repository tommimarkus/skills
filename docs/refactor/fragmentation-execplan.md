# Fragmentation Refactor ExecPlan

Status: In progress  
Branch: `refactor/fragmentation-cleanup`  
Worktree: `.worktrees/fragmentation-refactor`  
Coordinator model: `gpt-5.5`  
Coordinator reasoning effort: `xhigh`

## Goal

Reduce fragmentation in the `tommimarkus/skills` plugin/skill repository while preserving installability, runtime parity, and existing capabilities.

The intended product boundary is:

```text
souroldgeezer-audit
  devsecops-audit and audit references

souroldgeezer-design
  software-design
  responsive-design
  api-design

souroldgeezer-architecture
  architecture-design
  OEF XML / ArchiMate® support
  layout/runtime/render validation references
  architecture schemas and procedures

souroldgeezer-ops
  issue-ops and operational workflows
```

## Non-goals

- Do not rewrite skill content for taste only.
- Do not remove shipped capability without an explicit migration note.
- Do not add temporary refactor agents to the repository’s shipped `.codex/agents/` directory.
- Do not broaden this into unrelated prompt, style, naming, or branding rewrites.
- Do not let runtime wrappers become independent sources of behavior.
- Do not merge or declare completion while JSON, TOML, unit tests, parity checks, or the skill architecture report fail.

## Invariants

- Published plugin manifests must remain valid JSON.
- TOML surfaces must remain parseable.
- Marketplace entries must point to existing plugin paths.
- Claude and Codex metadata must describe the same user-facing capability.
- `SKILL.md` files remain the canonical behavioral source for skills.
- Runtime wrappers may launch or route, but must not duplicate full workflows.
- Heavy examples, rubrics, procedure tables, layout details, XML details, and validation procedures should live behind explicit load conditions.
- The root README should become a product map, not a full manual.
- Architecture capability should be split into `souroldgeezer-architecture` unless implementation evidence shows that a staged isolation approach is safer.
- Validation commands run from the main checkout must not recursively scan `.worktrees/`.

## Operating Model

Use one branch and one worktree for the whole refactor:

```text
Branch:   refactor/fragmentation-cleanup
Worktree: .worktrees/fragmentation-refactor
```

Use commits as phase boundaries instead of separate branches:

```text
P0: Add this ExecPlan and baseline map
P1: Fix manifests and validation gates
P2: Add runtime metadata parity validation
P3: Split architecture into dedicated plugin
P4: Slim architecture-design/SKILL.md
P5: Simplify public docs and add release checklist
P6: Final validation and review
```

## Global Verification Commands

Run these from `.worktrees/fragmentation-refactor` after each phase:

```bash
find . -name '*.json' -print0 | xargs -0 -n1 jq -e .

python - <<'PY'
import pathlib, tomllib

for path in pathlib.Path(".").rglob("*.toml"):
    tomllib.loads(path.read_text())

print("TOML OK")
PY

python -m unittest
python scripts/check-runtime-metadata-parity.py --check .
scripts/validate-fragmentation.sh
scripts/skill-architecture-report.sh --strict .
git status --short
```

The P2 runtime parity checker is part of the recurring verification set and is
also called by `scripts/validate-fragmentation.sh`.

P0 discovered that bare `python -m unittest` exited `5` because the repo's tests
use the `*_test.py` filename pattern under `tests/`. P1 restored that recurring
command with a root discovery shim.
P1 decision: restore bare `python -m unittest` with a root discovery shim and
add a repo-local validation script for JSON, TOML, marketplace path, and plugin
manifest checks.

When validating from the main checkout root instead of the worktree, prune `.worktrees/`:

```bash
find . \
  -path './.worktrees' -prune -o \
  -name '*.json' -print0 \
  | xargs -0 -n1 jq -e .
```

## Phase Board

| Phase | Status | Owner | Goal | Acceptance |
|---|---|---|---|---|
| P0 | Done | Coordinator + `sog_baseline_explorer` | Create plan and baseline map | ExecPlan exists; surfaces and drift points documented |
| P1 | Done | `sog_manifest_ci` | Fix manifest validity and add syntax/path gates | JSON/TOML/path checks pass and are scripted; bare `python -m unittest` now reaches the `*_test.py` suite |
| P2 | Done | `sog_runtime_parity` | Prevent Claude/Codex metadata drift | Checker detects drift; tests exist |
| P3 | Done | `sog_architecture_split` | Split architecture out of design | `souroldgeezer-architecture` exists; manifests pass; migration note exists |
| P4 | Todo | `sog_skill_slimming` | Slim architecture skill into compact router | Heavy material moved to references with load conditions |
| P5 | Done | `sog_docs_release` | Simplify README and add plugin/release docs | README is a map; docs/plugins and release checklist exist |
| P6 | Todo | `sog_final_reviewer` | Final read-only review and validation | All checks pass; reviewer returns merge/no-merge |

## P0 Baseline Map

### Published plugin catalog

Current shared marketplace:

```text
souroldgeezer-audit   0.3.2  ./souroldgeezer-audit
souroldgeezer-design  0.31.0 ./souroldgeezer-design
souroldgeezer-ops     0.3.2  ./souroldgeezer-ops
```

Each published plugin currently has matching Claude Code and Codex plugin
manifests:

```text
souroldgeezer-*/.claude-plugin/plugin.json
souroldgeezer-*/.codex-plugin/plugin.json
```

The quick baseline found plugin `name`, `version`, `description`, Codex
`skills`, and Codex `interface.defaultPrompt` count synchronized across the
three shipped plugins. The current Codex prompt count is three for every plugin.

### Runtime surfaces

Skill runtime source:

```text
souroldgeezer-audit/skills/devsecops-audit/SKILL.md
souroldgeezer-audit/skills/test-quality-audit/SKILL.md
souroldgeezer-design/skills/api-design/SKILL.md
souroldgeezer-architecture/skills/architecture-design/SKILL.md
souroldgeezer-design/skills/responsive-design/SKILL.md
souroldgeezer-design/skills/software-design/SKILL.md
souroldgeezer-ops/skills/issue-ops/SKILL.md
souroldgeezer-ops/skills/pr-ops/SKILL.md
```

Claude Code subagent surfaces:

```text
souroldgeezer-audit/agents/devsecops-audit.md
souroldgeezer-audit/agents/test-quality-audit.md
souroldgeezer-design/agents/api-design.md
souroldgeezer-architecture/agents/architecture-design.md
souroldgeezer-design/agents/responsive-design.md
souroldgeezer-design/agents/software-design.md
souroldgeezer-ops/agents/issue-ops.md
souroldgeezer-ops/agents/pr-ops.md
```

Codex project wrappers:

```text
.codex/agents/api-design.toml
.codex/agents/architecture-design.toml
.codex/agents/devsecops-audit.toml
.codex/agents/github-issue-lifecycle.toml
.codex/agents/issue-ops.toml
.codex/agents/pr-ops.toml
.codex/agents/responsive-design.toml
.codex/agents/software-design.toml
.codex/agents/test-quality-audit.toml
```

Codex per-skill metadata:

```text
souroldgeezer-*/skills/*/agents/openai.yaml
```

Repo-internal authoring overlays:

```text
.claude/skills/github-issue-lifecycle/SKILL.md
.claude/skills/ip-hygiene/SKILL.md
```

### Duplicated metadata surfaces

- Plugin `name`, `version`, and `description` are repeated in the shared
  marketplace plus both plugin manifests.
- Skill trigger descriptions are repeated in `SKILL.md` frontmatter,
  `agents/*.md` frontmatter, `.codex/agents/*.toml`, and
  `skills/*/agents/openai.yaml`.
- Plugin positioning and install guidance are repeated across `README.md`,
  `CLAUDE.md`, and `AGENTS.md`.
- Architecture capability is described in `souroldgeezer-design` manifests,
  README tables, Claude subagent prose, Codex metadata, the architecture skill,
  reference docs, runtime scripts, schemas, Java tooling, and fixtures.
- Issue/PR lifecycle behavior is intentionally split across public skills,
  GitHub provider extensions, repo-internal overlay guidance, and Codex wrappers;
  wrappers must remain routing surfaces rather than behavior sources.

### Behavior duplicated outside canonical `SKILL.md`

- `souroldgeezer-architecture/agents/architecture-design.md` contains detailed
  architecture workflow steps, finding-code lists, layout routing behavior, and
  render/readiness logic that overlap with canonical
  `architecture-design/SKILL.md` plus references. This is the largest behavior
  duplication risk and a target for P3/P4 routing cleanup.
- `README.md` and `CLAUDE.md` currently carry extensive architecture behavior,
  layout-runtime, render, and readiness details that should become calmer public
  and authoring summaries after the split.
- `responsive-design` and `api-design` correctly reference architecture drift
  handoff behavior, but their current text assumes `architecture-design` is in
  the same `souroldgeezer-design` plugin.
- Runtime scripts and Java tooling encode deterministic architecture behavior;
  they should stay as machinery, with `SKILL.md` and references explaining when
  to invoke them.

### Validation scripts and tests discovered

Repo-level validation:

```text
scripts/skill-architecture-report.sh
scripts/skill_architecture_report.py
tests/skill_architecture_report_test.py
tests/skill_architecture_report_ledger.jsonl
tests/generate_skill_architecture_report_ledger.py
```

Architecture runtime and render tests:

```text
tests/archi_render_script_test.py
tests/validate_model_script_test.py
tools/architecture-layout-java/src/test/java/com/souroldgeezer/architecture/layout/ArchLayoutCliTest.java
tools/architecture-layout-java/src/test/java/com/souroldgeezer/architecture/layout/geometry/GeometryTest.java
tools/architecture-layout-java/src/test/java/com/souroldgeezer/architecture/layout/png/PngAnalyzerTest.java
```

### P1 validation evidence

Recurring validation script:

```text
scripts/validate-fragmentation.sh
```

Passing commands from this worktree:

```text
scripts/validate-fragmentation.sh
python -m unittest
python -m unittest discover -s tests -p '*_test.py'
```

Observed results:

```text
JSON OK
TOML OK
Marketplace paths OK
Plugin manifests OK
Ran 21 tests
```

### Size and fragmentation signal

Current `SKILL.md` sizes:

```text
  9409 souroldgeezer-ops/skills/issue-ops/SKILL.md
 10709 souroldgeezer-audit/skills/test-quality-audit/SKILL.md
 11086 souroldgeezer-audit/skills/devsecops-audit/SKILL.md
 11171 souroldgeezer-design/skills/software-design/SKILL.md
 12200 souroldgeezer-ops/skills/pr-ops/SKILL.md
 26907 souroldgeezer-design/skills/responsive-design/SKILL.md
 35492 souroldgeezer-design/skills/api-design/SKILL.md
 67931 souroldgeezer-architecture/skills/architecture-design/SKILL.md
```

The architecture skill is the clear slimming target for P4. P3 should move it
without slimming except for path corrections.

### Constraints and drift points

- The current repo still presents three public plugins; P3/P5 must update it to
  four public plugins when `souroldgeezer-architecture` lands.
- Local Codex marketplace installs can diverge from source; packaging docs must
  keep the local refresh caveat.
- `docs/refactor/codex-master-prompt.md` and
  `docs/refactor/fragmentation-runbook.md` are currently untracked. They were
  left untouched in P0 and should be reconciled only if a later phase explicitly
  chooses to ship them.
- No committed canonical `docs/architecture/*.oef.xml` product models were
  found in this checkout; architecture OEFs are fixtures under the skill
  reference tree.

## P0 — Plan and Baseline

Goal:

Create this ExecPlan and document the current repository surfaces.

Tasks:

- Create `docs/refactor/fragmentation-execplan.md`.
- Use `sog_baseline_explorer` for read-only mapping.
- Map plugin manifests.
- Map marketplace files.
- Map Claude runtime surfaces.
- Map Codex runtime surfaces.
- Map `SKILL.md` files.
- Map per-skill `agents/openai.yaml` files.
- Map README and docs surfaces.
- Identify duplicated metadata.
- Identify behavior duplicated outside canonical skills.
- Identify validation scripts and tests.

Acceptance:

```bash
test -f docs/refactor/fragmentation-execplan.md
grep -q "P1" docs/refactor/fragmentation-execplan.md
grep -q ".worktrees/fragmentation-refactor" docs/refactor/fragmentation-execplan.md
```

Suggested commit:

```bash
git add docs/refactor/fragmentation-execplan.md
git commit -m "Add fragmentation refactor ExecPlan"
```

Completion notes:

```text
Completed 2026-05-05. `sog_baseline_explorer` ran read-only and the coordinator
cross-checked manifests, runtime metadata surfaces, skill sizes, architecture
asset locations, and validation tooling. No product files were edited beyond
this ExecPlan in P0.
```

## P1 — Manifest and Validation Gates

Goal:

Fix blocker-level syntax and manifest issues, then add deterministic validation so future breakage is caught early.

Tasks:

- Use `sog_manifest_ci`.
- Parse all JSON files.
- Parse all TOML files.
- Check marketplace plugin paths.
- Check plugin manifest shape.
- Check documented starter-prompt or manifest constraints.
- Make bare `python -m unittest` run the repo test suite, or replace the
  recurring command with an explicit discovery command if that proves safer.
- Add a local script or CI step for these checks.
- Keep changes minimal.
- Do not restructure plugins.
- Do not move architecture assets.

Acceptance:

```bash
find . -name '*.json' -print0 | xargs -0 -n1 jq -e .

python - <<'PY'
import pathlib, tomllib

for path in pathlib.Path(".").rglob("*.toml"):
    tomllib.loads(path.read_text())

print("TOML OK")
PY

python -m unittest
scripts/skill-architecture-report.sh --strict .
```

Additional acceptance:

```text
Manifest/path check exists and passes.
The ExecPlan progress log is updated with evidence.
```

Suggested commit:

```bash
git add .
git commit -m "Fix manifests and add validation gates"
```

Completion notes:

```text
Completed 2026-05-05. `sog_manifest_ci` added a root unittest discovery shim
and a marketplace-driven local validation script. The script parses JSON, parses
TOML, validates marketplace plugin paths, validates Claude/Codex plugin manifest
shape, checks marketplace-to-manifest name/version/description alignment, and
runs `python -m unittest`.
```

## P2 — Runtime Metadata Parity

Goal:

Prevent drift across Claude, Codex, README, marketplace, and per-skill metadata.

Tasks:

- Use `sog_runtime_parity`.
- Inventory canonical metadata fields.
- Identify generated or validated surfaces.
- Choose the least invasive durable approach:
  - source-of-truth metadata plus generator, or
  - strict parity checker.
- Add tests for drift detection.
- Avoid changing skill workflows.
- Avoid changing plugin boundaries in this phase.

Metadata surfaces to inspect:

```text
root marketplace JSON
.claude-plugin manifests
.codex-plugin manifests
.claude agents
.codex agents
per-skill agents/openai.yaml
SKILL.md frontmatter
README plugin tables
docs plugin tables
```

Acceptance:

```bash
python -m unittest
python scripts/check-runtime-metadata-parity.py --check .
scripts/skill-architecture-report.sh --strict .
```

Additional acceptance:

```text
A parity checker or generator check exists.
At least one test proves metadata drift is detected.
Canonical field map is documented.
The new parity command is added to the global verification set.
```

Canonical metadata field map:

| Canonical field | Canonical source | Validated/generated surfaces |
|---|---|---|
| Plugin `name` | `.claude-plugin/marketplace.json#plugins[].name` | `<plugin>/.claude-plugin/plugin.json#name`, `<plugin>/.codex-plugin/plugin.json#name` |
| Plugin `version` | `.claude-plugin/marketplace.json#plugins[].version` | `<plugin>/.claude-plugin/plugin.json#version`, `<plugin>/.codex-plugin/plugin.json#version` |
| Plugin `description` | `.claude-plugin/marketplace.json#plugins[].description` | `<plugin>/.claude-plugin/plugin.json#description`, `<plugin>/.codex-plugin/plugin.json#description` |
| Codex plugin skill root | Repo convention | `<plugin>/.codex-plugin/plugin.json#skills == "./skills/"` |
| Public skill `name` | `<plugin>/skills/<skill>/SKILL.md` frontmatter `name`, matching directory name | `<plugin>/agents/<skill>.md` frontmatter `name`, `.codex/agents/<skill>.toml#name` |
| Public skill trigger `description` | `<plugin>/skills/<skill>/SKILL.md` frontmatter `description` | `<plugin>/agents/<skill>.md` frontmatter `description`, `.codex/agents/<skill>.toml#description`, `<plugin>/skills/<skill>/agents/openai.yaml#interface.short_description` |
| Codex per-skill display name | Deterministic title case of the skill name, preserving known acronyms (`API`, `DevSecOps`, `PR`) | `<plugin>/skills/<skill>/agents/openai.yaml#interface.display_name` |
| Repo-internal Codex wrapper `name` and `description` | `.claude/skills/<name>/SKILL.md` frontmatter | `.codex/agents/<name>.toml#name`, `.codex/agents/<name>.toml#description` when no public skill of that name exists |
| README plugin tables | Public skill inventory | `README.md` must link every shipped public skill as `[skill](<plugin>/skills/<skill>/SKILL.md)` |
| Docs plugin tables | Public skill inventory when docs plugin pages exist | `docs/plugins/*.md` pages that mention a plugin must link every shipped public skill for that plugin using a doc-relative link |

P2 chose a strict checker over a generator. `SKILL.md` frontmatter remains the
canonical behavioral trigger surface for public skills; generated
source-of-truth metadata files would be more invasive and would add a second surface
before the P3 plugin split.

Suggested commit:

```bash
git add .
git commit -m "Add runtime metadata parity validation"
```

Completion notes:

```text
Completed 2026-05-05. Added `scripts/check-runtime-metadata-parity.py --check`
as a strict marketplace-driven parity checker, added drift-detection unittest
coverage, aligned metadata-only Codex wrapper and per-skill `openai.yaml`
descriptions to canonical `SKILL.md` frontmatter, and wired the checker into
`scripts/validate-fragmentation.sh`.
```

## P3 — Architecture Plugin Split

Goal:

Split architecture capability out of `souroldgeezer-design` into a dedicated `souroldgeezer-architecture` plugin, unless implementation evidence shows a staged isolation approach is safer.

Target boundary:

```text
souroldgeezer-design:
  software-design
  responsive-design
  api-design

souroldgeezer-architecture:
  architecture-design
  OEF XML support
  ArchiMate® support
  layout runtime support
  render validation
  architecture schemas
  architecture references
  architecture procedures
```

Tasks:

- Use `sog_architecture_split`.
- Create `souroldgeezer-architecture`.
- Move architecture skill assets.
- Move architecture references and schemas as appropriate.
- Update Claude plugin manifests.
- Update Codex plugin manifests.
- Update marketplace entries.
- Update runtime metadata/parity expectations.
- Update README or plugin docs minimally.
- Add migration note for users who expected architecture inside design.
- Preserve installability.
- Preserve behavior.
- Do not slim `architecture-design/SKILL.md` in this phase except for path corrections.

Acceptance:

```bash
find . -name '*.json' -print0 | xargs -0 -n1 jq -e .

python - <<'PY'
import pathlib, tomllib

for path in pathlib.Path(".").rglob("*.toml"):
    tomllib.loads(path.read_text())

print("TOML OK")
PY

python -m unittest
scripts/skill-architecture-report.sh --strict .
test -d souroldgeezer-architecture
```

Additional acceptance:

```text
Old path to new path move map is documented.
Migration note exists.
Design plugin no longer presents architecture as part of its primary scope.
Architecture plugin is installable for supported runtimes.
```

Suggested commit:

```bash
git add .
git commit -m "Split architecture design into dedicated plugin"
```

P3 move map:

```text
souroldgeezer-design/agents/architecture-design.md
  -> souroldgeezer-architecture/agents/architecture-design.md

souroldgeezer-design/docs/architecture-reference/
  -> souroldgeezer-architecture/docs/architecture-reference/

souroldgeezer-design/skills/architecture-design/
  -> souroldgeezer-architecture/skills/architecture-design/

souroldgeezer-design/skills/architecture-design/references/bin/arch-layout.jar
  -> souroldgeezer-architecture/skills/architecture-design/references/bin/arch-layout.jar

souroldgeezer-design/skills/architecture-design/references/scripts/
  -> souroldgeezer-architecture/skills/architecture-design/references/scripts/

souroldgeezer-design/skills/architecture-design/references/schemas/
  -> souroldgeezer-architecture/skills/architecture-design/references/schemas/

souroldgeezer-design/skills/architecture-design/references/fixtures/
  -> souroldgeezer-architecture/skills/architecture-design/references/fixtures/

souroldgeezer-design/skills/architecture-design/references/procedures/
  -> souroldgeezer-architecture/skills/architecture-design/references/procedures/

souroldgeezer-design/skills/architecture-design/references/evals/
  -> souroldgeezer-architecture/skills/architecture-design/references/evals/
```

P3 version decisions:

```text
souroldgeezer-design: 0.31.0 -> 1.0.0
Reason: removing architecture-design from the design plugin is
backwards-incompatible for users who installed design for architecture work.

souroldgeezer-architecture: 0.1.0
Reason: new installable plugin boundary carrying the moved architecture
capability.
```

P3 compatibility notes:

```text
Users who installed souroldgeezer-design for architecture-design must install
souroldgeezer-architecture@souroldgeezer. The architecture-design skill name,
canonical docs/architecture/<feature>.oef.xml handoff, project-scoped Codex
wrapper name, OEF XML behavior, layout runtime commands, render validation
procedures, schemas, fixtures, and support scripts are preserved. Only the
plugin namespace and bundled file paths changed.
```

P3 command evidence:

```text
find . -path './.worktrees' -prune -o -name '*.json' -type f -print0 | xargs -0 -n1 jq -e .
  -> JSON OK

python TOML parse check
  -> TOML OK

python scripts/check-runtime-metadata-parity.py --check .
  -> Runtime metadata parity OK

scripts/validate-fragmentation.sh
  -> JSON OK; TOML OK; Marketplace paths OK; Plugin manifests OK;
     Runtime metadata parity OK; Ran 23 tests in 2.116s; OK

python -m unittest
  -> Ran 23 tests in 2.080s; OK

scripts/skill-architecture-report.sh --strict .
  -> Findings: 0 total; replacement calibration passes: yes;
     trigger/behavior/source-grounding adoption: 10 of 10

git diff --check
  -> no whitespace errors

bash souroldgeezer-architecture/skills/architecture-design/references/scripts/package-arch-layout.sh
  -> BUILD SUCCESSFUL; included references/bin/arch-layout.jar 12584079 bytes

souroldgeezer-architecture/skills/architecture-design/references/scripts/arch-layout.sh --version
  -> arch-layout 0.28.0
```

Completion notes:

```text
Completed 2026-05-05. Created `souroldgeezer-architecture` as a distinct
Claude Code + Codex plugin, moved the full architecture runtime surface out of
`souroldgeezer-design`, updated the shared marketplace and both plugin manifest
sets, kept the project-scoped Codex `architecture-design` wrapper, updated
tests and runtime fallback paths, added migration notes, and rebuilt the
packaged layout runtime after the move. `architecture-design/SKILL.md` was not
slimmed in this phase; edits were limited to path and plugin-boundary
corrections.
```

## P4 — Architecture Skill Slimming

Goal:

Make `architecture-design/SKILL.md` a compact operational router and move heavyweight material into references with explicit load conditions.

Primary target:

```text
souroldgeezer-architecture/skills/architecture-design/SKILL.md
```

Fallback target if P3 used staged isolation:

```text
souroldgeezer-architecture/skills/architecture-design/SKILL.md
```

Preserve:

```text
capabilities
finding codes
validation hooks
render/readiness logic
external handoff rules
OEF/XML/ArchiMate® procedures
```

Move behind explicit load conditions:

```text
long tables
examples
rubrics
layout details
rendering policies
XML serialization details
route repair instructions
validation procedures
professional readiness checks
```

Target shape for always-loaded `SKILL.md`:

```text
purpose
ownership boundary
when to use
when not to use
modes
minimal workflow
reference load map
output contract
stop conditions
disclosure footer
```

Acceptance:

```bash
wc -c souroldgeezer-architecture/skills/architecture-design/SKILL.md || wc -c souroldgeezer-architecture/skills/architecture-design/SKILL.md
python -m unittest
scripts/skill-architecture-report.sh --strict .
```

Additional acceptance:

```text
Before/after size report is documented.
Moved content map is documented.
Every moved reference has a load condition.
Capabilities are preserved.
```

Suggested commit:

```bash
git add .
git commit -m "Slim architecture skill into router with references"
```

Completion notes:

```text
Completed 2026-05-05.

Before/after size report:
- Before P4 `architecture-design/SKILL.md`: 497 lines, 8,676 words, 68,018 bytes.
- After P4 `architecture-design/SKILL.md`: 313 lines, 1,733 words, 16,421 bytes.
- Always-loaded reduction: 184 lines, 6,943 words, 51,597 bytes
  (75.9% byte reduction).
- New one-hop operational reference:
  `souroldgeezer-architecture/skills/architecture-design/references/procedures/architecture-operational-workflow.md`
  is 420 lines, 2,574 words, 20,914 bytes.

Load-condition map:
- `../../docs/architecture-reference/architecture.md`: notation principles,
  element/relationship rules, OEF serialization, diagram kinds, smell
  definitions, and checklist references.
- `references/procedures/architecture-operational-workflow.md`: selected
  mode workflow, pre-flight, project assimilation, render-polish loop,
  forward-only rules, preservation rules, and validation sequencing.
- `references/smell-catalog.md`: emitting or interpreting `AD-*`, `AD-L*`,
  `AD-B-*`, `AD-Q*`, or `AD-DR-*` findings.
- `references/procedures/professional-readiness.md`: every Build, Extract,
  and Review readiness verdict, authority axis, render gate, and `AD-Q*`
  findings.
- `references/procedures/layout-strategy.md` plus
  `layout-backend-contract.md`, `layout-policies-by-viewpoint.md`,
  `routing-and-glossing.md`, and `layout-fallback.md`: Build/Extract layout,
  Review repair/polish, backend generation, viewpoint policy, routing, route
  repair, global polish, or fallback layout.
- `references/procedures/lifting-rules-*.md`, `process-view-emission.md`, and
  `seed-views.md`: Extract source lifting, process-view emission, and
  forward-only seed views.
- `references/procedures/drift-detection.md`: Review with current
  source/IaC/workflow comparison or explicit drift question.
- `references/procedures/external-validation-handoff.md`: supplied Archi
  import, Validate Model, schema, `xmllint --schema`, or conformant-tool
  findings.
- `references/procedures/rendered-png-validation.md`: PNGs exist or rendered
  view comparison is requested.
- `references/scripts/validate-oef-layout.sh`, `arch-layout.sh`,
  `archi-render.sh`, `validate-model.ajs`, and `package-arch-layout.sh`:
  source-geometry validation, layout runtime commands, render requests,
  jArchi Validate Model, and Java runtime packaging respectively.
- `references/schemas/*.schema.json`, `references/bin/arch-layout.jar`,
  `references/fixtures/**`, `references/red-flags.md`, `references/evals/`,
  and `references/source-grounding.md`: layout contract validation, packaged
  runtime execution through script wrapper, regression corpus changes,
  failed-check/readiness red flags, and behavior/source-grounding changes.

Moved content map:
- Purpose / ownership / mode dispatch stayed in `SKILL.md` as compact router
  text.
- Detailed mode procedures moved from `SKILL.md` to
  `references/procedures/architecture-operational-workflow.md`:
  Build, Extract, Review, Lookup, drift detection, render request, and
  render-polish iteration.
- Pre-flight questions, defaults, ask-vs-continue rules, change
  classification, layout intent selection, and canonical path handling moved
  behind the operational workflow load condition.
- Project assimilation discovery, forward-only preservation, render-contract
  disclosure, and existing-model reuse/non-compliance rules moved behind the
  operational workflow load condition.
- OEF/XML serialization constraints, metadata requirements, top-level child
  ordering, materialized view requirements, and view-specific relationship
  curation moved behind the Build workflow load condition.
- Validation sequencing, source-geometry gate behavior, external validation
  handoff, rendered PNG checks, render gate, per-view readiness/authority
  rollup, and red-flag stop rules moved behind explicit procedure/script load
  conditions.
- Long support inventory moved into the `SKILL.md` reference load map with
  exact load conditions for procedures, scripts, schemas, fixtures, packaged
  runtime, evals, and source grounding.

Validation evidence:
- `python scripts/check-runtime-metadata-parity.py --check .`:
  `Runtime metadata parity OK`.
- `scripts/validate-fragmentation.sh`: `JSON OK`, `TOML OK`,
  `Marketplace paths OK`, `Plugin manifests OK`, `Runtime metadata parity OK`,
  and 23 unit tests `OK`.
- `scripts/skill-architecture-report.sh --strict .`: 0 findings.
- `git diff --check`: clean.
```

## P5 — Public Docs and Release Surface

Goal:

Make the public surface calmer and add release hygiene.

Root README should become a product map containing:

```text
what this is
plugin matrix
install for Claude
install for Codex
local development
three examples
validation commands
links to detailed plugin docs
```

Detailed docs should live in:

```text
docs/plugins/audit.md
docs/plugins/design.md
docs/plugins/architecture.md
docs/plugins/ops.md
docs/release-checklist.md
```

Tasks:

- Use `sog_docs_release`.
- Slim root README.
- Move long plugin descriptions into `docs/plugins/*.md`.
- Add release checklist.
- Keep facts aligned with manifests.
- Keep facts aligned with runtime parity checks.
- Do not change skill behavior.

Acceptance:

```bash
find . -name '*.json' -print0 | xargs -0 -n1 jq -e .

python - <<'PY'
import pathlib, tomllib

for path in pathlib.Path(".").rglob("*.toml"):
    tomllib.loads(path.read_text())

print("TOML OK")
PY

python -m unittest
scripts/skill-architecture-report.sh --strict .

test -f docs/plugins/audit.md
test -f docs/plugins/design.md
test -f docs/plugins/architecture.md
test -f docs/plugins/ops.md
test -f docs/release-checklist.md
```

Suggested commit:

```bash
git add .
git commit -m "Simplify public docs and add release checklist"
```

Completion notes:

```text
Completed 2026-05-05. Public docs were simplified into a product map and
plugin-specific doc pages. README.md now covers what this repo is, the plugin
matrix, install flows for Claude and Codex, local development, three examples,
validation commands, and links to detailed plugin docs. Added
docs/plugins/audit.md, docs/plugins/design.md, docs/plugins/architecture.md,
docs/plugins/ops.md, and docs/release-checklist.md. Release hygiene now lives
in the checklist, including semver guidance and synchronized manifest updates.
Install and packaging guidance was cross-checked against current official
Claude Code plugin/marketplace docs and OpenAI Codex plugin/skills docs. During
review, plugin docs were corrected to use doc-relative skill links, and the
runtime metadata parity checker/test were tightened so docs pages cannot pass
with README-root links that are broken from `docs/plugins/`.

Validation evidence:
- `find . -name '*.json' -print0 | xargs -0 -n1 jq -e .`: exit 0.
- TOML parse command: `TOML OK`.
- `python -m unittest tests.runtime_metadata_parity_test`: 3 tests `OK`, including doc-relative plugin-link drift detection.
- `python -m unittest`: 24 tests `OK`.
- `python scripts/check-runtime-metadata-parity.py --check .`: `Runtime metadata parity OK`.
- `scripts/validate-fragmentation.sh`: `JSON OK`, `TOML OK`, `Marketplace paths OK`, `Plugin manifests OK`, `Runtime metadata parity OK`, and 24 unit tests `OK`.
- `scripts/skill-architecture-report.sh --strict .`: 0 findings.
- `git diff --check`: clean.
```

## P6 — Final Validation and Review

Goal:

Run full validation and perform final read-only review before merging back to `main`.

Tasks:

- Use `sog_final_reviewer`.
- Review against this ExecPlan.
- Review against `docs/skill-architecture.md`.
- Review runtime installability.
- Review manifest validity.
- Review metadata parity.
- Review release hygiene.
- Review regression risk.
- Do not make additional changes during read-only review unless the coordinator explicitly opens a fix commit after the review.

Validation:

```bash
find . -name '*.json' -print0 | xargs -0 -n1 jq -e .

python - <<'PY'
import pathlib, tomllib

for path in pathlib.Path(".").rglob("*.toml"):
    tomllib.loads(path.read_text())

print("TOML OK")
PY

python -m unittest
scripts/skill-architecture-report.sh --strict .
git status --short
```

Final reviewer must return:

```text
merge/no-merge recommendation
blockers
high-risk regressions
missing verification
suggested follow-up issues
```

Acceptance:

```text
All validation commands pass.
Final reviewer returns merge recommendation or explicit blockers.
Migration notes are present.
Docs reflect final product boundary.
The ExecPlan status is updated to Complete or Blocked.
```

Suggested final commit if needed:

```bash
git add .
git commit -m "Finalize fragmentation refactor"
```

Completion notes:

```text
Initial P6 review returned no-merge on 2026-05-05. Blockers:
- `souroldgeezer-architecture/agents/architecture-design.md` duplicated the
  detailed architecture workflow instead of routing to the canonical skill.
- `.codex/agents/architecture-design.toml` duplicated the same detailed
  workflow in `developer_instructions`.
- The ExecPlan was not yet final.

Applied blocker fix:
- Slimmed both architecture runtime wrappers to thin routers that point back to
  `architecture-design` / `SKILL.md` as the source of truth and preserve only
  route, load, and footer requirements.
- Added deterministic skill architecture report coverage:
  `SAC-RUNTIME-WRAPPER-WORKFLOW-DUPLICATION`.
- Added generated ledger case `SAC-T00534` so workflow-heavy runtime wrappers
  are caught by replacement calibration.

Validation evidence before rerunning P6:
- `python -m unittest tests.skill_architecture_report_test`: 15 tests `OK`.
- `scripts/skill-architecture-report.sh --strict .`: 0 findings, 534 ledger
  cases, 521/521 tool-detected gold findings, 100.0% automated replacement
  recall.
```

## Decision Log

| Date | Decision | Reason | Consequence |
|---|---|---|---|
| 2026-05-05 | Use one branch and one worktree | The multi-branch plan was too complex | Phases are tracked by commits instead of separate branches |
| 2026-05-05 | Use `.worktrees/fragmentation-refactor` | Repo already gitignores `.worktrees/` | Validation from main must prune `.worktrees/` |
| 2026-05-05 | Keep temporary refactor agents outside repo | Repo `.codex/agents/` is a shipped product surface | Subagents live in `~/.codex/agents/` |
| 2026-05-05 | Fix manifests before product refactor | Later moves need a reliable validation floor | P1 precedes P2/P3 |
| 2026-05-05 | Split architecture after parity work | Large moves should not increase metadata drift | P3 depends on P2 |
| 2026-05-05 | Treat untracked refactor prompt/runbook as out of P0 scope | P0 commit is only the ExecPlan baseline map | Later phases may reconcile them deliberately |
| 2026-05-05 | Keep `python -m unittest` as the recurring unit command | The user-approved command should exercise the existing `*_test.py` suite | A root `test_all.py` shim discovers `tests/*_test.py` |
| 2026-05-05 | Make the manifest gate marketplace-driven | P3 adds another plugin, so hardcoding current plugin directories would create immediate drift | `scripts/validate-fragmentation.sh` iterates `.claude-plugin/marketplace.json` |
| 2026-05-05 | Use a parity checker instead of a generator | Generation would add a second source of truth before the architecture split | `scripts/check-runtime-metadata-parity.py --check .` validates canonical metadata fields |
| 2026-05-05 | Treat `SKILL.md` frontmatter as canonical skill trigger metadata | `SKILL.md` remains the canonical skill surface | Claude agents, Codex wrappers, and per-skill OpenAI metadata align to it |
| 2026-05-05 | Move architecture into a dedicated plugin | Architecture had a distinct runtime, references, schemas, render support, and long behavior surface | `souroldgeezer-architecture` owns `architecture-design`; `souroldgeezer-design` is now software/UI/API only |
| 2026-05-05 | Bump `souroldgeezer-design` to `1.0.0` for the split | Removing `architecture-design` from design is backwards-incompatible for existing design-plugin users | Users needing architecture install `souroldgeezer-architecture` at `0.1.0` |

## Progress Log

| Date | Phase | Update | Evidence |
|---|---|---|---|
| 2026-05-05 | P0 | Baseline map recorded; no product files edited; recurring unittest command issue assigned to P1 | `sog_baseline_explorer`; `jq -r '.plugins[] ...' .claude-plugin/marketplace.json`; manifest `jq` scans; `find ... SKILL.md`; `find ... agents/openai.yaml`; `wc -c souroldgeezer-*/skills/*/SKILL.md`; `find . -name '*.json' -print0 \| xargs -0 -n1 jq -e .` exit 0; TOML parse command printed `TOML OK`; `python -m unittest` exit 5 / `NO TESTS RAN`; `python -m unittest discover -s tests -p '*_test.py'` ran 21 tests OK; `scripts/skill-architecture-report.sh --strict .` found 0 findings; `git status --short` showed only this ExecPlan plus two pre-existing untracked refactor docs |
| 2026-05-05 | P1 | Manifest/path validation added; bare unittest discovery fixed | `scripts/validate-fragmentation.sh` printed `JSON OK`, `TOML OK`, `Marketplace paths OK`, `Plugin manifests OK`, and ran 21 tests OK; `find . -name '*.json' -print0 \| xargs -0 -n1 jq -e .` exit 0; TOML parse command printed `TOML OK`; `python -m unittest` ran 21 tests OK; `scripts/skill-architecture-report.sh --strict .` found 0 findings; `git status --short` showed P1 files plus the two pre-existing untracked refactor docs |
| 2026-05-05 | P2 | Runtime metadata parity checker added and wired into recurring validation | `python -m unittest tests.runtime_metadata_parity_test` ran 2 tests OK with intentional drift detection; `python scripts/check-runtime-metadata-parity.py --check .` printed `Runtime metadata parity OK`; `scripts/validate-fragmentation.sh` printed `Runtime metadata parity OK` and ran 23 tests OK; `python -m unittest` ran 23 tests OK; `scripts/skill-architecture-report.sh --strict .` found 0 findings; `git diff --check` clean |
| 2026-05-05 | P3 | Architecture plugin split completed; migration note and move map recorded | `find . -name '*.json' -print0 \| xargs -0 -n1 jq -e .` exit 0; TOML parse command printed `TOML OK`; `python -m unittest` ran 23 tests OK; `python scripts/check-runtime-metadata-parity.py --check .` printed `Runtime metadata parity OK`; `scripts/validate-fragmentation.sh` printed all validation OK and ran 23 tests OK; `scripts/skill-architecture-report.sh --strict .` found 0 findings; `test -d souroldgeezer-architecture` exit 0; `bash souroldgeezer-architecture/skills/architecture-design/references/scripts/arch-layout.sh --version` printed `arch-layout 0.28.0`; `git diff --check` clean |
| 2026-05-05 | P4 | Architecture-design skill slimmed into compact operational router; detailed procedures moved to one-hop operational workflow reference with explicit load conditions | `wc -l -w -c` showed `SKILL.md` reduced from 68,018 bytes to 16,421 bytes and new `architecture-operational-workflow.md` at 20,914 bytes; `python scripts/check-runtime-metadata-parity.py --check .` printed `Runtime metadata parity OK`; `scripts/validate-fragmentation.sh` printed all validation OK and ran 23 tests OK; `scripts/skill-architecture-report.sh --strict .` found 0 findings; `git diff --check` clean |
| 2026-05-05 | P5 | Public docs simplified into a product map; plugin docs and release checklist added; plugin-doc link parity tightened to require doc-relative links | Official Claude Code plugin/marketplace docs and OpenAI Codex plugin/skills docs cross-checked; `find . -name '*.json' -print0 \| xargs -0 -n1 jq -e .` exit 0; TOML parse command printed `TOML OK`; `python -m unittest tests.runtime_metadata_parity_test` ran 3 tests OK; `python -m unittest` ran 24 tests OK; `python scripts/check-runtime-metadata-parity.py --check .` printed `Runtime metadata parity OK`; `scripts/validate-fragmentation.sh` printed `JSON OK`, `TOML OK`, `Marketplace paths OK`, `Plugin manifests OK`, `Runtime metadata parity OK`, and 24 unit tests `OK`; `scripts/skill-architecture-report.sh --strict .` found 0 findings; `git diff --check` clean |
| YYYY-MM-DD | P6 | Pending | Pending |
