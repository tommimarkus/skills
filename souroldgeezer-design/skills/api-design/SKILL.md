---
name: api-design
description: Use when building, extracting, reviewing, or looking up modern HTTP APIs and client-facing API architecture — endpoint/service/API surfaces, data-access efficiency, portfolio cohesion, fragmentation, sprawl, consolidation, overlap, policy drift, or consumer chattiness. Applies the bundled reference at souroldgeezer-design/docs/api-reference/api-design.md, using strong defaults for OpenAPI™, RFC 9457 problem+json, versioning, conditional requests, security, reliability, and observability while respecting compatible project contracts. Supports composable extensions for Azure® Functions™ .NET, Node.js® hosted/serverless APIs, hosted Next.js™, Python® ASGI/WSGI and serverless APIs, Azure® Cosmos DB™, and Azure® Blob Storage™. Defer general code/module design to software-design, frontend/UI to app-design, infrastructure/IaC to infra-design, architecture models to architecture-design, and security and test quality to devsecops-audit and test-quality-audit.
---

# API Design

## Contract

Own Build, Extract, Review, and Lookup for HTTP API contracts, endpoints,
service surfaces, API runtime reliability, data-service API patterns, API
observability, and verification-layer disclosure. Use
[../../docs/api-reference/api-design.md](../../docs/api-reference/api-design.md)
as the core reference; this file is the router.

Keep one canonical HTTP contract per capability and consumer/trust/lifecycle
boundary unless a documented exception applies.

Delegate general code/module design, frontend app work, infrastructure topology,
ArchiMate packages, pipeline/security posture, and test quality to
`software-design`, `app-design`, `infra-design`, `architecture-design`,
`devsecops-audit`, and `test-quality-audit`.

Inputs: user request, files/diffs/proposals, consumer/auth/runtime/data context,
provided evidence, and optional paired architecture package at
`docs/architecture/<feature>.dediren/`. Do not infer runtime SLIs, load behavior,
security-tool results, or cloud-control-plane facts from static source. If a
default would be unsafe, ask; otherwise continue with disclosed defaults.

Modes: Build, Extract, Review, Lookup. Existing API with no requested change
defaults to Extract. New endpoint or feature defaults to Build.
Explicit Review/audit/check requests select Review, including lifetime questions.
Otherwise narrow principle/status-code/header questions default to Lookup. Infer
the useful route; ask only when a material missing decision affects safe work.

## Load Map

Load what applies:

- Before analyzing HTTP-to-storage paths in Build/Review or explicit debt Extract,
  read relevant [data efficiency](../../docs/design-reference/data-efficiency.md) sections.
  Factual Extract skips it; Lookup reads only the matched section.

- Relevant core reference sections for the decision in every mode. Expand
  inspection when dependencies, uncertainty, or material risk calls for it.
- [references/procedures/preflight.md](references/procedures/preflight.md) for
  Build, Extract, and Review.
- [references/procedures/project-assimilation.md](references/procedures/project-assimilation.md)
  when existing source, OpenAPI, auth, errors, observability, IaC, data clients,
  or runtime wiring are in scope. Factual Extract records facts and uncertainty;
  debt classification applies only to Review or explicit debt/compliance Extract.
- [references/procedures/architecture-pairing.md](references/procedures/architecture-pairing.md)
  (mechanics canonical in
  [../../docs/design-reference/architecture-pairing-core.md](../../docs/design-reference/architecture-pairing-core.md))
  when a paired `docs/architecture/<feature>.dediren/` package exists or the
  user asks to update architecture after API work.
- [references/procedures/surface-architecture.md](references/procedures/surface-architecture.md)
  when API surface architecture, overlap, consolidation, consumer journeys, or
  API portfolio decisions are in scope.
- [references/procedures/red-flags.md](references/procedures/red-flags.md)
  before final output in Build and Review.
- [extensions/azure-functions-dotnet.md](extensions/azure-functions-dotnet.md)
  for Azure Functions .NET isolated-worker or ASP.NET Core integration signals.
