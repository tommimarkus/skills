# Determinism verification

**When this runs:** optional determinism verification in [../../SKILL.md](../../SKILL.md). Deep may compare two non-E2E suite runs. Quick may confirm only its bounded target using a known project command; it does not load the whole Deep extension or establish suite-level stability. A pass/fail divergence is observed flakiness, stronger evidence than a static smell.

## Why two runs is worth the cost

Static smells `HC-11`, `LC-5`, `I-HC-A5`, `I-HC-A11`, `E-HC-F3` all flag *suspected* determinism problems. Two runs convert suspicion into evidence. The cost is a second test-suite execution. Gate on:

- **Suite size** — a test project with < 500 methods and known-fast execution (< 60 s) reruns cheaply. Larger suites take proportionally longer; the audit agent should recommend but not run.
- **Task authority and safety** — apply [testing-core's local-confirmation rule](../../../../docs/quality-reference/testing-core.md#local-confirmation-and-task-authority). A cheap known-safe local confirmation within the requested audit can proceed under existing task authority; explicit no-rerun, existing-results-only, count, and scope limits remain binding. Ask before work whose safety, cost, side effects, or authority is unclear.
- **Command evidence** — use a known project-configured command or the selected extension's documented cheap-rerun command. If neither establishes safe scope, skip or ask; do not load a whole Deep pack merely for a Quick confirmation.
- **Existing findings** — if prior steps already produced five or more static determinism smells, the marginal value of the second run is lower. Run only if the user explicitly asks.

## Procedure

1. **Apply the shared execution rule** before either run. Use the configured target command or selected extension's determinism-verification section; if neither is known, skip. Keep a Quick confirmation within its named target without claiming Deep suite coverage.
2. **Run the test project(s) once** via the extension's cheap-rerun command, within the authorized scope. Capture the pass / fail list — prefer test-result XML (`.trx` for .NET, JUnit XML for most other stacks) for structured parsing.
3. **Run the same test project(s) again**, isolated from the first run's state (fresh process for xUnit / NUnit, `pytest --forked` for Python). Capture a second pass / fail list.
4. **Diff the two lists:**
   - A test that passed both times → stable.
   - A test that failed both times → deterministic failure (a non-flake bug).
   - A test that passed once and failed once → **flake**. This is the finding.
   - A test that errored with a different exception between runs → also a flake.
5. **Emit a `## Determinism findings` subsection** in the step-5 suite assessment listing each flake, its test name, the failure messages from both runs, and the suspected cause (cross-reference to any static smell that fired on that test).

## Output (appended to the step-5 suite assessment)

```markdown
### Determinism findings (runtime-proven)

- **`OrderServiceTests.GetOrders_Returns_Seeded_Rows`** — passed run 1, failed run 2 with `assert HaveCount(1), was 2`. Matches static smell `dotnet.I-HC-A1` (shared `WebApplicationFactory` with no per-test data scoping). Root cause: prior test left rows in the container.
- **`TokenCacheTests.Expires_After_Ttl`** — passed run 1, passed run 2 with different elapsed time (490 ms vs 512 ms). No divergence; not flagged.
```
```markdown
### Determinism findings (skipped)

- **Reason:** suite size (827 test methods) exceeds the 500-method threshold for automatic rerun. Recommend: rerun a bounded sample from the slow tail recorded in `## Suite health`, or opt in explicitly for a full rerun.
```
