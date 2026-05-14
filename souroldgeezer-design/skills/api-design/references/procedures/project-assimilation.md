# API Project Assimilation

Load when existing project source, API contracts, auth, errors, observability,
data clients, storage clients, IaC, or runtime configuration are in scope.

Direction is one-way: assimilate the project to the reference, not the reference
to the project. Reuse compliant infrastructure, flag non-compliant
infrastructure as legacy debt, and never extend a broken pattern into added
code.

## Discovery

Inspect only canonical, source-readable locations before deciding:

1. OpenAPI / contract: `swagger.json`, `openapi.yaml`, `openapi.json`,
   `*.openapi.*`, `Swashbuckle.*`, `Microsoft.OpenApi.*`, or Azure Functions
   OpenAPI packages.
2. Error shape: `application/problem+json`, `ProblemDetails`,
   `TypedResults.Problem`, `Results.Problem`, custom error DTOs, string/HTML
   error responses.
3. Versioning: `/v1/`, `/v2/`, `api-version=`, `Asp.Versioning`, or mixed
   strategy evidence.
4. Auth config: `[Authorize]`, endpoint policy metadata, OIDC/OAuth/Entra ID
   config, managed identity, function keys, Easy Auth, Next.js middleware/proxy,
   maintained JWT/session middleware.
5. Secrets: Key Vault references, committed `.env*` with secret-shaped values,
   connection strings, access keys, token/query-string patterns, and literals.
6. Observability: OpenTelemetry, Application Insights, Azure Monitor exporter,
   structured logging, `traceparent`, `Activity.Current`, AsyncLocalStorage, or
   Next.js `instrumentation.ts|js`.
7. Manifest signals: `.csproj`, `package.json`, lockfiles, `host.json`, Bicep,
   Terraform, and deployment manifests.

Loaded extensions own deeper stack-specific discovery.

## Reuse Or Replace

| Asset | Reuse when | Flag or migrate when |
|---|---|---|
| Auth module | OAuth/OIDC or Entra ID + managed identity; secret references for any secret | Function keys only on public endpoints, custom token parsing, secrets in literals |
| Error middleware | Emits `application/problem+json` with stable `type` URIs | Custom shape, English-string matching, stack traces, HTML/string errors |
| Versioning | One explicit strategy applied uniformly | Mixed strategies, implicit v1, version only in domain name |
| Pagination | Cursor-based opaque token with capped `limit` | Offset/skip on unbounded collections or no cap |
| Data client lifetime | Singleton/module/app-container lifetime with managed/workload identity where available | Per-invocation construction, account keys, duplicate clients |
| Observability | Startup-registered telemetry, structured logs, trace propagation | Console logging, ad-hoc telemetry, missing outbound propagation |
| Rate limiting | Edge-level or documented policy with `429` and `Retry-After` | Origin-only throttling without `Retry-After`, wildcard throttling |

## Conflict Handling

Classify conflicts as `legacy debt` or `would-be-added-code`.

- Added code must comply with the reference and loaded extensions.
- Legacy debt is fixed only when migration is in scope.
- If legacy debt is load-bearing for the requested change, stop and ask for
  scope.
- If not migrated, add `Legacy debt:` entries to the footer with file, line,
  violated rule, and reason it was not changed.

## Footer Block

Use this shape when assimilation applies:

```text
Project assimilation:
  Reused: <compliant infrastructure and evidence>
  Legacy debt: <file:line - rule - reason not migrated>
  Migrations performed: <file:line - rule fixed>
```
