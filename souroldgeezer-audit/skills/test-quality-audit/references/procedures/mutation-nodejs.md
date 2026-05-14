# Node.js / TypeScript Mutation Testing Procedure

Load only in Deep mode when the Node.js / TypeScript extension is active and
mutation evidence is requested or the Deep audit reaches the mutation section.
Never load for Quick audits.

Stryker JS cannot mutate every JavaScript / TypeScript SUT shape. Before
attempting a run, check the limitations in this file and report the exact skip
state when a limitation applies.

## Mutation tool

The core skill runs mutation testing conditionally in deep mode (see [SKILL.md § Mutation testing (conditional)](../../SKILL.md)). It uses the subsections below to decide whether Stryker Mutator JS is available, how to run it, and whether the SUT is a shape the tool can handle. Applies under unit and integration rubrics; never run under the E2E rubric.

### 1. Tool name and link

**[StrykerJS (Stryker Mutator)](https://stryker-mutator.io/docs/stryker-js/introduction/)** — mutation testing for JavaScript and TypeScript. Runner-neutral (Jest / Vitest / Mocha / Karma / Cucumber all supported via dedicated runner plugins).

### 2. Install instructions

Install Stryker plus the runner matching the detected test runner. From the repo root:

```bash
npm install --save-dev @stryker-mutator/core
# Pick one based on the detected runner:
npm install --save-dev @stryker-mutator/jest-runner       # Jest
npm install --save-dev @stryker-mutator/vitest-runner     # Vitest
npm install --save-dev @stryker-mutator/mocha-runner      # Mocha
# TypeScript projects — adds compile-error elimination:
npm install --save-dev @stryker-mutator/typescript-checker
```

Create a minimal `stryker.conf.mjs` at the repo root:

```js
/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
export default {
  packageManager: 'npm',
  reporters: ['clear-text', 'progress', 'html', 'json'],
  testRunner: 'vitest',                 // or 'jest' / 'mocha'
  coverageAnalysis: 'perTest',
  checkers: ['typescript'],             // omit on JS-only projects
  tsconfigFile: 'tsconfig.json',
  mutate: ['src/**/*.ts', '!src/**/*.test.ts', '!src/**/*.spec.ts'],
};
```

The default reporter set is `['clear-text', 'progress', 'html']`; adding `json` gives the audit agent a machine-readable report alongside the defaults. See https://stryker-mutator.io/docs/stryker-js/configuration/#reporters-string for the full reporter list.

Add `.stryker-tmp/` and `reports/mutation/` to `.gitignore`. Commit `stryker.conf.mjs`. Future contributors run `npm install` to get the pinned Stryker version from `package-lock.json`.

**Monorepo note:** in a workspaces repo, run Stryker from inside each workspace (with its own `stryker.conf.mjs`), not at the repo root — the mutation pass needs per-workspace `package.json` / runner context to resolve correctly.

### 3. Detection command

Check whether Stryker is installed and invokable from the audit target. The audit agent runs this before attempting a mutation run and skips the step gracefully if it exits non-zero.

```bash
# Side-effect-free check: prefer the local install (project-pinned) over global.
test -x node_modules/.bin/stryker \
  || npx --no-install stryker --version >/dev/null 2>&1
```

In a workspaces repo, run the detection inside the specific workspace being audited, not at the repo root.

### 4. Run command

Run from the **repo root or workspace root** (wherever `stryker.conf.mjs` lives).

**Baseline (full project):**

```bash
npx stryker run --reporters json,html,clear-text
```

- `--reporters json` produces `reports/mutation/mutation.json` — this is what the audit agent parses to extract scores and surviving-mutant details.
- `--reporters html` produces `reports/mutation/mutation.html` — browser-viewable report with inline surviving-mutant highlights for the user.
- `--reporters clear-text` produces the summary table printed at the end of the run.

**PR-scoped (fast):**

```bash
npx stryker run --since main
```

Mutates only files changed since `main`. Use when the audit target is a PR diff rather than the full suite.

**Single-file (demo / targeted):**

```bash
npx stryker run --mutate "src/services/pricing.ts"
```

Useful for demonstrating mutation testing on one file without waiting for a full run. Typical runtime: seconds.

**Useful flags:**

- `--mutationScore <threshold>` — configure the `thresholds.break` value in config. Used for CI gating, not audits.
- `--concurrency <N>` — override default parallelism. Default is half the available CPU cores; Stryker JS is IO-heavy and setting `concurrency: N` matching the runner's own worker count is often faster.
- `--incremental` — only re-mutate files changed since the last recorded incremental run (`reports/stryker-incremental.json`). Fastest for iterative local use once a baseline exists.
- `--dryRunOnly` — run the initial unmutated test pass and stop. Useful for debugging `stryker.conf.mjs` without paying for the full mutation run.
- `--logLevel debug` (or `trace`) — enable diagnostic logging when troubleshooting a failed run.

### 5. Known SUT limitations

Stryker JS cannot mutate every JavaScript / TypeScript SUT shape. Before attempting a run, the audit agent should check for each of these patterns and skip with the documented workaround if any match.

#### ESM-only packages (`"type": "module"` with no CJS interop layer)

- **How to detect:** `package.json` declares `"type": "module"` AND the project's runner config is Jest (Jest's ESM support is behind `--experimental-vm-modules` as of v29). Vitest is native ESM and doesn't hit this. The audit agent reads `package.json` and detects this combination.
- **Root cause:** Stryker's Jest runner sandboxes mutants using CJS module resolution. An ESM-only SUT — one that uses `import ... from '...'` with no bundler step and expects native Node ESM — trips the runner's module-loader assumptions. Vitest's runner is ESM-native and handles this cleanly.
- **Workaround:** if the project is Jest + ESM, either (a) migrate the test runner to Vitest (native ESM, often a one-hour migration) and use `@stryker-mutator/vitest-runner`, or (b) transpile-to-CJS via a Stryker `files` / `testRunnerNodeArgs` configuration hook — document the hook in `stryker.conf.mjs`. If neither is possible, skip with state C citing ESM-only + Jest.

