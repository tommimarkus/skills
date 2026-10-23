# Software Project Assimilation

Load when existing project source, diffs, manifests, generated clients, shared
libraries, adapters, state owners, domain vocabulary, or module boundaries are
in scope.

Start from the user's outcome and the project's actual contracts. Bundled
conventions are strong defaults, not authority to redesign a compatible project.
Reuse justified local structure; a reference difference alone is not debt.
Identify concrete incompatibility, unsafe behavior, or a substantiated
maintenance consequence before recommending migration. Factual Extract records
behavior and uncertainty without unsolicited compliance judgments.

## Discovery

Inspect the relevant source-readable locations before deciding; do not require
a complete project inventory for a bounded change:

1. Module and package roots: solution/workspace files, project references,
   package manifests, public exports, barrels, crate/workspace members, or
   script entrypoints.
2. Dependency direction: imports, project references, generated-client use,
   framework/storage imports in policy code, and cross-boundary model sharing.
3. Responsibility boundaries: adapters, service/application/domain layers,
   composition roots, command handlers, workers, CLI commands, and shared
   libraries.
4. State and invariant owners: mutable module state, caches, repositories,
   units of work, aggregates, process state, config loading, and environment
   reads.
5. Vocabulary and models: duplicate terms, vendor DTOs, generated types,
   persistence entities, API contracts, and mapping/translation points.
6. Evolution signals: feature flags, migration branches, branch-by-abstraction
   code, deprecated paths, ownership notes, and churn/history when available.
7. Stack signals: load the matching extension for .NET, Java, Rust,
   TypeScript, shell, or Python when its files or manifests are present.

Loaded extensions own deeper stack-specific discovery and carve-outs.

## Reuse Or Migrate

| Asset | Reuse when | Flag or migrate when |
|---|---|---|
| Module boundary | Hides a volatile decision, has clear owner, and limits propagation | Folder split only, mixed reasons to change, cycles, or broad fan-out hotspot |
| Adapter | Translates external mechanism or vocabulary without owning policy | Adapter contains domain policy, leaks generated/vendor fields, or becomes a pass-through wrapper |
| Shared library | Stable, boring, owned mechanics with low semantic load | Shared domain core, unstable utility grab bag, or ownership unclear |
| Model / DTO | Kept inside its owning boundary or translated explicitly | Vendor/API/persistence model becomes domain state across boundaries |
| State owner | One boundary owns invariant changes and lifetime | Controllers/workers/adapters mutate the same state without one owner |
| Migration seam | Has owner, metric or acceptance condition, and removal path | Permanent transitional layer, hidden dual writes, or no exit condition |

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
  Reused: <compatible local boundaries/adapters/state owners and evidence>
  Legacy debt: <file:line - rule or smell family - reason not migrated>
  Migrations performed: <file:line - rule or smell family fixed>
```
