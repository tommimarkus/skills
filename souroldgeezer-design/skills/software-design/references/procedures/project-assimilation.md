# Software Project Assimilation

Load when existing project source, diffs, manifests, generated clients, shared
libraries, adapters, state owners, domain vocabulary, or module boundaries are
in scope.

Direction is one-way: assimilate the project to the software-design reference,
not the reference to the project. Reuse compliant local structure, flag
non-compliant structure as legacy debt, and never extend a broken pattern into
added code.

## Discovery

Inspect source-readable locations before deciding:

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

Classify conflicts as `reused`, `legacy debt`, `blocking debt`, or
`migration performed`.

- Added code must comply with the core reference and loaded extensions.
- Legacy debt is fixed only when migration is in scope.
- If requested work would depend on or extend blocking debt, stop and ask for
  migration scope or propose the smallest safe migration move.
- If a legacy pattern is not migrated, name the file, violated rule or smell
  family, and reason it remains out of scope.

## Footer Block

Use this shape when assimilation applies:

```text
Project assimilation:
  Reused: <compliant local boundaries/adapters/state owners and evidence>
  Legacy debt: <file:line - rule or smell family - reason not migrated>
  Migrations performed: <file:line - rule or smell family fixed>
```
