# Extensions

Per-stack packs loaded on demand by the responsive-design skill. The core workflow in `../SKILL.md` is framework-neutral; extensions add stack-specific primitives, patterns, smells, positive signals, and carve-outs.

## Load order

1. The skill detects stack by globbing the target and inspecting manifests (`.csproj`, `package.json`, `wwwroot/index.html`, etc.).
2. Every matching extension is loaded.
3. Each extension's additions (primitives, patterns, smells, positive signals, carve-outs) are added to the active reference.
4. On conflict between a carve-out and a core rule, the carve-out wins — but only for the exact pattern described.

Extensions **never override** core rules. They may only **add** or **carve out**.

## File layout per extension

Each extension is a single markdown file in this directory. Required sections:

- **Name and detection signals** — which files / manifests / content patterns trigger the load.
- **Stack-specific primitives** — APIs, descriptors, or conventions the core reference doesn't cover.
- **Stack-specific patterns** — templates idiomatic for the stack (namespaced `<ext>.PAT-N`).
- **Project assimilation** — stack-specific discovery that the core SKILL.md's framework-agnostic discovery delegates here. Must cover: (1) how to read the stack's token config (Tailwind's `theme`, Sass `_tokens.scss`, CSS-in-JS `config.*`, etc.), (2) the stack's component-library catalog (which libraries to detect and which of their primitives to reuse for §5.8 dialog / §5.11 popover / §5.9 skeleton / etc.), (3) the stack's framework image/head/router components (Next.js `<Image>`, Nuxt `<NuxtImg>`, SvelteKit `<enhanced:img>`, Blazor `<HeadContent>`), (4) a mapping table from reference defaults to stack idioms, (5) carve-outs for core smells the stack's idiomatic primitives legitimately satisfy.
- **Smell codes** — namespaced as `<ext>.HC-N` (high-confidence), `<ext>.LC-N` (low-confidence), `<ext>.POS-N` (positive signals).
- **Carve-outs** — explicit "do not flag <core rule> when <pattern>" entries.
- **Applies to reference sections** — which parts of the core reference this extension augments.

## Current extensions

| File | Applies to | Notes |
|---|---|---|
| `blazor-wasm.md` | Blazor WebAssembly components (`*.razor`, `*.razor.css`, WASM `Program.cs`, `wwwroot/index.html`) | CSS isolation, render-mode choice, JS interop for `matchMedia` / `visualViewport` / Web Vitals, assembly lazy-loading, focus restoration on NavigationManager transitions |

## Adding a new extension

1. Copy `blazor-wasm.md` as a template.
2. Pick a short, stable prefix (e.g. `rn` for React Native Web, `sw` for Svelte, `vue` for Vue, `angular` for Angular, `astro` for Astro).
3. Fill in detection signals — both globs and content matches. Detection must be unambiguous; false-positive loads pollute findings.
4. Add stack-specific primitives that the core reference does not already cover. Do not re-document CSS already in reference §4.
5. Add stack-specific patterns if the stack's idiomatic solution differs structurally from reference §5 — otherwise cite the core pattern.
6. Add smell codes, namespaced with the prefix.
7. Add carve-outs for idiomatic patterns the stack enforces.
8. Add the extension to the table in the SKILL.md § "Extensions" with its detection mapping.
9. Add the extension to the table above.

## Non-goals for extensions

- Extensions are not general framework guides. They address the *responsive / a11y / i18n / perf* surface only.
- Extensions do not duplicate the core reference. If a point already lives in `../../../docs/ui-reference/responsive-design.md`, cite it; do not restate.
- Extensions do not override the WCAG 2.2 AA, i18n, and CWV baselines. A stack cannot opt out of logical properties or Core Web Vitals — it can only provide its own idiomatic way of honouring them.

## Wanted extensions (roadmap)

The skill's core is framework-neutral; extensions close the framework-specific surface. The following are the highest-value stacks currently uncovered. Each would follow the `blazor-wasm.md` template (detection signals → hosting-model surface → stack-specific primitives → patterns → project assimilation → smell codes → carve-outs → applies-to). Pull requests welcome.

| Prefix | Stack | Key surfaces the extension needs to cover |
|---|---|---|
| `react` | React (plain, no meta-framework) | `useEffect` for focus restoration after route changes, React Router `useNavigate`-driven focus management, `useSyncExternalStore` bridges for `matchMedia` / `visualViewport`, `Suspense` + skeleton integration, Strict Mode double-render pitfalls for a11y, component-library catalogue (Radix, Headless UI, Base UI, shadcn/ui, Mantine, Chakra, MUI) with reuse rules |
| `nextjs` | Next.js (App Router + Pages Router) | `next/image` (fetchpriority, sizes, placeholder), `next/font` (self-hosting, size-adjust defaults), `next/link` `scroll` / `prefetch` behaviour, `usePathname` + focus restoration, Server Components → Client Components `'use client'` boundary effects on hydration-driven CLS, metadata API for `theme-color` / `color-scheme`, Route Groups and parallel routes for responsive shells, partial-prerendering interaction with LCP |
| `vue` | Vue 3 (Composition API) | `<script setup>` + `useHead` / `Unhead`, Vue Router `beforeEach` focus management, `Teleport` for modals / popover, `KeepAlive` + scroll restoration, reactive matchMedia via `useMediaQuery` (VueUse), component-library catalogue (Vuetify, PrimeVue, Naive UI) with reuse rules |
| `nuxt` | Nuxt 3 | `<NuxtImg>` + IPX provider, `<NuxtLink>` prefetch strategies, `useHead` for theme meta, Nuxt UI / Nuxt components responsive conventions, app.config tokens, `definePageMeta({ scrollToTop })`, SSR hydration CLS |
| `svelte` | Svelte 5 (runes) | `$state` / `$effect` for matchMedia bridges, SvelteKit `+page.svelte` / `+layout.svelte` focus on navigation, `<svelte:head>` for meta, View Transitions API as a first-class feature, `enhanced:img` for responsive images, Skeleton UI / Svelte Headless UI component library catalogue |
| `astro` | Astro | `<Image>` / `<Picture>` from `astro:assets`, Partial hydration directives (`client:load` / `client:visible` / `client:media`) and their CLS implications, Astro Islands focus-island boundaries, View Transitions built-in |
| `angular` | Angular (v17+) | `@defer` blocks for LCP and below-the-fold, `NgOptimizedImage` (`priority`, `fill`, `placeholder`), standalone components, Signals for matchMedia bridges, Router `scrollPositionRestoration: 'enabled'`, Angular CDK a11y primitives (`FocusTrap`, `LiveAnnouncer`), Material component-library reuse rules |
| `solid` | SolidJS / SolidStart | `createEffect` for matchMedia, Solid Router focus on navigation, `Suspense` + skeleton integration, fine-grained reactivity minimising re-render cost |
| `qwik` | Qwik / QwikCity | Resumability-vs-hydration CLS implications, `useVisibleTask$` for matchMedia bridges, `<Image>` from `qwik-image`, `qwikcity` route-change focus handling |
| `rn-web` | React Native Web | Shared-stylesheet constraints (no logical properties in RN paper backend), `useWindowDimensions` vs `matchMedia`, Pressable hit-slop vs SC 2.5.8 target-size, accessibility bridge between RN and ARIA |
| `webcomp` | Web Components / Lit | Shadow DOM scoped styles, `::part()` theming for consumers, `adoptedStyleSheets` for shared stylesheets, focus delegation (`delegatesFocus`), light-DOM slots vs focus restoration, Lit reactive controllers for matchMedia bridges |
| `tailwind` | Tailwind v4 (standalone or on any stack above) | `@theme` directive, `@layer` integration with reset / base / components / utilities, first-class `light-dark()` and container-query support (`@container`), `@custom-variant`, breakpoint tokens as CSS variables, per-component `@apply` vs arbitrary-variant trade-offs |

Cross-stack pairs worth noting: `nextjs` is a superset of `react`; `nuxt` of `vue`; `astro` composes with any island framework (React / Vue / Svelte / Solid); `tailwind` composes with any stack. When authoring a superset extension, load the base first then layer stack-specific additions on top (the `test-quality-audit` skill's `nextjs-core` → `nodejs-core` stacking is the reference pattern).
