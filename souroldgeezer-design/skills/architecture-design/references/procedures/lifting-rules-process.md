# Lifting rules — Durable Functions and Logic Apps to ArchiMate Business processes

Rules for lifting ArchiMate **Business Layer** Process, Event, and Interaction elements from backend workflow sources. Invoked by Extract mode when those sources are present. Every lifted element carries a per-element `LIFT-CANDIDATE` marker (reference §7.4) so the architect can accept, reject, or enrich each one independently.

The reference is [../../../../docs/architecture-reference/architecture.md](../../../../docs/architecture-reference/architecture.md). This procedure cites §4.1 (Business Layer elements), §7.2 (partial forward-only posture for Business), §7.4 (the `LIFT-CANDIDATE` marker), and §9.7 / §9.3 (the process diagram kinds that consume the lifted elements).

## Sources read

- **Durable Functions orchestrators.** C# functions carrying `[Function]` (isolated worker) or `[FunctionName]` (in-process, deprecated — flag per `afdotnet.LC-1` from `serverless-api-design` if encountered) whose trigger parameter type is `TaskOrchestrationContext` (isolated worker) or `IDurableOrchestrationContext` (in-process).
- **Logic Apps definitions.** `workflow.json`, `*.logicapp.json`, and Bicep `Microsoft.Logic/workflows` resources carrying a `definition.$schema` of the Logic Apps workflow-definition language.
- **Function triggers on the same Function App** that invoke an orchestrator (`[DurableClient]` HTTP starters, queue / timer / event-grid triggers) — consulted only to identify the Business Event that starts each Process.

Out of scope: Service Bus subscription chains (plausible v2 input), Event Grid topology, non-Azure workflow engines (Temporal, Airflow, AWS Step Functions), long-running sagas implemented as custom state machines without a Durable / Logic Apps wrapper, and GitHub Actions workflows (those lift to the Implementation & Migration Layer via [lifting-rules-gha.md](lifting-rules-gha.md), not the Business Layer).

## Mapping rules — Durable Functions

### Orchestrator function → Business Process

Each orchestrator function is lifted to one **Business Process**. The orchestrator's `[Function]` attribute value (or function name for legacy `[FunctionName]`) becomes the element `<name>`; the file path and line become the `LIFT-CANDIDATE source=`.

### Activity calls → step chain

Inside the orchestrator body:

| Detection | ArchiMate element / relationship |
|---|---|
| `await context.CallActivityAsync<T>("StepName", ...)` | One **Business Process** (or **Business Interaction** when the step is intrinsically collaborative — fan-out to multiple partners, external callback), `<name>` = `StepName`, chained by **Triggering** from the previous step |
| `await context.CallSubOrchestratorAsync<T>(...)` | A nested **Business Process** with a **Composition** relationship to the parent Process |
| `await Task.WhenAll(CallActivityAsync(...), CallActivityAsync(...), ...)` | Parallel **Triggering** edges fan out from the preceding step to each activity; the continuation after `await` is the fan-in point |
| `await context.CreateTimer(...)` | **Business Event** — *timer expiry* — preceding the next step via **Triggering** |
| `await context.WaitForExternalEvent<T>("EventName")` | **Business Event** — `<name>` = `EventName` — preceding the next step via **Triggering** |

Activity function definitions (`[Function]` with `[ActivityTrigger]` parameter) are *not* lifted to separate elements — the activity name is already captured on the Business Process step. This keeps the process-level view free of implementation noise.

### Orchestrator entry point → Business Event

The mechanism that starts an orchestrator becomes a **Business Event** Triggering the first step:

| Detection | Business Event |
|---|---|
| HTTP-triggered starter that calls `client.StartNewAsync("OrchestratorName", ...)` | *HTTP request* (named after the starter route if discoverable) |
| Queue-triggered starter | *Queue message arrives* (named after the queue) |
| Timer-triggered starter | *Schedule fires* (named after the cron / schedule interval) |
| Event Grid / Service Bus starter | *Event received* (named after the topic or subscription) |
| No starter detected | No Business Event emitted; `confidence=low` on the resulting Process |

### Confidence scoring

