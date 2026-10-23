# CLAUDE.md

This is a cross-runtime plugin marketplace. Shared `<plugin>/skills/**` workflows
are the source of truth; runtime adapters package the same behavior for Claude
Code and Codex, with native Copilot CLI support where declared. This file is a
self-contained runtime contract; do not load the other host's guidance first.

## Start with the task

For skill-related changes, read
[working principles](docs/skill-architecture.md#working-principles), the affected
skill's entry, and the references needed for the actual decision. The full
architecture standard is an on-demand maintainer reference. Follow the user's
authorized outcome and project contracts; bundled conventions are strong defaults.
Use proportionate reading, planning, delegation, checks, and reporting. Expand
inspection when uncertainty, dependencies, or consequences warrant it. Keep
explicit user boundaries and record material exceptions once.

Use [contributing](docs/contributing.md) for contributor tasks,
[using skills](docs/using-skills.md) for routing, and
[runtime support](docs/runtime-support.md) for installation and host behavior.
Preserve source facts, tool results, and inference as distinct evidence. Missing
essential evidence limits the conclusion that needs it; continue independent work.

## Operation status

Acknowledge known slow work and give meaningful milestones or confirmed waiting
within 60 seconds when the host can emit them. Use real completed/total progress
only when known; otherwise describe the state without invented percentages or ETA.
Prefer host notifications and aggregate background updates. Clear busy status on
success, failure, cancellation, or awaiting input. Surface actionable failures;
disclose uninterruptible host calls. These timings are repository guidance.

## Repository and runtime contracts

- `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` publish
  the same plugin set, order, names, descriptions, and source paths. Marketplace
  entries have no version field.
- Each plugin has Claude and legacy Codex manifests. A root `plugin.json`, when
  present, is the Agent Plugins manifest and may also support Copilot CLI.
  Its identity and strict-SemVer version match legacy Codex.
- Shared skills live under `<plugin>/skills/<skill>/SKILL.md`; each has a matching
  Claude router-only `agents/<skill>.md`. Keep descriptions aligned. Do not copy
  workflows for another host. Internal sources live in `internal-skills/**`, with
  thin wrappers in both `.agents/skills/**` and `.claude/skills/**`.
- Preserve documented Claude content substitutions `${CLAUDE_SKILL_DIR}` and
  `${CLAUDE_PLUGIN_ROOT}`; give Codex an absolute loaded-skill source-path form.
  Claude hook commands use plugin-root/data variables; Codex hook commands use
  `${PLUGIN_ROOT}` / `${PLUGIN_DATA}`.
- Codex root Agent Plugins MCP configuration supports root/data interpolation;
  legacy `.codex-plugin` plus `mcp/codex.mcp.json` is literal and has no plugin data
  root. Keep the separate legacy Copilot adapter. Shared root `mcp.json` declares
  no `env` or `cwd`, since Codex and Copilot handle those differently.
- Architecture's router requires an absolute `workspaceRoot` per operation and
  launches the upstream process there. It preserves explicit runtime overrides,
  checksum-verified provisioning, and host-managed Java 21+. Use the authoritative
  [installation procedure](souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md)
  for pins, writable plugin data, offline operation, and diagnosis. A generic local
  stdio client must provide absolute `DEDIREN_HOME` when no plugin data root exists.
  Per-release behavior follows [source grounding](souroldgeezer-architecture/skills/architecture-design/references/source-grounding.md).
- Architecture Review preserves original package evidence. Reproduce only through
  its isolated-review procedure and persistent byte-accounted copy; never rebuild
  or refresh the reviewed original.
- Check official host documentation when changing packaging or launch semantics.
  Do not select contributor models, approval policy, or sandbox settings in a
  checked-in `.codex/config.toml`.

## Git and tooling

`git-workflow-policy: feature branches, persistent repo-local worktrees,
clean worktree, no direct main`.

Create task worktrees from the primary checkout under its gitignored persistent
`.worktrees/<task-name>/`. Never put a worktree or uncommitted task work under
`/tmp`, `$TMPDIR`, `/var/tmp`, tmpfs, or another ephemeral location. If that root
is unavailable, stop and ask. Preserve unrelated work and runtime data. Stage
explicit paths; do not force-add ignored files. Before committing,
`git ls-files -ci --exclude-standard` must be empty unless the user explicitly
approved the exact tracked exception.

Parent integration is local and fast-forward only after review and required
verification. Keep concurrent writers in separate worktrees. Before cleanup,
prove each task branch appears in `git branch --merged <target>`, remove only its
clean worktree, run `git worktree prune`, then `git branch -d`. Never force delete.
Stop cleanup on a failed proof. Integration does not authorize pushing.

Use `rg` for search, `jq` for JSON, and Mike Farah `yq` for YAML frontmatter, TOML,
and XML. Preserve Python 3.11 and repo-local `uv` configuration. Bundled Lean,
test-quality, and planning Python helpers follow ruff plus `mypy --strict` in
`pyproject.toml`. Run repository-wide checks in the task worktree, so nested
checkouts do not contaminate enumeration.

## Implementation and evidence

Inspect existing tests and classify changes at the observable seam. Changed
behavior gets a focused failing test first at the cheapest sufficient level;
refactors use existing passing tests, and trivial wiring/config gets no invented
RED. Keep cohesive scenarios and reuse `tests/surface_test_lib.py`. Run focused
checks during development. Remove obsolete tests when behavior is removed, naming
successors where coverage is replaced; retain meaningful regression protection.
Avoid fixed sleeps, real clocks, and machine locale/timezone assumptions.

Use evidence-backed findings beyond scanner nominations without misattributing
them to tools. Inventory differences and load-cost proxies are advisory evidence,
not semantic-fidelity or user-value proof. Keep actual broken references and
runtime defects visible. No generic Stop hook may require another workflow or
create an issue; lesson capture is explicitly invoked. Optional prevention hooks
are documented in [the hook recipe](souroldgeezer-audit/skills/lean-audit/references/hook-recipe.md).

For delegated audits, establish authoritative item identities before slicing;
reconcile coverage by identity, not counts alone. Missing optional evidence is
unknown. Retain explicit no-rerun and existing-results-only limits. API design owns
HTTP-to-storage efficiency; software design owns other data paths; report defects
once. Stack composition retains Vite before React, React before Next, and Node
before Next when the combined mechanics matter. Test-quality deep work assesses
suite management and setup/teardown before attributing suite cost; source inspection
cannot establish observed browser behavior or performance. DevSecOps cost policy
comes from the target repository's host-scoped guidance, including both runtime
files as evidence when applicable.

## Planning-policy execution contract (Claude Code)

Standard planning is proportionate: explicit implementation authority and settled
behavior do not require redundant approval, and small cohesive work may stay
inline. Explicit plan-first instructions require approval. Delegate when it helps;
the parent owns review, integration, and final verification. Routine necessary
adjacent work stays within the approved outcome; material scope or authority changes
need a decision. Independent review remains risk-based.

Explicit strict execution retains v5 contracts, bound worker/verifier handoffs,
and immutable approved leaves. Existing runs and explicit model pins retain their
settings. For new unpinned runs, use available suitable executors through existing
explicit assignment/capability bindings; do not guess capabilities or silently
weaken a requirement. The [planning entry](souroldgeezer-policy/skills/planning-policy/SKILL.md)
routes to standard and strict host instructions. No root-level model mapping or
managed ledger is required for ordinary work.

## Verification and local publication

Use the [contributor verification guide](docs/contributing.md#validate-the-change)
for the affected commands. Routine bounded changes run owning tests and relevant
structural checks. Cross-cutting changes and publication run the full candidate
sequence once, including `uv run python -m unittest discover -s tests -p '*_test.py'`
and the isolated host smoke with **both** `--fresh --assert-profile-isolation`.
Metadata parity is owned by fragmentation in the full sequence. Missing tools are
reported as skips or blockers; zero collected tests is a failure. Preserve the
actual command's exit status; a downstream pipeline stage is not gate evidence.

The host smoke uses temporary host/plugin-data state without replacing `HOME`,
clears inherited provisioning roots, and fingerprints normal host control planes.
Never provision into a user's normal plugin-data root during a smoke. A missing
standalone Codex validator is a disclosed skip.

A push of `main` is publication. Before an explicitly authorized push, run
`python3 -B scripts/publication_check.py --repo-root . record` from the exact clean
candidate. It retains the full ordered gates and unconditional isolated smoke.
The existing `record --version-followup` accepts only the documented single atomic
version-only descendant. Other publication-source drift needs a new receipt;
proportionate local checks cannot authorize a push. Installing the pre-push hook,
pushing, and changing external security settings need explicit task authority.
The local receipt is bypassable, not independent approval or artifact provenance.

Feature branches carry content, with no existing version-cell increments. After
verified local integration, run `uv run python scripts/version_stamp.py guard` and
`compute --plugin <name>` on `main`. Apply padded CalVer to the Claude manifest and
README version cell, normalized strict SemVer to legacy Codex and root manifests,
in one version-only integration commit. Run focused version/parity checks afterward.
Full verification evidence survives that fixed follow-up only under the documented
ancestry/content proof. New manifests may carry the current normalized version.

[SECURITY.md](SECURITY.md) owns reporting and supported versions; private reporting
enablement is pending/unverified until re-read live. Keep sensitive reports out of
public issues. [Security baseline](docs/security-baseline.md) owns the threat model,
accepted residuals, and assurance limits. Public changes receive proportionate
source/IP inspection; breaking or additive public-surface work retains in-depth
IP hygiene and cosmetic work scoped triage. Never claim legal clearance.

## Documentation and ownership

Keep this file, the other runtime's self-contained guidance, and README current
when public contracts, structure, runtime support, install commands, or validation
change. Update contributor navigation and release/maintenance guides when their
procedures change. Keep executable hook configuration and scripts in CODEOWNERS.
Use outcome, checks, and material limitations in the final response; avoid routine
policy inventories unless requested or required by a real consumer.
