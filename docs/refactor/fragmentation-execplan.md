# Fragmentation Refactor ExecPlan

Status: Draft  
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
  OEF XML / ArchiMate support
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
scripts/skill-architecture-report.sh --strict .
git status --short
```

If a runtime parity checker or generator is added in P2, add it to this verification set and run it after P2 through P6.

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
| P0 | Todo | Coordinator + `sog_baseline_explorer` | Create plan and baseline map | ExecPlan exists; surfaces and drift points documented |
| P1 | Todo | `sog_manifest_ci` | Fix manifest validity and add syntax/path gates | JSON/TOML/path checks pass and are scripted |
| P2 | Todo | `sog_runtime_parity` | Prevent Claude/Codex metadata drift | Checker or generator detects drift; tests exist |
| P3 | Todo | `sog_architecture_split` | Split architecture out of design | `souroldgeezer-architecture` exists; manifests pass; migration note exists |
| P4 | Todo | `sog_skill_slimming` | Slim architecture skill into compact router | Heavy material moved to references with load conditions |
| P5 | Todo | `sog_docs_release` | Simplify README and add plugin/release docs | README is a map; docs/plugins and release checklist exist |
| P6 | Todo | `sog_final_reviewer` | Final read-only review and validation | All checks pass; reviewer returns merge/no-merge |

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
Pending.
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
Pending.
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
scripts/skill-architecture-report.sh --strict .
```

Additional acceptance:

```text
A parity checker or generator check exists.
At least one test proves metadata drift is detected.
Canonical field map is documented.
The new parity command is added to the global verification set.
```

Suggested commit:

```bash
git add .
git commit -m "Add runtime metadata parity validation"
```

Completion notes:

```text
Pending.
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
  ArchiMate support
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

Completion notes:

```text
Pending.
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
souroldgeezer-design/skills/architecture-design/SKILL.md
```

Preserve:

```text
capabilities
finding codes
validation hooks
render/readiness logic
external handoff rules
OEF/XML/ArchiMate procedures
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
wc -c souroldgeezer-architecture/skills/architecture-design/SKILL.md || wc -c souroldgeezer-design/skills/architecture-design/SKILL.md
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
Pending.
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
Pending.
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
Pending.
```

## Decision Log

| Date | Decision | Reason | Consequence |
|---|---|---|---|
| YYYY-MM-DD | Use one branch and one worktree | The multi-branch plan was too complex | Phases are tracked by commits instead of separate branches |
| YYYY-MM-DD | Use `.worktrees/fragmentation-refactor` | Repo already gitignores `.worktrees/` | Validation from main must prune `.worktrees/` |
| YYYY-MM-DD | Keep temporary refactor agents outside repo | Repo `.codex/agents/` is a shipped product surface | Subagents live in `~/.codex/agents/` |
| YYYY-MM-DD | Fix manifests before product refactor | Later moves need a reliable validation floor | P1 precedes P2/P3 |
| YYYY-MM-DD | Split architecture after parity work | Large moves should not increase metadata drift | P3 depends on P2 |

## Progress Log

| Date | Phase | Update | Evidence |
|---|---|---|---|
| YYYY-MM-DD | P0 | Pending | Pending |
| YYYY-MM-DD | P1 | Pending | Pending |
| YYYY-MM-DD | P2 | Pending | Pending |
| YYYY-MM-DD | P3 | Pending | Pending |
| YYYY-MM-DD | P4 | Pending | Pending |
| YYYY-MM-DD | P5 | Pending | Pending |
| YYYY-MM-DD | P6 | Pending | Pending |
