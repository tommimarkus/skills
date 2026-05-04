# SUT surface enumeration

**When this runs:** step 2.5 of the deep-mode workflow in [../../SKILL.md](../../SKILL.md). This is the skill's static gap-detection pass — *find tests that don't exist yet* for public API, HTTP routes, migrations, throw sites, and validation attributes in the SUT. Never run in quick mode. Never run against E2E audit targets.

Unlike mutation testing (step 4) which observes runtime kill behavior, surface enumeration reads the production code to ask "what ought to be tested?" and cross-references against the test project. Both are complementary — mutation testing catches tests that execute code without verifying it; surface enumeration catches code that has no test at all.

## Why both static surface enumeration and mutation testing

- **Static audit alone** only examines files that already have tests.
- **Mutation testing** catches `NoCoverage` files at runtime, but only when the tool is installed and the SUT shape is supported (e.g. Stryker.NET cannot mutate Blazor WASM — see [../../extensions/dotnet-core.md § Known SUT limitations](../../extensions/dotnet-core.md)).
- **Static surface enumeration** works on any SUT the stack extension has grep patterns for, even Blazor WASM. It produces *probable* gaps from grep, so it is noisier than mutation testing.
- When both run on the same suite, a symbol flagged by both is a **confirmed gap**; a symbol flagged by static-only is a *probable* gap; a symbol flagged by mutation-only is a signal the grep patterns need tuning.

## Procedure

1. **Read the extension's SUT surface enumeration section.** Every extension that supports gap detection must provide: SUT identification instructions, grep patterns per gap class (API / routes / migrations / throw sites / validation), and cross-reference matching rules. Extensions without this section produce no gap report — record the skip reason and continue with static findings only.
2. **Identify the SUT.** For each test project in scope, walk its `<ProjectReference>` closure (or equivalent module graph) to the production project(s) under test. Record the SUT project list in the gap-report header. A test project may have multiple SUT projects (e.g. a shared contract library plus the API that consumes it).
3. **Enumerate testable surface** by running the extension's grep patterns against the SUT source tree. For each pattern, capture:
   - A symbol identifier (method name, route template, migration class name, exception-throwing method name, validation-attribute target property).
   - A source location (file path and line number).
4. **Cross-reference against test discovery.** For each enumerated symbol, check whether test evidence reaches the surface and whether it asserts the relevant contract. Classify the best evidence as:
   - `covered-strong` — a test reaches the SUT surface and asserts the relevant externally visible contract, state, error, validation result, or domain outcome.
   - `referenced-weak` — a test names the route, function, symbol, component, keyword, or endpoint but asserts only setup, transport, status-only success, element presence, snapshot shape, or internal invocation.
   - `referenced-incidental` — the surface appears in setup, mocks, fixtures, seed data, imports, or navigation but is not the behavior under test.
   - `not-referenced` — no meaningful evidence found.
   - `probable-static` — a surface looks intentionally static or pass-through, but the audit cannot prove that from tests alone.
   - `confirmed-static-or-delegated` — the gap is dismissed with explicit evidence that the surface is static, generated, or delegated to another covered contract.
5. **Classify confirmation state.** Each entry without `covered-strong` evidence remains a gap candidate. Upgrade it only when evidence supports it:
   - `confirmed-mutation` — mutation testing reports `NoCoverage` or surviving mutants for the same symbol/file.
   - `confirmed-manual` — manual read proves no test reaches the symbol through a caller, adapter, generated route, or cross-extension public-boundary test.
   - `dismissed-indirect` — a test reaches the symbol indirectly and asserts the published contract.
