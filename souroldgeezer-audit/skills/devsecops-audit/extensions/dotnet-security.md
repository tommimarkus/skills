# Extension — .NET Security

**Applies to:** C# source files (`*.cs`), project files (`*.csproj`, `*.props`), and settings files (`appsettings*.json`, `local.settings.json`) under `api/`, `app/`, `shared/`, `tests/`.

**Detection signals:**

- Any `*.csproj` or `*.sln` in the audit target.
- Any `*.cs` file under the covered directories.
- Any `appsettings*.json` or `local.settings.json`.

**Applies to rubric sections:** §5.1 items 1, 16, 20, §5.3 item 5 (developer-facing), §6 items 3, 4, 5, 6 (code-level subtle failures).

**Complementary skills:** `test-quality-audit` owns test quality in these same files; this extension is the **security lens**, not a general code review. Findings here should focus on security-relevant patterns, not style, complexity, or non-security bugs.

## Smell codes

### `dns.HC-1` — Secret material in `appsettings*.json` / `.csproj` / `*.props`

**Relationship to core:** this code is the .NET-specific extension of core `DSO-HC-1` (secrets in source control). Core `DSO-HC-1` applies to any file; `dns.HC-1` adds .NET-file-specific patterns and places the finding under the `dotnet-security` extension's remediation flow. When both fire for the same file, cite `dns.HC-1` (more specific wins) and suppress the duplicate core finding.

**Pattern:** any of the following in a committed `.cs`, `.csproj`, `*.props`, `appsettings*.json`, or `local.settings.json` file:
- AWS access key shape (`AKIA[0-9A-Z]{16}`)
- Azure storage account key shape (`AccountKey=[A-Za-z0-9+/=]{88}`)
- GitHub PAT shape (`ghp_[A-Za-z0-9]{36}`)
- Slack token shape (`xox[baprs]-[A-Za-z0-9-]+`)
- Generic bearer token shape (long base64, > 20 chars, assigned to a key named `*Token*` / `*Secret*` / `*Password*`)
- Blizzard OAuth client secret shape (hex or mixed-case, assigned to `Blizzard__ClientSecret`)
- `Cosmos__Endpoint` or similar concatenated with `;AccountKey=`
- Any private key header (`-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----`)

**Detection (per-pattern ripgrep):**
```
rg -nE 'AKIA[0-9A-Z]{16}' <path>
rg -nE 'AccountKey=[A-Za-z0-9+/=]{88}' <path>
rg -nE 'ghp_[A-Za-z0-9]{36}' <path>
rg -nE 'xox[baprs]-[A-Za-z0-9-]+' <path>
rg -nE 'Blizzard__ClientSecret\s*[:=]\s*["''][^"'']+' <path>
rg -nE '^-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----' <path>
```

Any real-shape credential in a committed file is a smell — **including** placeholder values shaped like real credentials in `.env.example` or `appsettings.Example.json`.

**Severity:** `block`

**Rubric:** devsecops.md §5.1.1; CICD-SEC-6.

**Remediation action:**
> Rotate the credential immediately (assume public compromise). Move to Key Vault. Reference in `appsettings.json` via the App Service / Functions Key Vault reference syntax: either `@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/<name>/)` or the equivalent `@Microsoft.KeyVault(VaultName=<vault>;SecretName=<name>;SecretVersion=<optional>)`. Or prefer managed identity directly for Azure SDK clients. Add a pre-commit secret-scan hook. See https://learn.microsoft.com/azure/app-service/app-service-key-vault-references.

### `dns.HC-2` — `[AllowAnonymous]` on a non-public endpoint

**Pattern:** a `[AllowAnonymous]` attribute on a controller action, minimal-API endpoint, or HTTP-triggered function that is not in a documented public allow-list.

**Detection:** grep for `[AllowAnonymous]` in `api/` and `app/`, then cross-reference against an allow-list (or against `SECURITY.md` if one documents public endpoints).

**Severity:** `warn` (because false positives are common — not every `[AllowAnonymous]` is wrong)

**Rubric:** devsecops.md §5.1.10 (disclosure surface); §6.4 (BOLA-adjacent).

**Remediation action:**
> Verify the endpoint is intentionally public. If yes, add a comment linking to the design decision. If no, replace with `[Authorize]` and the appropriate scope / role check.

### `dns.HC-3` — Missing `[Authorize]` / `AuthorizationLevel.Function` on non-public endpoint

