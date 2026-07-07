# Repo maintenance procedures

Rare-occasion repo maintenance procedures relocated from CLAUDE.md; each section is loaded on demand via the pointer at its original site.

## Dediren upstream release adoption

(The one architecture-specific version procedure, documented nowhere else.) Adopting a new `tommimarkus/dediren` release is a **mechanical pin bump** across ~14 repo-owned surfaces plus a **judgment pass** (parity, classification, skill support) the tool cannot make for you. The mechanical bump and its re-verification are owned by the repo-maintenance tool `scripts/dediren_bump.py` (stdlib-only, run `uv run python scripts/dediren_bump.py <subcommand>`); it lives outside every plugin tree, so it needs no CalVer stamp of its own. Run, in order:

1. **Parity diff (judgment input).** `uv run python scripts/dediren_bump.py parity --to <version>` downloads the current and target release bundles via the release resolver and diffs the judgment surfaces (`bundle.json`, `docs/agent-usage.md`, plugin manifests, schemas, bundled fixtures). Read the diff: a version-string change can hide a runtime-contract change (e.g. the render-envelope schema version, `data.content`→`data.artifacts`) that requires test/doc updates and makes the bump non-cosmetic. Cover the full feature set the pin spans (agent-usage guide, plugin manifests, schemas, bundled fixtures, commands, semantic profiles) and add or update architecture-design skill support for any new capability — do not only bump refs and sync.
2. **Bump the pins.** `uv run python scripts/dediren_bump.py bump --to <version>` replaces every embedded pin in one scoped, re-verified pass — the release-script default and usage line, `EXPECTED_DEDIREN_VERSION`, the basic and mixed fixtures' `required_plugins` version, the UML notation worked examples, and the source-grounding claim. It reads the current pin from the single source of truth (`DEDIREN_VERSION_DEFAULT` in `souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren-release.sh`), refuses when a pin has already drifted, and re-runs the release test's pin discovery so a duplicated pin cannot be silently missed. Preview with `--check` first. The bump deliberately does **not** touch `architecture.md` (capability docs are judgment) or any CalVer cell.
3. **Gated smoke suite.** `DEDIREN_RELEASE_SMOKE=1 uv run python -m unittest tests.architecture_dediren_release_test` runs the full validate→layout→render→export pipeline against the new bundle. It must pass before you classify or re-stamp — the re-pinned source-grounding claim is only honest once the smoke suite confirms the new bundle.
4. **Classify + record.** Classify the bump (cosmetic only when the smoke suite and parity diff confirm no skill-contract change) and record the parity finding in closeout (new features supported, or "maintenance-only, no contract change").
5. **Re-stamp + sync at integration.** Re-stamp `souroldgeezer-architecture` and sync manifests / marketplace / README / version-sync test. The re-stamp follows "Where that stamp lands" (CLAUDE.md § Plugin versioning): deferred to the `main` integration commit when the adoption work is in a worktree, computed with `uv run python scripts/version_stamp.py compute --plugin souroldgeezer-architecture`.

Never patch the downloaded bundle; report runtime defects upstream. Tool-ownership and runtime-evidence rules live in the architecture-design `SKILL.md` and `docs/architecture-reference/architecture.md`.

## Removing a runtime's or tool's support

Scope the cut to the marketplace's **own** surfaces — per-runtime manifests/wrappers/metadata, runtime-parity tooling and finding fields, install docs, and version-cell sets. Do **not** scrub (a) general agent-guidance conventions a downstream *target* repo uses (e.g. `AGENTS.md` in the policy / `ip-hygiene` skills); (b) optional external-plugin handoffs; (c) vendor-named security/detection patterns (e.g. an `openai-key` secret regex). Confirm no regression with a same-engine before/after report diff, and re-run the gold ledger so the ≥500-case / ≥90%-recall floor still holds after pruning rule families and regenerating it.

## architecture-design plugin migration

`architecture-design` moved from `souroldgeezer-design` to `souroldgeezer-architecture`; users who installed `souroldgeezer-design` for architecture work must install `souroldgeezer-architecture@souroldgeezer`. Canonical handoff is the dediren package directory `docs/architecture/<feature>.dediren/`.
