# HTTP API design — a reference for building, extracting, and reviewing

## 1. Context

A deployed endpoint that returns 200 OK is not the same as a production HTTP API. The central problem of API design is **presence vs. efficacy**: an endpoint that responds to a curl command is not evidence that the API holds up under retries, ships a stable error contract, survives key rotation, emits correlated telemetry, handles 429 from its own data store, stays inside its latency budget, or degrades sensibly when the downstream dependency is the one throttling. An HTTP status code is not a contract.

API design in 2026 is less about wiring a route than about writing an API whose **contract, security posture, reliability envelope, and observability** are correct by construction — before the first load test, and regardless of which hosting model, runtime, or data service sits underneath. This reference is a playbook for that practice: principles, decisions with defaults, a cheatsheet of primitives and status codes, worked patterns, named gotchas, and a review checklist — organized for the person building, extracting, or reviewing an API, not for a scanner.

**Security is enforced throughout, not referenced.** Every decision, pattern, and checklist item that touches authentication, authorization, secrets, or data access names the specific discipline it protects: HTTPS-only, OAuth 2.0 / OIDC through maintained middleware, managed or workload identity where the platform supports it, platform secret managers over literals, data-plane RBAC for managed data services, least-privilege scopes, input validation at the boundary. A design choice that compromises any of these is called out, never silently accepted.

**Contract discipline is a baseline, not a future concern.** Every endpoint here ships with an OpenAPI 3.1 definition, RFC 9457 `application/problem+json` on every error path, an explicit versioning strategy (no implicit v1), RFC 9110 conditional requests (`ETag`, `If-Match`, `If-None-Match`) on mutable resources, and idempotency semantics that match the HTTP verb. POSTs that retry without an `Idempotency-Key` are a smell; PUT / DELETE without `If-Match` on concurrently-writable resources is a smell.

**Reliability is baseline.** Mutations are idempotent (by verb or by idempotency key). Outbound calls retry with exponential backoff and jitter. Throttle responses are `429 Too Many Requests` with `Retry-After`. Async workers carry bounded retry plus poison / dead-letter handling. Long-running work does not block a synchronous HTTP request past the runtime's timeout budget.

**Observability is baseline.** Every request carries a W3C `traceparent`; every log is structured; every error carries a correlation ID (`traceparent`-derived or explicit); every outbound call propagates `traceparent` downstream. Application Insights / OpenTelemetry is wired at the worker level, not retrofitted per endpoint.

**Performance is responsiveness for APIs.** Responsive here means responsive to startup latency, connection exhaustion, dependency latency, throttling, and scale events — not just to a raw RPS number. The reference environment is mobile-client p95 over public internet; the hosting choice is a design-time decision governed by latency tolerance, workload shape, operations model, and cost, not a deployment afterthought.

**Scope.** HTTP APIs in 2026, with runtime and data specifics supplied by extensions. Current bundled extensions cover Azure Functions .NET (isolated worker), Node.js hosted/serverless APIs, hosted Next.js API surfaces, Cosmos DB, and Azure Blob Storage. gRPC, GraphQL, SOAP, and runtimes without a bundled extension are out of scope — see §8. Data-model design (schema, DDD, event-sourcing) is also out of scope; this reference covers the contract and the runtime around it, not the domain model.

## 2. Principles

### 2.1 Contract-first, not code-first
The OpenAPI 3.1 definition is the source of truth. Endpoint signatures, request and response shapes, error types, and auth requirements are decided in the contract before a handler is written, and the handler is verified against the contract. Generated SDKs, client codecs, mocks, and API Management / Front Door policies all consume the same document.

### 2.2 Semantic HTTP
HTTP verbs carry meaning and HTTP status codes are part of the contract. `GET` is safe and cacheable; `PUT` and `DELETE` are idempotent; `POST` is neither unless explicitly made so. 200 is not a catch-all: `201 Created` ships `Location`; `202 Accepted` ships `Location` pointing at a status endpoint; `204 No Content` means a body is never sent; 400 is client error; 409 is conflict; 412 is precondition; 422 is semantically-invalid-but-syntactically-valid; 429 is throttle; 5xx is server fault. Status code is not a log level.

### 2.3 Errors are data
Every error response is `application/problem+json` per RFC 9457 — `type` (URI identifying the error class), `title`, `status`, `detail`, `instance`, plus any extension members the error family needs. Error `type` URIs are stable across versions; the set of types is documented in the OpenAPI. A client that sees `{ "type": "https://api.example.com/errors/rate-limited" }` never has to parse an English string.

### 2.4 Versioning is mandatory and explicit
Every endpoint belongs to a version. New APIs default to URI-path versioning (`/v1/...`); the alternative — header or media-type versioning — is chosen explicitly and with a documented reason. "Implicit v1" is a smell; clients must not be able to tell which version they are speaking by omission.

### 2.5 Security is baseline
HTTPS-only, TLS 1.2+. Use OAuth 2.0 / OIDC through maintained middleware for end-user and service-to-service auth; use managed identities or workload identities for cloud-to-cloud hops where the hosting platform supports them; use platform secret managers for the few remaining secrets; use data-plane RBAC for managed data stores. Azure extensions map this to Entra ID, managed identities, Key Vault references, Cosmos `disableLocalAuth=true`, and Storage `allowSharedKeyAccess=false`. Input is validated at the boundary, not in the handler body. Authorization is explicit and scope-based — "the function key or API key proves anything about the caller" is false.

### 2.6 Reliability is baseline
Mutations are idempotent by verb (PUT, DELETE) or by idempotency key (POST with `Idempotency-Key` + a replay cache). Outbound calls retry with exponential backoff and jitter, capped, and honour server-supplied `Retry-After`. Throttle responses are 429 with `Retry-After` (seconds or HTTP-date). Async workers carry bounded retry plus poison / dead-letter handling. Long-running work does not live inside the synchronous HTTP request — it moves to a queue-backed processor or workflow runtime.

