# AGENTS.md

This repository is a dual Claude Code + Codex plugin marketplace. For full
authoring policy, read [CLAUDE.md](CLAUDE.md); it remains the canonical repo
guide so we do not duplicate rules across agent entrypoints.

Keep this file as a thin Codex-native pointer. When canonical policy changes,
update [CLAUDE.md](CLAUDE.md) first and only adjust this file when Codex entry
rules change.

## Codex Quick Rules

- Use the existing [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json)
  as the shared marketplace. Do not add `.agents/plugins/marketplace.json`
  unless a future design explicitly chooses to split catalogs.
- Before changing plugin packaging or install guidance, cross-check both
  official doc sets: Claude Code plugin / marketplace docs and Codex plugin /
  skills docs. This is a cross-agent skills repo, so one runtime's docs are
  not enough.
- Keep each plugin's `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`,
  and shared marketplace entry synchronized on `name`, `version`, and
  `description`.
- Codex consumes bundled skills through `.codex-plugin/plugin.json` with
  `"skills": "./skills/"`.
- `agents/*.md` files are Claude Code subagents. Project-scoped Codex custom
  agents live in `.codex/agents/*.toml`; plugin-bundled Codex skill metadata
  lives in `skills/<skill>/agents/openai.yaml`.
- Use `jq` for JSON inspection, validation, and sync checks. Use Mike Farah
  `yq` for YAML frontmatter, TOML, and XML.
- Follow the repo-internal `ip-hygiene` guidance in
  [.claude/skills/ip-hygiene/SKILL.md](.claude/skills/ip-hygiene/SKILL.md)
  when editing plugin manifests, skills, agents, bundled references, or
  README / CLAUDE / AGENTS sections that describe them.
- Before finishing any change to a published plugin skill or its related
  agent, runtime metadata, bundled reference, extension, manifest, marketplace
  entry, or repo docs, follow the repo-internal `review-published-skill`
  guidance in
  [.claude/skills/review-published-skill/SKILL.md](.claude/skills/review-published-skill/SKILL.md).
