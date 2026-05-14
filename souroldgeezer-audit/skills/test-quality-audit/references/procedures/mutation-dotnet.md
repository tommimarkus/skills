# .NET Mutation Testing Procedure

Load only in Deep mode when the .NET extension is active and mutation evidence
is requested or the Deep audit reaches the mutation section. Never load for
Quick audits.

Stryker.NET cannot mutate every .NET SUT shape. Before attempting a run, check
the limitations in this file and report the exact skip state when a limitation
applies.

## Mutation tool

The core skill runs mutation testing conditionally in deep mode (see [SKILL.md § Mutation testing (conditional)](../../SKILL.md)). It uses the subsections below to decide whether Stryker.NET is available, how to run it, and whether the SUT is a shape the tool can handle. Applies under unit and integration rubrics; never run under the E2E rubric.

### 1. Tool name and link

**[Stryker.NET](https://stryker-mutator.io/docs/stryker-net/introduction/)** — mutation testing for .NET Core and .NET Framework. Prefer it over coverage-only tools.

### 2. Install instructions

The preferred install path is a **local tool manifest** so the Stryker version is pinned in git and every contributor gets the same tool. From the repo root:

```bash
dotnet new tool-manifest        # creates .config/dotnet-tools.json (skip if it already exists)
dotnet tool install dotnet-stryker
```

Commit `.config/dotnet-tools.json`. Future contributors run `dotnet tool restore` to get the same version. Add `StrykerOutput/` to `.gitignore` — Stryker writes its reports there and they should not be committed.

If the user has `StrykerOutput/` missing from `.gitignore`, suggest adding it as part of the install step; do not add it unilaterally.

Global install (fallback, not preferred because it's unpinned):

```bash
dotnet tool install -g dotnet-stryker
```

### 3. Detection command

Check whether Stryker is installed and invokable from the audit target. The audit agent runs this before attempting a mutation run and skips the step gracefully if it exits non-zero.

```bash
# Preferred: local manifest (exit 0 if installed locally)
dotnet tool list --local 2>/dev/null | grep -q dotnet-stryker \
  || dotnet tool list --global 2>/dev/null | grep -q dotnet-stryker
```

If the repo has a `.config/dotnet-tools.json`, also run `dotnet tool restore` before the detection command — the tool may be declared but not yet restored on a fresh clone.

### 4. Run command

Run from the **test project directory**, not the solution root. Stryker auto-discovers the SUT from the test project's `<ProjectReference>` entries.

**Baseline (full project):**

```bash
cd tests/<TestProject>
dotnet stryker --reporter json --reporter cleartext --reporter html
```

- `--reporter json` produces `StrykerOutput/<timestamp>/reports/mutation-report.json` — this is what the audit agent parses to extract scores and surviving-mutant details.
- `--reporter cleartext` produces the summary table printed at the end of the run — used for a quick human-readable snapshot.
- `--reporter html` produces a browser-viewable report with surviving mutants highlighted inline in source — useful for the user after the audit.

**PR-scoped (fast):**

```bash
dotnet stryker --since main --reporter json
```

Only mutates files changed since the `main` branch. Use this when the audit target is a PR diff rather than the full test suite.

**Single-file (demo / targeted):**

```bash
dotnet stryker --mutate "**/<FileName>.cs" --reporter cleartext
```

Useful for demonstrating mutation testing on one file without waiting for a full run. Typical runtime: seconds.

**Useful flags:**

- `--mutation-level` — controls aggressiveness. Default is `Standard`; `Advanced` and `Complete` generate more mutants but take proportionally longer.
- `--concurrency <N>` — override default CPU parallelism. Default is all cores.
- `-b|--break-at <0-100>` — return non-zero exit code if score drops below threshold. Useful for CI gating, not for audits.
- `--diag` — enable diagnostic logging when troubleshooting a failed run.

### 5. Known SUT limitations

Stryker.NET cannot mutate every .NET SUT shape. Before attempting a run, the audit agent should check for each of these patterns and skip with the documented workaround if any match.

#### Blazor WebAssembly (`Microsoft.NET.Sdk.BlazorWebAssembly` SDK)

- **How to detect:** any project in the test project's transitive `<ProjectReference>` closure uses `<Project Sdk="Microsoft.NET.Sdk.BlazorWebAssembly">` or references `Microsoft.AspNetCore.Components.WebAssembly`. The direct test csproj can be a plain `Microsoft.NET.Sdk` library — Stryker still compiles the full closure during its recompile step and hits the same Razor-generator error. Walk the chain: start at the test project's csproj, read its `<ProjectReference>` entries, and recurse into each referenced csproj. Stop at the first Blazor WASM SDK match.
- **Root cause:** Blazor WASM's `Program.cs` references types like `App` that are generated at build time by the Razor source generator from `.razor` files. Stryker runs its own Roslyn compilation step for each mutation batch and does **not** invoke source generators during that step. The generated types are therefore unresolvable during Stryker's mutated-recompile, producing `CS0246: The type or namespace name 'App' could not be found` and `CS8805: Program using top-level statements must be an executable` errors. There is no Stryker config option that excludes files from the internal recompilation step — the `mutate` option (with or without `!` exclusion patterns) only controls which files receive mutants, not which files get compiled. Verified against the official docs at https://stryker-mutator.io/docs/stryker-net/configuration/ and https://stryker-mutator.io/docs/stryker-net/ignore-mutations/ (2026-04).
- **Workaround:** extract pure-C# logic (services, HTTP clients, state managers, i18n, helpers) from the Blazor WASM project into a separate class library (e.g. `<AppName>.Core`). Reference that library from the Blazor project. Create a dedicated test project for the library that references **only** the extract (no transitive path to the Blazor WASM SDK). Run Stryker against that test project — it has no Razor dependencies and mutates cleanly. Blazor component tests (e.g. bUnit) stay in the Blazor test project and continue to rely on static audit for quality signal. This is also the approach the Stryker.NET team recommends for projects using source generators of any kind. Tip: set `<RootNamespace>` on the extract csproj to the Blazor project's original root namespace so the moved files keep their declared namespaces and consumer code (`.razor`, `Program.cs`, existing tests) needs no edits.
- **Audit output when detected:** before skipping, check whether the workaround is already in place. The "already-extracted" pattern: (a) the Blazor WASM project `<ProjectReference>`s a class library that uses plain `<Project Sdk="Microsoft.NET.Sdk">` (not the WebAssembly SDK), AND (b) some test project's transitive `<ProjectReference>` closure reaches that library WITHOUT reaching any Blazor WASM SDK project. When both conditions hold, the refactor is already done — use that test project as the Stryker target.
  - **Extract already applied:** run Stryker against the extract's test project as the mutation target. Skip the Blazor-transitive test project(s) with state C (citing this subsection) and **do not** emit the `P3` refactor recommendation — the refactor is already done. Note in the Mutation testing subsection that the extract was detected and used as the target.
  - **No extract yet:** skip the Blazor-transitive test project(s) with state C, cite this subsection, and emit the extract-to-library workaround as a `P3` item in the remediation worklist. Continue the mutation run against any other non-Blazor projects in scope (e.g. a separate backend project).

#### Other source-generator-heavy projects

Projects that rely heavily on source generators (e.g. `[LoggerMessage]`-only codebases, Mapperly, Refit, MediatR source generator) may hit similar "generated type not found" errors during Stryker's mutated-recompile. The audit agent should:

1. Attempt the run.
2. If it fails with `CS0246` on a type that grep suggests is generator-produced (check for `[<GeneratorAttributeName>]` in the SUT), treat as a known limitation, report state C with the specific generator named as the root cause, and recommend a selective `--mutate` exclude of the files that reference the generator output (this may or may not help — document uncertainty honestly).

#### .NET Framework projects without `msbuild-path`

Stryker requires `--msbuild-path` on .NET Framework (classic) projects. If the SUT is .NET Framework and the detection command succeeds but the run fails with MSBuild errors, instruct the user to pass `--msbuild-path` pointing at their Visual Studio or Build Tools MSBuild installation.

### 6. Output parser notes

- **Report location:** `<test-project>/StrykerOutput/<timestamp>/reports/mutation-report.json`. The timestamp is `YYYY-MM-DD.HH-MM-SS`; pick the newest directory if multiple exist.
- **Top-level score:** the last line of the cleartext report prints `The final mutation score is N.NN %`. The JSON report stores per-file data; the overall score is computed as `(killed + timeout) / (killed + survived + timeout + no_coverage)`. Ignored and compile-error mutants are excluded from the denominator.
- **Per-file extraction:** iterate `.files` in the JSON; for each file, group `.mutants` by `.status`. Meaningful statuses are `Killed`, `Survived`, `NoCoverage`, `Timeout`, `Ignored`, `CompileError`.
- **Surviving-mutant details:** for each surviving mutant, extract `.location.start.line`, `.mutatorName`, and `.replacement` (or `.description`) to show what was changed. This is the raw material for the "audit-vs-mutation disagreement" reconciliation in step 5 of deep-mode output.
- **Files entirely without tests:** filter for files whose mutant list has zero `Killed` + zero `Survived` + zero `Timeout` entries. These are the "no test touches this file" findings the static audit cannot see.

### When to run it

**Always run in deep mode when the detection command succeeds**, regardless of which smells the static audit found. Mutation testing's highest-value output is the audit-vs-mutation disagreement: files rated `strong` by static audit that have surviving mutants. Those disagreements only surface if you run the tool unconditionally on a successful-audit suite.

If the suite has many `HC-1` / `HC-3` / `HC-5` / `HC-6` / `dotnet.HC-5` / `dotnet.HC-6` findings, the mutation run is especially valuable — those smells all indicate tests that execute code without verifying it, which mutation testing surfaces mechanically — but this is not a gating criterion.
