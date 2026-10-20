# Extension — JavaScript/TypeScript Security

**Applies to:** JavaScript, TypeScript, React, Node.js, and Vite code or
configuration that receives data across a trust boundary. This is a security
lens, not a general frontend, API, or test-design review.

**Evidence rule:** Emit a `jsts.*` finding only when a risky sink and visible trust-boundary/taint path are both present. Boundary evidence includes request,
route, form, message, CLI, environment supplied by a deployer, uploaded file,
database field written by a caller, or documented external producer. API names alone are not findings, and a suggestive variable name is not provenance. A
fixed repository-owned value, explicit finite allowlist, or close-to-sink
validation can be a carve-out only where it actually constrains the risky use.
For `jsts.HC-12` to `jsts.HC-16` the HTTP request or response is the trust
boundary and the sink is the access decision, emitted cookie,
stored password verifier, protected value, or non-public handler.

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

### `jsts.HC-12` — Self-contained token validation weakened

**Pattern:** `jsonwebtoken` `jwt.decode()` output drives an access decision instead of `jwt.verify()`; `jwt.verify` is called without an `algorithms` option where key types allow algorithm confusion, allows `none`, or sets `ignoreExpiration: true`; `jose` `decodeJwt` or `decodeProtectedHeader` is used for trust instead of `jwtVerify`, or `jwtVerify` omits issuer or audience where multiple issuers or audiences are accepted. Decoding only parses a token; it proves nothing about who issued it.

**Carve-outs:** decoding a token already verified by `jwtVerify` or `jwt.verify` to render or log its claims; test fixtures; documented gateway validation (emit an info note naming the reliance).

**Severity:** `block` when signature verification, algorithm allowlisting, or trusted-key sourcing is absent or bypassed for a token that gates access; `warn` when only lifetime, issuer, or audience checks are disabled, escalated to `block` when multiple issuers or audiences are accepted.

### `jsts.HC-13` — Sensitive cookie attributes weakened

**Pattern:** `express-session` or `cookie-session` options with `secure: false` or `httpOnly: false` in production configuration; `res.cookie`, Next.js `cookies().set`, or a raw `Set-Cookie` header carrying a session or authentication token without `httpOnly` and `secure`; or `sameSite: 'none'` without `secure`.

**Carve-outs:** development-only configuration guarded by an explicit non-production check; script-readable cookies carrying no secret, including a double-submit CSRF token (`httpOnly` only).

**Severity:** `block` when a session or authentication cookie lacks `Secure` or `HttpOnly` on a production path; `warn` for weakened `SameSite` or other sensitive cookies.

### `jsts.HC-14` — Disallowed or legacy cryptographic primitive used for a security purpose

**Pattern:** `crypto.createHash('md5')` or `'sha1'` for signatures, integrity, tokens, or key derivation; `createCipheriv` with an ECB mode, `des`, `des-ede3`, or `rc4`; the deprecated `crypto.createCipher`; a constant or reused IV or nonce; `RSA_PKCS1_PADDING` for encryption. Approved primitives are not findings.

**Carve-outs:** non-security uses (ETags, cache keys, non-adversarial checksums, isolated and documented legacy interoperability). `jsts.HC-6` stays the specific rule for randomness.

**Severity:** `block`, with a visible security purpose, for a primitive the ASVS 5.0.0 cryptography appendix disallows or does not approve — MD5, `des`, `des-ede3`, `rc4`, an ECB mode, `crypto.createCipher` (an MD5-based key derivation), `RSA_PKCS1_PADDING` encryption, or SHA-1 inside a signature or key derivation — or for a constant or reused IV or nonce; `warn` for one it keeps as legacy: SHA-1 as a plain digest, or HMAC-SHA-1.

### `jsts.HC-15` — Password verifier stored with a fast or reversible scheme

**Pattern:** a stored password verifier comes from `createHash` (salted or not), reversible encryption, or `pbkdf2` / `scrypt` with parameters below the approved minimums of the ASVS 5.0.0 cryptography appendix, instead of argon2, bcrypt, or `crypto.scrypt` with adequate parameters.

**Carve-outs:** fast hashing of high-entropy random API keys or tokens for lookup; breached-password k-anonymity SHA-1 prefixes; a client pre-hash followed by a server-side approved password hash.

**Severity:** `block`

### `jsts.HC-16` — Non-public route, Route Handler, or Server Action lacks authorization enforcement

**Pattern:** Express, Fastify, Koa, or Hono routes on non-public endpoints are registered without the project's auth middleware and are not covered by app- or router-level middleware; Next.js Route Handlers or Server Actions (`'use server'`) change state or return non-public data without an in-handler session or authorization check (middleware matcher coverage alone does not count, because Server Actions are directly invocable POST endpoints); or tRPC `publicProcedure` is used for non-public operations. Object-level ownership stays `DSO-SUB-4`.

**Carve-outs:** routes in a documented public allowlist, and health/status endpoints returning no non-public data.

**Severity:** `block` for a state-changing or non-public-data handler with no enforcement and no covering default-deny; `warn` for an explicit opt-out (`publicProcedure`, a skip-auth flag) on a route absent from a documented public allowlist.

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
### `jsts.POS-12` — Strict token validation
### `jsts.POS-13` — Hardened production cookie settings
### `jsts.POS-14` — Approved primitives plus an adaptive password KDF
### `jsts.POS-15` — Default-deny routing plus in-handler checks in every Route Handler and Server Action

## Sources and scope

This pack paraphrases current primary guidance rather than reproducing examples:
[Node child process](https://nodejs.org/api/child_process.html),
[Node crypto](https://nodejs.org/api/crypto.html),
[MDN dynamic import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/import),
[MDN HTML injection sinks](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML),
[Node TLS](https://nodejs.org/api/tls.html),
[Vite server options](https://vite.dev/config/server-options),
[OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html),
[jsonwebtoken](https://github.com/auth0/node-jsonwebtoken),
[jose jwtVerify](https://github.com/panva/jose/blob/main/docs/jwt/verify/functions/jwtVerify.md),
[express-session](https://github.com/expressjs/session),
[Express API reference](https://expressjs.com/en/api.html),
[Next.js data security](https://nextjs.org/docs/app/guides/data-security),
[Next.js authentication](https://nextjs.org/docs/app/guides/authentication), and
[OWASP ASVS 5.0.0 cryptography appendix](https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md).

Static review cannot prove sanitizer behavior, DNS/IP resolution, proxy/egress
controls, final client bundles, or listener reachability. Require the evidence
rule, state those limits, and hand frontend/API/design decisions to the owning
sibling rather than inventing certainty.
