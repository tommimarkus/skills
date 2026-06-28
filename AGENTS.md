# AGENTS.md

This repository is a dual Claude Code + Codex plugin marketplace. For full
authoring policy, read [CLAUDE.md](CLAUDE.md) — the canonical repo guide, so
rules aren't duplicated across agent entrypoints.

Keep this file a thin Codex-native pointer. When canonical policy changes,
update [CLAUDE.md](CLAUDE.md) first and adjust this file only when Codex entry
rules change. The bullets below are Codex-entry mechanics and routing; every
general policy is owned by a CLAUDE.md section, linked under "Canonical policy"
rather than restated here.

## Codex packaging & entry mechanics

- Use the existing [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json)
  as the shared marketplace. Do not add `.agents/plugins/marketplace.json`
  unless a future design explicitly splits catalogs.
- Codex consumes bundled skills via `.codex-plugin/plugin.json` with
  `"skills": "./skills/"`.
- Keep Codex `interface.defaultPrompt` arrays to three or fewer entries.
- `agents/*.md` are Claude Code subagents. Project-scoped Codex custom agents
  live in `.codex/agents/*.toml`; plugin-bundled Codex skill metadata lives in
  `skills/<skill>/agents/openai.yaml`.
- Shared repo-internal skill workflows live under `internal-skills/<name>/`.
  Tool-specific folders only hold entrypoints: Claude Code wrappers in
  `.claude/skills/<name>/SKILL.md`, Codex wrappers in `.codex/agents/*.toml`.
  Keep every wrapper pointed at `internal-skills/<name>/SKILL.md`; do not copy
  shared workflow or reference prose into runtime-specific folders.
- Local Codex marketplace dev: refresh changed installed plugins through the
  plugin browser and restart Codex; `codex plugin marketplace upgrade <name>` is
  for Git-backed marketplaces and won't refresh local clone sources. Verify the
  materialized cache has the expected version and `skills/` directories.

## Codex invocation map

Terse trigger → Codex wrapper. The skill (and CLAUDE.md) own what each does.

- GitHub™ issue lifecycle (handle / triage / resume / implement / close /
  process end to end here) → [.codex/agents/github-issue-lifecycle.toml](.codex/agents/github-issue-lifecycle.toml)
  (overlay source: [internal-skills/github-issue-lifecycle/SKILL.md](internal-skills/github-issue-lifecycle/SKILL.md)).
- Lesson capture, when the lesson-capture Stop hook fires →
  [.codex/agents/lesson-capture.toml](.codex/agents/lesson-capture.toml)
  (source: [internal-skills/lesson-capture/SKILL.md](internal-skills/lesson-capture/SKILL.md)).
- Lesson review, on `/lessons` or a request to review captured lessons →
  [.codex/agents/lessons.toml](.codex/agents/lessons.toml)
  (source: [internal-skills/lessons/SKILL.md](internal-skills/lessons/SKILL.md)).
- PR/MR work (create / review / update / fix / merge / close / resume / process
  end to end, including prepared branches) → [.codex/agents/pr-ops.toml](.codex/agents/pr-ops.toml)
  with the identified provider extension (normally GitHub™ here).
- `git-workflow-policy`, when target repo guidance initializes it or the user
  asks to inspect / adopt / enforce git workflow policy →
  [.codex/agents/git-workflow-policy.toml](.codex/agents/git-workflow-policy.toml).
- `release-policy`, when target repo guidance initializes it or the user asks to
  inspect / adopt / enforce release policy →
  [.codex/agents/release-policy.toml](.codex/agents/release-policy.toml).

`souroldgeezer-policy` skills are passive: plugin installation or marketplace
availability is not enforcement authority until a target repo initializes them.

## Canonical policy (owned by CLAUDE.md — read before acting, don't restate here)

- Cross-check both runtime doc sets before changing packaging or install
  guidance → [CLAUDE.md](CLAUDE.md) "Runtime documentation cross-checks".
- Manifest / marketplace version sync and CalVer stamping — do **not** stamp
  version cells inside a worktree; `scripts/version_stamp.py guard` before
  integration, `scripts/version_stamp.py compute --plugin <name>` at integration
  on `main`; the breaking/additive `ip-hygiene` gate → [CLAUDE.md](CLAUDE.md)
  "Plugin versioning (MUST)".
- Read [docs/skill-architecture.md](docs/skill-architecture.md) before scoping
  any skill-related change, and run `scripts/skill-architecture-report.sh` at
  closeout → [CLAUDE.md](CLAUDE.md) "Skill architecture craft standard (MUST)".
- `jq` for JSON; Mike Farah `yq` for YAML / TOML / XML →
  [CLAUDE.md](CLAUDE.md) "Structured-file tooling".
- `.gitignore` is a hard staging boundary (no force-add; `git ls-files -ci
  --exclude-standard` must be empty before commit) → [CLAUDE.md](CLAUDE.md)
  "Git ignore hygiene (MUST)".
- `uv` project, `.cache/uv`, report-engine ledger (`SAC-T#####`) cases, and the
  empirical recall bar → [CLAUDE.md](CLAUDE.md) "Repo-local Python® tooling".
- `ip-hygiene` when editing plugin manifests, skills, agents, bundled
  references, or README / CLAUDE / AGENTS sections describing them
  ([SKILL.md](souroldgeezer-audit/skills/ip-hygiene/SKILL.md); repo Stop hooks
  also prompt for it).
- The Dediren release bundle (resolved by
  `souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren-release.sh`
  into `.cache/dediren/releases/`, needs Java™ 21+) and any future packaged
  bundles are imported upstream artifacts, not repo-owned source — Do not patch
  them; disclose defects under `Dediren tool issues` with release version,
  command, input summary, envelope/error, expected behavior, and repro
  evidence. Release-adoption checklist and CalVer re-stamp →
  [CLAUDE.md](CLAUDE.md) "Plugin versioning (MUST)" (Dediren paragraph).
