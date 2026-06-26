# AGENTS.md

This repository is a dual Claude Code + Codex plugin marketplace. For full
authoring policy, read [CLAUDE.md](CLAUDE.md) — the canonical repo guide, so
rules aren't duplicated across agent entrypoints.

Keep this file a thin Codex-native pointer. When canonical policy changes,
update [CLAUDE.md](CLAUDE.md) first and adjust this file only when Codex entry
rules change.

## Codex Quick Rules

- Use the existing [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json)
  as the shared marketplace. Do not add `.agents/plugins/marketplace.json`
  unless a future design explicitly splits catalogs.
- Before changing plugin packaging or install guidance, cross-check both
  official doc sets (Claude Code plugin / marketplace docs and Codex plugin /
  skills docs) — one runtime's docs aren't enough for this cross-agent repo.
- Keep each plugin's `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`,
  and the shared marketplace entry synced on `name`, `version`, `description`.
- Codex consumes bundled skills via `.codex-plugin/plugin.json` with
  `"skills": "./skills/"`.
- For any work on skills, agents, runtime metadata, bundled references,
  extensions, deterministic machinery, manifests, marketplace entries,
  repo-internal authoring skills, or repo docs describing them, read
  [docs/skill-architecture.md](docs/skill-architecture.md) before deciding scope
  or editing. This is an entry rule, not only a closeout check.
- Local Codex marketplace dev: refresh changed installed plugins through the
  plugin browser and restart Codex; `codex plugin marketplace upgrade <name>` is
  for Git-backed marketplaces and won't refresh local clone sources. Verify the
  materialized cache has the expected version and `skills/` directories.
- Keep Codex `interface.defaultPrompt` arrays to three or fewer entries.
- `agents/*.md` are Claude Code subagents. Project-scoped Codex custom agents
  live in `.codex/agents/*.toml`; plugin-bundled Codex skill metadata lives in
  `skills/<skill>/agents/openai.yaml`.
