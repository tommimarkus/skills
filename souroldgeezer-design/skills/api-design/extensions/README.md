# Extensions

Per-stack packs loaded on demand by the `api-design` skill. The workflow in
[`../SKILL.md`](../SKILL.md) owns route selection; every stack pack separates
an always-loaded core from mutually exclusive Build and Review lanes.

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
they do not replace or weaken the core API reference.

## Load order

1. Detect stacks from manifests, source, and deployment signals using each
   core file's `Name and detection signals` section.
2. Load every matching core for Build, Extract, and Review.
3. Select lanes by mode:
   - Build loads each matching `build.md` and excludes `review.md`.
   - Review loads each matching `review.md` and excludes `build.md`.
   - Factual Extract loads cores only. Explicit debt/compliance Extract also
     loads matching review lanes and discloses the escalation.
   - Lookup starts from one anchored core-reference section. A stack-specific
     Lookup loads one stack core plus at most one relevant lane.
4. Apply the selected rules after the framework-neutral reference.

A Lookup that needs more than one stack's mechanics, both lanes, or a data
extension in addition to the Node.js/Next.js base escalates to Review or Build,
or asks the user. Node.js followed by Next.js is the one composed-base
exception and counts as a single runtime stack for this cap.

## Review Or Extract Rules

Review always loads the matching review lanes. Factual Extract stays core-only;
an explicit debt/compliance Extract adds only matching review lanes and reports
that choice in its footer.

## Footer Field

The ordinary API-design footer lists the selected mode, every core and lane
loaded, evidence layers, project assimilation, delegations, and limits. An
Extract that adds review detail states the user request that triggered it.

## Extensions compose

Build, Review, and Extract compose every detected stack. An Azure Functions
API that stores entities in Cosmos DB and payloads in Blob Storage loads all
three cores, then the lane selected by the mode for each core. A hosted Next.js
API loads the Node.js core first and the Next.js core second, then the same
selected lane for both. A Python API loads the Python core for ASGI, WSGI, or
serverless signals, then selects exactly one Python lane for Build or Review.

Smell-code namespaces are orthogonal: `afdotnet.*`, `nodejs.*`,
`nextjs.*`, `pyapi.*`, `cosmos.*`, and `blob.*`. Pattern namespaces use the same
prefixes. Findings therefore remain attributable when Review composes multiple
packs, while Build patterns remain attributable across compute and data layers.

On conflict, an exact review-lane carve-out wins only for its documented stack
boundary. Extensions never override the core contract, security, reliability,
observability, or verification-layer baseline.

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
7. Add route tests proving mode inclusion and exclusion, then measure a declared
   scenario before updating the committed cost snapshot.
8. Document common composition with existing stacks.

## Future hosted API extensions

Add another hosted runtime only when its detection, hosting surface, safety
invariants, patterns, review codes, and mode-route tests are concrete. Keep the
generic API contract in the core reference.

## Non-goals for extensions

- Extensions are not general framework guides.
- Extensions do not duplicate the framework-neutral API reference.
- A mode lane may not smuggle the other lane's concrete code namespace into
  its closure.
- Factual Extract does not produce a compliance verdict from core-only
  evidence.