### 2.7 Observability is baseline
Every request carries a W3C `traceparent` header (`00-<trace-id>-<span-id>-<flags>`); the runtime propagates it into request-local context / logger scopes and onto outbound HTTP calls. Logs are structured — named fields, not interpolated strings. Every error response carries a correlation identifier the client can quote back (the `traceparent` trace-id is sufficient). OpenTelemetry or the platform-native telemetry bridge is wired at worker / process startup, not inside individual handlers. Per-request cost signals (Cosmos RU charge, Blob Storage request count, external dependency count / latency) are emitted as structured fields so dashboards are one query away.

### 2.8 Performance is responsiveness for APIs
Responsive means responsive to startup latency, connection overhead, dependency latency, and scale events — not raw throughput. HTTP and data clients (`HttpClient`, Undici / `fetch` dispatcher, CosmosClient, BlobServiceClient, database pools, queue clients) live in DI, module scope, or an app container, never in handler bodies. Hosting selection is a design-time decision keyed to latency tolerance, scale shape, operational ownership, and cost; runtime extensions supply concrete platform defaults.

### 2.9 Progressive enhancement across capability axes
Sync HTTP is the baseline; async patterns (202 + polling, webhook delivery, workflow orchestration, queue-backed processor) are additive. Reach for the simplest pattern that satisfies the requirement and move up only when it doesn't: if a queue + 202 will do, don't reach for a full orchestration runtime; if a broker or worker platform gives you dead-lettering for free, don't hand-roll retry loops.

## 3. Decisions

Each decision states the choice, the default rule, and when to deviate. Defaults are written on a single bold line so they can be lifted wholesale into code review.

### 3.1 REST over RPC-over-HTTP
Resource-oriented URLs and verbs scale better than function-style endpoints. `POST /orders/{id}/cancel` beats `POST /cancelOrder` because the resource model is discoverable from the URL space.

**Default:** REST. URLs name resources; verbs name operations; state transitions are `POST` sub-resources (`/orders/{id}/cancel`), not verbs in paths.

*When to deviate:* genuinely RPC-style internal endpoints (e.g., `POST /rpc/recomputeCache`) where there is no resource being mutated and the caller is a trusted internal service. Document the RPC-style endpoint as such.

### 3.2 Versioning scheme
URI-path versioning is the most discoverable for public APIs and the easiest to route at the edge.

**Default:** URI path — `/v1/...`, `/v2/...`. New v2 coexists with v1 until v1 is sunset per §5.10.

*When to deviate:* internal APIs where a single client controls both sides and header versioning reduces churn; public APIs that must preserve exact existing URLs across schema changes and choose `api-version=` query parameter for compatibility with the existing clients. Media-type versioning (`Accept: application/vnd.example.v2+json`) is rarely warranted; pick it only when content negotiation is the clearest expression of the contract.

### 3.3 Authentication model
End-user calls authenticate with OAuth 2.0 / OIDC through maintained middleware. Service-to-service calls use OAuth 2.0 client credentials or platform managed/workload identity when available. Azure targets use Microsoft Entra ID and managed identities. Function keys and API keys are a narrow fallback for tightly-scoped service-to-service with a single trusted caller.

**Default:** OAuth 2.0 / OIDC for callers, managed/workload identity where available, and no secrets in code. Azure targets default to Entra ID + managed identity.

*When to deviate:* a narrow service-to-service hop where both sides are internal, the caller is a single trusted service, and the overhead of OAuth setup is not justified — use a scoped key sourced from a platform secret manager and rotated. Document the scope and the rotation policy.

### 3.4 Authorization model
Authentication proves who. Authorization proves what they can do. Never use "holds a key" as proof of "allowed to perform this operation."

**Default:** scope-based or app-role-based authorization on every endpoint; deny-by-default; explicit route/handler policy metadata. Anonymous runtime-level access is allowed only if the endpoint is genuinely public (e.g., a health probe).

**OAuth 2.0 flow matrix.** Pick the flow by caller type, not by token shape:

| Flow | Use when | Caller holds |
|---|---|---|
| **Authorization Code + PKCE** | Interactive end-user via SPA, mobile, or native client | User identity (OID claim) + delegated scopes |
| **Client Credentials** | Service-to-service, no user present | App identity (AppId) + app roles (`roles` claim) |
| **On-Behalf-Of (OBO)** | Downstream API calls that must preserve the user's identity | User identity *and* app identity (dual token exchange) |
| **Device Code** | Headless / constrained input (CLI, smart TV) | User identity + delegated scopes (fallback when browser flow is impractical) |

Resource Owner Password Credentials (ROPC) is **disallowed** for Entra ID per Microsoft's guidance — do not add it to the matrix.

**Scope vs app role:** scopes (`scp` claim) are delegated permissions tied to the signed-in user ("this user consented to this app acting on their behalf"). App roles (`roles` claim) are application permissions granted to the app identity directly. An endpoint that a user invokes checks `scp`; an endpoint that only other services invoke checks `roles`. An endpoint that accepts both (end-user *and* service caller) checks whichever is present.

**Token validation:** use the platform's maintained OAuth / OIDC middleware rather than hand-rolling JWT validation against raw JWKs. Issuer multi-tenancy, issuer-version drift, audience checks, clock skew, and JWK rotation are all easy to get wrong.

*When to deviate:* health / readiness / liveness probes that must be reachable without credentials for platform health checks. Document and rate-limit.

### 3.5 Error contract
Errors are data, and the data shape is RFC 9457 `application/problem+json`.

**Default:** every error path returns `application/problem+json` with `type` (stable URI), `title`, `status`, `detail`, `instance`, plus extension members. Error `type` URIs are stable across versions and listed in the OpenAPI.