6. **Emit a gap report** (see [§ Gap report format](#gap-report-format) below). Each `not-referenced`, `referenced-weak`, or `referenced-incidental` entry is a *probable* gap unless it was upgraded by mutation or manual evidence. A true negative requires either mutation testing, manual verification, or explicit static/delegation evidence.
7. **On extension section missing**, report: "Gap detection skipped — stack extension has no SUT surface enumeration section. Mutation testing remains the only gap-finding mechanism for this scope." Continue with static findings.

## Gap classes

The extension's patterns must populate these five categories. Extensions may add their own categories (e.g. `Gap-Resource` for a REST resource that has no test class) as long as they document them.

- **`Gap-API`** — public type or method without strong observable test evidence. *Medium confidence:* indirect coverage via a caller is common.
- **`Gap-Route`** — HTTP route / function handler / message-queue handler without strong route / queue / topic contract coverage. *High confidence:* routes are registered by string identity; status-only happy-path tests are weak references.
- **`Gap-Migration`** — database migration class (or file) without migration or upgrade-path evidence. *High confidence.*
- **`Gap-Throw`** — exception throw site without a test that reaches the behavior and asserts the published error contract. *Medium confidence:* may be covered by a generic "error path" test that doesn't name the type.
- **`Gap-Validate`** — a validation attribute (`[Required]`, `[StringLength]`, etc.) or custom validator on an input type without a test that sends a bad value for that field and asserts the validation contract. *High confidence* on serialization-layer input types.

## Rules

- **Extensions own the grep patterns.** The core workflow is framework-neutral; language-specific patterns belong in `extensions/<stack>.md`.
- **Gap detection is suite-level.** Never run step 2.5 in quick mode — a PR-diff or single-file audit produces noise.
- **Never treat a probable gap as a confirmed gap** without verification. The report must flag each finding as probable and recommend mutation testing or manual review for confirmation.
- **Do not create implementation-only worklist items from static-only gaps.** Worklist entries based on `probable-static` gaps must be framed as verification tasks first. Implementation work is allowed only after `confirmed-mutation` or `confirmed-manual` evidence exists.
- **Weak references are still gaps.** A test that merely names a surface, asserts `200 OK`, checks element presence, or verifies an internal call does not suppress a gap for missing invalid, unauthorized, conflict, timeout, duplicate, boundary, or state-change behavior on that same surface.
- **Account for cross-extension public-boundary coverage.** A Robot, Python, Node.js, or other external-runner test can satisfy a SUT-stack route/adapter gap when it exercises the public boundary and asserts the contract. It must not suppress source-level seam or mutation-target findings it cannot observe.
- **Reconcile with mutation testing** in step 5 when both steps produced output.

## Gap report format

In the step-5 suite assessment, emit a `### Gap report` subsection in one of two states:

**State A — enumeration ran:**

```markdown
### Gap report (static SUT surface enumeration)

- **SUT projects:** <project list>
- **Method:** grep-based cross-reference from test files to SUT symbols via the stack extension's patterns. Static-only findings are *probable* and require verification before implementation.

| Class | Enumerated | Covered strong | Referenced weak | Referenced incidental | Not referenced | Probable-static | Confirmed | Dismissed | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| `Gap-API` — public methods | <N> | <S> | <W> | <I> | <NR> | <P> | <C> | <D> | medium |
| `Gap-Route` — HTTP / function routes | <N> | <S> | <W> | <I> | <NR> | <P> | <C> | <D> | high |
| `Gap-Migration` — migration classes | <N> | <S> | <W> | <I> | <NR> | <P> | <C> | <D> | high |
| `Gap-Throw` — throw sites | <N> | <S> | <W> | <I> | <NR> | <P> | <C> | <D> | medium |
| `Gap-Validate` — validation attributes | <N> | <S> | <W> | <I> | <NR> | <P> | <C> | <D> | high |

#### Top gaps and verification candidates

- **Confirmed (`confirmed-mutation`) `Gap-Route`** — `DELETE /api/orders/{id}` (`api/Functions/OrdersApi.cs:88`): static probable gap and mutation `NoCoverage`. Action may be implementation work.
- **Weak reference (`referenced-weak`) `Gap-Route`** — `POST /api/orders` (`api/Functions/OrdersApi.cs:42`): test names the route and asserts `201` only; no invalid-payload, conflict, auth, or state oracle. Next step: confirm contract branches and add focused tests.
- **Probable (`probable-static`) `Gap-Migration`** — `AddOrderStatusColumnMigration` (`api/Migrations/0007_order_status.cs:14`): migration class name not mentioned in any test. Next step: manually verify migration path or run mutation before implementing.
- **Probable (`probable-static`) `Gap-Validate`** — `[Required] CustomerId` on `CreateOrderRequest` (`shared/Requests.cs:22`): no test sends a request with missing `CustomerId`. Next step: confirm no API contract test covers invalid request binding.
- **Dismissed (`dismissed-indirect`) `Gap-API`** — `OrderService.CancelOrderAsync` (`api/Services/OrderService.cs:42`): covered through `DELETE /api/orders/{id}` contract test with state assertion.
- **Probable (`probable-static`) `Gap-Throw`** — `throw new InvalidOperationException("Order already shipped")` (`api/Services/OrderService.cs:142`): no test names both the exception type and the method. Next step: manual read or mutation confirmation.

#### Reconciliation with mutation testing (when step 4 produced results)

- **Confirmed gaps** (`confirmed-mutation`): <list>
- **Static-only probable gaps** (`probable-static`): <verification candidates only; no implementation-only worklist item>
- **Dismissed indirect coverage** (`dismissed-indirect`): <list with covering test evidence>
- **Mutation-only gaps**: <list — signal to tune the grep patterns in the extension>
```

**State B — enumeration skipped:**

```markdown
### Gap report

- **Status:** skipped — <extension name> has no `SUT surface enumeration` section (or: target is quick mode / target is E2E-only).
- **What this means:** static gap detection is unavailable for this scope. Mutation testing (if applicable) is the only gap-finding mechanism. Consider writing an extension section to enable surface enumeration.
```
