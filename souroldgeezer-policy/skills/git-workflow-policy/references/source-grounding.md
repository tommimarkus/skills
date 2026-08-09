# Git Workflow Policy Source Grounding

This skill centralizes duplicated git, branching, integration, and
version-policy guidance into a passive policy that repositories initialize with
local options and exceptions. Plugin installation alone does not enforce it;
loaded repo guidance initialization is the standing enforcement trigger for
matching git workflow actions. Adopt mode consolidates existing related
guidance into initialization options or local exceptions instead of leaving
parallel workflow authority.
Keep guidance original; link external manuals only when needed.

The delegated closeout helper exists because cherry-picked equivalent commits
do not preserve branch ancestry: later non-force deletion correctly refuses
them. Rebasing the owned branch onto the live parent tip and fast-forwarding
preserves ancestry, while a separate merged-branch proof keeps cleanup
recoverable and deterministic. Cleanup treats worktree removal and branch
deletion as separate verified states so a process crash between them can be
retried without weakening branch-tip, upstream, ancestry, registration, or
filesystem-ownership checks. Once both owned artifacts are absent, target
ancestry of the recorded integrated commit is the idempotent completion proof.

## Boundary Decisions

- Developer git movement: `git-workflow-policy`.
- PR/MR lifecycle writes: `pr-ops`.
- Issue lifecycle work: `issue-ops`.
- Distribution, tagging, and publication: `release-policy`.
- Security controls: `devsecops-audit`.
- Test-suite adequacy: `test-quality-audit`.