**Type URI organization.** Pick one base URI per API (e.g., `https://api.example.com/errors/`) and hang kebab-case error names off it (`…/errors/invalid-parameter`, `…/errors/rate-limited`, `…/errors/insufficient-scope`, `…/errors/archived-blob`). The URI does not need to resolve to a hosted page at launch, but should resolve to a human-readable description before the API goes public (a registry page per type, or a documented redirect target). Once published, a type URI is forever — treat it like a database primary key, not a message.

*When to deviate:* never. Backward-compatibility with an existing non-conformant shape is a migration path, not a licence to emit new non-problem+json errors.

### 3.6 Idempotency for mutations
HTTP verbs carry idempotency guarantees that clients rely on when retrying. PUT and DELETE are idempotent by spec. POST is not, unless the server makes it so.

**Default:** PUT and DELETE use `If-Match: <etag>` for concurrent-write safety → 412 Precondition Failed on mismatch. POST accepts an optional `Idempotency-Key` header; the server stores `(key, result)` in a replay cache with TTL and returns the cached result on retry. Non-idempotent POST (no key, no dedup) is only safe when the client will never retry, which in practice means almost never.

*When to deviate:* a POST endpoint whose effect is inherently idempotent because the payload carries a client-assigned natural key (e.g., an upsert by external ID) can skip the replay cache. Document the natural key and the uniqueness guarantee.

### 3.7 Pagination
Cursor pagination survives reshuffling of the source (inserts, deletes, reindexing) and does not require the server to skip rows. Offset pagination is linear in the offset — pathological for large result sets — and unstable under concurrent writes.

**Default:** cursor-based. Request: `?limit=N&cursor=<opaque>`. Response: `{ items, nextCursor }`. The cursor is opaque to the client.

*When to deviate:* read-only aggregates with a stable total order (e.g., admin audit log in strict time order, materialised report tables) where offset is simpler and cheap. Document the offset contract and cap the maximum offset.

### 3.8 Filtering / projection
Filters and field projections that trust client-supplied names expand the API surface by accident and open authorization holes.

**Default:** explicit allowlist. Filter fields and projection fields are enumerated in the OpenAPI; anything outside the list is 400 Bad Request with a problem+json `type` of `invalid-parameter`.

*When to deviate:* internal admin endpoints where the caller is trusted and the cost of maintaining an allowlist exceeds the value. Document the trust boundary.

### 3.9 Async patterns
Long-running or deferred work is an explicit design choice with a named pattern; it is never achieved by blocking a synchronous HTTP request past the runtime timeout.

**Default:** 202 Accepted + `Location` + polling for most async work. Webhook delivery when the client is itself a service with a reachable callback endpoint. Workflow orchestration when the process is multi-step, requires fan-out / fan-in, or needs compensation logic.

*When to deviate:* a synchronous endpoint that legitimately takes 2–3 seconds and whose callers are tolerant (interactive admin action, for instance) can stay sync — but not past the loaded runtime extension's request timeout, gateway idle timeout, or configured platform limit.

### 3.10 Rate limiting & throttling
Throttling is a first-class response, not an implementation detail. Clients that retry without observing `Retry-After` create amplification loops.

**Default:** 429 Too Many Requests on throttle, always with `Retry-After` (seconds). `RateLimit-Limit` / `RateLimit-Remaining` / `RateLimit-Reset` informational headers on successful responses so clients can self-pace. Rate limiting is enforced at the edge (API gateway, reverse proxy, CDN/WAF, Front Door / API Management on Azure) on public endpoints; origin-only limiting is a fallback, not a primary defence.

*When to deviate:* internal service-to-service endpoints with a small, trusted set of callers can skip `RateLimit-*` informational headers, but 429 + `Retry-After` remains mandatory.

### 3.11 Input validation
Input is validated at the boundary. Handler bodies should not defend against shapes the OpenAPI rejected.

**Default:** schema validation (OpenAPI 3.1) on request bodies, query parameters, and headers; semantic validation (ranges, cross-field rules, allowlist values) at boundary; failures return 400 with problem+json `type` of `invalid-parameter` (syntactic) or 422 with `invalid-entity` (semantic-but-syntactically-valid). Oversized payloads return 413 Payload Too Large.

*When to deviate:* never. Internal endpoints get the same discipline.

### 3.12 Payload size limits
API runtimes have memory, timeout, and request-size ceilings that a blob payload can hit long before business logic does.

**Default:** request bodies capped at a documented size (typically 25 MB for JSON / form uploads unless the loaded runtime extension says otherwise). Anything larger uses direct-to-object-store upload via a scoped delegated URL — the API mints the upload grant and the client uploads directly to storage, bypassing the API runtime. Response bodies are bounded or streamed (`Transfer-Encoding: chunked`).

*When to deviate:* genuinely small-payload endpoints may skip streaming infrastructure. Object-store direct upload is the escape hatch for anything that would otherwise exhaust API runtime memory.

### 3.13 CORS
`Access-Control-Allow-Origin: *` and credentials do not mix, and wildcard origin on an authenticated endpoint is a confused-deputy invitation.

**Default:** explicit origin allowlist. Wildcard is allowed only on genuinely public read-only endpoints (e.g., public metadata / status endpoints).

*When to deviate:* never on authenticated endpoints.

### 3.14 Observability contract
Observability is wired at worker startup, not per endpoint.

**Default:** structured logger scopes / request context on every handler with named fields; W3C `traceparent` propagation end-to-end (inbound → scope/context → outbound HTTP → data-store SDK); correlation identifier (trace-id) in every error response body; OpenTelemetry / Application Insights / platform telemetry registered at startup. Per-request cost signals (Cosmos `RequestCharge`, storage request count, dependency latency/count) emitted as structured log fields.

*When to deviate:* never. Every endpoint gets the same discipline.