**Pattern:** an HTTP-triggered Azure Function without `AuthorizationLevel.Function` or higher (`AuthorizationLevel.Admin`), or a minimal-API endpoint mapped without a `RequireAuthorization()` call.

**Detection:**
```
[HttpTrigger\(.*?AuthorizationLevel\.Anonymous
```
Plus: grep for `MapGet` / `MapPost` / `MapPut` / `MapDelete` in `app/` / `api/` that are not followed by `.RequireAuthorization()`.

**Severity:** `block`

**Rubric:** devsecops.md §5.1.10; §6.3 (shadow APIs); §6.4 (BOLA).

**Remediation action:**
> For Functions: set `AuthorizationLevel.Function` (or `Admin` for ops endpoints). For minimal API: chain `.RequireAuthorization("policy-name")` with a specific policy that asserts per-object authz, not just "logged in."

### `dns.HC-4` — `AllowAnyOrigin()` with `AllowCredentials()`

**Pattern:** a CORS configuration that combines `.AllowAnyOrigin()` with `.AllowCredentials()`. The browser rejects this combination, so it's both broken **and** a security smell (nobody thought about it).

**Detection (ripgrep):**
```
AllowAnyOrigin\(\)[\s\S]*?AllowCredentials\(\)
```
Or the reverse order.

**Severity:** `block`

**Rubric:** devsecops.md §5.1.20.

**Remediation action:**
> Replace `.AllowAnyOrigin()` with `.WithOrigins(<explicit list>)`. The origins should come from the `Cors__AllowedOrigins__0` config, not be hardcoded.

### `dns.HC-5` — Missing security headers middleware

