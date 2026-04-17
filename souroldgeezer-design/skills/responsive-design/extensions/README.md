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
