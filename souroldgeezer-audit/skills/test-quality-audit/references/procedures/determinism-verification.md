# Determinism verification

**When this runs:** step 4.5 of the deep-mode workflow in [../../SKILL.md](../../SKILL.md). Runs the non-E2E test suite twice in sequence and compares the pass / fail list. Any test that passes once and fails once (or produces a different error) is a runtime-proven flake — stronger evidence than any static smell. Optional; gated on project size.

## Why two runs is worth the cost

Static smells `HC-11`, `LC-5`, `I-HC-A5`, `I-HC-A11`, `E-HC-F3` all flag *suspected* determinism problems. Two runs convert suspicion into evidence. The cost is a second test-suite execution. Gate on:

- **Suite size** — a test project with < 500 methods and known-fast execution (< 60 s) reruns cheaply. Larger suites take proportionally longer; the audit agent should recommend but not run.
- **User authorization** — determinism verification is additional execution. Before its first run, apply the shared consent check in [the Deep output procedure](deep-mode-output-format.md): proceed only when existing user authorization explicitly covers the reruns and their scope; otherwise ask first. Runtime estimates and batch flags do not grant authority.
- **Extension support** — the loaded extension must declare a cheap-rerun command. Without it, skip the step.
- **Existing findings** — if prior steps already produced five or more static determinism smells, the marginal value of the second run is lower. Run only if the user explicitly asks.

## Procedure

1. **Pass the shared consent check** before either run. Read the extension's determinism-verification section; if absent, skip.
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
