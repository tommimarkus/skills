# TypeScript Software Design Extension

Load for TypeScript or JS-with-TS tooling: `package.json`, lockfiles,
workspaces, `tsconfig.json`, `tsconfig.*.json`, project references, `.ts`,
`.tsx`, `.mts`, `.cts`, `.d.ts`, declarations, generated types, `checkJs`, or
`allowJs`.

Covers package/module/API surface design. Delegate UI to `app-design`, HTTP to
`api-design`, security/dependency posture to `devsecops-audit`, and tests to
`test-quality-audit`.

Sources for platform facts:
- TypeScript project references: https://www.typescriptlang.org/docs/handbook/project-references.html
- TypeScript modules: https://www.typescriptlang.org/docs/handbook/modules/reference.html
- TSConfig: https://www.typescriptlang.org/tsconfig/
- TypeScript JavaScript and JSDoc: https://www.typescriptlang.org/docs/handbook/intro-to-js-ts.html
- TypeScript `checkJs`: https://www.typescriptlang.org/tsconfig/checkJs.html
- Node.js packages: https://nodejs.org/api/packages.html
- Node.js abort-controller: https://nodejs.org/api/globals.html#class-abortcontroller
- npm `package.json` / workspaces: https://docs.npmjs.com/cli/v11/configuring-npm/package-json/

Use project-first assimilation. Before choosing a migration, compiler flag, or
tool, inspect the project-owned package manager/lockfile, workspace graph,
scripts, config inheritance, existing JS/TS boundary, supported Node/runtime,
emitter/bundler, and validation commands. Inspect package surface (`name`,
`type`, `exports`, `imports`, `types`, `bin`, scripts/workspaces, and
`dependencies`/`peerDependencies`/optional dependency roles), compiler graph
(`extends`, project references, `composite`, `declaration`, `rootDir`, `outDir`,
`paths`, `module`, `moduleResolution`, `allowJs`, `checkJs`), module/API surface
(exports, barrels, ambient declarations, generated types), dependency direction,
DTO/schema/domain splits, runtime state, and the cheapest authoritative
typecheck/build/declaration/smoke command.

Defaults: boundaries match ownership, release, runtime, or policy; entrypoints
and framework adapters stay thin; exports, subpaths, declarations, and `.d.ts`
are compatibility contracts; `paths`/`baseUrl` must not bypass public exports;
types do not validate runtime input. Keep plain JS with JSDoc when it preserves
the project boundary and confidence; use `checkJs` to type-check selected JS
and `allowJs` only for a deliberate mixed-source migration with ownership and
exit criteria, not as a silent second language. Generic utilities, decorators,
and plugin points need current variation; discriminated unions and literal-union
types carry state semantics; the project-reference graph and the package
dependency graph tell one story. Dependency-role identity must match how a
consumer receives the package: runtime requirements, peer-provided contracts,
and optional integrations must not be interchangeable.

Align package metadata, compiler resolution, emitted specifiers, bundler
resolution, and actual runtime loading. In particular, conditional exports and
their import/require branches must resolve to the same intended public contract
for each supported consumer; do not let a `paths` alias, declaration branch, or
test-only resolver mask a branch unavailable at runtime. Module-level mutable
state duplicates per module instance under dual-format or skewed loads; name a
single state owner or make the state instance-scoped.

Treat public declarations as consumer compatibility contracts: compare exported
types, overloads, generics, re-exports, subpaths, and generated declarations
with a supported baseline. Prefer the project-configured compatibility check;
otherwise use a bounded declaration/import/require smoke for each supported
entrypoint and disclose its limit. Do not claim a source-only diff proves public
declaration compatibility.

For asynchronous or streaming work, pass one `AbortSignal` through every
cancellable boundary and name who creates, closes, cancels, and joins each
promise, timer, stream, listener, or background task. Keep one error contract
owner at each module boundary: preserve domain/transport/infrastructure meaning,
translate only at the owned boundary, and assign retry, timeout, fallback, and
cleanup budgets to one layer (`SD-S-5`, `SD-Q-4`, `SD-C-6`). Delegate HTTP error
payloads to `api-design` and browser interaction to `app-design`.

Treat performance changes as hypotheses. Measure the relevant profile, trace,
bundle/runtime cost, or user-visible latency before and after the smallest move;
record the workload and limit of that performance evidence rather than inferring
benefit from types, bundler choice, or intuition.

For Build mode, include `devsecops-audit` Quick review when dynamic import/eval,
process execution, installer scripts, generated code, package export changes,
untrusted deserialization, browser/server splits, or dependency/tooling changes
are in scope and available. Otherwise use `npm/pnpm/yarn run typecheck`,
`tsc --noEmit`, `tsc -b`, build/declaration generation, a public-types
compatibility diff for published packages, or public-surface smoke. Keep the
project commands and configuration authoritative; an installed tool without a
project-owned invocation is evidence only, not a reason to prescribe a stack.

Smell codes: `typescript.SD-B-*` for package/export/tsconfig/barrel/framework
boundary drift; `typescript.SD-C-*` for dependency direction, path-alias, module
format, or ambient-state coupling; `typescript.SD-S-*` for type/runtime/DTO or
error-shape drift; `typescript.SD-W-*` for generic/plugin/facade ceremony;
`typescript.SD-E-*` for brittle public types or unvalidated reference/export
changes; `typescript.SD-Q-*` for type-only validation and browser/server or
compiler/runtime ownership gaps.

Key codes: `typescript.SD-B-2` public exports, declarations, and source exports
tell different contract stories; `typescript.SD-C-2` `paths`/relative imports
bypass public exports; `typescript.SD-S-1` generated DTO/schema/domain types
drift without translator; `typescript.SD-E-1` exported type is too structurally
easy to depend on; `typescript.SD-Q-1` type-only boundary is treated as runtime
validation.

Only these key codes are citable; the `Smell codes:` families above describe
scope only. Emit core `SD-*` for anything not covered by a key code.

Do not flag TypeScript syntax, generics, barrels, package exports, project
references, or path aliases by themselves. Flag the boundary, coupling,
semantic, evolution, or tradeoff risk and name the smaller shape.