### 3.15 Hosting and runtime selection
Hosting is a contract parameter: it fixes startup tolerance, scale-out characteristics, timeout behavior, instance memory, operations model, and failure domains.

**Default:** choose the smallest runtime shape that satisfies the API's latency, scale, timeout, payload, and operational requirements; document the decision in IaC or deployment docs. Loaded runtime extensions provide concrete defaults for their platforms.

*When to deviate:* clear cost, topology, compliance, or platform-standard reasons. Document the reason; the hosting choice is visible in IaC or deployment manifests and reviewable.

### 3.16 Data-access contract
Every outbound HTTP and data-store client (`HttpClient`, Undici / `fetch` dispatcher, database pool, `CosmosClient`, `BlobServiceClient`, `SqlConnection`, `ServiceBusClient`) is registered as a singleton in DI, module scope, or an application container and uses managed/workload identity where the platform supports it. Per-invocation construction is a bug.

**Default:** singleton / process-scope client; managed/workload-identity auth where available; preferred-regions configured for multi-region clients; per-request cost signals surfaced.

*When to deviate:* dev-only local emulator usage may differ. Production code does not instantiate clients per request.

### 3.17 Secrets contract
Secrets live in the platform secret manager and are referenced from runtime configuration rather than committed files or code literals. Azure targets use Key Vault references from app settings via the `@Microsoft.KeyVault(SecretUri=...)` syntax. Account keys, shared access keys, API keys in query strings, committed `.env` files, and connection strings with embedded secrets are legacy debt.

**Default:** platform secret references in runtime settings; managed/workload identity on the API runtime with the minimum data-plane role needed. Azure Cosmos DB accounts have `disableLocalAuth=true`. Azure Storage accounts have `allowSharedKeyAccess=false`. No secrets in code literals, no keys in local settings committed to git.

*When to deviate:* never for new code. Legacy code is migration debt, not a reference pattern.

## 4. Primitives cheatsheet

Modern HTTP and API primitives with one-line purpose, minimal shape, and the key pitfall. If a primitive is cited in §5 patterns, this is where the signature lives.

### HTTP verbs
- **`GET`** — safe, idempotent, cacheable. Never mutates server state.
- **`POST`** — creates a resource or runs a non-idempotent operation. Default status 201 on create, 202 on async accept, 200 on non-creating action with body.
- **`PUT`** — replaces a resource. Idempotent by spec. Use with `If-Match` for concurrent safety.
- **`PATCH`** — partial update. Idempotent only if the patch document is (e.g., JSON Merge Patch). Use with `If-Match`.
- **`DELETE`** — removes a resource. Idempotent: second DELETE returns 404 or 204, both acceptable.
- **`HEAD`** — `GET` without body. For cache validation and existence checks.
- **`OPTIONS`** — CORS preflight; not a general-purpose metadata endpoint.

### Status codes (the ones that recur)
- **`200 OK`** — success with body.
- **`201 Created`** — resource created. MUST include `Location` header pointing at the new resource.
- **`202 Accepted`** — async work started. MUST include `Location` header pointing at the status endpoint.
- **`204 No Content`** — success, no body. Used on `DELETE` and successful `PUT` without return representation.
- **`206 Partial Content`** — response to a `Range` request. Include `Content-Range`.
- **`301 / 302`** — redirect (permanent / temporary). Prefer 308 / 307 if method preservation matters.
- **`400 Bad Request`** — syntactically invalid request (malformed JSON, unknown field, bad type). problem+json with `invalid-parameter` or similar.
- **`401 Unauthorized`** — missing or invalid credentials. Include `WWW-Authenticate`.
- **`403 Forbidden`** — valid credentials, insufficient authorization. Never use when 404 would leak existence of a resource the caller cannot see.
- **`404 Not Found`** — resource does not exist (or exists but caller cannot see it, when existence itself is sensitive).
- **`405 Method Not Allowed`** — verb is unsupported on this resource. Include `Allow` header.
- **`409 Conflict`** — request conflicts with current state (duplicate unique-key insert, concurrent update without If-Match).
- **`410 Gone`** — resource was deliberately deleted; do not reintroduce.
- **`412 Precondition Failed`** — `If-Match` / `If-None-Match` mismatch; client must retry with fresh `ETag`.
- **`413 Payload Too Large`** — request body exceeds server cap.
- **`415 Unsupported Media Type`** — `Content-Type` not accepted.
- **`416 Range Not Satisfiable`** — bad `Range`.
- **`422 Unprocessable Entity`** — syntactically valid, semantically rejected (business rule failure).
- **`429 Too Many Requests`** — throttled. MUST include `Retry-After`.
- **`500 Internal Server Error`** — unexpected server fault. Log the correlation ID in the response body.
- **`502 / 503 / 504`** — upstream dependency failures.

### Headers that matter
- **`Location`** — where to go next. 201 points at new resource; 202 points at status endpoint.
- **`Retry-After`** — seconds to wait, or HTTP-date. Required on 429, recommended on 503.
- **`ETag`** — opaque version identifier for a resource. Set on every `GET` of a mutable resource.
- **`If-Match`** — "only proceed if current ETag matches." 412 on mismatch.
- **`If-None-Match`** — "only return if ETag has changed." 304 on match (cache validation).
- **`Idempotency-Key`** — client-supplied dedup token for non-idempotent POSTs. Server stores `(key, result)` in a TTL'd cache.
- **`traceparent`** / **`tracestate`** — W3C Trace Context. Inbound propagated into logs and outbound calls.
- **`RateLimit-Limit`** / **`RateLimit-Remaining`** / **`RateLimit-Reset`** — IETF httpapi draft headers for client self-pacing (still draft as of 2026-04; check IETF status when authoring).
- **`Content-Range`** — response to a `Range` request: `bytes <start>-<end>/<total>`.
- **`Cache-Control`** — `no-store` on authenticated responses by default; `max-age` on genuinely cacheable resources.
- **`WWW-Authenticate`** — scheme and realm on 401.
- **`Link`** — typed relationships between resources per **RFC 8288**: `Link: </resources?cursor=xyz>; rel="next"`, `Link: </resources/{id}>; rel="self"`. On list endpoints, pairs with (or replaces) cursor fields in the body. Multiple relations comma-separated in a single header.

