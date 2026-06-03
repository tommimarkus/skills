# Release Policy Core Workflow

This workflow governs distribution. It is passive until loaded repo guidance
initializes `release-policy`, or until the user explicitly asks for lookup,
adoption, preflight, or release action. Once initialized, it is a standing
enforcement gate before matching release and distribution actions. Code movement
belongs to `git-workflow-policy`; PR/MR lifecycle actions belong to `pr-ops`.

## Evidence Contract

Before release writes, inspect the request, repository identity, branch/worktree
state, base branch, candidate commit, tags, version source/strategy, automatic
bump command/result, notes/changelog, manifests, release guidance,
verification, provider tooling/auth and existing releases, registry or
marketplace target, rollback/deprecation guidance, and prior lifecycle markers.

## Modes

- `lookup`: answer the applicable release rule without changing files.
- `preflight`: inspect whether the repository state is ready for release work.
- `adopt-guidance`: consolidate existing release guidance into this policy's
  initialization/options/exceptions, removing competing prose.
- `enforce-initialized`: apply initialized policy before release state changes.
- `prepare-release`: make authorized release-preparation edits such as version
  bump files, changelog/release notes, and release PR handoff.
- `cut-release`: run final verification, create authorized tags, and create or
  update provider release metadata.
- `publish`: publish packages or marketplace artifacts only with explicit
  target and authority.
- `post-release`: verify published artifacts, record follow-up work, and hand
  cleanup to `pr-ops` or `git-workflow-policy` when needed.
- `resume`: re-read live git/provider/registry state and continue from the
  first incomplete release gate.

## Policy Resolution

Loaded guidance means repo instructions already in context, such as root or
path-local `AGENTS.md`, `CLAUDE.md`, release docs, or packaging docs, plus
guidance read during repo inspection. If loaded guidance contains
`release-policy` with or without options, treat that as an explicit current-task
trigger for matching version bump, changelog/release note, tag, provider
release, publication, rollback, or release-exception actions. Do not downgrade
an initialized policy to lookup because the user did not name the skill.

## Release Baseline

## Adoption Consolidation

In adopt mode, inspect existing version, changelog, tag, provider-release,
publication, rollback, and post-release guidance. Absorb related rules into the
initialization line or adjacent local options/exceptions, then remove or replace
competing release-policy prose. Keep only non-policy runbooks or evidence
references that do not override the initialized policy, and report why they
remain. Stop and ask when existing release guidance conflicts and no safe
consolidation is clear.

Start from a clean, policy-compliant git state. Identify one release candidate
and one version source of truth. Validate notes against release contents. Run
repository-defined verification before tags or publication, create immutable
markers only after verification, and verify publication after the write.

Version strategy is shared with `git-workflow-policy`: that skill owns developer
rules about where the version lives and when version edits are allowed; this
skill owns concrete version bump execution, tag naming, release metadata, and
publication verification.

Default profile when initialized without options: use SemVer intent; infer one
version source from a workspace/package manifest, language manifest, `VERSION`,
or documented release file; stop on conflicting sources; use annotated
`v<version>` git tags; treat a change as releasable only when guidance says so,
the user asks for release work, or the touched surface is explicit release
surface; run documented verification before version writes and before tag
creation when scope changed; do not create provider releases, publish, mutate
tags, or yank artifacts without named authority.

Initialization may be a compact declarative line, for example:

```md
release-policy: calver YYYY.MM.build, git tagging
```

That example authorizes version-source updates with the selected CalVer shape
and matching git tags for repo-defined releasable changes after verification.
Provider releases and package or marketplace publication still need explicit
authority unless the initialization names the target and action.

## Automatic Version Bump Tool

Use `references/scripts/version-bump` for routine version calculation. Run
`--help` for the current CLI. The helper is dependency-free, prints JSON by
default, and changes files only with `--write --source`.

Supported strategy surface:

- `semver`: major, minor, patch, prerelease, release, and build bumps.
- `calver` / `calendar`: schemes using `YYYY`, `YY`, `MM`, `M`, `DD`, `D`,
  `build`, or `micro`; pass existing tags with `--existing-tag` so build/micro
  values advance from live release markers.
- `pep440`: common Python package version bumps: major, minor, patch,
  prerelease, release, post, and dev.

Supported source writes are deliberately narrow: top-level JSON `version`,
common TOML `version` fields, and single-line `VERSION` or text files. If the
repo uses a richer manifest, use the helper to compute the next version and
apply the manifest edit with the repo's normal tooling.

Example dry runs:

```bash
python references/scripts/version-bump --strategy semver --current 1.2.3 --bump minor
python references/scripts/version-bump --strategy calver --scheme YYYY.MM.build --existing-tag v2026.05.7
```

Before `--write`, confirm version-source authority, a clean
`git-workflow-policy` preflight, and a single source of truth.

## Authority Gates

Ask before tag creation, provider release creation, publication, destructive
correction, tag deletion/move, yanking, or any operation that cannot be safely
retried. Continue for read-only preflight, authorized release-prep file edits,
and local verification when tooling is available.

## Escalation Gates

Escalate on dirty unrelated work, unclear candidate, missing version source,
unsupported or conflicting strategy, version/tag mismatch, helper failure,
conflicting tags or provider releases, missing target or credentials, failing
verification or required checks, notes not tied to commits, undocumented package
dry-run failures, unclear rollback, or security-sensitive blockers.

## Output

End with a concise report containing: mode; repository, branch, and candidate
commit inspected; initialization source or explicit request; release policy
source and options; git-workflow preflight state; version source and version
action, including helper command/result when used; changelog/release-notes
state; tags inspected or written; provider release state; publication targets
and actions; verification summary; delegated sibling skills; conflicts or
escalation gates; post-release checks; and next action.
