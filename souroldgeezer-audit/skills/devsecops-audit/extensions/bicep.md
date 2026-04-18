# Extension — Bicep (Azure IaC)

**Applies to:** `infra/**/*.bicep`, `infra/**/*.bicepparam`, `main.bicep`, any `.bicep` file in the repo.

**Detection signals:**

- Path matches `**/*.bicep` or `**/*.bicepparam`.
- Any file whose first non-comment line contains `targetScope`, `resource`, `module`, `param`, `var`, or `output`.

**Applies to rubric sections:** §3 (Deploy stage), §5.1 items 1, 17, 19, §5.3 items 2, 4, and the WAF pillars from `CLAUDE.md` § "Infrastructure Development".

## Cost banding

This extension splits smells into two bands:

- **Band 1 — always-block.** Remediation is free or near-free. Fires under all cost stances.
- **Band 2 — cost-gated.** Remediation requires a paid Azure SKU. Fires only when the resolved cost stance is `full` or `mixed` with the specific code enabled.

The cost-stance resolver is `../references/procedures/cost-stance-detection.md`.

## Band 1 — always-block

### `bicep.HC-1` — Shared keys / connection strings instead of managed identity

**Pattern:** a `listKeys(...)` call, a `connectionString` property, or `accountKey` / `primaryKey` / `masterKey` in a module output or resource property where a managed identity is feasible (Cosmos, Storage, Service Bus, Key Vault, Event Grid, App Configuration, SignalR).

**Detection (ripgrep):**
```
listKeys\(|connectionString\s*:|accountKey\s*:|primaryKey\s*:|masterKey\s*:
```

**Severity:** `block`

**Remediation action:**
> Replace with a system-assigned or user-assigned managed identity. Grant the caller role-based access (e.g. `Cosmos DB Built-in Data Contributor`, `Storage Blob Data Contributor`). Remove the key-based path entirely.

### `bicep.HC-2` — TLS < 1.2

**Pattern:** a minimum-TLS property set below 1.2, or the property missing on a resource type that supports it. Property name and value space differ by resource type:

- **Storage** (`Microsoft.Storage/storageAccounts`): `minimumTlsVersion` with `'TLS1_0'` / `'TLS1_1'` / `'TLS1_2'` / `'TLS1_3'`.
- **App Service** (`Microsoft.Web/sites` → `siteConfig.minTlsVersion`): `'1.0'` / `'1.1'` / `'1.2'` / `'1.3'`.
- **SQL** (`Microsoft.Sql/servers`): `minimalTlsVersion` with `'1.0'` / `'1.1'` / `'1.2'` / `'1.3'`.
- **Cosmos DB** (`Microsoft.DocumentDB/databaseAccounts`): `minimalTlsVersion` with `'Tls'` / `'Tls11'` / `'Tls12'` (three-tier enum — no 1.3 option yet).
- **Key Vault**: no TLS-version property (service-level TLS ≥ 1.2 only).

**Detection (ripgrep, union of spellings; anchor values with quotes to avoid matching unrelated `1.0` / `1.1` fragments):**
```
(minimumTlsVersion|minTlsVersion|minimalTlsVersion)\s*:\s*['"](TLS1_0|TLS1_1|1\.0|1\.1|Tls|Tls11)['"]
```
Also flag resources of the supported types that omit the property entirely.

**Severity:** `block`

**Remediation action:**
> Storage / App Service / SQL: prefer TLS 1.3 where downstream clients tolerate it, otherwise TLS 1.2. Cosmos DB: `minimalTlsVersion: 'Tls12'` (1.3 not yet exposed). Verify downstream clients before merging.

### `bicep.HC-3` — Local auth enabled

**Pattern:** any of:
- Cosmos: `disableLocalAuth` absent or `false`
- Storage: `allowSharedKeyAccess: true` or absent
- Service Bus: `disableLocalAuth: false`
- Event Grid: `disableLocalAuth: false`
- App Configuration: `disableLocalAuth: false`

**Detection (ripgrep, per resource type):**
```
allowSharedKeyAccess\s*:\s*true
disableLocalAuth\s*:\s*false
```

**Severity:** `block`

**Remediation action:**
> Set the local-auth-disable flag to the restrictive value. Grant the caller an appropriate RBAC role. Verify no other consumer of the resource still uses shared-key auth.

### `bicep.HC-4` — FTP / basic auth on App Service

**Pattern:** an `Microsoft.Web/sites` resource without `siteConfig.ftpsState: 'Disabled'` or without `basicPublishingCredentialsPolicies` disabled.