### RFC 9457 problem+json shape
```json
{
  "type": "https://api.example.com/errors/invalid-parameter",
  "title": "Invalid query parameter",
  "status": 400,
  "detail": "'limit' must be between 1 and 100.",
  "instance": "/v1/orders?limit=5000",
  "errors": [
    { "name": "limit", "reason": "out-of-range", "value": 5000 }
  ],
  "traceId": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
}
```
`type` is a stable URI (not a message). `traceId` (or the trace-id inside `traceparent`) is the correlation handle clients cite back.

### W3C Trace Context
Header: `traceparent: 00-<trace-id 32 hex>-<span-id 16 hex>-<flags 2 hex>`. Optional `tracestate`. Runtime propagates inbound trace-id into `ILogger` scope; outbound `HttpClient` attaches `traceparent` automatically when registered via `IHttpClientFactory`.

### `Idempotency-Key`
Client sends an opaque string (UUID typical) on a POST. Server stores `(key, responseStatus, responseBody, responseHeaders)` in a replay cache with TTL (24 h typical). Retries with same key return the cached response bit-for-bit. Different bodies under the same key are a client bug — return 409.

### OpenAPI 3.1 `operationId`
Every operation has a stable `operationId` (camelCase, unique per document). Generated SDKs use this as the method name; changing it is a breaking change for consumers. `operationId` is not the same as path; it survives path renames.

### Cursor pagination shape
Request: `?limit=<n>&cursor=<opaque>` with `limit` capped at 100 (typical) and defaulted to 25. Response: `{ items: [...], nextCursor: "opaque string or null" }`. `nextCursor: null` means end of list. Cursors are not portable across filter changes. Optionally mirror the cursor in a `Link: </resources?cursor=xyz>; rel="next"` header (RFC 8288) so clients that prefer header-driven pagination (hypermedia, generic HTTP libraries) can follow without body parsing.

### Webhook signatures (HMAC)
Signed header carries `t=<unix-ts>,v1=<hmac-sha256-hex>` over canonical request (timestamp + body). Receiver MUST (a) reject timestamps older than ~5 min to defeat replay, (b) constant-time compare the hex. Rotate the secret via Key Vault; support overlapping validity on rotation.

### `Cache-Control` for API responses
Authenticated default: `no-store`. Public cacheable (rare on APIs): `public, max-age=<seconds>, immutable` on content-addressable resources. Never `public` on responses that vary by caller identity.

## 4.5 Baseline contract

Every new API starts from this baseline; skip the parts that don't apply, but start from here.

### OpenAPI 3.1 fragment
```yaml
openapi: 3.1.0
info:
  title: Orders API
  version: "1"
servers:
  - url: https://api.example.com/v1
components:
  schemas:
    Problem:
      type: object
      required: [type, title, status]
      properties:
        type:    { type: string, format: uri }
        title:   { type: string }
        status:  { type: integer }
        detail:  { type: string }
        instance:{ type: string }
        traceId: { type: string }
  responses:
    BadRequest:
      description: Invalid request
      content:
        application/problem+json:
          schema: { $ref: "#/components/schemas/Problem" }
    RateLimited:
      description: Throttled
      headers:
        Retry-After: { schema: { type: integer, description: "seconds" } }
      content:
        application/problem+json:
          schema: { $ref: "#/components/schemas/Problem" }
  securitySchemes:
    oauth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/oauth2/authorize
          tokenUrl:         https://auth.example.com/oauth2/token
          scopes:
            "api://<app-id>/Orders.Read":  Read orders
            "api://<app-id>/Orders.Write": Create / modify orders
security:
  - oauth2: ["api://<app-id>/Orders.Read"]
paths:
  /orders/{id}:
    get:
      operationId: getOrderById
      parameters:
        - { in: path, name: id, required: true, schema: { type: string } }
      responses:
        "200": { description: OK, headers: { ETag: { schema: { type: string } } } }
        "400": { $ref: "#/components/responses/BadRequest" }
        "401": { description: Unauthorized }
        "404": { description: Not found }
        "429": { $ref: "#/components/responses/RateLimited" }
```

### `traceparent` propagation sketch
```csharp
// Program.cs
builder.Services
    .AddHttpClient("downstream")
    .AddStandardResilienceHandler();     // retry + circuit-breaker

// handler
public async Task<IActionResult> Handle(HttpRequest req, IHttpClientFactory factory, ILogger<Handler> log)
{
    using var scope = log.BeginScope(new Dictionary<string, object>
    {
        ["operationId"] = "getOrderById",
        ["orderId"]     = req.RouteValues["id"]!
    });
    var client = factory.CreateClient("downstream");   // traceparent auto-propagated
    var result = await client.GetFromJsonAsync<Order>($"/orders/{req.RouteValues["id"]}");
    return Results.Ok(result);
}
```

## 5. Patterns

### 5.1 CRUD resource
- `GET /resources/{id}` → 200 + `ETag` header (or 404).
- `POST /resources` → 201 + `Location: /resources/{id}` + body.
- `PUT /resources/{id}` with `If-Match` → 200 + new `ETag`, or 412.
- `DELETE /resources/{id}` with `If-Match` → 204, or 412, or 404.
- All errors: problem+json. OpenAPI 3.1 definition first.

