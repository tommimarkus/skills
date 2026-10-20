# Extension — Python Security

**Applies to:** Python source (`*.py`), dependency/runtime configuration that
executes Python, and Python web handlers, jobs, CLIs, or libraries that receive
data across a trust boundary. This is a security lens, not a general Python
design or test review; delegate those concerns to the appropriate sibling.

**Evidence rule:** Emit a `pys.*` finding only when both the risky sink and a
visible trust-boundary/taint path are present. Boundary evidence includes HTTP
request/query/form/body/header/cookie data, CLI arguments, environment supplied
by a caller, queue/event payloads, uploaded files, database fields originally
written by a user, archive members, or a value documented as external. A name
such as `input`, `url`, or `command` is not evidence by itself. When provenance
cannot be established, report an `info` investigation note rather than a
security smell. Explicit validation must be close enough to the sink to show
that it constrains the value, not merely parses it.
For `pys.HC-10` to `pys.HC-14` the HTTP request or response is the trust
boundary and the sink is the access decision, emitted cookie,
stored password verifier, protected value, or non-public handler.

## Smell codes

### `pys.HC-1` — Unsafe object or YAML deserialization

**Pattern:** externally controlled bytes reach `pickle.load(s)`, `marshal.load(s)`,
`shelve.open`, `dill`, or `yaml.load` without `SafeLoader`/`safe_load`. Python
warns that pickle is not safe for untrusted data; use a data-only format or a
strictly restricted deserializer where the input format is under the project’s
control.

**Carve-outs:** a bundled, integrity-verified artifact from the same release
pipeline with a documented signature/hash verification immediately before the
load is trusted input. `yaml.safe_load` and `yaml.load(..., Loader=SafeLoader)`
are not this smell. Do not flag internal test fixtures, migrations, or a local
cache unless their producer crosses a user/external boundary.

**Severity:** `block` when boundary evidence is present.

### `pys.HC-2` — Dynamic execution of externally controlled source

**Pattern:** tainted values reach `eval`, `exec`, `compile`, `__import__`,
`importlib` dynamic loading, or a template/DSL execution API capable of running
Python. Parsing JSON, `ast.literal_eval`, or dispatch through a fixed mapping
of literal keys is not dynamic code execution.

**Carve-outs:** a fixed, repository-owned expression selected by an allowlisted
identifier is trusted only when the selected source cannot be supplied or
modified by the caller. Developer-only REPL/debug commands are non-security
only when they are not reachable in the shipped service/CLI interface.

**Severity:** `block` when boundary evidence is present.

### `pys.HC-3` — Tainted shell command

**Pattern:** external data is interpolated or concatenated into a command run
with `shell=True`, `os.system`, `os.popen`, `commands`, or an equivalent shell
wrapper. Prefer a fixed executable plus an argument sequence with `shell=False`;
the Python subprocess documentation assigns shell quoting to the application.

**Carve-outs:** a constant command with no caller-controlled fragments is not a
finding. A fixed executable and argument list is not this smell if every
externally selected argument is validated against a strict finite allowlist or
a type/range that excludes shell syntax, and no shell is invoked. `shlex.quote`
alone does not establish a general safety claim for a complex shell program.

**Severity:** `block` when boundary evidence is present.

### `pys.HC-4` — Path traversal or unsafe archive extraction

**Pattern:** external path/archive-member input controls a file read, write,
delete, or extraction destination without a visible containment check; or an
untrusted tar/zip archive is extracted wholesale without member validation.
For tar files, use an explicit restrictive extraction filter such as `data`
where supported and still bound size/count; Python warns archive extraction may
escape the destination and has residual risks.

**Carve-outs:** a path resolved against a fixed base and checked to remain below
that base after resolution is safe for this rule; reject absolute paths and
symlink escapes. A signed, release-owned archive with documented verification
is trusted input, but resource limits remain an availability concern. Do not
flag a static repository path or archive created and consumed entirely within
one closed build step.

**Severity:** `block` when boundary evidence is present.

### `pys.HC-5` — Insecure temporary file

**Pattern:** a boundary-influenced workflow uses `tempfile.mktemp`, predictable
temporary names, or opens a caller-selectable temporary path without exclusive
creation and ownership/permission controls. `mktemp` is deprecated because of
a race condition.

**Carve-outs:** `NamedTemporaryFile`, `TemporaryFile`, `mkstemp`, or a securely
created application-private directory is not this smell when the returned file
descriptor/path is used without a check-then-open race. A non-security scratch
name that never contains sensitive data and cannot be replaced/consumed by a
different principal is outside this rule.

**Severity:** `warn` when boundary or cross-principal evidence is present.

### `pys.HC-6` — Predictable randomness for a security value

**Pattern:** `random`, `random.Random`, NumPy pseudo-random output, timestamps,
or counters produce a token, reset code, session identifier, CSRF value, nonce,
credential, invitation, or authorization capability. Use `secrets` or OS CSPRNG
APIs; Python explicitly distinguishes `random` from security use.