- **`high`** — one unambiguous entry point, one linear or straightforward fan-out-fan-in chain, no sub-orchestrators, no dynamic activity names.
- **`medium`** — nested sub-orchestrators, multiple entry points (the same orchestrator callable from HTTP and queue), or dynamic activity names (variable-driven `CallActivityAsync(activityName, ...)`).
- **`low`** — fallback heuristic: the function shape looked orchestrator-like but the chain could not be reconstructed with confidence. Architect should treat the emitted stub as a placeholder and rewrite.

## Mapping rules — Logic Apps

### Workflow → Business Process

Each Logic Apps workflow is lifted to one **Business Process**. The workflow's `name` (from the resource definition or the containing file basename) becomes the element `<name>`.

### Trigger → Business Event

The workflow's `trigger` definition becomes a **Business Event** Triggering the first action:

| Trigger kind | Business Event |
|---|---|
| `Request` (HTTP) | *HTTP request received* |
| `Recurrence` | *Schedule fires* (including the interval in the label) |
| `EventGrid` / `ServiceBus` / `Eventhub` | *Event received* (named after the topic / queue / hub) |
| Connector-initiated (e.g., `When_a_file_is_created`, `When_an_email_arrives`) | Preserve the connector's verb-phrase as the Event `<name>` |

### Actions → step chain

Each action in the workflow's `actions` block becomes a **Business Process** step:

| Detection | Relationship |
|---|---|
| `runAfter: { <previous-action>: [Succeeded] }` (default succession) | **Triggering** from the previous step |
| `runAfter: { <previous-action>: [Failed, TimedOut, Skipped] }` | **Flow** (conditional divergence) from the previous step |
| `If` / `Switch` branches | Parallel **Triggering** paths from the conditional step; each branch's actions sequence as usual; convergence after the conditional is represented by **Triggering** from each branch-terminal to the next action |
| `Until` loop | Single **Business Process** step labelled with the loop condition; the loop body is not expanded into separate steps (v1) |
| `ForEach` fan-out | Parallel **Triggering** edges to the body actions; convergence after the `ForEach` |

Nested `workflow` invocations (one Logic App calling another) become **Composition** relationships between the parent and the called Business Process.

### Confidence scoring

- **`high`** — single trigger, sequential `runAfter` chain, no conditionals deeper than one `If` / `Switch`, no nested workflows.
- **`medium`** — multiple triggers, nested conditionals, `Until` loops, or nested workflows.
- **`low`** — dynamic action names (generated at runtime), deeply nested control flow.

## Naming conventions

- **Business Process identifier** — `id-bp-<slug>` where `<slug>` is the orchestrator / workflow name normalised to lowercase-hyphens (`PlaceOrderOrchestrator` → `id-bp-place-order`).
- **Business Process `<name>`** — preserve the orchestrator / workflow name in its original casing (`PlaceOrderOrchestrator` → "Place Order Orchestrator") unless the name is purely mechanical (`Orch1`, `Workflow_Copy`) — then derive a label from the trigger or primary activity.
- **Business Event identifier** — `id-be-<slug>` where `<slug>` is derived from the trigger (`id-be-http-checkout`, `id-be-queue-orders-incoming`, `id-be-timer-nightly`).
- **Triggering / Flow relationship identifier** — `id-rel-<source-slug>-to-<target-slug>`.

Identifiers are stable across re-extracts per reference §6.6. If an orchestrator is renamed, its identifier changes — by design; the architect may choose to rename the corresponding Business Process element in the canonical OEF file ahead of the next Extract to preserve identity.

## LIFT-CANDIDATE marker emission

Every lifted element (Business Process, Business Event, Business Interaction) carries an XML comment immediately preceding its `<element>` tag:

```xml
<!-- LIFT-CANDIDATE — architect confirms: source=src/Orders.Functions/Orchestrators/PlaceOrderOrchestrator.cs:18, confidence=high -->
<element identifier="id-bp-place-order" xsi:type="BusinessProcess">
  <name xml:lang="en">Place Order</name>
</element>
```

The `source=` attribute is the file path (optionally suffixed with `:line`) of the orchestrator / workflow that motivated the lift; it is the anchor reverse Lookup uses to answer "which process does this symbol belong to". The `confidence=` attribute captures the mapping quality (see per-source scoring above).

