# TypeScript Software Design Extension

Load for JavaScript/TypeScript `package.json`, `tsconfig.json`, project
references, source/declaration, JSDoc, `checkJs`, or `allowJs`. Own
package/module/runtime design; delegate UI, HTTP, security, and tests to
`app-design`, `api-design`, `devsecops-audit`, and `test-quality-audit`.

Sources: https://www.typescriptlang.org/docs/handbook/project-references.html;
https://www.typescriptlang.org/docs/handbook/modules/reference.html;
https://www.typescriptlang.org/tsconfig/;
https://www.typescriptlang.org/docs/handbook/intro-to-js-ts.html;
https://www.typescriptlang.org/tsconfig/checkJs.html;
https://nodejs.org/api/packages.html;
https://nodejs.org/api/globals.html#class-abortcontroller;
https://docs.npmjs.com/cli/v11/configuring-npm/package-json/.

## project-first review

Assimilate project package/runtime/build/validation contracts. Inspect package
`type`/`exports`/`imports`/`types`/`bin` and
`dependencies`/`peerDependencies`/optional roles; compiler references,
declarations/output, `module`/`moduleResolution`, aliases, `allowJs`/`checkJs`;
exports, generated boundary types, runtime state, resources, errors, and
performance evidence.

Defaults:

- Keep JS/JSDoc when sufficient; use `checkJs` selectively and `allowJs` only
  for an owned migration. Types never validate runtime input.
- Project references and package dependencies tell one story. Dependency roles
  reflect whether consumers receive runtime, peer-provided, or optional behavior.
- Align package metadata, compiler/emitted resolution, bundler, and runtime.
  conditional exports serve every supported import/require consumer; aliases,
  declarations, or test resolvers must not mask a missing branch. Mutable module
  state has one owner or is instance-scoped across dual/skewed loads.
- Public exports/subpaths and declarations are compatibility contracts. Prefer
  configured checks; otherwise run bounded declaration/import smokes. Paths
  must not bypass public exports; generated DTO/schema/domain types need a
  translator.
- Thread one `AbortSignal` through cancellable boundaries; name who creates,
  cancels, closes, and joins promises, timers, streams, listeners, and tasks.
  Give each boundary one error contract owner for translation, retry, timeout,
  fallback, and cleanup (`SD-S-5`, `SD-Q-4`, `SD-C-6`).
- Measure performance hypotheses before/after with named workload and
  profile/trace/bundle/latency evidence; never infer gains.

Validate with project typecheck/`tsc`, build/declarations, public-type diff, and
entrypoint smoke. Request `devsecops-audit` Quick for security-sensitive changes.

Smell families: `typescript.SD-B-*` boundary/config; `typescript.SD-C-*`
coupling; `typescript.SD-S-*` semantic drift; `typescript.SD-W-*` ceremony;
`typescript.SD-E-*` evolution; `typescript.SD-Q-*` validation/ownership.

Key codes only: `typescript.SD-B-2` exports/declarations/source disagree;
`typescript.SD-C-2` imports bypass exports; `typescript.SD-S-1` generated types
drift without translator; `typescript.SD-E-1` exported type invites brittle
structural dependency; `typescript.SD-Q-1` type-only boundary stands in for
runtime validation. Use core `SD-*` otherwise. Never flag syntax, generics,
barrels, exports, references, or aliases without evidenced design risk.