- [extensions/nodejs.md](extensions/nodejs.md) for Node.js / TypeScript hosted
  or serverless HTTP API signals.
- [extensions/nextjs.md](extensions/nextjs.md) for hosted Next.js API surfaces;
  compose it after Node.js as one base runtime surface.
- [extensions/azure-cosmosdb.md](extensions/azure-cosmosdb.md) for Azure Cosmos
  DB API/data-client/IaC signals.
- [extensions/azure-blob-storage.md](extensions/azure-blob-storage.md) for Azure
  Blob Storage API/object-store/IaC signals.
- [extensions/python.md](extensions/python.md) for Python ASGI, WSGI, and
  serverless HTTP API signals.
- [extensions/README.md](extensions/README.md) only when editing extensions.

| Stack | Build lane | Review lane |
|---|---|---|
| Azure Functions .NET | [build](extensions/azure-functions-dotnet/build.md) | [review](extensions/azure-functions-dotnet/review.md) |
| Node.js | [build](extensions/nodejs/build.md) | [review](extensions/nodejs/review.md) |
| Next.js | [build](extensions/nextjs/build.md) | [review](extensions/nextjs/review.md) |
| Azure Cosmos DB | [build](extensions/azure-cosmosdb/build.md) | [review](extensions/azure-cosmosdb/review.md) |
| Azure Blob Storage | [build](extensions/azure-blob-storage/build.md) | [review](extensions/azure-blob-storage/review.md) |
| Python ASGI / WSGI | [build](extensions/python/build.md) | [review](extensions/python/review.md) |

Detection identifies available guidance, not a mandatory reading set. Read the
relevant stack-core sections and Build or Review lane for the requested work;
consult the other lane only if its detail is needed for the same decision.
Factual Extract records behavior without unsolicited compliance judgments.
Lookup may combine multiple relevant stack excerpts without becoming a full
Build or Review. Node.js precedes Next.js when both mechanics are relevant.
Unknown stacks use applicable core guidance; do not invent runtime mechanics.
Extensions refine defaults and evidence requirements; compatible project
contracts may justify alternatives while preserving safety and protocol validity.

## Ask Vs Continue

Continue with safe defaults and compatible project contracts within existing
authority. Ask the user when a material product, security, cost, destructive, or pairing
decision cannot be inferred safely. Missing evidence limits the conclusion that
needs it; continue useful independent analysis. Do not guess runtime/load/security
results from static source.

Before changing trigger metadata, workflow behavior, extension selection,
source grounding, or evaluation coverage, read `references/evals` and
[`references/source-grounding.md`](references/source-grounding.md). Keep evals
synthetic or originally paraphrased.

## Workflow

1. Select mode, scope, consumer surface, and verification question.
2. Prefer `rg`; inspect source-readable API boundaries, manifests, OpenAPI,
   auth/error/versioning/observability signals, data/storage clients, IaC, and
   the paired architecture package path when relevant.
3. Read relevant procedures and extension excerpts; disclose selections only
   when they help explain a decision or evidence limit.
4. Apply project assimilation before deciding whether to reuse, flag, migrate,
   or ignore existing infrastructure.
5. Separate fact from inference, choose the smallest justified move, validate
   the actual contract, and report the useful result and material limits.

## Mode Outputs

Report the result, relevant contract or implementation decisions, validation,
and material limits. Extract separates facts from requested debt judgments;
Review gives evidence and consequence; Lookup answers the question directly.
A reference difference alone is not a finding. Use codes and the detailed
mode/extension/procedure/layer inventory only for a requested formal report or
an actual consumer. Do not repeat routine defaults, no-findings, or no-delegation
fields. Explain a material exception once where it changes the recommendation.

## Stop Conditions

Stop the affected action for missing authority, essential evidence, or a
concrete unsafe or incompatible change. Report unresolved findings without
automatically fixing them or stopping the rest of a read-only review. Continue
independent work; a reference deviation or absent optional tooling is not a stop.
