# Layout quality cases

Regression cases for Review-mode `AD-L*` geometry checks. These are small source-shape descriptions rather than full OEF documents so they can be reused with Build, Extract, or hand-authored fixture files.

## AD-L11 connector through unrelated node

- View: Technology Usage.
- Nodes: source Function App at `(40, 40, 160, 64)`, unrelated Runtime child at `(240, 40, 160, 64)`, target Application Insights at `(440, 40, 160, 64)`.
- Connection: source → target with a straight segment from source right midpoint to target left midpoint.
- Expected: `AD-L11 block`; readiness max `model-valid`.

## Allowed ancestor-container exit

- View: Service Realization.
- Nodes: parent Function App container, nested source Function runtime, target Application Insights outside the parent.
- Connection: nested source exits through its own parent boundary without crossing sibling nodes.
- Expected: no `AD-L11`; parent intersection is allowed only because it is an ancestor of the source.

## Business Process Cooperation long route

- View: Business Process Cooperation.
- Nodes: Active lane Actor, Behaviour lane five-step Triggering chain, Passive lane Business Object.
- Connection: Actor Assignment to final process must route around intermediate Behaviour nodes.
- Expected: no `AD-L11`; if the line crosses an intermediate process, `AD-L11 block`.

## Migration / Deployment Topology long route

- View: Migration.
- Nodes: sibling Development, Staging, Production Plateaus and one deploy Work Package below.
- Connections: Work Package Realization to each Plateau.
- Expected: no Plateau-to-Plateau Triggering (`AD-20` if present); Realization lanes do not cross sibling Plateaus (`AD-L11` if they do).

## Technology Security-style route

- View: Technology Usage.
- Nodes: Function App, Managed Identity Technology Service, Cosmos account, Storage account, Key Vault, Log Analytics.
- Connections: Managed Identity Access edges and diagnostic Flow edges.
- Expected: Access/Flow edges use separate lanes; no stacked target arrowheads (`AD-L13`) and no connector crossing resource nodes (`AD-L11`).

## Stale bendpoint reuse after relationship replacement

- View: Technology Usage or Technology Security.
- Prior route: Function App -> Application Insights Flow, with bendpoints chosen for that source/target direction.
- Refresh: relationship is replaced with Application Insights -> Function App Serving, or MI Access edges are replaced by resource -> Function App Serving edges.
- Expected: old bendpoints are discarded unless the new route still clears every unrelated and nested child node rectangle. If the preserved route crosses Cosmos, Storage, Key Vault, managed identity, or runtime child boxes, report `AD-L11 block` and readiness max `model-valid`.

## AD-L12 through AD-L15 readability checks

- `AD-L12`: any non-legend node with zero same-view connections.
- `AD-L13`: three resource Nodes all entering the same target midpoint with overlapping arrowheads.
- `AD-L14`: occupied layer rows separated by more than 100 px of unused vertical space without documentation.
- `AD-L15`: three or more fan-out edges from one source crossing each other or a non-endpoint sibling.
