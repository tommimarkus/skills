# Extension - Vite App Design

This extension adds Vite application-runtime mechanics to the framework-neutral
app-design workflow. It works alone for Vite application surfaces and composes
before `react.md` for Vite + React: Vite owns build/runtime topology, while
React owns component and Hook behavior. Next.js remains React then Next.js.

Source anchors used for this extension:

- Vite guide: <https://vite.dev/guide>.
- Vite production build: <https://vite.dev/guide/build>.
- Vite static assets: <https://vite.dev/guide/assets>.
- Vite environment variables and modes: <https://vite.dev/guide/env-and-mode>.
- Vite server-side rendering: <https://vite.dev/guide/ssr>.

Re-check these official pages when the Vite major version, environment model,
SSR target, or deployment behavior is load-bearing.

## Detection Signals

- `package.json` has `vite`, `vite dev`, `vite build`, or `vite preview`.
- `vite.config.{js,ts,mjs,mts,cjs,cts}` or a Vite plugin/config import exists.
- An HTML entry uses a module script into `src/**`, or code uses
  `import.meta.env`, `import.meta.glob`, `new URL(..., import.meta.url)`, or
  `?worker` / `?url` imports.
- Build, SSR, worker, or deployment configuration names Vite explicitly.

## Scope And Composition

Own Vite-specific app-design interpretation for development server, production
build, preview, root/entry topology, public base path, assets, dynamic imports
and chunks, client-exposed environment values, browser/server/worker boundaries,
SSR, and stale deployment recovery. Generic browser app behavior stays in the
core; React component and lifecycle behavior stays in `react.md`.

1. Load this extension alone for Vite-only Build, Extract, Review, or a
   Vite-specific Lookup.
2. For Vite + React, load this extension first, then `react.md`.
3. For React + Next.js, do not load Vite merely because a toolchain dependency
   is present: retain React then Next.js unless Vite configuration itself is in
   scope.

## Project Assimilation

Inspect `package.json` scripts and pinned Vite/plugins; `vite.config.*` for
`root`, `base`, aliases, plugins, `publicDir`, build output/target, worker and
SSR settings; `index.html` and module entry points; `.env*` and mode selection;
static `public/` versus imported assets; route-host rewrite rules; dynamic import
boundaries; and deploy/cache behavior for HTML, manifest, and hashed assets.

Record whether evidence is a development server observation, production build
artifact, or preview observation. The development server provides iteration and
HMR behavior; a production build produces deployable output; preview is a local
way to inspect built output and is not production hosting evidence.

## Build, Entry, Assets, And Environments

- Make the intended `root`, HTML/module entry, output directory, and deployment
  path explicit. The default HTML entry model is not a substitute for a route
  fallback or hosting decision.
- Set `base` for a nested deployment path and test generated links, CSS URLs,
  assets, and client-side navigation at that path. Dynamic URL construction must
  use a base-aware contract rather than assuming `/`.
- Use imported assets when the build should track, transform, and fingerprint
  them; use public assets only when their stable public URL is intentional.
  Dynamic imports create independently deployed chunks: loading, error, and
  recovery UI must match that boundary.
- Treat `import.meta.env` as compile-time exposed application configuration.
  Separate modes from `NODE_ENV`, type/parse values deliberately, and never put
  secrets in a client-exposed prefix. The receiving backend or platform owns
  secret storage and API security.
- Preserve browser/server/worker boundaries. Browser entries cannot assume Node
  APIs; worker imports and message/state ownership need explicit lifecycle and
  fallback behavior; SSR code must avoid browser-only reads before the client.

## SSR And Deployment Recovery

- SSR needs distinct client and server entry ownership, a deterministic HTML
  handoff, and explicit hydration/browser-only boundaries. Select the server or
  worker target from the actual host constraints rather than assuming Node.
- Treat a stale deployment as a user-visible recovery path: a retained HTML
  document can request a removed dynamic chunk after an atomic-looking deploy.
  Keep HTML/manifest and immutable hashed assets coherent where possible; when
  a dynamic import fails, provide a bounded refresh/retry path that preserves
  unsaved work or clearly warns before reload.
- Vite's dynamic-import preload error event is a useful integration signal, but
  verify its host/browser behavior and do not claim recovery from static source.

## Responsive, Accessibility, And Performance

- Build splitting, asset choice, worker boundaries, and SSR change perceived
  readiness. Preserve layout, reachable names, focus, and error recovery across
  initial load and deferred chunks.
- Static review can inspect base-path and chunk-recovery posture. Browser and
  deployment evidence are required for real asset URLs, HMR, preview behavior,
  hydration, caching, and performance claims.

## Positive Signals

- `vite.POS-APP-1`: root, HTML/module entry, output, and deployment path have
  one explicit owner and a verified production-build artifact.
- `vite.POS-APP-2`: development server, production build, and preview have
  distinct claimed purposes and evidence layers.
- `vite.POS-APP-3`: mode/env exposure is typed, client-safe, and separate from
  deployment secrets and server configuration.
- `vite.POS-APP-4`: base path, imported/public assets, and dynamic chunks have
  a coherent URL and loading/error contract.
- `vite.POS-APP-5`: SSR and browser/server/worker entry boundaries are explicit,
  and stale deployment recovery protects the user workflow.

## Smell Codes

- `vite.APP-BUILD-1`: configuration or review treats development server or
  preview behavior as proof that the production build, host path, or rewrites work.
- `vite.APP-ENV-1`: a mode is conflated with `NODE_ENV`, client-exposed env
  value is treated as secret, or unparsed env strings choose UI behavior.
- `vite.APP-ASSET-1`: `base`, public/imported asset ownership, or dynamic chunk
  URLs assume root hosting and lack loading/error behavior at the deployment path.
- `vite.APP-SSR-1`: SSR/browser/worker code crosses runtime boundaries without
  distinct entry ownership, browser guards, or hydration handoff.
- `vite.APP-RECOVERY-1`: a dynamic chunk failure after a stale deployment has no
  refresh/retry path or can discard user work without warning.

## Carve-Outs

- Do not require SSR for a browser-only Vite app with an explicit static-hosting
  and route-recovery contract.
- Do not flag public assets when a stable externally referenced URL is deliberate
  and cache/deployment ownership is documented.
- Do not treat `vite preview` as a production certification; it can be adequate
  local built-artifact inspection when the limitation is disclosed.