### 5.2 Search / list with cursor pagination and filtering
- `GET /resources?limit=<n>&cursor=<opaque>&filter=<allowlisted>&sort=<allowlisted>` → 200 `{ items, nextCursor }`.
- Unknown filter / sort fields → 400 with `invalid-parameter`.
- Stable `limit` cap (e.g., 100) enforced server-side.
- Cursor opaque; never interpretable by the client.
- **Total count is off by default.** A `totalCount` field requires a second (often expensive) aggregate query and invalidates as the source mutates — most UIs genuinely need "is there a next page?" not "how many in total?", and `nextCursor: null` answers that. Expose total count only on an explicit opt-in (`?includeTotal=true`) and document the cost; do not include it in the baseline envelope.
- Optionally mirror pagination in an RFC 8288 `Link` header: `Link: </resources?cursor=xyz>; rel="next", </resources/{id}>; rel="self"`. Useful for clients that follow hypermedia.

### 5.3 Long-running job via 202 + `Location` + polling
- Client: `POST /jobs` with payload → 202 + `Location: /jobs/{id}`.
- Worker: processes asynchronously (queue-backed processor, Durable activity, change-feed).
- Client: `GET /jobs/{id}` → 200 with `{ status: pending | running | succeeded | failed, result?, error? }`.
- Terminal statuses include the result (succeeded) or a problem+json under `error` (failed).
- Status endpoint is idempotent and cheap to call.

### 5.4 Long-running job via workflow orchestration
Prefer §5.3 for simple async. Reach for orchestration when coordination is required: fan-out / fan-in, external events, human approval, compensation, or long-running monitors.

**Default:** the HTTP surface still returns 202 + `Location`; orchestration status is exposed through the same job-status resource shape as §5.3. The loaded runtime extension supplies the concrete orchestration APIs and determinism rules.

**Core rules:**
- Keep orchestration state and job status versioned as an API contract.
- Bound fan-out width so downstream dependencies are not saturated.
- Keep orchestration steps idempotent or compensatable.
- Do not perform non-deterministic work in replay-based orchestrators; use the loaded runtime extension's deterministic clock, ID, timer, and activity APIs.
- For breaking workflow changes, drain in-flight instances or route old and new versions separately.

### 5.5a Webhook delivery (outbound)
- Server-side: publish via queue-backed processor; signature header `X-Signature: t=<ts>,v1=<hmac-sha256-hex>` computed over `<ts>.<raw-body>`; retry with exponential backoff + jitter; after N failures move to DLQ.
- Include a stable `X-Event-Id: <uuid>` header so consumers can deduplicate.
- Rotate the signing secret via Key Vault with a grace window — emit both the new and old signatures in parallel for one rotation cycle, then retire the old.
- Expose `GET /webhook-deliveries/{id}` for operators to inspect delivery status, retry count, DLQ reason.

### 5.5b Webhook receipt (inbound)
Receiving a webhook is not just "process a POST." A production-grade receiver:

1. **Read the raw body once, before model binding.** Signature is computed over bytes, and most frameworks canonicalize whitespace / JSON ordering when they deserialize. Use `HttpRequest.Body` with buffering enabled (`EnableBuffering()` + `ReadAsync` into a `byte[]` or `MemoryStream`) so both signature verification and handler can read it.
2. **Verify timestamp freshness** against a ±5-minute window (`|now - ts| ≤ 300`). Reject older with 401. This blocks replay of captured requests.
3. **Constant-time HMAC compare** (`CryptographicOperations.FixedTimeEquals`) against the expected signature; never `string ==`.
4. **Idempotent handler** via `(source, event-id)` dedup. Store processed event IDs in Cosmos (`cosmos.PAT-idempotency-container`) with TTL covering the provider's retry window (typically 24 h). Duplicate → return the same 200 / 202 that the first call returned, don't re-process.
5. **Respond fast.** Acknowledge receipt with 202 + enqueue to an internal processor; don't do the work synchronously in the receiver. Webhook senders interpret slow 200s as failures and retry, creating double-processing.
6. **Never block on signature secret lookup in the hot path** — cache the Key Vault secret with a short TTL; on rotation, fall back to trying the previous secret once before rejecting.

### 5.6 Idempotent POST with `Idempotency-Key` + replay cache
- Client: `POST /resources` with `Idempotency-Key: <uuid>`.
- Server: look up `(key)` in replay cache; hit → return cached response; miss → process, store `(key, status, body, headers)` with TTL (24 h typical), return response.
- Same key with different body → 409 (client bug).
- Cache implementation: dedicated Cosmos container with `DefaultTimeToLive` + unique-key policy on the idempotency key, or Redis with TTL.

### 5.7 Bulk / batch endpoint with partial-success semantics
- `POST /resources/batch` with an array of up to N items.
- Response: 207 Multi-Status (HTTP non-standard but widely used in APIs) or 200 with per-item result array: `{ results: [{ status, id?, error? }] }`.
- Size cap documented (e.g., 100 items or 2 MB).
- Per-item failures do not fail the whole request unless atomicity was requested.
- Combine with `Idempotency-Key` so whole-batch retries are safe.

### 5.8 Fan-out via queue-backed handler
- HTTP endpoint enqueues; returns 202 with `Location` pointing at status endpoint.
- Queue trigger processes (built-in retry, poison / DLQ).
- Status endpoint reads projection written by the processor.
- Cheaper and simpler than Durable for stateless fan-out.
- **Ordering:** Service Bus queues are FIFO *per session* only — no global order. If the API guarantees ordered processing per aggregate (all events for order-123 in order), use **Service Bus sessions** (`sessionId = aggregateId`) and a session-aware trigger. Without sessions, competing consumers reorder freely. Storage Queues have no session primitive — use Service Bus if ordering matters.
- **Dedup:** Service Bus has **broker-side duplicate detection** (`requiresDuplicateDetection: true`, `duplicateDetectionHistoryTimeWindow: PT10M` in Bicep) keyed on `MessageId`. Set `MessageId` to a stable, deterministic value for your event (not a random Guid) so retries on the producer side are discarded by the broker. Dedup window is ≤ 7 days; for longer windows, dedup on the consumer side via an idempotency-key container.

