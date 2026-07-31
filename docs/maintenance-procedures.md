# Repo maintenance procedures

Rare-occasion repo maintenance procedures relocated from CLAUDE.md; each section is loaded on demand via the pointer at its original site.

## Dediren upstream release adoption

(The one architecture-specific version procedure, documented nowhere else.) Adopting a new `tommimarkus/dediren` release is a **mechanical pin bump** across ~14 repo-owned surfaces plus a small **judgment residue** the tool cannot decide. One command — `adopt` — runs the whole mechanical spine and prints exactly what to do next; it never asks a question. The tool (`scripts/dediren_bump.py`, stdlib-only) lives outside every plugin tree, so it needs no CalVer stamp of its own. You don't need to look the version up: `scripts/dediren_bump.py latest` prints the newest published release (it follows GitHub's `/releases/latest` redirect, no API token), and every `--to` accepts the literal `latest`.

**There is a support floor below the pin.** `dediren-release.sh` carries `DEDIREN_VERSION_FLOOR` (currently `2026.07.28`, the oldest release whose rendered views arrive already labelled for assistive technology) and refuses to resolve anything older, or any non-CalVer `DEDIREN_VERSION`. `adopt` only moves `DEDIREN_VERSION_DEFAULT` and its preflight requires a *newer* target, so a normal bump never meets the floor — but a **rollback below it fails at resolve time**, by design, because the post-render band step refuses artifacts with no accessible name (`architecture.md` §9). Lowering the floor is a support decision: change it deliberately, and restore the step's name-synthesising path with it.

**Happy path (a maintenance/cosmetic bump — the common case): three commands.**

```bash
# 0. Resolve the newest release and isolate the work in a worktree named for it.
#    (Or set version=<X> by hand to target a specific release.)
version="$(uv run python scripts/dediren_bump.py latest)"
git worktree add -b dediren-"$version" .worktrees/dediren-"$version" main
cd .worktrees/dediren-"$version"

# 1. Run the whole adoption; read the verdict it prints. (`--to latest` also works.)
uv run python scripts/dediren_bump.py adopt --to "$version"

# 2. Commit the bump on the branch (the verdict's NEXT lines confirm this).
git commit -am "chore(architecture-design): adopt Dediren $version (<classification>)"

# 3. Integrate on main using the exact INTEGRATION recipe the verdict printed.
```

**What `adopt --to <version>` does, in one non-interactive pass** (`--to` also accepts `latest`; add `--plan` for a read-only preview that classifies but does not bump or verify; add `--json` for machine-readable output):

1. **Preflight** — target is CalVer and newer than the current pin; the pin surfaces are clean. Blocks with exit 2 and a fix if not.
2. **Parity + auto-classification** — downloads the current and target bundles (in parallel, cached) and diffs the judgment surfaces (`bundle.json`, `docs/agent-usage.md`, plugin manifests, schemas, fixtures). It classifies **cosmetic** when the bundle changed only version strings, **non-cosmetic** when any contract surface changed, and lists the substantive surfaces. Conservative: anything it cannot prove is version-only counts as substantive.
3. **Bump** — the scoped, re-verified pin replacement (release-script default + usage line, `EXPECTED_DEDIREN_VERSION`, the fixtures' `required_plugins`, the UML notation examples, the source-grounding claim). Reads the pin from the single source of truth (`DEDIREN_VERSION_DEFAULT` in `souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren-release.sh`), refuses on pre-existing drift, and re-runs the release test's pin discovery so a duplicated pin cannot be missed. It never touches `architecture.md` or any CalVer cell.
4. **Verify** (parallel) — the gated smoke suite (`DEDIREN_RELEASE_SMOKE=1` full validate→layout→render→export against the new bundle, plus the `dediren mcp` tool surface the plugin now bundles — `dediren_validate` / `dediren_build` / `dediren_guide`), the dediren surface tests, and `git diff --check`. A real upstream contract break (e.g. render-envelope schema version, `data.content`→`data.artifacts`) surfaces here as a **verify failure** (exit 1), not a silent cosmetic pass — this is the honesty backstop for auto-classification.

Exit codes: **0** = ready to integrate, **1** = a verify gate failed (fix, then re-run `adopt` — it is idempotent), **2** = preflight/parity could not proceed.

**Follow the verdict's `NEXT` lines** — the only residual steps, spelled out so no question is needed:

- **cosmetic** → commit and go straight to integration; a normal scoped `ip-hygiene` triage is enough.
- **non-cosmetic** → run the `ip-hygiene` skill **in-depth** over the changed architecture surface. Then, **before judging capability**, search this repo's and `tommimarkus/dediren`'s issue trackers for prior feature requests and recorded roadmap dependencies on the listed surfaces: a closed or `not_planned` upstream request is **not** durable evidence about that capability's future — a superseding issue can ship it later, and the shipped bundle outranks both any recorded closure and the superseding issue's own lifecycle marker. Now review each listed substantive surface for a **new capability**. If one needs architecture-design skill support, that is feature work — file a follow-up issue and **stop before integrating**. Otherwise record `maintenance-only, no contract change`, commit, and integrate.

**Integration (step 3) always lands on `main`, never on the branch** — the feature branch carries content only (`AGENTS.md` / `CLAUDE.md` plugin versioning). The verdict prints the exact recipe: `version_stamp.py guard`, then `version_stamp.py compute --plugin souroldgeezer-architecture`, then apply the padded stamp to the Claude manifest and README and its month-normalized derivative to the Codex manifest, update the version-sync test, and commit on `main`. Marketplace entries never carry a `version` key.

Never patch the downloaded bundle; report runtime defects upstream. Tool-ownership and runtime-evidence rules live in the architecture-design `SKILL.md` and `docs/architecture-reference/architecture.md`.

## Removing a runtime's or tool's support

Scope the cut to the marketplace's **own** surfaces — per-runtime manifests/wrappers/metadata, runtime-parity tooling and finding fields, install docs, and version-cell sets. Do **not** scrub (a) general agent-guidance conventions a downstream *target* repo uses (e.g. `AGENTS.md` in the policy / `ip-hygiene` skills); (b) optional external-plugin handoffs; (c) vendor-named security/detection patterns (e.g. an `openai-key` secret regex). Confirm no regression with a same-engine before/after report diff, and re-run the gold ledger so the ≥500-case / ≥90%-recall floor still holds after pruning rule families and regenerating it.

## architecture-design plugin migration

`architecture-design` moved from `souroldgeezer-design` to `souroldgeezer-architecture`; users who installed `souroldgeezer-design` for architecture work must install `souroldgeezer-architecture@souroldgeezer`. Canonical handoff is the dediren package directory `docs/architecture/<feature>.dediren/`.