**Pattern:** `Program.cs` or `Startup.cs` has no middleware setting the headers that ASP.NET Core does **not** ship out-of-the-box: `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`. (Note: `UseHsts()` is built-in, and ASP.NET Core's Antiforgery middleware emits `X-Frame-Options: SAMEORIGIN` on responses that set antiforgery cookies — so `XFO` is partially covered automatically. Blazor Web App also auto-emits `Content-Security-Policy: frame-ancestors 'self'`, tunable via `ContentSecurityFrameAncestorsPolicy`.) Detection should focus on the gaps, not duplicate what the framework already does.

**Detection:** read `Program.cs` / `Startup.cs` and check for any of: explicit `Content-Security-Policy` header, `Referrer-Policy` header, `Permissions-Policy` header, or a hand-rolled `app.Use(async ctx => { ctx.Response.Headers["..."] = ...; await next(); })`. A third-party middleware library (e.g. `NetEscapades.AspNetCore.SecurityHeaders`) also counts — Microsoft does not endorse a specific library by name, so any reasonable implementation is acceptable.

**Severity:** `warn` (because the skill can't know the app's threat model without context)

**Rubric:** devsecops.md §5.1.16; ASVS V14.

**Remediation action:**
> Add explicit middleware for CSP, Referrer-Policy, and Permissions-Policy. Verify `UseHsts()` is present (built-in). For Blazor WASM, headers must be set by the host (SWA `staticwebapp.config.json` or Functions middleware). For Blazor Server / Blazor Web App, headers go in `Program.cs`; note the framework already sets `frame-ancestors` and antiforgery handles XFO — don't override these unless you have a reason.

### `dns.HC-6` — Connection string via string concatenation

**Pattern:** a connection-string construction like `"AccountEndpoint=" + endpoint + ";AccountKey=" + key` rather than using a typed builder or config sections.

**Detection (ripgrep):**
```
"AccountEndpoint=".*\+.*"AccountKey="
```
Similar for SQL: `"Server=".*\+.*"Password="`.

**Severity:** `warn`

**Rubric:** devsecops.md §5.1.1 (ties into secret handling).

**Remediation action:**
> Use the SDK's credential-based client construction (managed identity preferred). Where a typed builder is applicable: `SqlConnectionStringBuilder` (SQL), `DbConnectionStringBuilder` (generic ADO.NET). Cosmos / Blob / Service Bus do **not** expose a `ConnectionStringBuilder` — use `CosmosClientBuilder`, `BlobClientOptions`, `ServiceBusClientOptions` with a `TokenCredential`. Never concatenate secrets into strings that may end up in logs.

### `dns.HC-7` — Cosmos / Blob / Service Bus client with shared key

**Pattern:** `new CosmosClient(connectionString)` or `new BlobServiceClient(connectionString)` where a `TokenCredential`-based constructor is available and managed identity is feasible.

**Detection (ripgrep):**
```
new\s+CosmosClient\s*\(\s*.*ConnectionString
new\s+BlobServiceClient\s*\(\s*.*ConnectionString
new\s+ServiceBusClient\s*\(\s*.*ConnectionString
```

**Severity:** `warn`

**Rubric:** devsecops.md §5.3.2 (positive is OIDC / MI); §5.1.7.

**Remediation action:**
> Replace with a `TokenCredential`-based client. In **production**, prefer a deterministic credential: `new CosmosClient(endpoint, new ManagedIdentityCredential(clientId: "<uami-client-id>"))`. Microsoft's current guidance deprecates `DefaultAzureCredential` for production use because its credential chain can silently pick the wrong identity when multiple are available — use it only in dev/local. If `DefaultAzureCredential` is used anywhere, set `ManagedIdentityClientId` or `ManagedIdentityResourceId` explicitly via `DefaultAzureCredentialOptions`. Grant the identity the appropriate data-plane role (e.g. `Cosmos DB Built-in Data Contributor`). See https://learn.microsoft.com/dotnet/azure/sdk/authentication/best-practices#use-deterministic-credentials-in-production-environments.

### `dns.HC-8` — Authz denial log missing security-relevant fields

**Pattern:** a log statement on an authz denial path that omits actor identity, resource ID, decision, and trace ID. Specifically: `_logger.LogWarning("Access denied")` with no structured fields.

**Detection:** grep for `_logger.(LogWarning|LogError).*denied` and inspect arguments.

**Severity:** `warn`

**Rubric:** devsecops.md §6.6; CICD-SEC-10.

**Remediation action:**
> Log structured fields: `_logger.LogWarning("Access denied for user {UserId} on resource {ResourceId}: {Decision} (trace {TraceId})", userId, resourceId, decision, Activity.Current?.TraceId)`.

### `dns.HC-9` — Antiforgery not applied to state-changing endpoints

**Pattern:** Razor Pages / MVC controllers that handle POST / PUT / DELETE without `[AutoValidateAntiforgeryToken]` at the application/controller level or `[ValidateAntiForgeryToken]` per action. Applies to server-rendered forms; not required for pure JSON APIs that never accept browser-submitted form posts. See https://learn.microsoft.com/aspnet/core/security/anti-request-forgery.

**Detection (ripgrep):**
```
\[HttpPost\]|\[HttpPut\]|\[HttpDelete\]
```
Then check whether the declaring type / assembly has `AddControllersWithViews()` + `AddRazorPages()` (i.e. server-rendered) and whether `[AutoValidateAntiforgeryToken]` is configured globally.

**Severity:** `warn`

**Remediation action:**
> Register globally: `services.AddControllers(options => options.Filters.Add&lt;AutoValidateAntiforgeryTokenAttribute&gt;())`. Or decorate controllers with `[AutoValidateAntiforgeryToken]`. Or per-action with `[ValidateAntiForgeryToken]`.

### `dns.HC-10` — `System.Random` used for security-sensitive values

**Pattern:** `new Random()` or `Random.Shared` used to generate tokens, IDs, nonces, password-reset values, CSRF tokens, session IDs, or anything consumed by an authentication / authorization path. `System.Random` is not cryptographically secure. Microsoft analyzer rule CA5394 already tracks this — turning it on as a build error is the simplest remediation. See https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca5394.

**Detection (ripgrep):**
```
new\s+Random\s*\(
Random\.Shared
```
Cross-reference with security-adjacent variable names (`token`, `nonce`, `secret`, `csrf`, `sessionId`, `resetCode`).

**Severity:** `block` when confirmed security use; `warn` otherwise.

**Remediation action:**
> Use `System.Security.Cryptography.RandomNumberGenerator.GetBytes(span)` or `GetInt32(fromInclusive, toExclusive)`. Enable CA5394 as an error in `.editorconfig`.

### `dns.HC-11` — SQL injection via `CommandText` concatenation

**Pattern:** `SqlCommand.CommandText = "SELECT ... " + userInput` or interpolation `$"SELECT ... {userInput}"` instead of parameterized queries. Microsoft analyzer CA2100 covers this. See https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca2100.

**Detection (ripgrep):**
```
CommandText\s*=\s*\$?"[^"]*"\s*\+
new\s+SqlCommand\s*\(\s*\$"
```

**Severity:** `block`

**Remediation action:**
> Use `SqlParameter` (or the equivalent on your driver): `cmd.CommandText = "SELECT ... WHERE id = @id"; cmd.Parameters.AddWithValue("@id", id)`. For Dapper / EF Core, use parameterized APIs — never `FromSqlRaw($"...{input}...")`.

### `dns.HC-12` — `BinaryFormatter` usage

**Pattern:** any reference to `System.Runtime.Serialization.Formatters.Binary.BinaryFormatter`. Known-vulnerable by design; obsolete since .NET 5, made unusable in .NET 9 (throws `PlatformNotSupportedException` at runtime). See https://learn.microsoft.com/dotnet/core/compatibility/serialization/9.0/binaryformatter-removal.

**Detection (ripgrep):**
```
BinaryFormatter
```

**Severity:** `block`

**Remediation action:**
> Migrate to `System.Text.Json` for general data, or `DataContractSerializer` / MessagePack for typed contracts. See the migration guide: https://learn.microsoft.com/dotnet/standard/serialization/binaryformatter-migration-guide/.

### `dns.HC-13` — Data Protection keys not persisted to a durable store

**Pattern:** `AddDataProtection()` call with no `PersistKeysToAzureBlobStorage(...)` and no `ProtectKeysWithAzureKeyVault(...)` (or their file-system / Redis equivalents). Without persistence, keys regenerate on every deploy and in every replica, breaking auth cookies and antiforgery tokens across a multi-instance app. See https://learn.microsoft.com/aspnet/core/security/data-protection/configuration/overview.

**Detection (ripgrep):**
```
AddDataProtection\(
```
Then check whether the chain contains `PersistKeysTo...` and `ProtectKeysWith...`.

**Severity:** `warn` (single-instance dev) / `block` (multi-instance production confirmed)

**Remediation action:**
> `services.AddDataProtection().PersistKeysToAzureBlobStorage(blobClient).ProtectKeysWithAzureKeyVault(keyIdentifier, credential);` using the `Azure.Extensions.AspNetCore.DataProtection.Blobs` + `...DataProtection.Keys` packages.

### `dns.HC-14` — `DefaultAzureCredential` used without explicit managed identity

**Pattern:** `new DefaultAzureCredential()` with no `DefaultAzureCredentialOptions.ManagedIdentityClientId` or `ManagedIdentityResourceId` set. In production environments with multiple identities (user-assigned + system-assigned + environment variables), the credential chain may silently pick the wrong one — auth failures appear as permission errors, not identity selection errors. See https://learn.microsoft.com/dotnet/azure/sdk/authentication/best-practices#use-deterministic-credentials-in-production-environments.

**Detection (ripgrep):**
```
new\s+DefaultAzureCredential\s*\(\s*\)
```
Then check whether the call is wrapped with options setting `ManagedIdentityClientId` / `ManagedIdentityResourceId`.

**Severity:** `warn`

**Remediation action:**
> Production: replace with `new ManagedIdentityCredential(clientId: "<uami-client-id>")`. Dev: keep `DefaultAzureCredential` but pass `new DefaultAzureCredentialOptions { ManagedIdentityClientId = "<id>" }`.

### `dns.LC-1` — Shadow / zombie function endpoint

**Pattern:** a `[Function]` or `[HttpTrigger]` handler registered in `api/Functions/` whose route does not appear in any OpenAPI / route inventory document.

**Detection:** enumerate `[HttpTrigger(...)]` route values in `api/Functions/*.cs`, cross-reference against any OpenAPI document or routing manifest. Unreferenced routes are candidate zombies.

**Severity:** `warn`

**Rubric:** devsecops.md §6.3; API9:2023.

**Remediation action:**
> Either document the endpoint in the OpenAPI / route inventory, or delete the handler if it's dead.

### `dns.LC-2` — Mass assignment / BOPLA risk

**Pattern:** a request-body DTO whose properties are a superset of the documented OpenAPI schema. Specifically: a property on the class that has no counterpart in the schema, and the class is used as a parameter on an HTTP-triggered function or API controller.

**Detection:** for each `[FromBody]` model, compare `public` settable properties against the OpenAPI definition (if present). Fields only in the model are candidates.

**Severity:** `warn`

**Rubric:** devsecops.md §6.5; API3:2023.

**Remediation action:**
> Either add the missing fields to the OpenAPI schema (if intentional) or add `[JsonIgnore]` / make the property `init`-only / remove the setter to prevent mass-assignment. Prefer explicit input DTOs that carry only the documented fields.

### `dns.LC-3` — `new HttpClient(...)` without `IHttpClientFactory`

**Pattern:** direct instantiation of `HttpClient` held as a static or singleton, bypassing `IHttpClientFactory` and without `SocketsHttpHandler.PooledConnectionLifetime` configured. Causes socket exhaustion (short-lived) or stale-DNS (long-lived). Security-adjacent: stale DNS can route to a decommissioned endpoint the attacker now controls. See https://learn.microsoft.com/dotnet/fundamentals/networking/http/httpclient-guidelines.

**Detection (ripgrep):**
```
new\s+HttpClient\s*\(
```
Cross-reference against `IHttpClientFactory` / `AddHttpClient` usage in the same project.

**Severity:** `warn`

**Remediation action:**
> Register `services.AddHttpClient&lt;TClient&gt;(...)` and inject `IHttpClientFactory` (or the typed client). If a singleton is unavoidable, configure `SocketsHttpHandler { PooledConnectionLifetime = TimeSpan.FromMinutes(2) }`.

### `dns.LC-4` — PII destructured into structured logs

**Pattern:** a log template using the `@` destructuring operator on an object that contains PII (user, account, profile). `_logger.LogInformation("Request from {@User}", user)` serializes the whole object — including `Email`, `PhoneNumber`, `Address` — into log sinks that may have weaker access controls than the app DB.

**Detection (ripgrep):**
```
Log(Information|Debug|Trace|Warning|Error).*\{@(user|account|profile|customer|claims)\}
```

**Severity:** `warn`

**Remediation action:**
> Log scalar IDs only (`{UserId}`), not whole objects. Or define an explicit log-safe projection (`LogInfo`-style record) and destructure that instead.

### `dns.LC-5` — Hardcoded PFX path / password for certificate loading

**Pattern:** `new X509Certificate2("<path>", "<password>")` where path and password are string literals. Should come from Key Vault certificates + managed identity, not from the file system.

**Detection (ripgrep):**
```
new\s+X509Certificate2\s*\(\s*"[^"]+\.pfx"\s*,\s*"
```

**Severity:** `warn`

**Remediation action:**
> Store the cert in Key Vault, load via `CertificateClient(new Uri(vault), new ManagedIdentityCredential())` and the certificate's secret ID. No PFX on disk, no password in code.

## Positive signals

### `dns.POS-1` — Production-grade managed identity client construction

**Pattern:** Azure SDK clients instantiated with a deterministic `TokenCredential` — `ManagedIdentityCredential` with an explicit `clientId` / `resourceId`, or `DefaultAzureCredential` with `DefaultAzureCredentialOptions.ManagedIdentityClientId` set. Bare `new DefaultAzureCredential()` does **not** count (see `dns.HC-14`).

### `dns.POS-2` — Key Vault reference resolution

**Pattern:** app settings resolved via `@Microsoft.KeyVault(SecretUri=...)` or via `AddAzureKeyVault(...)` in config builder.

### `dns.POS-3` — Explicit security headers middleware

**Pattern:** `Program.cs` or `Startup.cs` with explicit CSP / HSTS / XFO / Referrer-Policy configuration.

### `dns.POS-4` — `[Authorize(Roles=...)]` with specific role checks

**Pattern:** `[Authorize]` attributes that name specific roles or policies, not bare `[Authorize]` (which only asserts "logged in").

### `dns.POS-5` — OpenAPI-driven request models

**Pattern:** request DTOs generated from an OpenAPI source-of-truth, or validated against the schema at runtime via a library.

## Carve-outs

- **Do not flag `dns.HC-1` on files matching `*.Example.*`** — example files are expected to contain placeholder credentials. Still flag if the placeholder shape matches a real credential format exactly (that's `DSO-HC-1` under a different lens).
- **Do not flag `dns.HC-2` on endpoints explicitly listed in `SECURITY.md`** as public.
- **Do not flag `dns.HC-3` on Static Web Apps routes** — SWA handles auth at the edge via `staticwebapp.config.json` (the legacy `routes.json` is ignored when `staticwebapp.config.json` exists), not via `[Authorize]`. See https://learn.microsoft.com/azure/static-web-apps/configuration.
- **Do not flag `dns.HC-5` on Blazor WASM projects** — the host (SWA / Functions) is responsible for headers, not the WASM client. For Blazor **Server** / **Web App**, the framework auto-emits `Content-Security-Policy: frame-ancestors 'self'` and Antiforgery emits `X-Frame-Options: SAMEORIGIN`; do not double-flag those specific headers as missing.
