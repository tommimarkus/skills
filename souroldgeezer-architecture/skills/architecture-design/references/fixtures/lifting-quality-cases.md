# Lifting quality cases

Representative snippets for validating architecture-design Extract behavior after procedure edits.

## Bicep security lifting

- System-assigned Function App identity plus Cosmos `disableLocalAuth: true` and Cosmos SQL role assignment Contributor GUID.
  - Expected: Managed Identity Technology Service, Composition from Function App Node, Access `ReadWrite` to Cosmos, no `AD-18`.
- User-assigned identity resource referenced by Function App plus Storage `allowSharedKeyAccess: false` and role assignment to Blob Data Contributor.
  - Expected: Managed Identity Node / Technology Service, Assignment to Function App, Access `ReadWrite` to Storage, no `AD-18`.
- Diagnostic setting with `workspaceId`.
  - Expected: Flow from source resource Node to Log Analytics Node.
- Key Vault reference app setting.
  - Expected: Access from consuming identity to Key Vault Secret Artifact.
- Private endpoint with `publicNetworkAccess: 'Disabled'`.
  - Expected: Communication Network / Path elements between consumer and protected resource.

## Deployment topology lifting

- Single deploy workflow with no `environment:` and production IaC tag.
  - Expected: one Production Plateau, no fabricated Development or Staging Plateau.
- Deploy workflow with matrix environments `dev`, `staging`, `prod`.
  - Expected: three sibling Plateaus, one Work Package Realization to each, no Plateau-to-Plateau Triggering.
- Architect-authored Build request "migrate from baseline monolith to target serverless".
  - Expected: true Migration pattern may use Baseline / Target Plateaus, Gaps, and Triggering.

## Forward-only seed views

- Extract emits Strategy Capability stubs and Business Service stubs.
  - Expected: FORWARD-ONLY Capability Map seed view.
- Extract emits Driver / Goal / Requirement stubs.
  - Expected: FORWARD-ONLY Motivation seed view.

## External trust boundaries

- `.csproj` internal Components plus `AddHttpClient` with third-party base address.
  - Expected: `{Project} (internal)` Grouping and `{Provider} (external)` Grouping; external Component nested in the external Grouping; no `AD-21`.
- CSP `connect-src` / `img-src` allowlist names a third-party domain.
  - Expected: external Application Component assigned to provider Grouping.
