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

## Positive signals

`pys.POS-1`: data-only deserialization with a restrictive loader and verified
producer boundary. `pys.POS-2`: fixed subprocess argument vectors with no shell.
`pys.POS-3`: resolved-path/archive member containment plus resource limits.
`pys.POS-4`: `secrets`/CSPRNG for capability values. `pys.POS-5`: verified TLS,
bound SQL parameters, or an outbound destination allowlist with redirect/DNS-IP
policy appropriate to the deployment.

## Sources and scope

This pack paraphrases current primary guidance rather than reproducing examples:
[Python security considerations](https://docs.python.org/3/library/security_warnings.html),
[pickle](https://docs.python.org/3/library/pickle.html),
[subprocess security](https://docs.python.org/3/library/subprocess.html#security-considerations),
[tarfile extraction filters](https://docs.python.org/3/library/tarfile.html#extraction-filters),
[Python secrets](https://docs.python.org/3/library/secrets.html),
[Requests SSL verification](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification),
[SQLAlchemy bound parameters](https://docs.sqlalchemy.org/en/20/core/sqlelement.html), and
[OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).

Static review cannot prove runtime network containment, archive resource limits,
or a value’s original producer. Require the evidence rule above, report those
limits, and hand runtime/architecture decisions to the relevant sibling rather
than inventing certainty.