**Carve-outs:** simulations, tests, sampling, UI layout, backoff jitter, and
non-secret identifiers are non-security uses. A value is not a capability merely
because its variable name contains `id`; emit only where its later use or API
contract makes it security-sensitive.

**Severity:** `block` when security use is visible.

### `pys.HC-7` — TLS verification disabled

**Pattern:** an external HTTPS request/client disables certificate verification
(`verify=False`, `CERT_NONE`, an unverified SSL context, or equivalent) without
a narrowly scoped, documented test-only boundary. Restore verification and use
the platform trust store or a pinned/private CA bundle as the deployment requires.

**Carve-outs:** a test fixture isolated from production transport and marked as
test-only is not a finding. A custom CA bundle or hostname policy is not disabled
verification when certificate chain and hostname verification remain enabled.

**Severity:** `block` when it can reach a shipped outbound client.

### `pys.HC-8` — SQL built by interpolation

**Pattern:** external data is concatenated, formatted, or interpolated into SQL
text passed to a driver/ORM raw-query sink. Use the driver/ORM parameter binding
API; identifiers require a finite allowlist because parameters generally bind
values, not SQL syntax.

**Carve-outs:** a complete constant query is not a finding. A dynamically chosen
column/order/table is safe for this rule only if it comes from an explicit finite
allowlist mapped to literal SQL identifiers; parameterized values remain needed.
Do not flag non-SQL string formatting or migration SQL that is static and not
influenced by deployment/user input.

**Severity:** `block` when boundary evidence is present.

### `pys.HC-9` — Outbound URL trust is uncertain

**Pattern:** external input controls an outbound URL, host, redirect target, or
webhook destination and the code has no visible scheme/host/port allowlist and
no DNS/IP policy that excludes loopback, link-local, private, and cloud metadata
addresses. This is an SSRF review finding: static source usually cannot prove
the resolved address, proxy behavior, redirect policy, or network egress rules.

**Carve-outs:** a literal endpoint or an endpoint selected from a finite
repository-owned allowlist is trusted. Merely parsing a URL, checking it begins
with `https://`, or validating a user-controlled hostname is insufficient.
An internal service-discovery client is outside this smell only with a visible
authenticated service boundary and an explicit policy for its target namespace.

**Severity:** `warn` when boundary evidence is present; escalate to `block` for
access to credentials, internal administration, or a privileged callback path.

### `pys.HC-10` — Self-contained token validation weakened

**Pattern:** `jwt.decode` (PyJWT) is called with `options` that disable `verify_signature`, `verify_exp`, `verify_aud`, or `verify_iss`; is called without an explicit `algorithms` allowlist, or allows `none`; or an unverified header/claims helper (PyJWT, python-jose, Authlib) drives an access decision. Reading unverified claims only parses the token; it proves nothing about who issued it.

**Carve-outs:** decoding for display, logging, or routing hints after a verified decode makes the access decision; test fixtures; validation delegated to a documented gateway (emit an info note naming the reliance).

**Severity:** `block` when signature verification, algorithm allowlisting, or trusted-key sourcing is absent or bypassed for a token that gates access; `warn` when only lifetime, issuer, or audience checks are disabled, escalated to `block` when multiple issuers or audiences are accepted.

### `pys.HC-11` — Sensitive cookie attributes weakened

