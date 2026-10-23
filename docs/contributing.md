# Contributing

This guide is the entry point for changes to this marketplace. The shared
workflow in each plugin's `skills/` directory is the source of truth; host
manifests, marketplaces, agents, hooks, and MCP adapters package that workflow
for their respective runtimes.

## Start with the change you are making

- For a skill, manifest, marketplace, agent wrapper, hook, bundled reference,
  extension, or related repository documentation, read the
  [working principles](skill-architecture.md#working-principles), then only the
  architecture-standard sections relevant to the change. Then read the affected skill's `SKILL.md` and only the
  references selected by its load map.
- For evaluation cases and source-grounding records, follow the
  [evaluation evidence guide](skill-evaluation.md). Keep bundled prompts and
  examples original or safely paraphrased.
- For a release or a version change, use the
  [release checklist](release-checklist.md). Feature branches carry content
  without version increments. Verify the candidate proportionately and fast-forward the exact clean commit;
  after integration, `main` owns computing and applying the version stamp. The
  release policy documents the fixed version cell follow-up and its focused
  checks; publication receipts still require their exact clean candidate; local changes rerun the checks their impact requires.
- For a security-sensitive change or vulnerability report, use the
  [security policy](../SECURITY.md) and
  [security baseline](security-baseline.md). Do not put sensitive details in a
  public issue while private reporting remains pending or unavailable.
- For a rare operational change, including Dediren adoption or support removal,
  use the [maintenance procedures](maintenance-procedures.md).

The repository's `AGENTS.md` is the Codex-facing operational contract and
`CLAUDE.md` is the self-contained Claude Code contract. Keep them aligned when
repository structure, runtime support, install commands, validation, or a
public skill contract changes.

## Set up a local checkout

Install Git, Python 3.11 or newer, `uv`, `jq`, and Mike Farah `yq`. The complete
host smoke also needs Claude Code, Codex, Copilot CLI, and Java 21+ for Dediren.
Use the repository's Python floor and local `uv` configuration; do not change
dependencies merely to make a documentation check run.

From the directory where you keep persistent repositories:

```bash
git clone https://github.com/tommimarkus/skills.git
cd skills
git worktree add .worktrees/my-change -b my-change main
cd .worktrees/my-change
uv sync --frozen
```

Use a distinct task and branch name for each change. If you already have a
clone, start the worktree command from its primary checkout. `uv` creates the
task's `.venv` and uses its repository-local cache. On an offline host with the
required packages already cached, use `uv sync --offline --frozen`.

## Work in a clean task worktree

Create feature worktrees under the primary checkout's persistent,
gitignored `.worktrees/<task-name>/` directory. Do not work directly on `main`
or put task work in a temporary directory. Keep a narrow change scoped to its
declared paths, stage exact paths, and do not force-add ignored files.

Before committing, confirm that no tracked file is ignored; this checks the
whole tracked inventory, not only the staging area. The output must be empty
unless the user approved an exact tracked exception:

```bash
git ls-files -ci --exclude-standard
```

The normal integration owner rebases the accepted task branch onto the current
parent and fast-forwards it. Routine integration does not cherry-pick. The
planning-policy workflow adds its own approved-plan, capability-binding, and
worktree-closeout requirements when it is in use.

The repository provides an optional local publication guard. It is scoped to
this clone's Git common directory and refuses to replace another pre-push hook:

```bash
python3 -B scripts/publication_check.py --repo-root . install-hook
python3 -B scripts/publication_check.py --repo-root . uninstall-hook
```

Install or remove it only within the authority for the current task. The hook
reduces accidental unchecked pushes to `main`; it remains bypassable and does
not change global Git configuration.

## Keep the runtime lanes aligned

Every published plugin appears in both marketplaces and has Claude and legacy
Codex manifests. When a root Agent Plugins `plugin.json` exists, its name,
description, skills path, and normalized SemVer version stay aligned with the
legacy Codex manifest; it is also the native Copilot manifest where supported.
Marketplace entries never carry a version.

Portable workflow belongs under `skills/**`. Put host metadata, hook
configuration, MCP launch variables, and host UI presentation in the relevant
adapter instead of copying a runtime-specific workflow.

## Validate the change

Choose checks from the changed behavior and its consumers. Explain material gaps;
there is no new verification profile or selection service.

| Change | Local verification |
|---|---|
| Bounded prose/reference edit | Owning content/eval checks, relevant strict architecture report and local links, scoped Lean check for introduced duplication, and `git diff --check`. |
| Skill behavior or load route | Owning contract tests and positive/negative behavior cases; update affected declared load scenarios and regenerate their shared snapshot after integration. Source tests establish consistency, not observed model behavior. |
| Executable helper, hook, manifest, or runtime config | Focused behavioral tests, fragmentation (including metadata parity), architecture checks where relevant, and configured Python lint/type checks for changed helpers. |
| Cross-cutting policy/tooling, packaging/bootstrap/provisioning, or changes whose effects cannot be bounded | Full candidate sequence below, including the safety-isolated host smoke. |
| Publication | Full exact-commit receipt, regardless of earlier local selections. |

Use a clean persistent task worktree for repository-wide checks. Run focused
checks during development, then the full sequence once for a cross-cutting
candidate, preserving each command's actual exit status:

```text
scripts/validate-fragmentation.sh
scripts/skill-architecture-report.sh --strict .
uv run python souroldgeezer-audit/skills/lean-audit/references/scripts/lean_engine.py .
uv run python -m unittest discover -s tests -p '*_test.py'
scripts/check-runtime-host-smoke.py --fresh --assert-profile-isolation --changed-since main .
git diff --check
uv run python scripts/version_stamp.py guard
```

Fragmentation owns metadata parity; do not repeat it as a separate full-candidate
gate. The explicit discovery command owns the full-suite run; zero tests fails.
Lean info/warn findings stay advisory; review introduced block findings and compare
changed-path findings against the base. Use available first-party host validators;
a missing standalone Codex validator is a disclosed skip.

Ordinary local edits rerun the checks their affected behavior needs. A change to
one report paragraph does not erase unrelated test evidence. Do not claim an old
full-suite run covered a newer tree. Exact fast-forward integration preserves the
checks run on that candidate; if integration changes behavior, rerun affected
checks and broaden when the effects cannot be bounded.

Before an explicitly authorized push of `main`, run:

```text
python3 -B scripts/publication_check.py --repo-root . record
```

Publication retains the complete ordered gates and an unconditional host smoke
with both safety flags. The receipt binds commit and tree. After exactly one
allowed atomic version-cell follow-up, use `record --version-followup`; any other
publication-source drift needs a fresh full receipt. Only the documented Claude,
normalized Codex/root-manifest and README version cells qualify. Proportionate
local verification never substitutes for publication evidence or authority.

Do not report a pipeline's downstream status as the check's status. Host smoke
uses temporary host/plugin-data state, never replaces `HOME`, and must preserve
normal host profiles. Missing tools and blocked checks remain explicit limits.

The only default Stop notification reports reference defects and advisory load/
inventory changes. It cannot require another workflow, block a read-only session,
or publish a lesson. Optional prevention guards and their overrides are described
in the [hook recipe](../souroldgeezer-audit/skills/lean-audit/references/hook-recipe.md).
Invoke lesson capture explicitly when wanted. Real artifact failures are caught by
owning tests and structural validation; arbitrary heading preservation is not a
semantic-fidelity gate.

Mutation testing is not configured in this repository. Do not adopt a new harness
just for a routine change. Use focused regression tests for changed executable
behavior; retain useful regression coverage even when no mutation operator models
its failure. Report behavioral probes actually executed separately from authored
cases or static contract checks.

## Documentation map

Use [README.md](../README.md) for installation and the published-plugin map.
Use this guide for contributor orientation, the [skill architecture
standard](skill-architecture.md) for authoring judgment, the [evaluation
evidence guide](skill-evaluation.md) for behavior evidence, the [release
checklist](release-checklist.md) for version and publication preparation, and
the [maintenance procedures](maintenance-procedures.md) for infrequent
operations. Use the [security policy](../SECURITY.md) for reporting and
response, and the [security baseline](security-baseline.md) for threats,
controls, assurance targets, and residual risk.
