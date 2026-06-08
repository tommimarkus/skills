# Git Workflow Policy Core Workflow

This workflow governs how code moves inside a repository. It is passive until
loaded repo guidance initializes `git-workflow-policy`, or until the user
explicitly asks for lookup, adoption, or enforcement. Once initialized, it is a
standing enforcement gate before matching git workflow actions. It does not
publish artifacts or execute PR/MR lifecycle actions.

## Evidence Contract

Before deciding or enforcing workflow, inspect the request, repository identity,
remotes, branch/worktree/upstream state, default/base branch, guidance files,
verification expectations, release guidance when it affects version edits,
provider/protection evidence when available, and existing issue/PR handoff
context.

## Policy Resolution

Resolve workflow authority in this order:

1. Explicit user instruction for the current task.
2. Repository guidance that initializes `git-workflow-policy`, such as
   `AGENTS.md`, `CLAUDE.md`, contribution guides, or workflow docs.
3. Project-local options and exceptions in the same guidance.
4. Conservative default for lookup/preflight only.

Loaded guidance means repo instructions already in context, such as root or
path-local `AGENTS.md`, `CLAUDE.md`, contribution guides, or workflow docs, plus
guidance read during repo inspection. If loaded guidance contains
`git-workflow-policy` with or without options, treat that as an explicit
current-task trigger for matching branch, staging, commit, merge, rebase,
force-push, destructive git, or PR/MR handoff actions. Do not downgrade an
initialized policy to lookup because the user did not name the skill.

If project guidance defines a bespoke workflow, adopt mode must absorb the
related rules into the initialization options or adjacent local exceptions, then
remove or replace competing branch, staging, commit, worktree, or handoff prose.
Keep only non-policy runbooks or evidence references that do not override the
initialized policy, and report why they remain.

If loaded repo guidance initializes `git-workflow-policy` without options,
apply the default profile below. Treat explicit repo options as overrides or
additions to the default, and report the resolved option set.

Suggested initialization: `git-workflow-policy: feature branches, clean
worktree, no direct main`; list project-local exceptions beside it.

## Modes

- `lookup`: answer the applicable git workflow rule without changing files.
- `inspect`: classify the current repo workflow, conflicts, exceptions, and
  next action.
- `adopt-guidance`: consolidate existing developer git guidance into this
  policy's initialization/options/exceptions, removing competing prose.
- `preflight`: check whether the current repository state is ready for the next
  requested development action.
- `enforce-initialized`: apply initialized policy before matching git state
  changes.

## Developer Workflow Baseline

Default profile when initialized without options: use a feature branch or
documented worktree for non-trivial changes; keep the default branch clean
unless guidance allows direct edits; inspect `git status --short --branch`
before edits and staging; preserve unrelated work; stage explicit paths only;
honor `.gitignore`; run the narrowest documented verification before commit or
PR/MR handoff; stop before destructive git actions.

Do not mix unrelated tasks in one branch. Re-read live git state before any write action or `pr-ops` handoff.

Version policy belongs here only as developer guidance: where the version source
lives, when version files may change, which branches may carry version bumps,
and what local evidence is needed before a release handoff. Version bump
execution, tags, provider releases, package publication, and post-release checks
belong to `release-policy`.

## Ask Vs Continue

Continue when repository, target branch, local work area, policy source, and
verification are clear and no destructive action is required. Ask on missing
repository identity, conflicting base/integration authority, blocking version
ambiguity, missing write permission, destructive history/branch operations, or
unresolved policy precedence.

## Escalation Gates

Escalate on dirty unrelated work, unclear generated output, tracked ignored
files, divergent branches, unexpected remotes, missing upstreams, active
merge/rebase/cherry-pick state, protected-branch conflicts, policy conflicts,
version ambiguity, release-tag or publishing requests, unsafe force-push or
history rewrite, or missing verification tooling.

## Output

End with a concise report containing: mode; repository and branch inspected;
initialization source or explicit request; base/default branch evidence;
workflow policy source; project-local options and exceptions; git state summary;
version-policy placement when relevant; delegated sibling skills; conflicts or
escalation gates; verification inferred or run; and next action.
