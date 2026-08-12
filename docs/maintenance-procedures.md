# Repo maintenance procedures

Rare-occasion repo maintenance procedures relocated from CLAUDE.md; each section is loaded on demand via the pointer at its original site.

## Dediren upstream release adoption

The architecture plugin provisions a **pinned, checksum-verified** Dediren
release into the host's own plugin data directory. Two module constants in
[`dediren_runtime.py`](../souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren_runtime.py)
govern it: `DEDIREN_VERSION_DEFAULT` (the release provisioned when nothing else
resolves) and `DEDIREN_VERSION_FLOOR` (the oldest release supported at all).
Resolution order stays `DEDIREN_COMMAND` → the managed install → a `PATH`
`dediren` reporting at or above the floor → the legacy migration cache →
provisioning the pin; `DEDIREN_AUTO_INSTALL=0` disables the last step. Java is
never downloaded. Operator-facing install steps ship with the plugin at
[`references/procedures/dediren-install.md`](../souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md).

Adopting a new `tommimarkus/dediren` release is therefore a plugin release
procedure, not a host operation. Work the steps in order.

**1. Survey the candidate.** Read its release notes and confirm it publishes
both assets provisioning needs — one `dediren-agent-bundle-<version>.*` and
`SHA256SUMS`. `uv run python scripts/dediren_pin.py --check` reports the current
pin, the floor, and the latest published release (`--format json` for
automation); it never writes and is not an error merely because a newer release
exists.

**2. Run the gated smoke suite against the candidate.** Provision it to a
scratch data directory, then bind both lanes to that executable:

```bash
candidate=YYYY.0M.MICRO
launcher=$(DEDIREN_VERSION="$candidate" DEDIREN_HOME="$PWD/.cache/dediren-adoption" \
  python3 souroldgeezer-architecture/skills/architecture-design/references/scripts/dediren_runtime.py --ensure)
"$launcher" --version   # must report $candidate before either lane means anything
DEDIREN_RUNTIME_SMOKE=1 DEDIREN_COMMAND="$launcher" \
  uv run python -m unittest tests.architecture_dediren_release_test
DEDIREN_COMMAND="$launcher" \
  scripts/check-runtime-host-smoke.py --fresh --assert-profile-isolation .
```

Check that printed version: resolution prefers a floor-meeting `dediren` already
on `PATH` over provisioning, so on a developer machine `--ensure` can hand back
the host's runtime instead of the candidate — trim `PATH` and re-run if it does.
Without `DEDIREN_COMMAND` the two lanes likewise test whatever is on `PATH`,
which is not the adoption question. `tests.architecture_dediren_runtime_test`
covers the resolver and provisioner offline and needs no gate.

**3. Diff feature parity against the release notes.** The adapter discovers the
live tool catalog, so *additive* upstream tools need no plugin change. A changed
schema, protocol, CLI surface, or result contract does — map each note to the
repo surface that carries it: the MCP router and its tool set, the bundle schema
version, the stage `--plugin` selectors, the export lanes, the render-policy
defaults, and the workflow guidance. Update those, the live tests, and the
release notes' consequences together, in one change.

**4. Move the pin.** `scripts/dediren_pin.py --set <version>` (or `--latest`)
rewrites `DEDIREN_VERSION_DEFAULT` only, refusing a non-CalVer version, one below
the floor, or one whose release does not publish both required assets; `--dry-run`
reports the move without writing. It resolves the repo root from the working
directory, so run it from the checkout you mean to change.

**5. Decide the floor separately.** A pin move never touches
`DEDIREN_VERSION_FLOOR`. Raise it only when the skill's own pipeline *requires*
behaviour absent below the new value — the 2026.07.28 precedent is per-view
`presentation` titles, which the post-render step demands rather than injects.
Raising it drops support for below-floor `PATH` installs and for hosts pinning
an older `DEDIREN_VERSION`, so it is a breaking support decision: state the
behavioural reason in `pinned_version()`'s refusal message in the same change.
Lowering it is equally a support decision, because older SVG output may lack
accessible names.

**6. Leave the fixture baseline alone unless its contract moved.**
The version in repo fixtures is a compatibility evidence baseline, not a runtime
selector, and `tests.architecture_dediren_release_test` holds every copy of it —
fixtures and UML notation examples alike — to one value. Move it only when the
fixture contract itself must move, and then move every copy.

**7. Classify and stamp.** A pin move touches
`souroldgeezer-architecture/skills/architecture-design/references/**`, so the
plugin takes a stamp at integration (see CLAUDE.md § "Plugin versioning"). A
plain pin move is **additive**: users get a new provisioned runtime with no
contract regression. A floor raise, a removed or renamed upstream tool, or a
changed result contract is **breaking**. Both classes require the in-depth
`ip-hygiene` gate over the changed plugin surface — the candidate's CycloneDX
SBOMs are the evidence for any new or changed third-party licence it brings in.

The router bounds startup and catalog waits at 120 seconds and tool-call waits
at 360 seconds by default; controlled hosts may set positive
`DEDIREN_MCP_STARTUP_TIMEOUT_SEC` and `DEDIREN_MCP_REQUEST_TIMEOUT_SEC` values.

Never patch a host installation from this repo, and never patch a provisioned
bundle in place; report Dediren defects upstream.

## Removing a runtime's or tool's support

Scope the cut to the marketplace's **own** surfaces — per-runtime manifests/wrappers/metadata, runtime-parity tooling and finding fields, install docs, and version-cell sets. Do **not** scrub (a) general agent-guidance conventions a downstream *target* repo uses (e.g. `AGENTS.md` in the policy / `ip-hygiene` skills); (b) optional external-plugin handoffs; (c) vendor-named security/detection patterns (e.g. an `openai-key` secret regex). Confirm no regression with a same-engine before/after report diff, and re-run the gold ledger so the ≥500-case / ≥90%-recall floor still holds after pruning rule families and regenerating it.

## architecture-design plugin migration

`architecture-design` moved from `souroldgeezer-design` to `souroldgeezer-architecture`; users who installed `souroldgeezer-design` for architecture work must install `souroldgeezer-architecture@souroldgeezer`. Canonical handoff is the dediren package directory `docs/architecture/<feature>.dediren/`.
