---
name: api-design
description: Use when building, extracting, reviewing, or looking up modern HTTP APIs — endpoints, services, API surfaces, or backend features. Applies the bundled reference at souroldgeezer-design/docs/api-reference/api-design.md, enforcing OpenAPI™ 3.1, RFC 9457 problem+json, explicit versioning, conditional requests, security, reliability, observability, and verification-layer disclosure. Supports composable extensions for Azure® Functions™ .NET, Node.js® hosted/serverless APIs, hosted Next.js™, Azure® Cosmos DB™, and Azure® Blob Storage.
---

# API Design

## Contract

Own Build, Extract, Review, and Lookup for HTTP API contracts, endpoints,
service surfaces, API runtime reliability, data-service API patterns, API
observability, and verification-layer disclosure. Use
[../../docs/api-reference/api-design.md](../../docs/api-reference/api-design.md)
as the core reference; this file is the router.

Delegate general code/module design, frontend app work, infrastructure topology,
ArchiMate packages, pipeline/security posture, and test quality to
`software-design`, `app-design`, `infra-design`, `architecture-design`,
`devsecops-audit`, and `test-quality-audit`.

Inputs: user request, files/diffs/proposals, consumer/auth/runtime/data context,
provided evidence, and optional paired architecture package at
`docs/architecture/<feature>.dediren/`. Do not infer runtime SLIs, load behavior,
security-tool results, or cloud-control-plane facts from static source. If a
default would be unsafe, ask; otherwise continue with disclosed defaults.

Modes: Build, Extract, Review, Lookup.

## Load Map

Load what applies:

- Core reference sections 2-7 for Build/Extract/Review; matched section plus
  immediate context for Lookup.
- [references/procedures/preflight.md](references/procedures/preflight.md) for
  Build, Extract, and Review.
- [references/procedures/project-assimilation.md](references/procedures/project-assimilation.md)
  when existing source, OpenAPI, auth, errors, observability, IaC, data clients,
  or runtime wiring are in scope.
- [references/procedures/architecture-pairing.md](references/procedures/architecture-pairing.md)
  when a paired `docs/architecture/<feature>.dediren/` package exists or the
  user asks to update architecture after API work.
- [references/procedures/red-flags.md](references/procedures/red-flags.md)
  before final output in Build and Review.
- [extensions/azure-functions-dotnet.md](extensions/azure-functions-dotnet.md)
  for Azure Functions .NET isolated-worker or ASP.NET Core integration signals.
- [extensions/nodejs.md](extensions/nodejs.md) for Node.js / TypeScript hosted
  or serverless HTTP API signals.
- [extensions/nextjs.md](extensions/nextjs.md) for hosted Next.js API surfaces;
  apply it after the Node.js / TypeScript extension.
- [extensions/azure-cosmosdb.md](extensions/azure-cosmosdb.md) for Azure Cosmos
  DB API/data-client/IaC signals.
- [extensions/azure-blob-storage.md](extensions/azure-blob-storage.md) for Azure
  Blob Storage API/object-store/IaC signals.
- [extensions/README.md](extensions/README.md) only when editing extensions.

Multiple extensions compose. Unknown stacks use the core reference only; do not
invent unsupported runtime mechanics.

## Ask Vs Continue

Continue with disclosed defaults when inputs are missing and the default is
safe. Ask the user when scope is ambiguous, multiple architecture packages
match, security/cost/destructive impact is unclear, or sibling-skill ownership
would dominate the requested work. Do not guess runtime/load/security results
from static source.

Before changing trigger metadata, workflow behavior, extension selection,
source grounding, or evaluation coverage, read `references/evals` and
`references/source-grounding.md`. Keep evals synthetic or originally
paraphrased.

## Workflow

1. Select mode, scope, consumer surface, and verification question.
2. Prefer `rg`; inspect source-readable API boundaries, manifests, OpenAPI,
   auth/error/versioning/observability signals, data/storage clients, IaC, and
   the paired architecture package path when relevant.
3. Load and announce the selected procedures and extensions.
4. Apply project assimilation before deciding whether to reuse, flag, migrate,
   or ignore existing infrastructure.
5. Separate fact from inference, choose the smallest compliant move, include
   available verification, then emit the mode contract/footer.

## Mode Outputs

- Build: OpenAPI/API contract shape, endpoint behavior, error/auth/versioning,
  reliability, observability, extension decisions, validation, delegations.
- Extract: route surface, contract presence, auth/error/version/runtime/data
  baseline, legacy debt, next smallest migration move.
- Review: findings only; each finding names code, bucket, layer, severity,
  evidence, action, and reference/extension citation.
- Lookup: direct rule, exception, citation, verification layer, one-line footer.

Every answer reports mode, extensions loaded, core reference path, procedures
loaded, evidence layers (`static`, `iac`, `contract`, `runtime`,
`security-tool`, `load`, `human`), project assimilation, architecture pairing,
delegations, and limits. If no findings, say so with verification limits.

## Stop Conditions

Stop when source/scope is missing, sibling ownership dominates, unsupported
runtime mechanics are required, required non-static evidence is absent, legacy
debt is load-bearing and outside scope, a static/contract/IaC red flag remains,
or output would copy a broken API/security/reliability pattern.
