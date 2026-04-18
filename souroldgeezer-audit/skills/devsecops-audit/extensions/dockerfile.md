# Extension — Dockerfile and docker-compose

**Applies to:** `**/Dockerfile`, `**/Dockerfile.*`, `**/docker-compose*.yml`, `**/docker-compose*.yaml`.

**Detection signals:**

- File name matches `Dockerfile` (exact) or `Dockerfile.*` (e.g. `Dockerfile.test`).
- File name matches `docker-compose*.y?ml` (including `docker-compose.test.yml`, `docker-compose.override.yml`).

**Applies to rubric sections:** §4 (CICD-SEC-3, -9), §5.1 items 8, 13, 19, §5.3 item 1.

**Note:** the lfm repo uses Azure Functions Flex Consumption for production (no production Dockerfile), but `docker-compose.test.yml` pulls images for the E2E test stack. Those pulls are subject to the same pin-by-digest smell as production images.

## Smell codes

### `docker.HC-1` — `USER root` or no `USER` directive

**Pattern:** a Dockerfile that explicitly sets `USER root` (or an equivalent UID of 0) or that has no `USER` directive at all.

**Detection (ripgrep):**
```
USER\s+(root|0)\s*$
```
Plus: any Dockerfile with zero `USER` lines.

**Severity:** `block`

**Rubric:** devsecops.md §5.1.13; OWASP Docker Security Cheat Sheet.

**Remediation action:**
> Declare a non-root `USER` explicitly. Prefer the numeric `UID:GID` form (`USER 10001:10001`) — a named-only `USER app` silently falls back to the root group if no primary group is set. Create a dedicated user in the Dockerfile: `RUN adduser --system --uid 10001 --gid 10001 app` then `USER 10001:10001`. For language base images, many already ship a `nonroot` user or numeric UID; prefer those. See https://docs.docker.com/reference/dockerfile/#user.

### `docker.HC-2` — `FROM image:tag` without `@sha256:` digest

**Pattern:** any `FROM` line whose reference is `image:tag` or `image:tag@sha256:` but the sha256 portion is missing.

**Detection (two-pass, default ripgrep — avoids lookbehind):**

1. Enumerate every `FROM` line: `rg -nE '^FROM\s+\S+' **/Dockerfile* **/Dockerfile`
2. For each match, check whether the image reference contains `@sha256:[a-f0-9]{64}`. Any reference without a digest → `docker.HC-2` finding. All references digest-pinned across the file → `docker.POS-1` positive.

**Compose variant (portable regex — `\n` in character classes is grep-dialect dependent, so use `[:space:]`):**

- Unpinned: `rg -nE '^\s*image:\s*[^@[:space:]]+:[^@[:space:]]+$' docker-compose*.y?ml`
- Pinned: `rg -nE '^\s*image:\s*[^[:space:]]+@sha256:[a-f0-9]{64}\b' docker-compose*.y?ml`

(If the caller insists on a single-pass regex, `rg --pcre2 '^FROM\s+[^\s]+(?<!@sha256:[a-f0-9]{64})\s*($|AS)'` works with PCRE2.)

**Severity:** `block` (third-party registry) / `warn` (organization-internal registry with signed tags, or Microsoft-owned `mcr.microsoft.com` registries per carve-out)

**Rubric:** devsecops.md §5.1.8; CICD-SEC-3; CICD-SEC-9.

**Remediation action:**
> Pin by digest: `FROM python:3.12-slim@sha256:<digest>`. Use `docker pull` + `docker image inspect` to capture the current digest. Update via Dependabot or Renovate with digest-pinning enabled.

**Compose variant:** the same rule applies to `image:` keys in `docker-compose*.yml`. Example:
```yaml
services:
  cosmos:
    image: mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest  # SMELL
```
Must become:
```yaml
    image: mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator@sha256:<digest>
```

### `docker.HC-3` — Build args containing secret material

**Pattern:** `ARG` declarations whose name matches `(password|secret|token|key|credential)` (case-insensitive), used via `--build-arg` at build time. Build args are baked into layer metadata and visible via `docker history`.