**Detection:** walk the module for `Microsoft.Web/sites` and verify the block contains `ftpsState: 'Disabled'` and a sibling resource of type `Microsoft.Web/sites/basicPublishingCredentialsPolicies` with `allow: false`.

**Severity:** `block`

**Remediation action:**
> Disable FTP and basic publishing credentials. Deployment should go through OIDC-federated Run From Package or ZIP deploy with RBAC.

### `bicep.HC-5` — Secrets in params instead of Key Vault references

**Pattern:** a `param` declared as `@secure() param <name> string` that is used as a direct value in a resource property, without a Key Vault reference wrapper.

**Detection:** grep for `@secure()` in params, then cross-reference the usage site. If the value is passed directly to `appSettings` or `connectionStrings` without a `Microsoft.KeyVault(...)` reference form, it's a smell.

**Severity:** `block`

**Remediation action:**
> Move the secret to Key Vault. Reference it from Bicep via `@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/<secret>/)` in the target resource's settings block.

### `bicep.HC-6` — Missing `CanNotDelete` lock on stateful resources

**Pattern:** a module creating Cosmos DB account, Storage account, Key Vault, SQL server, or any stateful resource, without a corresponding `Microsoft.Authorization/locks` sub-resource with `level: 'CanNotDelete'`.

**Detection:** for each stateful resource type, check whether a locks sub-resource exists in the same module.

**Severity:** `block`

**Remediation action:**
> Add a `Microsoft.Authorization/locks` resource scoped to the stateful resource with `level: 'CanNotDelete'`. Required by CLAUDE.md § Infrastructure Development / Reliability pillar.

### `bicep.HC-7` — Soft delete / purge protection disabled

**Pattern:**
- **Key Vault:** `enablePurgeProtection` missing or `false`; `softDeleteRetentionInDays` < 7. Note that soft delete itself has been on-by-default and irrevocable since 2020 — **setting `enableSoftDelete: false` will fail deployment**, so any such literal in IaC is a latent deploy break, not a runtime risk.
- **Storage:** `deleteRetentionPolicy.enabled: false` (or missing) on blob services; `containerDeleteRetentionPolicy.enabled: false`.
- **Cosmos DB:** no `backupPolicy` configured, or a `Periodic` policy without a suitable retention.

**Detection (per resource type):**
```
enableSoftDelete\s*:\s*false
enablePurgeProtection\s*:\s*false
softDeleteRetentionInDays\s*:\s*[0-6]\b
deleteRetentionPolicy[\s\S]*?enabled\s*:\s*false
```

**Severity:** `block`

**Rubric note:** Key Vault soft-delete-disable is not suppressible — call it out as a deploy break when seen. References: https://learn.microsoft.com/azure/key-vault/general/soft-delete-overview.

**Remediation action:**
> Key Vault: set `enablePurgeProtection: true` and `softDeleteRetentionInDays: 90`. Remove any `enableSoftDelete: false` literal. Storage: enable blob soft delete with ≥ 7-day retention. Cosmos: configure continuous backup.

### `bicep.HC-8` — Diagnostic settings missing

**Pattern:** any resource that supports `Microsoft.Insights/diagnosticSettings` without one configured. Relevant for Cosmos, Storage, Key Vault, App Service, Functions, Application Gateway, Front Door.

**Detection:** for each resource of a type that supports diagnostic settings, check whether a same-scope `Microsoft.Insights/diagnosticSettings` sub-resource exists.

**Severity:** `block`

**Rubric note:** CLAUDE.md § Cost Guidance explicitly grants the free 5 GB/month LAW ingestion — this remediation is free within the declared budget.

**Remediation action:**
> Add a `Microsoft.Insights/diagnosticSettings` resource targeting the existing Log Analytics workspace. For logs, use `categoryGroup: 'AllLogs'` (or `'audit'` for audit-only). For metrics, use `metrics: [{ category: 'AllMetrics', enabled: true }]`. The category-group form is for logs only; metrics still use the per-category form. See https://learn.microsoft.com/azure/azure-monitor/essentials/diagnostic-settings.

### `bicep.HC-9` — Hardcoded names / regions / domains

**Pattern:** a string literal in a module that is (a) a resource name (e.g. `'lfm-prod-cosmos'`), (b) a region (`'eastus'`, `'westeurope'`), (c) a domain (`'example.com'`), or (d) a numeric resource ID.

**Detection:** grep for resource-name patterns and region names in `.bicep` files, excluding `main.bicep` where the parent composition is allowed to pass them in.

**Severity:** `block`

**Remediation action:**
> Promote to a `param` with a `@description` and, where applicable, `@minLength` / `@maxLength`. Values come from `parameters.example.json` or `deploy-infra.yml` inline overrides (see CLAUDE.md § Workflow parameterization).