### 5.9 Backend-for-frontend (BFF) aggregation endpoint
- Client-facing endpoint composes several downstream calls; returns a shape tuned for the UI.
- Emit `traceparent` to every downstream; aggregate errors into problem+json extension members.
- Cache-per-request (request-scoped DI services) to avoid duplicate downstream fetches.
- If aggregation is slow, switch to async 202 + polling.

### 5.10 Versioned endpoint rollout
- Introduce `/v2/...` alongside `/v1/...`; both live.
- v1 responses gain `Deprecation: @<unix-ts>` (RFC 9745, Standards Track, March 2025) and `Sunset: <HTTP-date>` (RFC 8594) headers at rollout.
- Sunset date is at least 6 months out, documented in the OpenAPI, tracked in observability (count of v1 calls per week).
- After sunset, v1 endpoints return 410 Gone with problem+json pointing at v2.

### 5.11 Event-driven ingress (HTTP → Service Bus → processor)
- HTTP endpoint validates + publishes to Service Bus; returns 202 with `Location`.
- Service Bus trigger processes; tune `maxConcurrentCalls` / `maxAutoLockRenewalDuration` via `host.json`.
- Broker-side dedup via `MessageId` (`requiresDuplicateDetection: true` on the queue) so producer retries don't double-process.
- Dead-letter subscriber writes a problem+json error record clients retrieve via `/jobs/{id}`. Include the original `MessageId` and the dead-letter reason (`DeadLetterReason`, `DeadLetterErrorDescription`).
- **Sessions** (`sessionId = aggregateId`) are required if ordering per aggregate matters; the trigger uses `IsSessionsEnabled = true` and the queue is configured for sessions in Bicep.
- **Partitioning and throughput:** a partitioned queue distributes across message brokers; use when target throughput exceeds a single-partition ceiling. Sessions and partitioning are compatible but require session-affinity awareness on the consumer side.
- **Poison handling:** after `MaxDeliveryCount` (default 10) the message is dead-lettered automatically. Don't reset `DeliveryCount` on transient failures — let the broker's retry count drive dead-lettering, and surface it in the `/jobs/{id}` failure record.

### 5.12 OAuth2 / OIDC-protected endpoint with scope check
- Authentication: maintained OAuth2 / OIDC validator at the edge or in the API runtime.
- Authorization: `[Authorize(Policy="Orders.Write")]`, framework policy middleware, or equivalent scope-based check.
- 401 on missing / invalid token + `WWW-Authenticate: Bearer realm="...", error="invalid_token"`.
- 403 on valid token without the required scope + problem+json `type: insufficient-scope`.
- Never use 404 to mask missing authorization unless existence is itself sensitive.

## 6. Gotchas — named anti-patterns

- **SAD-G-secrets-in-settings** — account keys, connection strings with embedded secrets, function keys, or `.env` secrets committed as literals. Fix per §3.17: platform secret reference + managed/workload identity where available.
- **SAD-G-shared-key-public** — shared-key / account-key / API-key auth exposed to public callers. Fix per §3.3 / §3.5.
- **SAD-G-httpclient-per-invocation** — outbound HTTP client constructed inside a handler body (`new HttpClient()`, new Node dispatcher/Agent per request); socket exhaustion under load. Fix per §3.16 / §2.8: singleton via DI, app container, or module scope.
- **SAD-G-unbounded-response** — response body that scales with result-set size; OOM under growth. Fix per §3.7: cursor pagination with `limit` cap, or streaming.
- **SAD-G-post-no-idempotency** — POST mutation with no idempotency key and no natural key; retries double-submit. Fix per §3.6 / §5.6.
- **SAD-G-at-least-once-no-dedup** — claiming at-least-once delivery without a dedup mechanism; silently double-processes. Fix: idempotency key or natural key dedup on the receiving side.
- **SAD-G-429-no-retry-after** — 429 response without `Retry-After`. Clients retry on their own timeline; amplification loop. Fix per §3.10.
- **SAD-G-500-where-4xx** — 500 emitted for a 400 / 404 / 409 / 422 condition (typically an unhandled validation exception). Fix: validate at boundary and emit specific 4xx.
- **SAD-G-silent-retry** — try-catch-retry loop that swallows the failure cause; prod issues present as latency bumps with no errors. Fix: observe retries (`retry-attempt` log field), bound them, surface exhaustion as 5xx with detail.
- **SAD-G-no-correlation-id** — error response with no trace-id / correlation field; support tickets become scavenger hunts. Fix per §3.14.
- **SAD-G-timer-doing-http-work** — timer trigger that calls outbound HTTP APIs in a loop (effectively an HTTP client); no scale, no observability, no DLQ. Fix: queue-backed processor.
- **SAD-G-anonymous-private** — anonymous or key-only access on an endpoint that handles non-public data. Fix per §3.3 / §3.4 and the loaded runtime extension.
- **SAD-G-secrets-in-query-strings** — secrets, tokens, or PII placed in query strings; they end up in access logs, referer headers, and browser history. Fix: request body or `Authorization` header.
- **SAD-G-cors-wildcard-auth** — `Access-Control-Allow-Origin: *` on an authenticated endpoint. Fix per §3.13.
- **SAD-G-http-request-long-running** — work inside a synchronous HTTP request that regularly exceeds the runtime timeout. Fix per §3.9.
- **SAD-G-orchestration-overkill** — workflow orchestration for a single-step async job. Fix: queue-backed handler per §5.8.
- **SAD-G-static-runtime-claim** — a review claiming p95 latency, cold-start time, or error rate from static analysis. Fix: restate as "static signals aligned; runtime metrics require load test / RUM."
- **SAD-G-version-drift** — coexisting versioning strategies (URI-path for most, query string for some) or an "implicit v1" that's really v1.5. Fix per §3.2.