Emitted without the marker → `AD-14-LC`. Missing `source=` or `confidence=` attributes → also `AD-14-LC`; both are required.

## Output shape

Lifted elements are emitted as OEF XML into the canonical file at `docs/architecture/<feature>.oef.xml`, grouped under a Business Layer block. Minimal fragment:

```xml
<!-- ==== Business Layer (lifted from backend workflow sources) ==== -->

<elements>
  <!-- LIFT-CANDIDATE — architect confirms: source=src/Orders.Functions/Orchestrators/PlaceOrderOrchestrator.cs:18, confidence=high -->
  <element identifier="id-bp-place-order" xsi:type="BusinessProcess">
    <name xml:lang="en">Place Order</name>
  </element>

  <!-- LIFT-CANDIDATE — architect confirms: source=src/Orders.Functions/Orchestrators/PlaceOrderOrchestrator.cs:24, confidence=high -->
  <element identifier="id-bp-validate-order" xsi:type="BusinessProcess">
    <name xml:lang="en">Validate Order</name>
  </element>

  <!-- LIFT-CANDIDATE — architect confirms: source=src/Orders.Functions/Orchestrators/PlaceOrderOrchestrator.cs:31, confidence=high -->
  <element identifier="id-bp-ship-order" xsi:type="BusinessProcess">
    <name xml:lang="en">Ship Order</name>
  </element>

  <!-- LIFT-CANDIDATE — architect confirms: source=src/Orders.Functions/HttpStarters/PlaceOrderStarter.cs:15, confidence=high -->
  <element identifier="id-be-http-place-order" xsi:type="BusinessEvent">
    <name xml:lang="en">Place-order request received</name>
  </element>
</elements>

<relationships>
  <relationship identifier="id-rel-be-to-bp-place-order"
                source="id-be-http-place-order" target="id-bp-place-order"
                xsi:type="Triggering"/>
  <relationship identifier="id-rel-bp-place-to-validate"
                source="id-bp-place-order" target="id-bp-validate-order"
                xsi:type="Triggering"/>
  <relationship identifier="id-rel-bp-validate-to-ship"
                source="id-bp-validate-order" target="id-bp-ship-order"
                xsi:type="Triggering"/>
</relationships>
```

Other Business-layer elements (Actor, Role, Collaboration, Object, Contract, Product, Service, Function) are **not** emitted by this procedure — they remain forward-only per reference §7.2 and are stubbed via the `FORWARD-ONLY` block in the wider Extract output.

## UI lifting deferred — architect hand-authors

UI routes are **not** lifted in v1. Reference §9.3 Service Realization views in the Process-rooted modality that model a user-driven Business Process include a UI Application Component and Application Interface at the entry point; the architect authors these by hand.

**Blazor idiom (v1).** For a Blazor page component at `src/Client/Pages/Checkout.razor` carrying `@page "/checkout"`:

```xml
<element identifier="id-uicomp-checkout" xsi:type="ApplicationComponent">
  <name xml:lang="en">src/Client/Pages/Checkout.razor</name>
</element>
<element identifier="id-uiapi-checkout" xsi:type="ApplicationInterface">
  <name xml:lang="en">/checkout</name>
</element>
<relationship identifier="id-rel-uiapi-to-uicomp"
              source="id-uiapi-checkout" target="id-uicomp-checkout"
              xsi:type="Assignment"/>
<relationship identifier="id-rel-uicomp-to-bp"
              source="id-uicomp-checkout" target="id-bp-place-order"
              xsi:type="Realization"/>
```

The `<name>` on the UI Application Component is the repo-relative file path so reverse Lookup can match a file symbol back to the Business Process by string equality (reference §9.3; SKILL.md "Lookup"). Architects preferring a human-readable name can place the file path in a `source=` custom property and use a friendlier `<name>` — the Lookup resolver consults both.

