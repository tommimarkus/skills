# Extension — JavaScript/TypeScript Security

**Applies to:** JavaScript, TypeScript, React, Node.js, and Vite code or
configuration that receives data across a trust boundary. This is a security
lens, not a general frontend, API, or test-design review.

**Evidence rule:** Emit a `jsts.*` finding only when a risky sink and visible trust-boundary/taint path are both present. Boundary evidence includes request,
route, form, message, CLI, environment supplied by a deployer, uploaded file,
database field written by a caller, or documented external producer. API names alone are not findings, and a suggestive variable name is not provenance. A
fixed repository-owned value, explicit finite allowlist, or close-to-sink
validation can be a carve-out only where it actually constrains the risky use.

## Smell codes

### `jsts.HC-1` — Dynamic execution or module loading

**Pattern:** external data reaches `eval`, `Function`, `vm`, dynamic
`import()`, `require`, or an equivalent loader capable of executing/selecting
code. Parse data or dispatch through a literal allowlisted mapping instead.

**Carve-outs:** a fixed module chosen from a repository-owned finite mapping is
not this smell when the caller cannot alter the map or path.

**Severity:** `block` with boundary evidence.

### `jsts.HC-2` — Process execution with external fragments

**Pattern:** external data reaches `child_process.exec`, `spawn` with a shell,
or a command string that is interpreted by a shell. Prefer a fixed executable,
argument vector, and strict finite validation for any caller-selected option.

**Carve-outs:** constant commands or non-shell argument vectors with a visible
strict allowlist are not this smell.

**Severity:** `block` with boundary evidence.

### `jsts.HC-3` — Untrusted HTML reaches a browser sink

**Pattern:** external content reaches `innerHTML`, `outerHTML`,
`insertAdjacentHTML`, React `dangerouslySetInnerHTML`, or a similar executable
HTML sink without a proven sanitizer/typed-safe rendering boundary.

**Carve-outs:** framework text-node rendering and a narrowly configured,
documented sanitizer immediately before the sink are not this smell.

**Severity:** `block` with boundary evidence.

### `jsts.HC-4` — Prototype-pollution path

**Pattern:** external object keys flow into deep merge, assignment, or path-set
logic without rejecting prototype-changing keys and without a safe target
shape. Restrict keys and use null-prototype data where appropriate.

**Carve-outs:** a schema that rejects `__proto__`, `constructor`, and
`prototype` before the merge, or a fixed key mapping, is not this smell.

**Severity:** `block` with boundary evidence.

### `jsts.HC-5` — Filesystem path escapes its base

**Pattern:** external path segments control file read, write, delete, upload,
or archive destination without resolution against a fixed base and a post-
resolution containment check. Reject absolute paths and symlink escapes.

**Carve-outs:** a resolved path proven to remain under a fixed base is not this
smell; static repository paths have no visible boundary.

**Severity:** `block` with boundary evidence.

### `jsts.HC-6` — Predictable randomness creates a capability

**Pattern:** `Math.random`, timestamps, counters, or non-cryptographic PRNG
output creates a session, reset token, CSRF value, credential, invitation, or
authorization capability. Use `crypto.getRandomValues` or Node `crypto`.

**Carve-outs:** simulations, layout, sampling, test data, and non-secret IDs
are non-security uses unless later behavior makes the value a capability.

**Severity:** `block` when security use is visible.

### `jsts.HC-7` — TLS verification is bypassed

**Pattern:** a shipped outbound HTTPS client disables certificate validation,
for example `rejectUnauthorized: false`, an accepting agent, or equivalent.
Use the platform trust store or a deployment-appropriate CA while retaining
hostname and chain checks.

**Carve-outs:** isolated test-only transport is not a finding; a private CA is
not a bypass when verification remains enabled.

**Severity:** `block` when the client can ship or run in production.

### `jsts.HC-8` — SQL text interpolates external data

**Pattern:** request or other external values are concatenated, formatted, or
templated into SQL text sent to a driver/ORM raw-query API. Use bound values;
choose SQL identifiers only from a finite literal allowlist.

**Carve-outs:** a constant query or an allowlisted literal identifier with
bound values is not this smell.

**Severity:** `block` with boundary evidence.

### `jsts.HC-9` — Outbound URL trust is uncertain

**Pattern:** external input selects an outbound URL, host, redirect, or webhook
without visible scheme/host/port allowlisting and DNS/IP policy excluding local,
private, link-local, and metadata destinations. This is an SSRF review finding;
static review cannot prove DNS, proxy, redirect, or egress behavior.

**Carve-outs:** a literal endpoint or repository-owned finite endpoint mapping
is trusted. Parsing a URL or checking an HTTPS prefix is insufficient.

**Severity:** `warn`; use `block` for privileged internal or credential access.

### `jsts.HC-10` — Secret is bundled into client code

**Pattern:** a credential, private key, service token, or server-only secret
from source/environment reaches browser-delivered JS, client configuration, or
a `VITE_*` value. Move it behind a server-side boundary and rotate exposed
material.

**Carve-outs:** public identifiers intentionally designed for browser exposure
are not secrets; do not infer secrecy from a variable name alone.

**Severity:** `block` with visible source-to-client-bundle evidence.

### `jsts.HC-11` — Vite dev server is externally exposed

**Pattern:** Vite development-server configuration binds a non-loopback host or
permits external host access without an explicit, documented local-network
need and suitable access boundary. Vite’s dev server is not a production
security boundary.

**Carve-outs:** loopback-only defaults, or a documented isolated development
network with explicit host policy, are not this smell. Static source cannot
prove deployed listener reachability.

**Severity:** `warn` with visible configuration and exposure evidence.

## Positive signals

### `jsts.POS-1` — Fixed code/module allowlist
### `jsts.POS-2` — Fixed executable and non-shell argument vector
### `jsts.POS-3` — Sanitized external HTML or text-node rendering
### `jsts.POS-4` — Prototype-changing keys rejected before merge
### `jsts.POS-5` — Resolved path containment under a fixed base
### `jsts.POS-6` — CSPRNG creates capability values
### `jsts.POS-7` — Verified TLS with deployment-appropriate CA
### `jsts.POS-8` — Bound SQL values and literal identifier allowlist
### `jsts.POS-9` — Controlled outbound destination plus redirect/DNS-IP policy
### `jsts.POS-10` — Server-only secrets absent from client bundle
### `jsts.POS-11` — Loopback-only or explicitly controlled Vite dev listener

## Sources and scope

This pack paraphrases current primary guidance rather than reproducing examples:
[Node child process](https://nodejs.org/api/child_process.html),
[Node crypto](https://nodejs.org/api/crypto.html),
[MDN dynamic import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/import),
[MDN HTML injection sinks](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML),
[Node TLS](https://nodejs.org/api/tls.html),
[Vite server options](https://vite.dev/config/server-options), and
[OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).

Static review cannot prove sanitizer behavior, DNS/IP resolution, proxy/egress
controls, final client bundles, or listener reachability. Require the evidence
rule, state those limits, and hand frontend/API/design decisions to the owning
sibling rather than inventing certainty.
