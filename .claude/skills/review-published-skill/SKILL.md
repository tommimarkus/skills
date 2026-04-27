---
name: review-published-skill
description: Use when reviewing a modified published plugin skill, matching subagent, bundled reference, extension, manifest, marketplace entry, runtime metadata, repo-internal .claude/skills authoring skill, or related repo documentation before commit or release. Checks trigger quality, user-value regressions, progressive disclosure, validation evidence, cross-runtime packaging parity, semver and docs drift, and IP-hygiene handoff.
---

# Published Skill Review

Review changed published plugin skills and their release surfaces before a commit
or release. This is a repo-internal gate for `souroldgeezer-*` plugin content,
not a distributed plugin capability.

## Scope

Use this review for changes under:

- `souroldgeezer-*/skills/**`
- `souroldgeezer-*/agents/**`
- `souroldgeezer-*/docs/*-reference/**`
- `souroldgeezer-*/.claude-plugin/plugin.json`
- `souroldgeezer-*/.codex-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.codex/agents/*.toml`
- `README.md`, `CLAUDE.md`, or `AGENTS.md` sections describing those surfaces

For repo-internal `.claude/skills/**` edits, apply the same quality checks when
the change affects authoring behavior, but do not require plugin semver bumps or
published runtime metadata.

## Review Workflow

1. Identify the changed files:
   - Start with `git status --short` for dirty working-tree, staged, and
     untracked changes.
   - If the working tree is clean but the branch is ahead, behind, or under
     review, inspect the branch scope with `git status -sb` and a base diff
     such as `git diff --name-status <upstream-or-base>...HEAD` (for example
     `origin/main...HEAD` when `origin/main` is the review base).
   - Use `git diff --name-only` only after choosing the correct comparison
     scope.
2. Run the `ip-hygiene` procedure for any changed skill, agent, reference,
   manifest, marketplace, or repo-doc surface before judging content quality.
3. Read `references/skill-quality-metrics.md` and apply its hard gates and
   scorecard to the changed skill or affected skill family.
4. Verify the changed skill's frontmatter and resource layout:
   - `name` matches its directory, uses lowercase letters, digits, and hyphens,
     and is 64 characters or fewer.
   - `description` is 1024 characters or fewer, front-loads the trigger, and
     names specific positive and boundary contexts.
   - `SKILL.md` stays focused; detailed reference material is moved to one-hop
     references with explicit load conditions.
   - Bundled scripts are non-interactive, have documented usage, emit helpful
     errors, and are tested if changed.
5. Verify package parity for published plugin content:
   - Plugin `name`, `version`, and `description` match across
     `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and
     `.claude-plugin/marketplace.json`.
   - Changed skills still have the expected paired Claude subagent and
     `skills/<skill>/agents/openai.yaml` metadata.
   - Contract changes are reflected in `.codex/agents/<skill>.toml` when a
     project-scoped wrapper exists.
   - Required version bump is present according to `CLAUDE.md` plugin
     versioning rules.
6. Verify documentation drift:
   - `CLAUDE.md` reflects current repo policy, directory layout, and
     skill-specific contracts.
   - `AGENTS.md` reflects Codex entry rules without duplicating all policy.
   - `README.md` reflects published plugin behavior when user-facing plugin
     surfaces changed.
7. If packaging, install guidance, marketplace behavior, or runtime exposure
   changed, cross-check the current official docs for both runtimes before
   approving the change.
8. Run structural validation with repo-native tools:
   - Use `jq` for JSON manifest and marketplace inspection.
   - Use Mike Farah `yq` for YAML frontmatter, TOML, and XML inspection.
   - Run any changed script's `--help` or representative command.

## Output

Lead with findings. Order by severity and use file references.

```markdown
## Findings

- [blocker|warn|info] path:line — Finding title
  Evidence: concrete file, command, or diff detail.
  Why it matters: agentic skill, runtime parity, release, or IP impact.
  Fix: specific action.

## Skill Metrics

- Trigger quality: pass|warn|fail|not assessed
- Context efficiency: pass|warn|fail|not assessed
- Agentic operability: pass|warn|fail|not assessed
- Degree-of-freedom calibration: pass|warn|fail|not assessed
- Runtime parity: pass|warn|fail|not assessed
- Release hygiene: pass|warn|fail|not assessed
- IP/source hygiene: pass|warn|fail|not assessed

## Verification

- Commands run:
- Official docs checked:
- Not assessed:

## Footer

Changed scope:
IP-hygiene result:
Reference: .claude/skills/review-published-skill/references/skill-quality-metrics.md
```

If there are no findings, say so explicitly and still list unverified runtime
or behavior evidence as residual risk.