## 7. Review checklist

Each item is tagged with a **verification layer**:

- `[static]` — source-readable (grep, read code, read OpenAPI / IaC).
- `[iac]` — requires inspecting IaC (Bicep / Terraform / ARM) for hosting plan, managed identity, RBAC assignments, network posture.
- `[contract]` — requires the OpenAPI document and an opinion on what the API promises.
- `[runtime]` — requires real invocations; load test, RUM, Azure Monitor, Application Insights. Not inferable from source.
- `[security-tool]` — requires an API security scanner or policy engine (OWASP ZAP, Burp, API Management policies, WAF logs).
- `[load]` — requires a load test (Azure Load Testing, k6, JMeter).

Only `[static]` / `[iac]` / `[contract]` findings are definitively pass/fail from a review. The rest are "source-aligned; final verification requires <layer>."

### Contract discipline
- OpenAPI 3.1 document exists and is current `[static][contract]`.
- Every operation has a stable `operationId` `[static][contract]`.
- Every error response is `application/problem+json` `[static][contract]`.
- Error `type` URIs are documented, stable across versions `[contract]`.
- Versioning strategy is explicit; no implicit v1 `[static][contract]`.
- Idempotency semantics documented for every mutating operation `[contract]`.
- Pagination shape is cursor-based (or justified offset) `[static][contract]`.

### Security (hard requirements)
- HTTPS-only enforced at platform `[iac]`.
- Authentication via OAuth 2.0 / OIDC, maintained session/JWT middleware, Entra ID, managed identity, or workload identity `[static][iac]`.
- Authorization scope- or role-based, deny-by-default `[static][contract]`.
- Secrets via platform secret references; no literals or committed `.env` secrets `[static][iac]`.
- Data-plane: when Azure data extensions load, Cosmos `disableLocalAuth=true`, Storage `allowSharedKeyAccess=false` `[iac]`.
- Input validated at boundary (OpenAPI schema + semantic) `[static][contract]`.
- CORS allowlist, not wildcard on authenticated endpoints `[static][iac]`.
- Rate limiting at the edge (Front Door / API Management) on public endpoints `[iac][security-tool]`.
- No anonymous or key-only access on non-public endpoints `[static]`.
- No secrets in logs, query strings, or error `detail` fields `[static][runtime]`.

### Reliability (hard requirements)
- Idempotency on every mutation (verb-idempotent or `Idempotency-Key` + replay cache) `[static][contract]`.
- Outbound retries use exponential backoff + jitter; bounded `[static]`.
- 429 responses include `Retry-After` `[static]`.
- Poison / dead-letter configured on every queue trigger `[static][iac]`.
- No long-running work inside a synchronous HTTP request past the runtime timeout `[static]`.
- ETag / If-Match on concurrently-writable resources `[static][contract]`.

### Observability (hard requirements)
- Structured logger scopes / request context on every handler, with named fields `[static]`.
- `traceparent` propagated inbound → scope/context → outbound HTTP client `[static]`.
- Correlation ID (trace-id) in every error response `[static][contract]`.
- OpenTelemetry / Application Insights / platform telemetry registered at worker or process startup `[static][iac]`.
- Per-request cost signals surfaced in logs (Cosmos `RequestCharge`, storage request count) `[static]`.
- p95 latency + error rate + cold-start tracked in RUM / Azure Monitor `[runtime]`.

### Performance (hard requirements, at p95)
- Singleton outbound HTTP client/factory/dispatcher (`IHttpClientFactory`, Undici / `fetch` dispatcher, or equivalent) `[static]`.
- Singleton data-store clients / pools (`CosmosClient`, `BlobServiceClient`, database pools, queue clients) via DI, module scope, or app container `[static]`.
- Hosting/runtime choice fits latency, scale, timeout, payload, and operational requirements `[iac]`.
- Runtime-specific startup optimizations are enabled for latency-sensitive apps when the loaded extension requires them `[static][iac]`.
- Response / request payload sizes bounded; large payloads use direct-to-blob SAS `[static][contract]`.
- p95 latency and cold-start observed under load `[load][runtime]`.

## 8. Out of scope

- **Non-HTTP wire formats.** gRPC, GraphQL, SOAP, JSON-RPC — separate disciplines with their own contracts; this reference is HTTP APIs.
- **Runtimes without bundled extensions.** Edge, gateway, mobile backend, and non-Node hosted/serverless runtimes need their own extension when their primitives differ; the core principles here are portable but runtime mechanics are not.
- **Other Azure data layers.** Azure SQL, Table Storage, Queue Storage, Service Bus, Event Hubs, Azure Cache for Redis — future per-service extensions; the Cosmos + Blob pair is the current scope.
- **Cosmos DB non-NoSQL APIs.** MongoDB API, Cassandra API, Gremlin, Table — separate SDK surfaces with different idioms.
- **Data-model design.** Schema design, DDD, event-sourcing, CQRS — this reference covers the HTTP contract and runtime around the model, not the model itself.
- **General .NET / Node.js / Next.js code quality.** Null-safety, LINQ style, async-correctness lint, module-structure lint, React component design — out of scope; `devsecops-audit` and `test-quality-audit` in the `souroldgeezer-audit` plugin cover the audit side.
- **UI on top of the API.** Responsive UI, a11y, i18n — that's the `responsive-design` sibling skill.
- **Runtime SLO verification.** p95, cold-start, error rate, RU charges — these require load / RUM and are out of scope for static review; §7 tags these as `[load]` / `[runtime]` and defers to the appropriate tool.
