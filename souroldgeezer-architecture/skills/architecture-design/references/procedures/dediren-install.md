# Dediren Installation

Read this when the MCP server or CLI fallback reports that Dediren is missing,
or when preparing a host to run this skill for the first time. This plugin never
bundles, downloads, pins, downgrades, or patches Dediren — the runtime is
host-managed, so installing and updating it is an operator action. The adapter
contract itself (resolution order, routing, timeouts) stays in
[self-check](self-check.md) § Server availability; this file only covers getting
a runnable executable onto the host.

## Prerequisite: a Java runtime

The bundle ships launch scripts and jars with **no bundled JRE**, so the host
needs **Java™ 21 or newer** reachable as `java`:

```bash
java -version
```

Any JDK 21+ distribution works; pick whatever your platform already manages
(distribution package, a vendor build, or a version manager). Install it before
the bundle — a present-but-too-old `java` is the most common cause of a Dediren
launcher that exits without a useful message.

## Install the bundle

Releases publish one platform-neutral archive, a `SHA256SUMS` file, and
CycloneDX SBOMs, all covered by GitHub™ artifact attestations.

Download the archive and its checksums with any HTTP client — `curl` below, but
a browser download works the same:

```bash
VERSION=2026.08.2   # or newer; see https://github.com/tommimarkus/dediren/releases
BASE="https://github.com/tommimarkus/dediren/releases/download/v${VERSION}"

curl -fLO "${BASE}/dediren-agent-bundle-${VERSION}.tar.xz"
curl -fLO "${BASE}/SHA256SUMS"
```

Verify before unpacking. The checksum check needs no extra tooling and is the
baseline (use `shasum -a 256 -c` where `sha256sum` is unavailable; the
`--ignore-missing` flag skips the release's other assets):

```bash
sha256sum --check --ignore-missing SHA256SUMS
```

That proves the download is intact, not that it is genuine — `SHA256SUMS`
travels the same channel as the archive. Where provenance matters, add the
attestation check on top. It is strictly stronger but needs more: the GitHub™
CLI installed **and** authenticated, plus API reachability, none of which the
rest of this procedure requires:

```bash
gh attestation verify "dediren-agent-bundle-${VERSION}.tar.xz" \
  --repo tommimarkus/dediren
```

Skip it on an air-gapped or otherwise locked-down host; the checksum check
still stands on its own there.

Then unpack somewhere stable and durable — not a temporary directory, because
the host relaunches the server from this path on every session:

```bash
mkdir -p ~/.local/lib
tar -xf "dediren-agent-bundle-${VERSION}.tar.xz" -C ~/.local/lib
```

That yields the launcher at
`~/.local/lib/dediren-agent-bundle-${VERSION}/bin/dediren`, alongside the
bundle's `lib/`, `schemas/`, `fixtures/`, licence, and third-party notices.

## Make it resolvable by the host

The launcher resolves Dediren in a fixed order: `DEDIREN_COMMAND` first, then
`dediren` on `PATH`, then — for hosts migrating from a pre-2026.08 plugin
version — the newest executable **already present** in the former verified
release cache (`${XDG_CACHE_HOME:-$HOME/.cache}/dediren/releases/`). That last
lane is migration-only: it is never populated, so it will not pick up the bundle
you just unpacked. Use one of the first two.

**Either** put it on `PATH`:

```bash
ln -sfn "$HOME/.local/lib/dediren-agent-bundle-${VERSION}/bin/dediren" \
  ~/.local/bin/dediren
```

**or** set `DEDIREN_COMMAND` to the absolute launcher path in the host's own MCP
server environment.

Prefer `DEDIREN_COMMAND` when the host is not started from your interactive
shell. The MCP launcher runs as a **host process**, so `PATH` entries exported
only from an interactive shell profile may never reach it — `dediren` works in
your terminal while the plugin still reports it missing. `DEDIREN_COMMAND` with
an absolute path removes that ambiguity, and is also the right lane when you
deliberately pin one executable for controlled validation.

Restart the host (or refresh the plugin) after either change so the MCP server
relaunches with the new environment.

## Confirm

```bash
dediren --version          # or: "$DEDIREN_COMMAND" --version
```

The reported version must be **2026.07.28 or newer**. That is this skill's
rendering-behaviour compatibility floor, not a pin — newer releases are expected
and supported. Anything older fails the self-check before a render claim.

## Optional: offline and proxied export validation

`curl` is needed on `PATH` only when export validation must fetch a standards
schema. For offline hosts, supply the schemas locally through
`DEDIREN_OEF_SCHEMA_DIR` / `DEDIREN_XMI_SCHEMA_PATH`; behind a proxy, the usual
`HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` variables are forwarded.

## Update and removal

Updating is a host operation with no plugin involvement: install the newer
bundle the same way, re-point the symlink or `DEDIREN_COMMAND` at it, restart
the host, and re-confirm the version. Remove an installation by deleting the
unpacked bundle directory and whichever pointer you created. A stale bundle left
in the legacy release cache keeps satisfying the migration lane, so remove that
too if you want a clean state.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `dediren-mcp: install the current Dediren CLI on PATH or set DEDIREN_COMMAND.` (exit 127) | No executable found in any of the three lanes | Complete the install above, then make it resolvable by the host process |
| `dediren-mcp: DEDIREN_COMMAND was not found on PATH: …` (exit 127) | `DEDIREN_COMMAND` is a bare name the host process cannot resolve | Use an absolute path to the bundle's `bin/dediren` |
| `dediren-mcp: DEDIREN_COMMAND is not executable: …` (exit 127) | Path is wrong, or the extracted file lost its executable bit | Check the path; re-extract, or `chmod +x` the launcher |
| Works in your terminal, missing from the plugin | Host process does not inherit your interactive shell `PATH` | Set `DEDIREN_COMMAND` in the host's MCP environment and restart |
| Launcher starts, then fails without a Dediren envelope | Missing or pre-21 `java` | Install a JDK 21+ and confirm the host process sees it |
| Version below the floor | An older bundle is still first in the resolution order | Point `DEDIREN_COMMAND` at the newer bundle, or clear the stale `PATH` entry / legacy cache copy |
