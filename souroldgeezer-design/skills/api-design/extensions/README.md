# Extensions

Per-stack packs loaded on demand by the `api-design` skill. The core workflow in `../SKILL.md` is framework-neutral; extensions add stack-specific primitives, patterns, smells, positive signals, and carve-outs.

## Load order

1. The skill detects stack by globbing the target and inspecting manifests (`.csproj`, `package.json`, `host.json`, `local.settings.json`, IaC under `infra/`, etc.).
2. Every matching extension is loaded. **Multiple extensions compose** on the same target — an API on Azure Functions .NET that stores entities in Cosmos and blobs in Storage loads all three extensions simultaneously; a hosted Next.js API loads `nodejs.md` first and then `nextjs.md`.
3. Each extension's additions (primitives, patterns, smells, positive signals, carve-outs) are added to the active reference.
4. On conflict between a carve-out and a core rule, the carve-out wins — but only for the exact pattern described.

Extensions **never override** core rules. They may only **add** or **carve out**.

## Extensions compose

Unlike some earlier skill designs where one extension per target was the norm, `api-design` expects **multi-extension composition** as the common case. A typical production API loads:

- `azure-functions-dotnet.md` for the compute / runtime layer (HTTP trigger shape, DI in `Program.cs`, managed identity, retry attributes, problem+json emission, hosting plan).
- `nodejs.md` for a hosted or serverless Node.js runtime layer (HTTP listener or handler shape, request context, body limits, OpenTelemetry startup, reverse proxy, graceful shutdown).
- `nextjs.md` for hosted Next.js API surfaces (Route Handlers, Pages API routes, Server Actions, route segment config, instrumentation, shared cache, deployment consistency). It loads after `nodejs.md`.
- `azure-cosmosdb.md` for the primary data layer (partition-key strategy, point-read vs query shape, ETag → 412, continuation-token cursors, change-feed processor, data-plane RBAC).
- `azure-blob-storage.md` for the object-storage layer (direct-to-blob SAS for large payloads, Event-Grid-sourced triggers, range requests, optimistic concurrency, `allowSharedKeyAccess=false`).

**Smell-code namespaces are orthogonal by construction.** Each extension owns its own prefix (`afdotnet.*`, `nodejs.*`, `nextjs.*`, `cosmos.*`, `blob.*`); core gotchas in reference §6 use `SAD-G-*`. Findings from multiple extensions never collide in the review output — each finding is unambiguously attributable to one extension (or to the core).

**Patterns compose, not override.** An idempotent POST that writes to Cosmos and invoices to Blob is:

- `afdotnet.PAT-http-problem-details` + `afdotnet.PAT-idempotent-post` (the Functions-layer shape)
- `cosmos.PAT-idempotency-container` + `cosmos.PAT-etag-conditional` (the Cosmos-layer shape)
- `blob.PAT-direct-upload-sas` (the Blob-layer shape for the invoice PDF)

A hosted Next.js API route backed by a database is:

- `nodejs.PAT-hosted-server` + `nodejs.PAT-async-context` (the Node.js hosted-process shape)
- `nextjs.PAT-route-handler-problem-details` + `nextjs.PAT-instrumentation` (the Next.js framework shape)
- the matching data extension, when the datastore is one of the bundled data surfaces

Each pattern cites the reference section it implements; there is no ambiguity about which layer is responsible for which concern.

## File layout per extension

Each extension is a single markdown file in this directory. Required sections:

- **Name and detection signals** — which files / manifests / content patterns trigger the load. Detection must be unambiguous; false-positive loads pollute findings.
- **Hosting-model surface** — where the stack has genuinely distinct sub-surfaces that shape the rules (isolated worker vs legacy in-process; Cosmos provisioned vs serverless; Blob SAS-direct vs API-proxy). Rules tagged with the surface they apply to.
- **Stack-specific primitives** — APIs, attributes, configuration properties, SDK types, and bindings the core reference doesn't cover.
- **Stack-specific patterns** — templates idiomatic for the stack (namespaced `<ext>.PAT-N`). If the core §5 pattern suffices, cite it instead of duplicating.
- **Project assimilation** — stack-specific discovery that the core SKILL.md's framework-agnostic discovery delegates here. Covers: (1) stack-level configuration (hosting plan, RBAC assignments, data-plane auth mode), (2) idiomatic infrastructure to reuse vs replace, (3) mapping from reference defaults (§3) to stack idioms, (4) carve-outs for core smells the stack's primitives legitimately satisfy.
- **Smell codes** — namespaced as `<ext>.HC-N` (high-confidence), `<ext>.LC-N` (low-confidence), `<ext>.POS-N` (positive signals).
- **Carve-outs** — explicit "do not flag <core rule> when <pattern>" entries.
- **Applies to reference sections** — which parts of the core reference this extension augments (e.g., §3.5, §3.6, §5.6, §6).