**Pattern:** Django `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, or `SESSION_COOKIE_HTTPONLY` set to `False` in production settings; Flask `SESSION_COOKIE_SECURE` or `SESSION_COOKIE_HTTPONLY` set to `False`, or `SESSION_COOKIE_SAMESITE = None` without `Secure`; or `set_cookie` (Django, Flask, Starlette/FastAPI) for a session or authentication value with `secure=False` or `httponly=False`.

**Carve-outs:** development-only settings modules or `DEBUG`-gated branches; script-readable cookies carrying no secret, including a double-submit CSRF token whose design requires script access (`HttpOnly` only).

**Severity:** `block` when a session or authentication cookie lacks `Secure` or `HttpOnly` on a production path; `warn` for weakened `SameSite` or other sensitive cookies.

### `pys.HC-12` — Disallowed or legacy cryptographic primitive used for a security purpose
<!-- lean-audit:sync-intentional: per-stack packs load independently (Quick audits read only one), so this family's severity split and carve-outs are deliberately restated in dns.HC-18, pys.HC-12, and jsts.HC-14; edit all three together. -->

**Pattern:** `hashlib.md5` / `hashlib.sha1` (or `hashlib.new` naming them) used for signatures, integrity, tokens, or key derivation without `usedforsecurity=False`; `cryptography` `modes.ECB` or PyCryptodome `AES.MODE_ECB`; DES, TripleDES, or ARC4; a constant or reused IV or nonce; PKCS1v15 padding for RSA encryption. Approved primitives are not findings.

**Carve-outs:** `usedforsecurity=False` and other non-security uses (ETags, cache keys, non-adversarial checksums, isolated and documented legacy interoperability). `pys.HC-6` stays the specific rule for randomness.

**Severity:** `block`, with a visible security purpose, for a primitive the ASVS 5.0.0 cryptography appendix disallows or does not approve — MD5, DES, TripleDES, ARC4, ECB mode, PKCS1v15 encryption padding, or SHA-1 inside a signature or key derivation — or for a constant or reused IV or nonce; `warn` for one it keeps as legacy: SHA-1 as a plain digest, or HMAC-SHA-1.

### `pys.HC-13` — Password verifier stored with a fast or reversible scheme
<!-- lean-audit:sync-intentional: per-stack packs load independently (Quick audits read only one), so this family's pattern and carve-outs are deliberately restated in dns.HC-19, pys.HC-13, and jsts.HC-15; edit all three together. -->

**Pattern:** a stored password verifier comes from `hashlib.sha*` or `hashlib.md5` (salted or not), reversible encryption, or `hashlib.pbkdf2_hmac` / `hashlib.scrypt` with parameters below the approved minimums of the ASVS 5.0.0 cryptography appendix; or Django `PASSWORD_HASHERS` lists an MD5, SHA-1, or unsalted hasher first.

**Carve-outs:** fast hashing of high-entropy random API keys or tokens for lookup; breached-password k-anonymity SHA-1 prefixes; a client pre-hash followed by a server-side approved password hash.

**Severity:** `block`

### `pys.HC-14` — Non-public route lacks authentication/authorization enforcement

**Pattern:** a Django view without `login_required`, `LoginRequiredMixin`, or `permission_required`; a DRF view with `permission_classes` set to `AllowAny` or empty; a Flask view without the project's login decorator; or a FastAPI route without the project's auth dependency, when the handler changes state or returns non-public data and no global default-deny (DRF `DEFAULT_PERMISSION_CLASSES`, Django `LoginRequiredMiddleware`, FastAPI app or router dependencies) covers it. Object-level ownership stays `DSO-SUB-4`.

**Carve-outs:** routes in a documented public allowlist (`SECURITY.md`, route documentation, or an explicit login-exempt marker), and health/status endpoints returning no non-public data.

**Severity:** `block` for a state-changing or non-public-data handler with no enforcement and no covering default-deny; `warn` for an explicit opt-out (`AllowAny`, a login-exempt decorator) on a route absent from a documented public allowlist.

## Positive signals

`pys.POS-1`: data-only deserialization with a restrictive loader and verified
producer boundary. `pys.POS-2`: fixed subprocess argument vectors with no shell.
`pys.POS-3`: resolved-path/archive member containment plus resource limits.
`pys.POS-4`: `secrets`/CSPRNG for capability values. `pys.POS-5`: verified TLS,
bound SQL parameters, or an outbound destination allowlist with redirect/DNS-IP
policy appropriate to the deployment.
`pys.POS-6`: strict token validation with explicit algorithms, issuer, audience, and
lifetime checks. `pys.POS-7`: hardened production cookie settings (`Secure`,
`HttpOnly`, explicit `SameSite`). `pys.POS-8`: approved primitives plus an
adaptive password KDF. `pys.POS-9`: global default-deny route authorization with
documented public exceptions.

## Sources and scope

This pack paraphrases current primary guidance rather than reproducing examples:
[Python security considerations](https://docs.python.org/3/library/security_warnings.html),
[pickle](https://docs.python.org/3/library/pickle.html),
[subprocess security](https://docs.python.org/3/library/subprocess.html#security-considerations),
[tarfile extraction filters](https://docs.python.org/3/library/tarfile.html#extraction-filters),
[Python secrets](https://docs.python.org/3/library/secrets.html),
[Requests SSL verification](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification),
[SQLAlchemy bound parameters](https://docs.sqlalchemy.org/en/20/core/sqlelement.html),
[OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html),
[PyJWT API](https://pyjwt.readthedocs.io/en/stable/api.html),
[Django settings](https://docs.djangoproject.com/en/stable/ref/settings/),
[Django password management](https://docs.djangoproject.com/en/stable/topics/auth/passwords/),
[Django middleware](https://docs.djangoproject.com/en/stable/ref/middleware/),
[Flask web security](https://flask.palletsprojects.com/en/stable/web-security/),
[Python hashlib](https://docs.python.org/3/library/hashlib.html),
[cryptography symmetric encryption](https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/),
[FastAPI security](https://fastapi.tiangolo.com/tutorial/security/),
[Django REST framework permissions](https://www.django-rest-framework.org/api-guide/permissions/), and
[OWASP ASVS 5.0.0 cryptography appendix](https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x92-Appendix-C_Cryptography.md).

Static review cannot prove runtime network containment, archive resource limits,
or a value’s original producer. Require the evidence rule above, report those
limits, and hand runtime/architecture decisions to the relevant sibling rather
than inventing certainty.
