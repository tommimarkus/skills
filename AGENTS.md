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
- For any work on skills, agents, runtime metadata, bundled references,
  extensions, deterministic machinery, manifests, marketplace entries,
  repo-internal authoring skills, or repo docs that describe those surfaces,
  read [docs/skill-architecture.md](docs/skill-architecture.md) before deciding
  scope or editing. This is an entry rule, not only a closeout check.
- For local Codex marketplace development, refresh changed installed plugins
  through the plugin browser and restart Codex; `codex plugin marketplace
  upgrade <name>` is for Git-backed marketplaces and does not refresh local
  clone sources. Verify the materialized cache contains the expected version and
  `skills/` directories.
- Keep Codex `interface.defaultPrompt` arrays to three or fewer entries.
- `agents/*.md` files are Claude Code subagents. Project-scoped Codex custom
  agents live in `.codex/agents/*.toml`; plugin-bundled Codex skill metadata
  lives in `skills/<skill>/agents/openai.yaml`.
- When the user explicitly asks to handle, triage, resume, implement, close, or
  process GitHub™ issues end to end in this repository, use the repo-internal
  [.claude/skills/github-issue-lifecycle/SKILL.md](.claude/skills/github-issue-lifecycle/SKILL.md)
  overlay. It composes the public `issue-ops` skill, the GitHub™ provider
  extension, and this repo's extra gates. Codex can invoke the thin
  [.codex/agents/github-issue-lifecycle.toml](.codex/agents/github-issue-lifecycle.toml)
  wrapper for that overlay.
- When the user explicitly asks to create, review, update, fix, merge, close,
  resume, or process pull requests, merge requests, or prepared PR/MR branches end
  to end, use the public `pr-ops` skill from `souroldgeezer-ops` with the
  identified provider extension. In this repository, that is normally the
  GitHub™ provider extension. Codex can invoke the thin
  [.codex/agents/pr-ops.toml](.codex/agents/pr-ops.toml) wrapper for that
  workflow.
- Use `jq` for JSON inspection, validation, and sync checks. Use Mike Farah
  `yq` for YAML frontmatter, TOML, and XML.
- Treat `.gitignore` as a hard staging boundary. Do not force-add ignored files
  with `git add -f`, `git add --force`, `git update-index --add`, or
  equivalents unless the user explicitly names the exact ignored path and says
  it should be tracked. Before committing, `git ls-files -ci --exclude-standard`
  must be empty; any tracked ignored path must be uncommitted with
  `git rm --cached -- <path>` while keeping the local file.
- Use the packaged dediren tool directly for architecture-design runtime
  checks. The Linux bundle lives under
  `souroldgeezer-architecture/tools/dediren-linux/`; add
  `souroldgeezer-architecture/tools/dediren-macos/` when the macOS build exists.
  These bundle directories are imported upstream artifacts, not repo-owned
  tool source. Do not patch files under them directly to fix Dediren runtime,
  schema, plugin, or helper behavior; update this repo only by replacing the
  bundle from an upstream Dediren release. When a Dediren tool issue is found,
  disclose it under `Dediren tool issues` with repro evidence; keep
  agent-specific issue filing mechanics in agent-local configuration.
- For skill architecture report tooling, use the repo-local `uv` project:
  `uv venv`, `uv run python scripts/skill_architecture_report.py .`, and
  `uv run python scripts/skill_architecture_report.py --format json --strict .`,
  plus `uv run python -m unittest tests.skill_architecture_report_test`. Do
  not commit `.venv/`.
- Add report-engine cases one by one in
  `tests/skill_architecture_report_ledger.jsonl`; keep `SAC-T#####` IDs
  contiguous and let the unittest ledger checks reject duplicate intent or
  duplicate fixture fingerprints. The strict report also checks the empirical
  replacement bar: at least 500 local gold-finding cases and `>=90%` automated
  recall. If cases are bulk-generated, update
  `tests/generate_skill_architecture_report_ledger.py` and regenerate the JSONL
  ledger in the same change.
- Follow the repo-internal `ip-hygiene` guidance in
  [.claude/skills/ip-hygiene/SKILL.md](.claude/skills/ip-hygiene/SKILL.md)
  when editing plugin manifests, skills, agents, bundled references, or
  README / CLAUDE / AGENTS sections that describe them. Repo Stop hooks also
  prompt for this check when those surfaces change.
- Before finishing those same skill-related changes, apply the skill
  architecture craft standard and run `scripts/skill-architecture-report.sh`
  when it is available.
