# API Project Assimilation

Load when existing project source, API contracts, auth, errors, observability,
data clients, storage clients, IaC, or runtime configuration are in scope.

Start from the user's outcome and the project's actual contracts. Bundled
conventions are strong defaults, not authority to redesign a compatible project.
Reuse justified local structure; a reference difference alone is not debt.
Identify concrete incompatibility, unsafe behavior, or a substantiated
maintenance consequence before recommending migration. Factual Extract records
behavior and uncertainty without unsolicited compliance judgments.

## Discovery

Inspect relevant canonical, source-readable locations before deciding; do not
require a complete project inventory for a bounded change:

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

Use “Flag or migrate when” only in Build/Review or explicit debt/compliance
Extract. Factual Extract records assets and configuration without judgment.

| Asset | Reuse when | Flag or migrate when |
|---|---|---|
| Auth module | OAuth/OIDC or Entra ID + managed identity; secret references for any secret | Function keys on public endpoints or outside the documented narrow single-caller internal exception, custom token parsing, secrets in literals |
| Error middleware | Preserves a documented, stable machine-readable project contract; problem+json is the default for a new contract | Undocumented incompatible shapes, English-string matching, or secret/stack-trace disclosure |
| Versioning | A coherent compatibility strategy appropriate to consumers, including a jointly deployed unversioned internal contract | Consumer-breaking drift or conflicting version/lifecycle promises |
| Pagination | Cursor-based opaque token with capped `limit` | Offset/skip on unbounded collections or no cap |
| Data client lifetime | Reusable clients/pools/handlers with managed/workload identity; operation-scoped SQL/session/reader/transaction/`DbContext` handles | Per-invocation pools or handlers, singleton/concurrently shared `DbContext`, account keys |
| Observability | Project-appropriate diagnostics and correlation across consequential boundaries | Missing evidence needed to diagnose actual failures or fulfill an operational requirement |
| Rate limiting | Edge-level or documented policy with `429` and `Retry-After` | Origin-only throttling without `Retry-After`, wildcard throttling |

## Conflict Handling

- Preserve compatible local contracts and explain a material departure from a
  reference default once when it changes the recommendation.
- Judge candidate debt by evidence and consequence. Existing debt is fixed only
  within the authorized scope; do not expand a routine task to satisfy a rubric.
- Stop only the affected implementation action when a concrete unsafe or
  incompatible change cannot be avoided within authority. Ask for the material
  decision or propose the smallest safe move; continue independent work.
- Read-only Review reports load-bearing or blocking debt and continues its
  remaining analysis. Missing runtime or human evidence limits the conclusion
  needing it, not unrelated source-grounded findings.

## Footer Block

Use this optional shape for a requested formal report or a real handoff
consumer. Ordinary answers summarize only material reuse, migration, and limits;
they do not need an assimilation inventory or routine debt footer.

```text
Project assimilation:
  Reused: <compatible infrastructure and evidence>
  Legacy debt: <file:line - rule - reason not migrated>
  Migrations performed: <file:line - rule fixed>
```
