# Audit Rules And Common Mistakes

**When this runs:** read before finalizing audit findings. `SKILL.md` keeps
the short working set; this file carries the cross-rubric rules and common
auditor mistakes that prevent noisy or misrouted reviews.

## Rules Common To All Rubrics

- **Assume the code under test may be wrong.** Never use observed SUT output as
  ground truth for an expected value.
- **Test through public API and observable behavior.** Do not flag missing
  tests for private methods, framework code, or pure delegation glue.
- **Extensions augment, never override.** A carve-out suppresses a core smell
  only for the exact pattern it describes.
- **Respect extension `Applies to:` tags.** Only cite an extension smell when
  the selected rubric matches the tag; absent tags default to unit for
  backwards compatibility.
- **Be honest about static limits.** Git history, coverage, mutation, flake
  history, spec links, and contract pacts can change verdicts; name the limit
  instead of fabricating certainty.
- **Run mutation testing in deep mode when installed and applicable.** Use the
  extension's detection command first. If unavailable, unsupported, or failed,
  report state B/C and continue with static findings.
- **Mutation augments static audit.** A surviving mutant in a file rated strong
  by static audit is a reconciliation finding, not an automatic verdict
  downgrade.
- **Run SUT surface enumeration only in deep mode.** Gap detection is
  suite-level and noisy for single-file or PR-diff audits.
- **Gap findings are probable until verified.** Static-only gaps must carry
  confidence and a next verification step. Never convert a probable gap into an
  implementation-only work item; use mutation evidence or manual review before
  treating it as confirmed.
- **One finding per test, under one rubric.** Cite all matched smells, but make
  the verdict reflect the dominant failure.
- **Reward positive signals explicitly.** A useful audit names what is working.
- **Stay read-only during audits.** Do not modify tests or production code
  unless the user explicitly asks for fixes.

## Unit-Specific Rules

- Mock invocation is a last resort. Flag mocks of same-layer code; do not flag
  process-boundary mocks unless an extension says otherwise.
- A test without a stateable requirement is characterization regardless of how
  polished it looks.
- Labeled characterization scaffolding under `characterization/`, `legacy/`,
  or `golden/`, or with a clear scaffold comment, is not a characterization
  smell.

## Integration-Specific Rules

- Every integration test must state what it integrates and why a unit test
  would not do.
- Prefer narrow integration tests: one SUT, one real dependency, one seam.
  Broad tests must justify their breadth.
- Inside an integration test, a mock is a scope leak unless it represents a
  process or deployment boundary and no contract test is available.
- At service boundaries, prefer consumer-driven contracts over mocks.
- Test data is owned per test; shared mutable fixtures are a smell.
- Log and trace assertions are valid only against published structured
  contracts.
- Flake is a scope signal, not a quarantine problem.

## E2E-Specific Rules

- Every E2E test must state both its user outcome and why no cheaper lane can
  prove it.
- Default to no. Promote coverage to E2E only when the browser/user-agent seam
  is necessary.
- Name tests as user stories, not UI steps.
- Use accessible-name locators; implementation selectors are characterization
  in disguise.
- Use condition-based waits only.
- Each test owns its own browser context and session state.
- DOM snapshots and pixel baselines are valid only with a review gate, owner,
  and drift process.
- Performance budgets cite Web Vitals, RUM baselines, or team SLOs.
- Accessibility audits cite a WCAG conformance level and justify suppressions.
- Browser-security E2E tests exercise browser enforcement, not just response
  headers.
- Failure-only traces, screenshots, DOM snapshots, and console logs are
  diagnostics, not assertions.

## Common Auditor Mistakes

- Applying the unit rubric to a real host/server/container/emulator test.
- Applying the integration rubric to a direct-construction unit test.
- Applying the integration rubric to browser-driven tests.
- Applying the E2E rubric to HTTP/API contract tests that do not use a browser.
- Treating E2E security header checks as browser-security proof when they
  assert only server response values.
- Flagging heavy setup as a unit smell when the test was correctly routed to
  integration or E2E.
- Flagging failure diagnostics as snapshot assertions.
- Treating grep-based probable gaps as confirmed gaps. Public methods can be
  covered indirectly, interface methods can be exercised through
  implementations, and public-by-access methods can be private-by-intent.
- Running surface enumeration or mutation testing in quick mode.
- Running mutation testing against E2E targets.
- Flagging snapshots whose output is the published contract, such as RFC test
  vectors or schema-backed API responses.
- Treating `verify(mock...)` as a smell when the verified call is the published
  behavior, such as an outbound message, audit event, or process-boundary call.
- Calling a boundary-value assertion tautological just because it duplicates a
  simple case.
- Demanding intent for explicitly labeled characterization scaffolding.
- Scoring quality from coverage alone.
- Fabricating certainty about expected-value correctness when provenance is
  unknown.
- Stacking findings instead of reporting the one finding that matters.
- Treating a high mutation score as proof that tests are specification tests.
- Running mutation tooling without the extension's detection command first.
- Treating mutation failure as audit failure.
