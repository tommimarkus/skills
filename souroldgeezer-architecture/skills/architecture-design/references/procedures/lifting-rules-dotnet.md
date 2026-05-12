# .NET Lifting Rules

Use for Extract when .NET projects are in scope.

## Elements

- `*.sln`/`*.csproj`: Application Components when deployable or independently
  meaningful.
- Public HTTP/SDK/queue/storage clients: support services or relationships only
  with clear evidence.
- Durable Functions orchestrators: Business Process candidates with evidence and
  confidence.

## Relationships

- `ProjectReference`: Serving or Composition by package/runtime semantics.
- Host to function/workflow component: Assignment or Realization by behavior vs
  service claim.
- SDK data access: Access only when passive structure is identified.

## Package Output

Add source refs and only views with a clear question. Validate/render before
readiness. Use source-backed groups for solution folders, deployable hosts,
bounded contexts, or meaningful dependency clusters; avoid grouping generic
shared libraries.
