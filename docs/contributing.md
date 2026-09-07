# Contributing

This guide is the entry point for changes to this marketplace. The shared
workflow in each plugin's `skills/` directory is the source of truth; host
manifests, marketplaces, agents, hooks, and MCP adapters package that workflow
for their respective runtimes.

## Start with the change you are making

- For a skill, manifest, marketplace, agent wrapper, hook, bundled reference,
  extension, or related repository documentation, read the
  [skill architecture standard](skill-architecture.md) before choosing the
  change shape. Then read the affected skill's `SKILL.md` and only the
  references selected by its load map.
- For evaluation cases and source-grounding records, follow the
  [evaluation evidence guide](skill-evaluation.md). Keep bundled prompts and
  examples original or safely paraphrased.
- For a release or a version change, use the
  [release checklist](release-checklist.md). Feature branches carry content;
  integration on `main` owns version stamping.
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

Run the checks that cover the files you changed first. Before integration, the
parent runs the repository-wide gates from a clean worktree:

```text
python scripts/check-runtime-metadata-parity.py --check .
scripts/validate-fragmentation.sh
scripts/skill-architecture-report.sh --strict .
uv run python -m unittest discover -s tests -p '*_test.py'
scripts/check-runtime-host-smoke.py --fresh --assert-profile-isolation .
git diff --check
```

Do not use a pipeline or `||` fallback as evidence that a gate passed: capture
the actual command's exit status or run it unpiped. The host smoke's two safety
flags are required. It uses temporary host configuration and plugin-data state,
and must not replace `HOME`.

A test run that collects zero tests fails the gate. Use the available
first-party plugin validators as well: the architecture report invokes
`claude plugin validate --strict` when installed; the host smoke checks for a
Codex validator and reports its absence as a skip. Before changing the
published surface, apply the repository's in-depth IP-hygiene review;
cosmetic edits use scoped triage.

## Documentation map

Use [README.md](../README.md) for installation and the published-plugin map.
Use this guide for contributor orientation, the [skill architecture
standard](skill-architecture.md) for authoring judgment, the [evaluation
evidence guide](skill-evaluation.md) for behavior evidence, the [release
checklist](release-checklist.md) for version and publication preparation, and
the [maintenance procedures](maintenance-procedures.md) for infrequent
operations.