**Detection (ripgrep):**
```
ARG\s+[A-Z_]*(?:PASSWORD|SECRET|TOKEN|KEY|CREDENTIAL)[A-Z_]*
```

**Severity:** `block`

**Rubric:** devsecops.md §5.1.1; CICD-SEC-6.

**Remediation action:**
> Remove the secret-shaped ARG. Inject the secret via BuildKit `--mount=type=secret` (never baked into a layer) or at runtime via environment variables from a vault.

### `docker.HC-4` — Writable root filesystem in compose

**Pattern:** a service in `docker-compose*.yml` without `read_only: true`, especially for services that don't need to write to the root filesystem (cosmos emulator, azurite, functions host).

**Detection:** parse `services:` in each compose file and list services lacking `read_only: true`.

**Severity:** `warn`

**Rubric:** devsecops.md §5.2.5 (K8s analog); OWASP Docker Security Cheat Sheet.

**Remediation action:**
> Add `read_only: true` to each service. Mount any writable paths (temp dirs, data dirs) as explicit `tmpfs:` or named volumes.

### `docker.HC-5` — Privileged container

**Pattern:** `privileged: true` in a compose service or a `docker run --privileged` in any script committed to the repo.

**Detection (ripgrep):**
```
privileged\s*:\s*true
--privileged
```

**Severity:** `block`

**Rubric:** OWASP Docker Security Cheat Sheet; §5.2.5.

**Remediation action:**
> Remove `privileged: true`. If the container genuinely needs a capability (e.g. `NET_ADMIN`), use `cap_add:` with only that specific capability.

### `docker.HC-6` — `ADD` used instead of `COPY`, or `ADD` with a URL

**Pattern:** an `ADD` directive in a Dockerfile. `ADD <url>` is the harder smell (no authentication, auto-extraction of tarballs can be surprising, no digest verification); plain `ADD <src> <dst>` should be `COPY` unless tar-auto-extraction is explicitly wanted. See https://docs.docker.com/reference/dockerfile/#add.

**Detection (ripgrep):**
```
^ADD\s+https?://
^ADD\s+
```

**Severity:** `block` (URL form) / `warn` (plain form)

**Rubric:** OWASP Docker Security Cheat Sheet; Docker reference.

**Remediation action:**
> Replace `ADD` with `COPY` for local files. For remote downloads, use `RUN curl -fsSL <url> -o <path> && echo '<sha256>  <path>' | sha256sum -c -` (or `RUN --mount=type=secret` if the URL needs auth) so the fetch is explicit and digest-verified.

### `docker.HC-7` — `no-new-privileges` not set on compose services

**Pattern:** a service in `docker-compose*.yml` missing `security_opt: ["no-new-privileges:true"]`. This flag prevents setuid / file-capability escalation after process launch and is OWASP-recommended for all containers. See https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html.

**Detection:** parse `services:` and list those without `security_opt` containing `no-new-privileges:true`.

**Severity:** `warn`

**Remediation action:**
> Add `security_opt: ["no-new-privileges:true"]` to every service.

### `docker.HC-8` — Kernel capabilities not dropped

**Pattern:** a service without `cap_drop: [ALL]` (and optionally a narrow `cap_add:` listing only what is truly required). Default Docker capabilities include `NET_RAW`, `SETUID`, `SETGID`, and others that most application containers do not need.

**Detection:** parse `services:` and list those without `cap_drop:` containing `ALL` (or `- ALL`).

**Severity:** `warn`

**Rubric:** OWASP Docker Security Cheat Sheet.

**Remediation action:**
> Set `cap_drop: [ALL]`. Add a minimal `cap_add:` only for capabilities the service genuinely needs (e.g. `NET_BIND_SERVICE` to bind < 1024 as non-root).

### `docker.HC-9` — No resource limits (DoS surface)

**Pattern:** a service in compose without `mem_limit`, `cpus`, or `pids_limit`. A compromised or buggy container without limits can exhaust host resources and take down co-tenants. OWASP frames this as a DoS-mitigation control.

**Detection:** parse `services:` and list those without `deploy.resources.limits` (swarm form) or `mem_limit` / `cpus` / `pids_limit` (classic form).

