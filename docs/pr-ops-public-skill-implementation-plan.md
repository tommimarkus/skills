# PR Ops Public Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a public `pr-ops` skill to `souroldgeezer-ops` for full pull-request lifecycle operation.

**Architecture:** `pr-ops` follows the `issue-ops` architecture: a compact provider-agnostic core, a GitHub provider extension, a provider-extension convention file, and synchronized Claude Code / Codex runtime metadata. The plugin receives an additive minor version bump to `0.2.0`.

**Tech Stack:** Markdown skills and docs, JSON plugin manifests, YAML Codex skill metadata, TOML Codex custom-agent wrapper, `jq`, `yq`, `uv`, `unittest`, and the repo-local skill architecture report.

---

## File Structure

- Create `souroldgeezer-ops/skills/pr-ops/SKILL.md`: provider-agnostic PR lifecycle workflow.
- Create `souroldgeezer-ops/skills/pr-ops/extensions/README.md`: provider extension convention for PR operations.
- Create `souroldgeezer-ops/skills/pr-ops/extensions/github.md`: GitHub PR provider mechanics.
- Create `souroldgeezer-ops/skills/pr-ops/agents/openai.yaml`: Codex per-skill metadata.
- Create `souroldgeezer-ops/agents/pr-ops.md`: Claude Code subagent wrapper.
- Create `.codex/agents/pr-ops.toml`: project-scoped Codex custom-agent wrapper.
- Modify `souroldgeezer-ops/.claude-plugin/plugin.json`, `souroldgeezer-ops/.codex-plugin/plugin.json`, and `.claude-plugin/marketplace.json`: bump to `0.2.0` and update plugin description.
- Modify `README.md`, `CLAUDE.md`, and `AGENTS.md`: document the new skill and runtime surfaces.
- Keep `docs/pr-ops-public-skill-design.md` and this plan as implementation evidence.

## Task 1: Add Public Skill Surfaces

- [X] Create the provider-agnostic `pr-ops` core skill.
- [X] Create the GitHub provider extension and provider-extension README.
- [X] Create Claude Code subagent, Codex `agents/openai.yaml`, and `.codex/agents/pr-ops.toml`.

## Task 2: Synchronize Package Metadata

- [X] Bump `souroldgeezer-ops` to `0.2.0`.
- [X] Synchronize name, version, and description across Claude manifest, Codex manifest, and marketplace entry.
- [X] Keep Codex `interface.defaultPrompt` at three entries while covering both `issue-ops` and `pr-ops`.

## Task 3: Synchronize Repo Docs

- [X] Update README plugin summary, `souroldgeezer-ops` skill table, matching-agent notes, and repository layout.
- [X] Update CLAUDE directory layout, extension-pattern language, and skill-specific notes.
- [X] Update AGENTS quick rules so explicit GitHub™ PR lifecycle requests route to public `pr-ops`.

## Task 4: Validate

- [X] Run `jq empty .claude-plugin/marketplace.json souroldgeezer-ops/.claude-plugin/plugin.json souroldgeezer-ops/.codex-plugin/plugin.json`.
- [X] Run `uv run python -m unittest tests.skill_architecture_report_test`.
- [X] Run `uv run python scripts/skill_architecture_report.py --format json --strict .`.
- [X] Run `bash scripts/skill-architecture-report.sh .`.
- [X] Run `git diff --check`.
- [X] Apply repo-internal `ip-hygiene` triage to the touched public surfaces.

## Self-Review Checklist

- [X] `pr-ops` core does not include GitHub-specific mechanics beyond extension selection.
- [X] `extensions/github.md` owns GitHub PR state, reviews, comments, checks, branch update, merge, close, and cleanup mechanics.
- [X] `issue-ops` remains the issue/work-item lifecycle skill; `pr-ops` reports linked issue implications without taking issue closure authority by default.
- [X] Plugin version and description are synchronized across all published manifests.
- [X] Claude Code and Codex runtime surfaces are present and thin.
- [X] README, CLAUDE, and AGENTS describe the current package surface.
- [X] Final validation commands all pass.