### `bicep.HC-10` — `http20Enabled: false` or client affinity on stateless APIs

**Pattern:** an `Microsoft.Web/sites` resource with `siteConfig.http20Enabled: false` or `clientAffinityEnabled: true` where the API is stateless (which, for Functions, is always).

**Detection (ripgrep):**
```
http20Enabled\s*:\s*false
clientAffinityEnabled\s*:\s*true
```

**Severity:** `block` (HTTP/2) / `warn` (affinity)

**Remediation action:**
> Set `http20Enabled: true` and `clientAffinityEnabled: false`. WAF Performance pillar per CLAUDE.md.

### `bicep.HC-11` — Param missing metadata

**Pattern:** a `param` declaration with no `@description`, or a string param that accepts a bounded length without `@minLength` / `@maxLength`, or a numeric param accepting a bounded range without `@minValue` / `@maxValue`.

**Detection:** parse `param` declarations and check for the decorator annotations on preceding lines.

**Severity:** `warn`

**Remediation action:**
> Add `@description('...')` for every param. Add length/value bounds where Azure enforces them. Required by CLAUDE.md § Operational Excellence pillar.

### `bicep.HC-12` — Key Vault still in access-policy mode

**Pattern:** a `Microsoft.KeyVault/vaults` resource without `properties.enableRbacAuthorization: true`. The default (access-policy mode) is legacy; RBAC mode is Microsoft's current recommendation because it centralizes authz through Azure RBAC, supports scoped role assignments, and integrates with conditional access.

**Detection (ripgrep):**
```
enableRbacAuthorization\s*:\s*false
```
Also flag any Key Vault where the property is absent. See https://learn.microsoft.com/azure/key-vault/general/rbac-guide.

**Severity:** `block`

**Remediation action:**
> Set `enableRbacAuthorization: true`. Replace `accessPolicies[]` entries with `Microsoft.Authorization/roleAssignments` granting `Key Vault Secrets User` / `Key Vault Crypto User` at vault scope.

### `bicep.HC-13` — Storage infrastructure encryption not required

**Pattern:** a `Microsoft.Storage/storageAccounts` resource without `properties.encryption.requireInfrastructureEncryption: true`. This enables a second layer of service-side encryption (FIPS 140-2 compliant) and cannot be toggled after creation. See https://learn.microsoft.com/azure/storage/common/infrastructure-encryption-enable.

**Detection:** for each storage account, check whether the `encryption` block sets `requireInfrastructureEncryption: true`.

**Severity:** `warn`

**Remediation action:**
> Add `encryption: { requireInfrastructureEncryption: true, services: { blob: { enabled: true }, file: { enabled: true } }, keySource: 'Microsoft.Storage' }` at creation. Cannot be retrofitted — requires a new account.

### `bicep.HC-14` — Storage public-access flags permissive

**Pattern:** a `Microsoft.Storage/storageAccounts` resource with any of:
- `allowBlobPublicAccess: true` (or absent — default is `true` on older API versions)
- `supportsHttpsTrafficOnly: false`
- `publicNetworkAccess: 'Enabled'` without an accompanying `networkAcls.defaultAction: 'Deny'` + explicit allow-list
- `minimumTlsVersion` missing (see `bicep.HC-2`)

**Detection (ripgrep):**
```
allowBlobPublicAccess\s*:\s*true
supportsHttpsTrafficOnly\s*:\s*false
```

**Severity:** `block`

**Remediation action:**
> Set `allowBlobPublicAccess: false`, `supportsHttpsTrafficOnly: true`, and either `publicNetworkAccess: 'Disabled'` (paired with a private endpoint — see `bicep.B2-2`) or `networkAcls: { defaultAction: 'Deny', ... }`.

### `bicep.HC-15` — Cosmos DB free tier on production account

**Pattern:** a `Microsoft.DocumentDB/databaseAccounts` resource with `properties.enableFreeTier: true` outside a dev/test environment (determined by module name, target environment param, or resource-group naming). Free tier is one-per-subscription and not intended for production; its unpredictable throughput caps cause latency regressions and its SLA is weaker. See https://learn.microsoft.com/azure/cosmos-db/free-tier.

**Detection (ripgrep):**
```
enableFreeTier\s*:\s*true
```

**Severity:** `warn` (block if the module is clearly for production — name contains `prod`, `production`, or the environment param is `prod`).

**Remediation action:**
> Set `enableFreeTier: false` for production accounts. Use a dedicated dev/test subscription or non-prod Cosmos account for the free tier.

