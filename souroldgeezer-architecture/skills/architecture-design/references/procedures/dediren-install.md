# Dediren Runtime

Read this when the MCP server or CLI fallback reports that Dediren is missing or
unusable, when the installed release must be steered, or when preparing an
air-gapped host. Dediren installs itself: on first use the plugin's launcher
provisions a pinned, checksum-verified release into the host's own per-plugin
writable data directory, on Linux, macOS, and WSL. There is no operator install
step in the normal case. This file owns that runtime lifecycle — what
provisioning does, how to override it, how to run without a network, and how to
read a failure. The adapter contract around it (routing, timeouts, availability
disclosure) stays in [self-check](self-check.md) § Server availability.

Commands below are written with `${CLAUDE_PLUGIN_ROOT}`, which Claude Code
expands in `SKILL.md`; this file is read raw, so carry the already-resolved value
into them. In Codex, use the absolute `<skill-dir>` reported for the loaded skill
and drop the `skills/architecture-design/` segment.

## Prerequisite: a Java runtime

The bundle ships launch scripts and jars with **no bundled JRE**, so the plugin
never downloads Java. The host needs **Java™ 21 or newer** reachable as `java`
(or through `JAVA_HOME` / `JAVACMD`, or an sdkman current candidate):

```bash
java -version
```

Any JDK 21+ distribution works; pick whatever your platform already manages
(distribution package, a vendor build, or a version manager). The launcher checks
this **before** downloading anything and again before exec, and names the exact
cause — no runtime found, an unreadable version, or a too-old major — so a
pre-21 `java` reports itself instead of killing the launcher without a message.

## What the first run does

Provisioning runs once per host, on the first `tools/list`, and installs the
pinned release **2026.08.3**. The supported floor is **2026.07.28**: from that
release the render lane takes each view's accessible name from its own
`presentation`, which the skill's post-render step requires.

1. Resolve the data directory (below) and take a bounded cross-session lock, so
   concurrent sessions cannot half-install over each other.
2. Fetch `SHA256SUMS` from the release first and read the archive's name out of
   it — the compression format comes from the release, never an assumption here.
3. Fetch that archive and verify its SHA-256 **before** unpacking.
4. Unpack through explicit member sanitisation: absolute paths, `..` traversals,
   links that resolve outside the destination, devices, and fifos are all
   refused, so a tampered archive fails loudly instead of writing outside the
   directory.
5. Install atomically — the verified bundle replaces the target directory in one
   move, leaving no partially-extracted state behind.

The install lands at
`<data-dir>/releases/dediren-agent-bundle-<version>/bin/dediren`, beside the
bundle's `lib/`, `schemas/`, `fixtures/`, licence, and third-party notices.

### Where it installs

The data directory is the host's own per-plugin writable location, resolved in
order:

| Variable | Result |
|---|---|
| `DEDIREN_HOME` | used as given; **must be absolute** |
| `CLAUDE_PLUGIN_DATA` | `<value>/dediren` |
| `COPILOT_PLUGIN_DATA` | `<value>/dediren` |
| `PLUGIN_DATA` | `<value>/dediren` |

Each host manifest also sets `DEDIREN_HOME` explicitly from its own substitution
token, so the path is visible in the manifest rather than inferred. There is
deliberately **no invented fallback**: a guessed location is worse than none,
because the MCP launcher runs as a host process with the real `HOME` while the
same scripts run from an agent's shell tool may be sandboxed, and a guess can
strand the bundle where the launcher never looks. Offered none of the four, the
launcher exits 78 naming `DEDIREN_HOME`.

## Which runtime gets used

Resolution order, first match wins:

1. **`DEDIREN_COMMAND`** — an explicit executable, honoured without a floor
   probe. This is the deliberate lane for pinning one build for controlled
   validation; it is also the only lane that can select a runtime below the
   floor, so keep it current.
2. **The managed install** in the data directory, at the pinned version.
3. **A host `dediren` on `PATH`** that reports **at or above the floor**. An
   older one does not shadow the pin — below-floor renders would fail the
   skill's own post-render step rather than failing here.
4. **The legacy release cache** (`${XDG_CACHE_HOME:-$HOME/.cache}/dediren/releases/`),
   migration only: nothing populates it any more, and it exists so a host
   provisioned by a pre-2026.08 plugin version is not stranded.
5. **Provisioning** the pin, as above.

Only lanes 2 and 5 need a data directory, so a host that offers none still
resolves through the others.

## Overrides

| Variable | Effect |
|---|---|
| `DEDIREN_HOME` | absolute install location, ahead of every plugin-data variable |
| `DEDIREN_VERSION` | install a different release; must be CalVer (`YYYY.0M.MICRO`) and at or above the floor |
| `DEDIREN_COMMAND` | skip provisioning entirely and run this executable |
| `DEDIREN_AUTO_INSTALL=0` | never provision; fail with guidance instead |
| `DEDIREN_REPO` | source repository for the release assets, for a mirror |

Set them in the host's own MCP server environment, not an interactive shell
profile: the launcher runs as a **host process**, so shell-exported values may
never reach it. Restart the host (or refresh the plugin) after a change.

## Air-gapped hosts

Set `DEDIREN_AUTO_INSTALL=0` to disable provisioning. The launcher then resolves
only what is already present and fails with guidance instead of reaching the
network. Supply the runtime by either lane:

- unpack a release bundle into
  `<data-dir>/releases/dediren-agent-bundle-<version>/` so lane 2 finds it, or
- point `DEDIREN_COMMAND` at an executable the host already manages.