#### TypeScript path aliases (`compilerOptions.paths`)

- **How to detect:** `tsconfig.json` declares a non-empty `compilerOptions.paths` mapping (e.g. `{ "@/*": ["src/*"] }`).
- **Root cause:** Stryker's `@stryker-mutator/typescript-checker` reads `tsconfig.json` at startup, but paths resolution only works when `tsconfigFile` is set in `stryker.conf.mjs`. Without it, mutants that import via `@/*` aliases fail to compile, producing false-positive `CompileError` mutants.
- **Workaround:** set `tsconfigFile: 'tsconfig.json'` in `stryker.conf.mjs` (or the path to the project-relative tsconfig). For monorepos, set the per-workspace tsconfig. This is a config fix, not a skip — the audit should recommend the one-line config change before skipping.

#### Monorepo workspaces (`package.json` with `"workspaces"`, pnpm-workspace.yaml, turbo.json, nx.json)

- **How to detect:** repo root has any of `package.json` with `"workspaces"`, `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json`.
- **Root cause:** Stryker resolves the test runner and its deps relative to the directory where `stryker.conf.mjs` lives. Running at the repo root in a workspaces monorepo picks up the root `node_modules/` but tests live in `packages/*/test/` and depend on per-workspace dependencies.
- **Workaround:** run Stryker inside each workspace with its own `stryker.conf.mjs`. The audit should iterate over each workspace matching the detection signals and run Stryker separately per workspace, aggregating the per-workspace JSON reports.

#### Next.js App Router source files (`app/**/*.{ts,tsx}`) — probable but not officially documented

