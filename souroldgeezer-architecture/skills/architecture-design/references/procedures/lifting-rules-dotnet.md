# .NET Lifting Rules

Use for Extract when .NET projects are in scope.

## Elements

- `*.sln` and `*.csproj` projects become Application Components when they are
  deployable or independently meaningful.
- Public HTTP clients, SDK clients, queue clients, and storage clients can
  support Application Services or relationships when the source evidence is
  clear.
- Durable Functions orchestrators can support Business Process candidates;
  mark them with source evidence and confidence.

## Relationships

- `ProjectReference` edges usually become Serving or Composition depending on
  package structure and runtime semantics.
- Host project to function/workflow component is Assignment or Realization
  depending on whether the component performs behavior or delivers a service.
- Data access through SDK clients becomes Access only when source evidence
  identifies the passive structure.

## Package Output

Add source refs to `model.json`. Add or update only views that answer a clear
architecture question. Run dediren validation and render evidence before
claiming readiness.

Use source-backed groups when solution folders, deployable hosts, bounded
contexts, or dependency clusters reveal ownership or hosting structure. Keep
cross-cutting shared libraries out of a group unless the source makes that
boundary meaningful for the view.
