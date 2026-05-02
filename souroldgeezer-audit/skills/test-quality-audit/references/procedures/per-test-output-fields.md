# Per-Test Output Fields

**When this runs:** read when producing quick-mode findings or the per-test
section of deep-mode output. `SKILL.md` owns mode and rubric selection; this
file owns the required finding fields, severity rules, and examples.

## Unit Rubric Fields

For every unit or component test case, emit:

1. **Intent statement** — one sentence answering what requirement the test
   encodes. If none can be stated, say `no stateable intent`.
2. **Expected-value provenance** — `spec`, `fixture`, `domain-invariant`,
   `pasted-literal`, or `unknown`.
3. **Assertion target** — `return-value`, `published-side-effect`,
   `internal-mock-invocation`, `structural-shape`, or `none`.
4. **Test size** — `small`, `medium`, or `large` using Google sizing. Unit
   tests should be `small`; larger sizes suggest lane migration.
5. **Smells matched** — core `HC-*` / `LC-*` plus loaded extension codes.
6. **Positive signals matched** — core `POS-*` plus loaded extension codes.
7. **Verdict** — `specification`, `characterization`, or `ambiguous`.
8. **Severity** — `block`, `warn`, or `info`.
9. **Recommended action** — `rewrite-from-requirement`, `add-assertion`,
   `split`, `delete`, `keep`, or `move-to-integration-lane`.

## Integration Rubric Fields

For every integration test case, emit:

1. **Scope statement** — one sentence answering what seam the test exercises
   and why a unit test could not prove the same thing. If none can be stated,
   say `no stateable scope`.
2. **Sub-lane** — `A` in-process or `B` out-of-process contract.
3. **Test size** — `small`, `medium`, or `large`.
4. **Seam narrowness** — `narrow` or `broad`; broad tests must be justified.
5. **Fixture and data provenance** — `per-test-factory`,
   `shared-immutable`, `shared-mutable`, `external-snapshot`,
   `pasted-literal`, or `unknown`.
6. **Assertion target** — `published-contract`, `observable-state`,
   `response-value`, `internal-mock-invocation`, `structural-shape`, or
   `none`.
7. **Smells matched** — core `I-*` plus loaded extension codes.
8. **Positive signals matched** — core `I-POS-*` plus extension positives.
9. **Verdict** — `specification`, `incidental`, or `ambiguous`.
10. **Severity** — `block`, `warn`, or `info`.
11. **Recommended action** — `rewrite-from-requirement`, `add-assertion`,
    `split`, `narrow-the-seam`, `move-to-unit-lane`,
    `replace-with-contract-test`, `delete`, or `keep`.

## E2E Rubric Fields

For every E2E test case, emit:

1. **User-outcome statement** — one sentence answering what the user
   accomplishes or experiences. If none can be stated, say
   `no stateable user outcome`.
2. **Scope statement** — why a cheaper test could not prove the same thing. If
   none can be stated, say `no stateable scope`.
3. **Sub-lane** — `F` functional, `A` accessibility, `P` performance, or `S`
   security.
4. **Test size** — almost always `large`.
5. **Selector provenance** — `accessible-name`,
   `test-id-with-accessible-fallback`, `test-id-only`, `css-or-xpath`, or
   `mixed`.
6. **Wait strategy** — `condition-based`, `mixed`, `wall-clock`, or `none`.
7. **Fixture and data provenance** — `per-test-factory`,
   `shared-immutable`, `shared-mutable`, `external-snapshot`,
   `pasted-literal`, or `unknown`.
8. **Assertion target** — `user-observable-outcome`, `url-only`,
   `element-presence-only`, `snapshot`, `pixel-baseline`,
   `published-contract`, or `none`.
9. **Smells matched** — core `E-*` plus loaded extension codes.
10. **Positive signals matched** — core `E-POS-*` plus extension positives.
11. **Verdict** — `specification`, `characterization`, `incidental`, or
    `ambiguous`.
12. **Severity** — `block`, `warn`, or `info`.
13. **Recommended action** — `rewrite-from-user-story`, `add-assertion`,
    `split`, `narrow-the-journey`, `move-to-integration-lane`,
    `move-to-unit-lane`, `replace-selector-strategy`,
    `replace-wait-strategy`, `delete`, or `keep`.

## Finding Shape

```markdown
#### `TestFile.cs::Method_Scenario_Expected` (L42)

- **Rubric:** unit
- **Intent:** Persists an order when checkout succeeds.
- **Provenance:** unknown — expected value is a pasted literal with no fixture link.
- **Assertion target:** internal-mock-invocation
- **Smells:** HC-5, HC-7, dotnet.HC-1
- **Positive signals:** —
- **Verdict:** characterization
- **Severity:** warn
- **Action:** rewrite-from-requirement. Replace the internal interaction assertion with an observable return-value or state assertion.
```

Use the matching field names for integration and E2E findings. Include the
rubric on every finding so mixed files remain auditable.

## Severity Rules

- `block` — no assertions (`HC-1` / `I-HC-A10` / `E-HC-F1`), test logic that
  makes the test self-fulfilling (`HC-4`), tautology against trivial SUT
  (`HC-2`), every-dependency-mocked integration tests (`I-HC-A1`), transport
  mocks in contract tests (`I-HC-B5`), test-only endpoints
  (`I-HC-B2` / `E-HC-S5`), E2E re-proving an integration contract
  (`E-HC-F10`), or E2E security tests that assert only server headers
  (`E-HC-S1`).
- `warn` — characterization or incidental verdicts, interaction-only
  assertions on owned code, pasted literals, shared mutable fixtures,
  wall-clock waits, fragile setup, log-text assertions, empty-database
  migration tests, happy-path-only auth tests, implementation selectors, DOM
  or pixel snapshots without a workflow, uncited accessibility or performance
  contracts.
- `info` — low-confidence smells, ambiguous verdicts, or missing negative
  cases where the contract evidence is incomplete.

## Examples

### Integration

```markdown
#### `OrdersApiTests.cs::Get_Orders_Returns_Seeded_Rows` (L48)

- **Rubric:** integration
- **Scope:** no stateable scope — depends on order from a previous test.
- **Sub-lane:** A
- **Test size:** medium
- **Seam narrowness:** broad
- **Fixture/data provenance:** shared-mutable
- **Assertion target:** response-value
- **Smells:** I-HC-A2, I-HC-A4, I-LC-6
- **Positive signals:** —
- **Verdict:** incidental
- **Severity:** warn
- **Action:** narrow-the-seam. Use per-test data ownership and assert only the rows this test created.
```

### E2E

```markdown
#### `SignInJourney.cs::Login_Flow_Works` (L32)

- **Rubric:** e2e
- **User-outcome:** no stateable user outcome — the name describes UI steps.
- **Scope:** no stateable scope — a cheaper auth integration test would prove the asserted URL.
- **Sub-lane:** F
- **Test size:** large
- **Selector provenance:** css-or-xpath
- **Wait strategy:** wall-clock
- **Fixture/data provenance:** shared-mutable
- **Assertion target:** url-only
- **Smells:** E-HC-F1, E-HC-F2, E-HC-F3, E-HC-F5, E-HC-F6, E-HC-F10
- **Positive signals:** —
- **Verdict:** characterization
- **Severity:** block
- **Action:** rewrite-from-user-story. Assert a user-observable authenticated state with accessible-name locators and condition-based waits.
```

## Deep-Mode Rollup

After per-test findings in deep mode, emit the rollup defined by
[deep-mode-output-format.md](deep-mode-output-format.md).