## Band 2 — cost-gated

Each Band 2 code fires only when the resolved cost stance is `full`, or `mixed` with the specific code listed in `mixedEnabled`. Under `free`, the skill emits one `info` suppression line for this extension and does not evaluate these codes individually.

### `bicep.B2-1` — Defender for Cloud Standard tier absent

**Pattern:** no `Microsoft.Security/pricings` resource at subscription scope with `pricingTier: 'Standard'` for the relevant plans.

**Severity:** `warn` (block under `full` stance)

### `bicep.B2-2` — Private Link / private endpoints absent

**Pattern:** stateful resources (Cosmos, Storage, Key Vault) with `publicNetworkAccess: 'Enabled'` or no `Microsoft.Network/privateEndpoints` companion.

**Severity:** `warn`

### `bicep.B2-3` — Multi-region active-active absent

**Pattern:** single-region Cosmos DB (no `locations` array with ≥ 2 entries) or single-region Functions app.

**Severity:** `warn`

### `bicep.B2-4` — WAF on App Gateway / Front Door Premium absent

**Pattern:** no `Microsoft.Network/ApplicationGatewayWebApplicationFirewallPolicies`, or a `Microsoft.Cdn/profiles` fronting public endpoints whose `sku.name` is not `Premium_AzureFrontDoor`. Valid Front Door SKU names are `Standard_AzureFrontDoor`, `Premium_AzureFrontDoor`, and (legacy) `Classic_AzureFrontDoor`; Premium is the tier that includes managed WAF rulesets and DDoS protection. See https://learn.microsoft.com/azure/frontdoor/create-front-door-cli.

**Severity:** `warn`

### `bicep.B2-5` — HSM-backed / Premium Key Vault with CMK absent

**Pattern:** Key Vault with `sku.name: 'standard'` where customer-managed keys are required.

**Severity:** `warn`

### `bicep.B2-6` — Azure DDoS Protection Standard absent

**Pattern:** no `Microsoft.Network/ddosProtectionPlans` at the VNet.

**Severity:** `warn`

### `bicep.B2-7` — No Azure Policy assignments for guardrails

**Pattern:** the subscription / management-group deployment contains no `Microsoft.Authorization/policyAssignments` (built-in initiatives such as `Azure Security Benchmark`, `CIS Microsoft Azure Foundations Benchmark`, or a customer-defined initiative). Policy assignments are Microsoft's recommended mechanism for preventing regressions (deny-mode) and detecting drift (audit-mode). See https://learn.microsoft.com/azure/governance/policy/overview.

**Severity:** `warn`

### `bicep.B2-8` — No federated credential for workload identity

**Pattern:** a `Microsoft.ManagedIdentity/userAssignedIdentities` intended for CI/CD access to Azure with no `Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials` child configured for the GitHub / GitLab / AKS issuer. Federated workload identity is Microsoft's current recommendation over storing a client secret in the CI/CD system. See https://learn.microsoft.com/entra/workload-id/workload-identity-federation.

**Severity:** `warn`

## Positive signals

### `bicep.POS-1` — Managed identity usage

**Pattern:** resources with `identity: { type: 'SystemAssigned' }` or `type: 'UserAssigned'`, plus corresponding `Microsoft.Authorization/roleAssignments` granting RBAC.

### `bicep.POS-2` — Key Vault references in app settings

**Pattern:** `@Microsoft.KeyVault(SecretUri=...)` syntax used in `appSettings` / `connectionStrings`.

### `bicep.POS-3` — Key Vault hardened

**Pattern:** Key Vault with `enablePurgeProtection: true`, `enableRbacAuthorization: true`, and `softDeleteRetentionInDays: 90`. Soft delete itself is always-on and no longer a meaningful signal.

### `bicep.POS-4` — Diagnostic settings within free grant

**Pattern:** diagnostic settings targeting a Log Analytics workspace that has `dailyQuotaGb` set at or below the 5 GB free grant (5 or less).

### `bicep.POS-5` — Fully parameterized modules

**Pattern:** a module with zero hardcoded names, regions, or domains; all environment-specific values come through params.

## Carve-outs

- **Do not flag `bicep.HC-9` in `main.bicep`** for values passed as inline overrides in `deploy-infra.yml` — the composition root is allowed to receive hardcoded values from workflow variables per CLAUDE.md § Workflow parameterization.
- **Do not flag `bicep.HC-11` `@minLength` / `@maxLength` for params that accept free-form strings with no Azure-enforced bounds** (e.g. `@description`-style documentation strings).
- **Do not flag Band 2 codes when the resolved cost stance is `free`** — emit the single `info` suppression line instead.