**Other frontend stacks.** Next.js App Router (`app/checkout/page.tsx` → UI Component named by the file path; Application Interface `<name>` = the route `/checkout`), Next.js Pages Router (`pages/checkout.tsx`), and plain React Router (the declarative `<Route path="/checkout" element={<Checkout/>}/>` — UI Component `<name>` = the component's file path) follow the same convention without a v1-specific idiom callout.

**Architect ownership.** UI Application Components in §9.3 views (Process-rooted modality) always carry either a `LIFT-CANDIDATE` marker (if emitted by a future UI lifter) or no marker (architect-authored, the v1 default). There is no `FORWARD-ONLY` path for UI elements — they are not forward-only; they are simply not lifted automatically yet.

## Cross-layer linking

Lifted Business Processes link to the Application Layer through Realisation, preserving the reference's layer discipline (§2.1, §2.3):

| Detection | ArchiMate relationship |
|---|---|
| An activity function called from the orchestrator has the same Function App as an Application Component already present in the model | **Realisation** from that Application Component to the Business Process it implements |
| A Logic App action targets a known Application Service (API connector targeting an HTTP endpoint whose route matches an Application Interface in the model) | **Realisation** from the Application Service to the Business Process step |
| No resolvable target Application element | Omit the cross-layer link; the skill does not invent connections |

These links make the `AD-B-8` / `AD-B-9` between-view invariant checkable: a lifted Business Process that has no Realisation from any Application Service triggers `AD-B-8` at Review time.

## What this procedure does not do

- Lift **Business Actor / Role / Collaboration / Object / Contract / Product / Service / Function.** These remain forward-only per reference §7.2. An Actor Assignment on a lifted Process is the architect's decision.
- Lift **UI routes.** Blazor `@page`, Next.js `app/**/page.tsx`, React Router — none are parsed in v1; §9.3 Process-rooted modality UI elements are hand-authored.
- **Interpret business semantics.** A step named "ProcessPayment" in code does not become a Business Process named "Process Payment" in the lifted model without architect review — the `LIFT-CANDIDATE` marker is there because the mapping is structural, not semantic.
- **Track orchestration history.** The procedure reads orchestrator / workflow *definitions*, not runtime execution history. Drift between the lifted shape and actual production runs is out of scope; `AD-DR-11` / `AD-DR-12` compare definitions only.
- **Validate orchestrator correctness.** Missing `CallActivityAsync` return handling, unreachable code, non-idempotent activities — all are [`devsecops-audit`](../../../../../souroldgeezer-audit/skills/devsecops-audit/SKILL.md) or framework-level concerns, not this procedure's.

## Cross-link to view emission

This procedure lifts Business Layer **elements**. Per-feature **view emission** — the §9.7 cooperation view and the per-process §9.3 drill-down views — is governed by [`process-view-emission.md`](process-view-emission.md), invoked by the Extract workflow ([SKILL.md](../../SKILL.md) Extract step 3) after this procedure has produced the element set. The view-emission contract guarantees: one §9.7 per feature containing every top-level Business Process, and one §9.3 per orchestrator-level Business Process (top-level + Composition-nested sub-orchestrators). Suppression via `propid-coop-view-exclude` / `propid-drilldown-exclude` (reference §6.4b) is the architect's escape hatch for intentional under-coverage.

## Sources

Paraphrased guidance; no code samples copied from the sources below.

- Microsoft Learn, *Durable Functions overview* — orchestrator function structure, activity-call patterns, fan-out / fan-in, sub-orchestrators, timers, external events. <https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview>
- Microsoft Learn, *Durable Functions — isolated worker process (.NET)* — `TaskOrchestrationContext` method surface and trigger attributes. <https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-isolated-create-first-csharp>
- Microsoft Learn, *Schema reference for workflow definition language — Azure Logic Apps* — `trigger`, `actions`, `runAfter`, conditional control flow (`If`, `Switch`, `Until`, `ForEach`), and nested workflow invocations. <https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-workflow-definition-language>
- Microsoft Learn, *Blazor routing and navigation* — `@page` directive on Razor components, route templates, parameter binding. <https://learn.microsoft.com/en-us/aspnet/core/blazor/fundamentals/routing>

The Open Group ArchiMate® 3.2 Specification (C226, March 2023) is the notation anchor for Business Process / Event / Interaction semantics and for the Triggering / Flow / Realisation / Assignment relationship constraints applied above.
