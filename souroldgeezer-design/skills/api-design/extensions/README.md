# Extensions

Per-stack packs loaded on demand by the `api-design` skill. The workflow in
[`../SKILL.md`](../SKILL.md) owns route selection; every stack pack separates
a stack core from Build and Review detail lanes. Read only the sections needed
for the task; detection alone does not require a full pack.

## File layout per extension

Each stack has three files:

- `<stack>.md` — detection signals, hosting surface, compact primitive
  recognition, project assimilation, shared safety invariants, and the
  applies-to mapping.
- `<stack>/build.md` — detailed primitives and namespaced `<stack>.PAT-*`
  implementation patterns.
- `<stack>/review.md` — namespaced `<stack>.HC-*`, `<stack>.LC-*`, and
  `<stack>.POS-*` classifications plus exact carve-outs.

The core and its selected lane form one extension contract. Lanes add detail;
they refine the core API defaults and evidence requirements. Compatible project
contracts may justify alternatives while preserving protocol validity and safety.

## Load order

1. Detect task-relevant stacks from manifests, source, and deployment signals.
2. Read relevant core sections and the Build or Review detail needed for the
   decision. The other lane is available when its detail actually matters; do
   not preload every detected stack or both lanes.
3. Factual Extract records facts without an unsolicited compliance verdict.
   A requested debt/compliance judgment reads the applicable Review criteria.
4. Lookup may combine multiple relevant core or lane excerpts without changing
   mode. Expand inspection when uncertainty, dependencies, or material risk
   requires it, not merely because an extension-count cap was reached.
5. Compose Node.js before Next.js when both mechanics matter. Apply the same
   task-relevance rule to compute and data stacks.

## Review Or Extract Rules

A supported finding needs evidence of a violated project contract, actual unsafe
behavior, or a material consequence. A different error format, OpenAPI version,
versioning scheme, or telemetry product is not by itself a finding. Existing
codes identify the concern; their high-confidence bucket does not establish
severity or override a compatible project contract.

## Footer Field

Report the result and material evidence limits concisely. Give the selected
mode, cores, lanes, assimilation, and delegation inventory only for a requested
formal report or actual consumer. Explain material exceptions once.

## Extensions compose

Compose the excerpts needed for the decision. An Azure Functions API may need
Cosmos and Blob guidance for a storage change, while a bounded handler edit may
need neither. A hosted Next.js API reads relevant Node.js guidance before its
Next.js specialization. Preserve the namespaces `afdotnet.*`, `nodejs.*`,
`nextjs.*`, `pyapi.*`, `cosmos.*`, and `blob.*` so supported findings remain
attributable; a namespace is not an instruction to load unrelated rules.

On conflict, inspect the actual project contract and exact runtime boundary.
Preserve safety, protocol validity, and honest evidence; use justified defaults
or project-compatible alternatives instead of mandatory migration.

## Current extensions

| Core | Build lane | Review lane | Applies to |
|---|---|---|---|
| `azure-functions-dotnet.md` | `azure-functions-dotnet/build.md` | `azure-functions-dotnet/review.md` | Azure Functions .NET isolated worker |
| `nodejs.md` | `nodejs/build.md` | `nodejs/review.md` | Node.js / TypeScript hosted or serverless APIs |
| `nextjs.md` | `nextjs/build.md` | `nextjs/review.md` | Hosted Next.js API surfaces; after Node.js |
| `azure-cosmosdb.md` | `azure-cosmosdb/build.md` | `azure-cosmosdb/review.md` | Azure Cosmos DB NoSQL API |
| `azure-blob-storage.md` | `azure-blob-storage/build.md` | `azure-blob-storage/review.md` | Azure Blob Storage block blobs |
| `python.md` | `python/build.md` | `python/review.md` | Python ASGI, WSGI, and serverless HTTP API surfaces |

## Required core sections

- **Name and detection signals**
- **Hosting-model surface**
- **Mode lanes**
- **Stack-specific primitives** — compact recognition only
- **Shared safety invariants**
- **Project assimilation**
- **Applies to reference sections**

Build lanes own detailed primitive subsections and stack-specific patterns.
Review lanes own smell codes, positive signals, and carve-outs.

## Adding an extension

1. Pick a stable namespace prefix and define unambiguous detection signals.
2. Add `<stack>.md`, `<stack>/build.md`, and `<stack>/review.md` with the
   ownership boundaries above.
3. Put shared non-negotiable safety rules in the core; do not duplicate them
   across lanes.
4. Put only implementation mechanics and `PAT` definitions in Build.
5. Put only finding classifications, positive signals, and carve-outs in
   Review. A review action may describe the required fix without loading Build.
6. Add the core to the `SKILL.md` load map and this table.
7. Add representative route and behavior cases for relevant selection and
   safety, then update affected declared cost scenarios and snapshots deliberately.
8. Document common composition with existing stacks.

## Future hosted API extensions

Add another hosted runtime only when its detection, hosting surface, safety
invariants, patterns, review codes, and mode-route tests are concrete. Keep the
generic API contract in the core reference.

## Non-goals for extensions

- Extensions are not general framework guides.
- Extensions do not duplicate the framework-neutral API reference.
- Detail lanes keep their code ownership separate; consulting another lane for
  a relevant decision does not change that ownership.
- Factual Extract does not produce a compliance verdict from core-only
  evidence.