## Current extensions

| File | Applies to | Notes |
|---|---|---|
| `azure-functions-dotnet.md` | Azure Functions .NET isolated worker | Isolated-worker-only surface (in-process retired 2026-11-10), `[BuiltIn]` vs `[AspNetCore]` HTTP response styles, DI in `Program.cs`, managed identity via `DefaultAzureCredential`, Flex Consumption always-ready instances, OpenTelemetry wiring, Durable Functions, Key Vault references. |
| `nodejs.md` | Node.js / TypeScript HTTP APIs, hosted or serverless | `[Hosted]` vs `[Serverless]` vs `[Adapter]` surface, `package.json` runtime / lockfile, Node `http` listener timeouts, body-size limits, AsyncLocalStorage request context, OpenTelemetry startup, resilient `fetch`, serverless handler shape, reverse proxy evidence, graceful shutdown. |
| `nextjs.md` | Hosted Next.js API surfaces | Loads after `nodejs.md`; covers `[HostedNext]`, Route Handlers, Pages API routes, Server Actions, Route Segment Config, instrumentation, shared cache / deployment ID, Server Actions encryption key, and self-hosted reverse proxy expectations. |
| `azure-cosmosdb.md` | Azure Cosmos DB (NoSQL API) | Provisioned vs Serverless capacity surface, hierarchical partition keys, point-read vs query cost, ETag / `IfMatchEtag` → 412, continuation-token pagination, change-feed processor / trigger, data-plane RBAC, `disableLocalAuth=true`, TTL + unique-key idempotency cache. |
| `azure-blob-storage.md` | Azure Blob Storage (Block Blobs) | SAS-direct vs API-proxy surface, user-delegation SAS (no account keys), Event-Grid-sourced blob triggers, range requests + 206, ETag optimistic concurrency, archive rehydration as async 202, `allowSharedKeyAccess=false`, versioning + soft delete + immutable storage. |

## Future hosted API extensions

Hosted API guidance belongs in runtime extensions, not in the core workflow. The Node.js and hosted Next.js surfaces are now covered here. Likely future extension families include ASP.NET Core on Azure App Service, ASP.NET Core on Azure Container Apps, Kubernetes-hosted HTTP APIs, and Edge/runtime-platform APIs. Add those only when their runtime primitives, detection signals, and smells are specified.

## Adding an extension

1. Copy one of the existing extensions as a template (pick the closest domain — compute, data, object storage).
2. Pick a short, stable prefix (e.g., `lambda` for AWS Lambda, `gcf` for Google Cloud Functions, `sql` for Azure SQL, `sb` for Service Bus, `eh` for Event Hubs).
3. Fill in detection signals — both globs and content matches. Detection must be unambiguous; false-positive loads pollute findings.
4. Add stack-specific primitives that the core reference does not already cover. Do not re-document HTTP or OpenAPI primitives already in reference §4.
5. Add stack-specific patterns if the stack's idiomatic solution differs structurally from reference §5 — otherwise cite the core pattern.
6. Add smell codes, namespaced with the prefix.
7. Add carve-outs for idiomatic patterns the stack enforces.
8. Add the extension to the table in `../SKILL.md` § "Extensions" with its detection mapping.
9. Add the extension to the table above.
10. If the extension composes with an existing one (e.g., a Service Bus extension that commonly pairs with `azure-functions-dotnet`), document the composition in the "Extensions compose" section above.

## Non-goals for extensions

- Extensions are not general framework guides. They address the *contract / security / reliability / observability / performance* surface only.
- Extensions do not duplicate the core reference. If a point already lives in `../../../docs/api-reference/api-design.md`, cite it; do not restate.
- Extensions do not override the security / contract / reliability / observability baselines. A stack cannot opt out of problem+json, maintained OAuth/OIDC validation, or managed/workload identity where available — it can only provide its own idiomatic way of honouring them.
