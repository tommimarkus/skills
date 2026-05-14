# Skill Support Locality - Design

Status: design approved 2026-05-14.
Target: repo-wide plugin and skill support-file structure.
Approach: strict skill ownership with immediate report enforcement.

## Goal

Normalize support-file ownership across all published and repo-internal skills.
Skill-private material should live under the owning skill so agents, reviewers,
and evaluators see the real context cost and maintenance surface. Plugin-root
support material should exist only when it is shared, public, or intentionally
canonical beyond one skill.

This replaces the current odd shape where `test-quality-audit` loads private
support files from `souroldgeezer-audit/references/test-quality-audit-*`.

## Non-Goals

- Do not merge large reference material back into `SKILL.md`.
- Do not remove progressive disclosure.
- Do not make every extension use route cards when a small direct extension is
  clearer and cheap.
- Do not hide support cost outside a skill folder to make `plugin-eval` look
  better.
- Do not require plugin-root docs to move when they are truly shared, public, or
  canonical.

## Ownership Rule

A file is skill-private when exactly one skill loads, routes to, or maintains
it. Skill-private files must live under that skill:

```text
skills/<skill>/references/
skills/<skill>/references/extensions/
skills/<skill>/references/procedures/
skills/<skill>/references/evals/
skills/<skill>/references/golden-corpus/
```

Plugin-root `references/` is disallowed for private skill support. Any remaining
plugin-root reference file must either be loaded by more than one skill or be
documented as plugin-level material.

## Extension Placement

Use threshold-based extension placement:

```text
skills/<skill>/extensions/<name>.md
```

This path is for small overlays and route cards. A directly loaded extension
should stay cheap enough that loading it with the core skill is reasonable.
`plugin-eval:evaluate-skill` is the budget calibration source:

- Route card target: 100-250 tokens.
- Route card warning: 400+ tokens.
- Direct full extension target: under roughly 700-900 tokens and frequently
  loaded.
- Large or rarely loaded detail moves behind a route card.

Move long rubrics, examples, smell catalogs, tool output parsing, stack
taxonomies, and multi-rubric packs into:

```text
skills/<skill>/references/extensions/<name>.md
skills/<skill>/references/extensions/<family>/
  core.md
  unit.md
  integration.md
  e2e.md
```

For `test-quality-audit`, keep `extensions/index.md` as the matrix router and
move the full stack packs under `references/extensions/<stack>/`.

## Docs And Shared References

Plugin-root docs are allowed when they are genuinely plugin-level:

```text
<plugin>/docs/<domain>-reference/
```

A doc qualifies as plugin-level if at least one is true:

- Multiple skills load it.
- README, `CLAUDE.md`, or `AGENTS.md` presents it as public plugin reference
  material.
- It defines a canonical domain rubric for the plugin and skill files only
  route to it.
- It is intentionally stable external-facing documentation, not operational
  skill machinery.

For `souroldgeezer-audit`, keep:

```text
souroldgeezer-audit/docs/quality-reference/
souroldgeezer-audit/docs/security-reference/
```

Move:

```text
souroldgeezer-audit/references/test-quality-audit-smell-catalog.md
souroldgeezer-audit/references/test-quality-audit-procedures/
souroldgeezer-audit/references/test-quality-audit-extensions/
```

Target:

```text
souroldgeezer-audit/skills/test-quality-audit/references/smell-catalog.md
souroldgeezer-audit/skills/test-quality-audit/references/procedures/
souroldgeezer-audit/skills/test-quality-audit/references/extensions/
```

## Enforcement

Add a strict `skill-architecture-report` rule:

```text
SAC-REF-PRIVATE-PLUGIN-ROOT
Category: On-Demand Knowledge or Repo Guidance Drift
Severity: high
Trigger: plugin-root references/<skill-name>* material is advertised by exactly one skill
Fix: move under skills/<skill>/references/ or document why it is shared/public
Strict: yes
```

No grandfathering. The first implementation must migrate current private files
before enabling the strict rule so `scripts/skill-architecture-report.sh
--strict .` remains green.

The detector should avoid false positives for plugin-root docs and references
that are clearly shared/public. It should flag plugin-root `references/`
content that is named for one skill, linked only from one skill, or maintained
only by one skill's maintenance workflow.

## Migration Plan

1. Inventory plugin-root `references/` and classify each file as shared/public
   or skill-private.
2. Move skill-private material with ownership-preserving paths.
3. Update every load cue, markdown link, test expectation, source-grounding
   entry, golden-corpus procedure, README/CLAUDE/AGENTS mention, and report
   fixture that points to old paths.
4. Add the report rule and ledger cases for the bad and clean shapes.
5. Run validation and `plugin-eval` after the move.

The expected `plugin-eval` result for `test-quality-audit` may become more
expensive because the previously hidden support cost is now visible. That is an
accepted outcome.

## Validation

Use this closeout stack for the migration:

```text
rg "souroldgeezer-audit/references/test-quality-audit"
scripts/skill-architecture-report.sh --strict .
uv run python -m unittest tests.skill_architecture_report_test
uv run python scripts/skill_architecture_report.py --format json --strict .
plugin-eval analyze souroldgeezer-audit/skills/test-quality-audit --format markdown
jq empty <changed plugin and marketplace manifests>
yq --front-matter=extract -o=json '.' <changed SKILL.md files>
git diff --check
```

If the report rule changes the report engine, also update or regenerate the
ledger while preserving contiguous `SAC-T#####` IDs and the empirical recall
bar.

## Open Implementation Notes

- The implementation should be one coordinated change because enforcement is
  strict immediately.
- Move files with path-aware updates, not by duplicating and leaving stale
  compatibility copies.
- Keep `test-quality-audit` route cards compact after the move.
- Report any remaining plugin-root support file with an explicit shared/public
  rationale.
