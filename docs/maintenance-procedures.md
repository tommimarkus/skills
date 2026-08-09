# Repo maintenance procedures

Rare-occasion repo maintenance procedures relocated from CLAUDE.md; each section is loaded on demand via the pointer at its original site.

## Dediren upstream compatibility

The architecture plugin does not bundle or download Dediren. Each host adapter
prefers an explicit `DEDIREN_COMMAND`, then the current host-managed `dediren`
from `PATH`. As a migration fallback only, the launcher selects the newest
executable already present under the former verified release cache; it never
downloads or pins one there. Updating Dediren remains a host operation, not a
plugin release procedure.

After a host upgrade, run the live runtime suite and the three-harness smoke with
that executable:

```bash
DEDIREN_RUNTIME_SMOKE=1 uv run python -m unittest tests.architecture_dediren_release_test
DEDIREN_COMMAND=/absolute/path/to/dediren \
  scripts/check-runtime-host-smoke.py --fresh --assert-profile-isolation .
```

The version in repo fixtures is a compatibility evidence baseline, not a
runtime selector. Update it only when the fixture contract itself must move.
The router bounds startup and catalog waits at 120 seconds and tool-call waits
at 360 seconds by default; controlled hosts may set positive
`DEDIREN_MCP_STARTUP_TIMEOUT_SEC` and `DEDIREN_MCP_REQUEST_TIMEOUT_SEC` values.
The minimum supported rendering behavior remains Dediren 2026.07.28; lowering
that floor is a support decision because older SVG output may lack accessible
names. The adapter discovers the live tool catalog, so additive upstream tools
do not require a plugin change. A changed schema, protocol, or result contract
does: update the router, workflow guidance, and live tests together, then run
the in-depth `ip-hygiene` gate. Never patch a host installation from this repo;
report Dediren defects upstream.

## Removing a runtime's or tool's support

Scope the cut to the marketplace's **own** surfaces — per-runtime manifests/wrappers/metadata, runtime-parity tooling and finding fields, install docs, and version-cell sets. Do **not** scrub (a) general agent-guidance conventions a downstream *target* repo uses (e.g. `AGENTS.md` in the policy / `ip-hygiene` skills); (b) optional external-plugin handoffs; (c) vendor-named security/detection patterns (e.g. an `openai-key` secret regex). Confirm no regression with a same-engine before/after report diff, and re-run the gold ledger so the ≥500-case / ≥90%-recall floor still holds after pruning rule families and regenerating it.

## architecture-design plugin migration

`architecture-design` moved from `souroldgeezer-design` to `souroldgeezer-architecture`; users who installed `souroldgeezer-design` for architecture work must install `souroldgeezer-architecture@souroldgeezer`. Canonical handoff is the dediren package directory `docs/architecture/<feature>.dediren/`.