- GitHub™ issue lifecycle (handle / triage / resume / implement / close /
  process end to end here): use the repo-internal
  [.claude/skills/github-issue-lifecycle/SKILL.md](.claude/skills/github-issue-lifecycle/SKILL.md)
  overlay (composes the public `issue-ops` skill, the GitHub™ provider
  extension, and this repo's extra gates). Codex can invoke the thin
  [.codex/agents/github-issue-lifecycle.toml](.codex/agents/github-issue-lifecycle.toml)
  wrapper.
- Repo-internal lesson capture: when the lesson-capture Stop hook fires, follow
  [.claude/skills/lesson-capture/SKILL.md](.claude/skills/lesson-capture/SKILL.md);
  the hook is registered for both Claude Code and Codex. Codex can invoke
  [.codex/agents/lesson-capture.toml](.codex/agents/lesson-capture.toml).
- Repo-internal lesson review: when the user runs `/lessons` or asks to review
  captured lessons, follow
  [.claude/skills/lessons/SKILL.md](.claude/skills/lessons/SKILL.md). Codex can
  invoke [.codex/agents/lessons.toml](.codex/agents/lessons.toml).
- PR/MR work (create / review / update / fix / merge / close / resume / process
  end to end, including prepared branches): use the public `pr-ops` skill from
  `souroldgeezer-ops` with the identified provider extension — normally the
  GitHub™ provider extension here. Codex can invoke the thin
  [.codex/agents/pr-ops.toml](.codex/agents/pr-ops.toml) wrapper.
- `souroldgeezer-policy` skills are passive until a target repo initializes them
  in its own guidance. Plugin installation or marketplace availability is not
  enforcement authority.
- When target repo guidance initializes `git-workflow-policy` (or the user asks
  to inspect / adopt / enforce git workflow policy), treat it as standing
  enforcement authority before branch, staging, commit, merge, rebase,
  force-push, destructive-git, PR/MR-handoff, or git-workflow guidance edits.
  Codex wrapper: [.codex/agents/git-workflow-policy.toml](.codex/agents/git-workflow-policy.toml).
  Bare init applies the conservative default profile; adopt mode absorbs
  existing related guidance into init / options / exceptions and removes
  competing workflow prose.
- When target repo guidance initializes `release-policy` (or the user asks to
  inspect / adopt / enforce release policy), treat it as standing enforcement
  authority before version updates, changelog / release-note changes, tags,
  provider releases, package or marketplace publication, rollback, or release
  exceptions. A repo can declare options such as
  `release-policy: calver YYYY.MM.build, git tagging`. Codex wrapper:
  [.codex/agents/release-policy.toml](.codex/agents/release-policy.toml). Bare
  init applies the SemVer + annotated `v<version>` tag default profile; adopt
  mode absorbs existing related guidance and removes competing release prose.
- Use `jq` for JSON; Mike Farah `yq` for YAML frontmatter, TOML, and XML.
- Treat `.gitignore` as a hard staging boundary: no force-add (`git add -f` /
  `--force`, `git update-index --add`, equivalents) unless the user names the
  exact ignored path and says to track it. Before committing,
  `git ls-files -ci --exclude-standard` must be empty; uncommit any tracked
  ignored path with `git rm --cached -- <path>` while keeping the local file.
- architecture-design runtime checks use the release resolver
  `souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren-release.sh`
  — it downloads the pinned Java™-backed Dediren bundle from GitHub™ Releases
  into `.cache/dediren/releases/` (don't commit it; needs Java™ 21+). Release
  bundles and any future packaged bundles are imported upstream artifacts, not
  repo-owned source — Do not patch them to fix Dediren runtime / schema / plugin
  / helper / layout / render / export behavior; disclose defects under `Dediren
  tool issues` with release version, command, input summary, envelope/error,
  expected behavior, and repro evidence.
- For Dediren release adoption, follow the [CLAUDE.md](CLAUDE.md) checklist:
  verify the latest upstream release, update the resolver default + release-test
  expected version + basic fixture plugin version, re-stamp/sync
  `souroldgeezer-architecture` CalVer metadata when shipped references change,
  smoke the release when network and Java™ 21+ are available, and never patch
  downloaded bundles.
- Skill architecture report tooling uses the repo-local `uv` project: `uv venv`,
  `uv run python scripts/skill_architecture_report.py .`,
  `uv run python scripts/skill_architecture_report.py --format json --strict .`,
  and `uv run python -m unittest tests.skill_architecture_report_test`. Don't
  commit `.venv/`. `pyproject.toml` points `uv` at `.cache/uv` when run from the
  repo root; don't add `UV_CACHE_DIR=/tmp/codex-uv-cache` to normal plans or
  verification — confirm with `uv cache dir` and override `UV_CACHE_DIR` only as
  a one-off fallback if the repo config isn't applied or the cache isn't
  writable.
- Add report-engine cases one by one in
  `tests/skill_architecture_report_ledger.jsonl`; keep `SAC-T#####` IDs
  contiguous and let the unittest ledger checks reject duplicate intent or
  fixture fingerprints. The strict report also enforces the empirical bar: at
  least 500 local gold-finding cases and ≥90% automated recall. If cases are
  bulk-generated, update
  `tests/generate_skill_architecture_report_ledger.py` and regenerate the JSONL
  in the same change.
- Follow the public `ip-hygiene` skill
  ([SKILL.md](souroldgeezer-audit/skills/ip-hygiene/SKILL.md)) when editing
  plugin manifests, skills, agents, bundled references, or README / CLAUDE /
  AGENTS sections that describe them. Repo Stop hooks also prompt for this check
  when those surfaces change.
- Before finishing those same skill-related changes, apply the skill
  architecture craft standard and run `scripts/skill-architecture-report.sh`
  when available.