**Severity:** `warn`

**Remediation action:**
> Add `mem_limit: 512m`, `cpus: '1.0'`, `pids_limit: 200` (or whatever fits the service). Tune from actual usage; these are upper bounds, not targets.

### `docker.HC-10` — Missing or permissive `.dockerignore`

**Pattern:** a repo with a `Dockerfile` and either no `.dockerignore` file or a `.dockerignore` that does not exclude at least `.git/`, `.env*`, `*.pem`, `id_rsa*`. Without these exclusions, `COPY . .` bakes git history, local env files, and SSH keys into image layers. See https://docs.docker.com/build/building/best-practices/#exclude-with-dockerignore.

**Detection:** check for `.dockerignore` existence; if present, verify the excluded-pattern list.

**Severity:** `block` (when `.dockerignore` is missing on a repo with secret-adjacent files present) / `warn` (when present but missing core exclusions).

**Remediation action:**
> Create `.dockerignore` and add at minimum: `.git/`, `.env`, `.env.*`, `*.pem`, `id_rsa*`, `node_modules/` (when appropriate), `**/secrets.*`.

### `docker.HC-11` — No PID 1 / signal handling strategy

**Pattern:** a Dockerfile with an `ENTRYPOINT` that uses shell form (`ENTRYPOINT /app/run.sh`) rather than exec form (`ENTRYPOINT ["/app/run.sh"]`), and no `tini` / `dumb-init` wrapper, and no `STOPSIGNAL`. The shell form wraps the app under `/bin/sh -c`, which does not forward SIGTERM — container-stop becomes container-kill after the 10 s grace period, and subprocesses leak.

**Detection (ripgrep):**
```
^ENTRYPOINT\s+[^[]
```
(Matches shell form; exec form starts with `[`.) Also flag Dockerfiles with no `STOPSIGNAL` in long-lived services.

**Severity:** `warn`

**Remediation action:**
> Use exec form: `ENTRYPOINT ["/app/run.sh"]`. For apps that don't reap zombies (e.g. some Node / Python entrypoints), wrap with `tini` / `dumb-init` as PID 1. Set `STOPSIGNAL SIGTERM` (or the signal your app handles).

## Positive signals

### `docker.POS-1` — All `FROM` references pinned to `@sha256:`

**Pattern:** every `FROM` line and every compose `image:` key uses a `@sha256:<64-hex>` suffix.

### `docker.POS-2` — Non-root `USER` declared

**Pattern:** every Dockerfile ends with a `USER` directive whose value is not `root` or `0`.

### `docker.POS-3` — Multi-stage build used

**Pattern:** a Dockerfile with ≥ 2 `FROM` stages, where the final stage does not copy the build toolchain (compiler, package-manager cache, test tooling) into the runtime image. Reduces runtime attack surface. See https://docs.docker.com/build/building/best-practices/#use-multi-stage-builds.

### `docker.POS-4` — `COPY --chown` (or `--chmod`) used

**Pattern:** `COPY --chown=<user>:<group>` instead of a separate `RUN chown` layer. Avoids a layer-sized permissions change and pairs cleanly with a non-root `USER`.

### `docker.POS-5` — Build provenance and SBOM attestations emitted

**Pattern:** a CI workflow invokes `docker buildx build` with `--provenance=mode=max` and `--sbom=true` (or equivalent), and the resulting attestations are pushed alongside the image. See https://docs.docker.com/build/metadata/attestations/.

## Carve-outs

- **Do not flag `docker.HC-2` on test-only compose files that pull from Microsoft-owned registries** (`mcr.microsoft.com`) as `block`; downgrade to `warn` **only when all three conditions hold**: (a) the reference is `mcr.microsoft.com/*`, (b) the file is a test/dev compose (`docker-compose.test.yml`, `docker-compose.override.yml`, or similar — not the production compose), and (c) an in-file comment documents the signed-tag rationale. Microsoft's registry ships signed tags, but neither Docker's docs nor OWASP grant MCR a blanket exemption — require the comment so the decision is auditable.