- **How to detect:** the `nextjs` extension is loaded and the target includes files under `app/`.
- **Root cause (provisional):** Next.js's App Router files are compiled by the Next SWC pipeline at build time, which applies Server Component / Client Component boundary transforms (`'use client'` / `'use server'` splits, RSC payload generation, server-only module stripping). Stryker's runner compiles mutants through the Jest / Vitest runner's transformer, which does not apply these Next transforms. Mutants of files under `app/` may compile but fail at runtime, or fail compilation entirely.
- **This is probable, not officially documented.** Stryker JS's docs do not currently call out Next.js App Router as an unsupported target (as of the reference audit — 2026-04). First-audit workaround: attempt the run. If it succeeds, remove this caveat and report the success; if it fails with RSC-related errors, treat as state C and recommend the extract-to-library workaround below.
- **Workaround (if confirmed unsupported):** extract server-side logic (pure services, validators, formatters) from `app/` into a plain TS library (e.g. `lib/` or a separate workspace package). Reference the library from `app/` — your Server Components / Route Handlers / Server Actions become thin adapters. Mutate the library, not `app/`. Matches the Blazor WASM workaround in [`../extensions/dotnet/core.md`](../extensions/dotnet/core.md).

#### Files the project intentionally excludes from tests

- **How to detect:** the test runner's config has `testPathIgnorePatterns` / `exclude` / `coveragePathIgnorePatterns` listing files or directories (type-only `.d.ts` files, generated code, vendored code).
- **Root cause:** files with no tests always produce `NoCoverage` mutants. They're not a Stryker limitation — they're a known gap that mutation testing correctly surfaces.
- **Workaround:** no workaround needed; the `NoCoverage` report entries are the valuable output. Filter them into the "no-coverage discoveries" subsection of the deep-mode output.

### 6. Output parser notes

Stryker's JSON reporter writes the standard [mutation-testing-elements report schema](https://github.com/stryker-mutator/mutation-testing-elements/blob/master/packages/report-schema/src/mutation-testing-report-schema.json) (`schemaVersion: "1.x"`). Fields the audit agent reads:

- **Report location:** `reports/mutation/mutation.json` relative to the config-file directory (configurable via the `jsonReporter.fileName` option). The HTML report lives at `reports/mutation/mutation.html`.
- **Top-level fields:** `schemaVersion`, `thresholds: { high, low }`, `framework`, `system`, `config`, `files`, `testFiles`. There is **no** top-level `mutationScore` in the JSON; the score is computed from the mutant status counts (the cleartext reporter does print `Mutation score: N.NN%` and `Mutation score based on covered code: N.NN%` — `/reports/html/index.html` also displays the computed score).
- **Per-file extraction:** iterate `files` (an object keyed by file path relative to the project root). For each file, iterate `mutants` and group by `status`. Meaningful statuses: `Killed`, `Survived`, `NoCoverage`, `Timeout`, `Ignored`, `CompileError`, `RuntimeError`, `Pending`.
- **Surviving-mutant details:** for each surviving mutant, extract `location.start.line` / `location.start.column`, `mutatorName`, `replacement`, and `statusReason` (populated by some reporters). This is the raw material for the "audit-vs-mutation disagreement" reconciliation in step 5 of deep-mode output. The mutant's `coveredBy` / `killedBy` arrays reference test IDs in the top-level `testFiles`.
- **Score derivation:** mutation score = `killed / (killed + survived + timeout)` (excludes `NoCoverage` / `Ignored` / `CompileError` / `RuntimeError`); mutation score including no-coverage = `killed / (killed + survived + timeout + noCoverage)`. Use the same formula the CLI prints.
- **Files entirely without tests:** filter for files whose mutant list has zero `Killed` + zero `Survived` + zero `Timeout` entries (all `NoCoverage` or `Ignored`). These are the "no test touches this file" findings the static audit cannot see.

### When to run it

**Always run in deep mode when the detection command succeeds**, regardless of which smells the static audit found. Mutation testing's highest-value output is the audit-vs-mutation disagreement: files rated `strong` by static audit that have surviving mutants. Those disagreements only surface if you run the tool unconditionally on a successful-audit suite.

If the suite has many `HC-1` / `HC-3` / `HC-5` / `HC-6` / `nodejs.HC-2` / `nodejs.HC-5` findings, the mutation run is especially valuable — those smells all indicate tests that execute code without verifying it, which mutation testing surfaces mechanically — but this is not a gating criterion.