Releases publish one platform-neutral archive, a `SHA256SUMS` file, and CycloneDX
SBOMs, all covered by GitHub™ artifact attestations. When you carry a bundle in
by hand, verify it the way provisioning does — `sha256sum --check
--ignore-missing SHA256SUMS` (or `shasum -a 256 -c`) — and add
`gh attestation verify "${ARCHIVE}" --repo tommimarkus/dediren` where provenance
matters and the GitHub™ CLI is installed, authenticated, and able to reach the
API.

## Confirm

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/architecture-design/references/scripts/dediren_runtime.py --print-path    # resolve without touching the network
python3 ${CLAUDE_PLUGIN_ROOT}/skills/architecture-design/references/scripts/dediren_runtime.py --home          # the resolved data directory
python3 ${CLAUDE_PLUGIN_ROOT}/skills/architecture-design/references/scripts/dediren_runtime.py --version-pin   # pin and floor
python3 ${CLAUDE_PLUGIN_ROOT}/skills/architecture-design/references/scripts/dediren_runtime.py --ensure        # provision if needed, then print the path
```

`--print-path` is the safe read-only check; only `--ensure` can download. Then
confirm the executable itself:

```bash
dediren --version          # or: "$DEDIREN_COMMAND" --version
```

The reported version must be **2026.07.28 or newer**.

## Optional: offline and proxied export validation

`curl` is needed on `PATH` only when export validation must fetch a standards
schema — and as a download fallback when the host's Python has no usable TLS
trust store. For offline hosts, supply the schemas locally through
`DEDIREN_OEF_SCHEMA_DIR` / `DEDIREN_XMI_SCHEMA_PATH`; behind a proxy, the usual
`HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` variables are forwarded.

## Update and removal

The pin moves with the plugin release, so updating is normally just updating the
plugin: the launcher provisions the new pin on its next start and leaves the old
bundle in place. To move deliberately, set `DEDIREN_VERSION` and restart the
host. Remove an installation by deleting its
`<data-dir>/releases/dediren-agent-bundle-<version>/` directory; a stale bundle
left in the legacy release cache keeps satisfying that migration lane, so remove
it too for a clean state.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `dediren-mcp: no plugin data directory was offered by the host and no runtime was found.` (exit 78) | The host exposes none of `DEDIREN_HOME`, `CLAUDE_PLUGIN_DATA`, `COPILOT_PLUGIN_DATA`, `PLUGIN_DATA` | Set `DEDIREN_HOME` to an absolute path in the host's MCP environment, or `DEDIREN_COMMAND` to an existing executable |
| `DEDIREN_HOME must be an absolute path; got: …` (exit 78) | A relative value; the check runs after `~` expansion, so `~/...` is fine | Use an absolute path |
| `DEDIREN_VERSION must be CalVer (YYYY.0M.MICRO)` / `… is older than the supported floor` (exit 78) | Override is not CalVer, or below `2026.07.28` | Use a CalVer release at or above the floor, or unset it for the pin |
| `dediren-mcp: no Java runtime found.` (exit 69) | No `java`, `JAVA_HOME`, or `JAVACMD` visible to the host process | Install a JDK 21+ and make it visible to the host process, not only your shell |
| `dediren-mcp: could not read a Java version from …` (exit 69) | The named launcher exists but does not answer `-version` | Point `JAVACMD` / `JAVA_HOME` at a working JDK 21+ |
| `dediren-mcp: Dediren needs Java 21 or newer; … reports Java N` (exit 69) | A pre-21 JDK resolves first | Install or select a JDK 21+; set `JAVA_HOME` / `JAVACMD` when several are present |
| `checksum mismatch for …` or `refusing archive member …` (exit 69) | The download is corrupt or tampered | Retry; if it persists, treat the release mirror as suspect and report it — do not unpack it by hand |
| `download failed …` / `TLS certificate verification failed …` (exit 69) | No network, a proxy that blocks the release host, or a Python build with no usable trust store | Set the proxy variables, install `curl` or `wget` for the fallback client (on macOS python.org builds, run the bundled `Install Certificates.command` once), or go air-gapped with `DEDIREN_AUTO_INSTALL=0` |
| `dediren-mcp: no Dediren runtime is installed and automatic provisioning is disabled by DEDIREN_AUTO_INSTALL.` (exit 127) | Air-gapped mode with nothing supplied | Unpack a bundle into the data directory, or set `DEDIREN_COMMAND`; unset the variable to allow provisioning |
| `dediren-mcp: no Dediren runtime is installed yet. This mode only resolves an existing one` (exit 127) | `--print-path` on a host that has not provisioned yet | Run `--ensure`, or start the server and let the first `tools/list` provision |
| `dediren-mcp: DEDIREN_COMMAND was not found on PATH: …` (exit 127) | `DEDIREN_COMMAND` is a bare name the host process cannot resolve | Use an absolute path to the bundle's `bin/dediren` |
| `dediren-mcp: DEDIREN_COMMAND is not executable: …` (exit 127) | Path is wrong, or the file lost its executable bit | Check the path; re-extract, or `chmod +x` the launcher |
| `timed out waiting for the install lock; proceeding best-effort.` (stderr, not fatal) | Another session is provisioning the same data directory | None — the re-check and atomic replace keep the lost race safe; investigate only if it repeats |
| Renders fail the accessible-name step, or behaviour looks pre-`2026.07.28` | `DEDIREN_COMMAND` points at an older bundle and is honoured without a floor probe | Point it at `2026.07.28`+ or unset it and let the pin install |
