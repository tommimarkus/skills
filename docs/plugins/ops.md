# `souroldgeezer-ops`

`souroldgeezer-ops` ships the issue and pull-request lifecycle plugin. The
core skills are provider-agnostic; provider mechanics live in extensions.

## Skills

| Skill | What it covers | Notes |
|---|---|---|
| [issue-ops](../../souroldgeezer-ops/skills/issue-ops/SKILL.md) | Explicit issue and work-item lifecycle requests | Loads the provider extension after tracker identification |
| [pr-ops](../../souroldgeezer-ops/skills/pr-ops/SKILL.md) | Explicit pull-request lifecycle requests | Handles prepared branches, checks, review, merge, and cleanup |

## Packaging notes

- Claude Code and Codex share the same marketplace entry for this plugin.
- The repo-local issue lifecycle overlay and Codex wrappers remain separate
  from the published plugin surface.
- Core workflows stay provider-agnostic until the provider is identified.
