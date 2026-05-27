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
- Node.js packages: https://nodejs.org/api/packages.html
- npm `package.json` / workspaces: https://docs.npmjs.com/cli/v11/configuring-npm/package-json/

Inspect package surface (`name`, `type`, `exports`, `imports`, `types`, `bin`,
scripts/workspaces), compiler graph (`extends`, project references,
`composite`, `declaration`, `rootDir`, `outDir`, `paths`, `moduleResolution`),
module/API surface (exports, barrels, ambient declarations, generated types),
dependency direction, DTO/schema/domain splits, runtime state, and the cheapest
typecheck/build/declaration/smoke command.

Defaults: boundaries match ownership, release, runtime, or policy; entrypoints
and framework adapters stay thin; exports, subpaths, declarations, and `.d.ts`
are compatibility contracts; `paths`/`baseUrl` must not bypass public exports;
types do not validate runtime input; generic utilities, decorators, and plugin
points need current variation.

For Build mode, include `devsecops-audit` Quick review when dynamic import/eval,
process execution, installer scripts, generated code, package export changes,
untrusted deserialization, browser/server splits, or dependency/tooling changes
are in scope and available. Otherwise use `npm/pnpm/yarn run typecheck`,
`tsc --noEmit`, `tsc -b`, build/declaration generation, or public-surface smoke.

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

Do not flag TypeScript syntax, generics, barrels, package exports, project
references, or path aliases by themselves. Flag the boundary, coupling,
semantic, evolution, or tradeoff risk and name the smaller shape.
