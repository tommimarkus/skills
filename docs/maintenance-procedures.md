# Repo maintenance procedures

Rare-occasion repo maintenance procedures relocated from CLAUDE.md; each section is loaded on demand via the pointer at its original site.

## Dediren upstream release adoption

(The one architecture-specific version procedure, documented nowhere else.) When adopting a new `tommimarkus/dediren` release, bump only repo-owned refs — `DEDIREN_VERSION_DEFAULT` in `souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren-release.sh`, `EXPECTED_DEDIREN_VERSION` in `tests/architecture_dediren_release_test.py`, and the basic and mixed fixtures' `required_plugins` version. Before classifying the bump or re-stamping, run the gated `DEDIREN_RELEASE_SMOKE=1` release suite (full validate→layout→render→export pipeline against the new bundle): a version-string change can hide a runtime-contract change (e.g. the render-envelope schema version, `data.content`→`data.artifacts`) that requires test/doc updates and makes the bump non-cosmetic. Also run a feature-parity step before finishing — diff the new bundle against the current pin (agent-usage guide, plugin manifests, schemas, bundled fixtures, commands, semantic profiles) and add or update architecture-design skill support for any new capability, not only bump refs and sync; record the parity finding (new features supported, or "maintenance-only, no contract change") in closeout. Then re-stamp `souroldgeezer-architecture` (cosmetic only when the smoke suite and parity diff confirm no skill-contract change) and sync manifests / marketplace / README / version-sync test — the re-stamp follows "Where that stamp lands": deferred to the `main` integration commit when the adoption work is in a worktree. Never patch the downloaded bundle; report runtime defects upstream. Tool-ownership and runtime-evidence rules live in the architecture-design `SKILL.md` and `docs/architecture-reference/architecture.md`.

## Removing a runtime's or tool's support

Scope the cut to the marketplace's **own** surfaces — per-runtime manifests/wrappers/metadata, runtime-parity tooling and finding fields, install docs, and version-cell sets. Do **not** scrub (a) general agent-guidance conventions a downstream *target* repo uses (e.g. `AGENTS.md` in the policy / `ip-hygiene` skills); (b) optional external-plugin handoffs; (c) vendor-named security/detection patterns (e.g. an `openai-key` secret regex). Confirm no regression with a same-engine before/after report diff, and re-run the gold ledger so the ≥500-case / ≥90%-recall floor still holds after pruning rule families and regenerating it.

## architecture-design plugin migration

`architecture-design` moved from `souroldgeezer-design` to `souroldgeezer-architecture`; users who installed `souroldgeezer-design` for architecture work must install `souroldgeezer-architecture@souroldgeezer`. Canonical handoff is the dediren package directory `docs/architecture/<feature>.dediren/`.
