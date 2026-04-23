# Responsive web design — a reference for building, not auditing

## 1. Context

A layout that renders at 375×667 is not the same as a layout that adapts meaningfully across viewport, container, input modality, user preferences, zoom, writing direction, capability, and network. The central problem of responsive design is **presence vs. efficacy**: a site looking plausible in a mobile emulator is not evidence that it works for the Arabic-speaking user on a 2019 Android with Save-Data turned on, or the low-vision user at 400% zoom, or the keyboard user stuck behind a sticky header.

Responsive design in 2026 is less about breakpoints and more about writing layouts that *don't need to know* what screen they're on. This reference is a playbook for that practice: principles, decisions with defaults, a cheatsheet of modern primitives, worked patterns, named gotchas, and a review checklist — organized for the person building or reviewing a UI, not for a scanner.

**WCAG 2.2 AA is enforced throughout, not referenced.** Every decision, pattern, and checklist item that touches accessibility names the specific Success Criterion it guards. A design choice that compromises a WCAG 2.2 AA SC is called out, never silently accepted. The criteria new in 2.2 — SC 2.4.11 Focus Not Obscured (Minimum), SC 2.5.7 Dragging Movements, SC 2.5.8 Target Size (Minimum) — get particular attention because they are often missed.

**Internationalization is a baseline, not a future concern.** Every layout here works in LTR *and* RTL without code change, tolerates 30–40% text expansion (English → German is the canonical stress test), and respects script-aware line-breaking across Latin, CJK, Arabic, and Hebrew. Logical properties are the default; physical properties (`margin-left`, `padding-right`, `text-align: left`) are a smell in new code.

**Performance is responsiveness.** A layout that visually adapts but ships 2 MB of JS to a 3G user on a 2019 Android has failed. Core Web Vitals are hard thresholds: **LCP ≤ 2.5s, CLS ≤ 0.1, INP ≤ 200ms** at the 75th percentile of real-user mobile data — web.dev Core Web Vitals. INP replaced FID as a stable Core Web Vital in 2024 — web.dev. Low-end Android on throttled 4G is the default reference environment.

**Scope.** Web only, modern CSS. Native mobile (SwiftUI size classes, Jetpack Compose `WindowSizeClass`), cross-platform frameworks (React Native, Flutter), email HTML, and print are out of scope — see §8.

## 2. Principles

### 2.1 Content-first, not device-first
Breakpoints emerge from where content breaks — where a line measure gets too long, where a card grid hits an awkward gap — not from device dimensions. Designing for an iPhone and an iPad misses every viewport between them and every future one.

### 2.2 Fluid over stepped
Reach for `clamp()`, `min()`, `max()`, and intrinsic sizing before reaching for a media query. Media queries are discrete; real devices are continuous. `font-size: clamp(1rem, 2.5vw, 2rem)` handles infinite viewports without a single breakpoint — MDN `clamp()`.

### 2.3 Component-scoped adaptation
A card reused in a sidebar and a main column should respond to its *container*, not the viewport. Container queries — `@container` with `cqi`/`cqb`/`cqw`/`cqh` units — make layout a property of the component, not the page — MDN Container Queries.

### 2.4 Input-modality and capability, not just size
Small viewport does not mean touch; large viewport does not mean mouse. Gate hover affordances behind `@media (hover: hover) and (pointer: fine)`; gate touch affordances behind `@media (pointer: coarse)`. Detect capability, not device.

### 2.5 Respect user preferences
`prefers-reduced-motion`, `prefers-color-scheme`, `prefers-contrast`, and `forced-colors` are user speech acts. Honour them. Users who disable motion do so because motion makes them ill or disoriented, not as a stylistic preference.

### 2.6 WCAG 2.2 AA is non-negotiable
Treat these SCs as hard requirements and cite them where they apply:
- **SC 1.3.4 Orientation (AA, new in 2.1):** content does not restrict view or operation to a single orientation — W3C WCAG 2.2.
- **SC 1.4.3 Contrast (Minimum) (AA, carried from 2.0):** text has contrast ratio ≥ 4.5:1 (≥ 3:1 for large text ≥ 18pt / 14pt bold) — W3C WCAG 2.2.
- **SC 1.4.4 Resize Text (AA, carried from 2.0):** text resizable to 200% without loss of content or functionality — W3C WCAG 2.2.
- **SC 1.4.10 Reflow (AA, new in 2.1):** content presents without loss of information and without two-dimensional scrolling at 320 CSS pixels wide (vertical scrolling only) or 256 CSS pixels tall (horizontal scrolling only) — W3C WCAG 2.2.
- **SC 1.4.11 Non-text Contrast (AA, new in 2.1):** UI components and graphical objects needed to understand content have contrast ratio ≥ 3:1 against adjacent colors — W3C WCAG 2.2.
- **SC 1.4.12 Text Spacing (AA, new in 2.1):** no content loss when users override line-height, paragraph/letter/word spacing — W3C WCAG 2.2.
- **SC 2.4.7 Focus Visible (AA, carried from 2.0):** any keyboard-operable interface has a visible focus indicator — W3C WCAG 2.2.
- **SC 2.4.11 Focus Not Obscured (Minimum) (AA, new in 2.2):** focused components are not *entirely* hidden by author-created content — W3C WCAG 2.2.
- **SC 2.5.7 Dragging Movements (AA, new in 2.2):** drag functionality has a non-drag alternative unless dragging is essential — W3C WCAG 2.2.
- **SC 2.5.8 Target Size (Minimum) (AA, new in 2.2):** pointer targets ≥ 24×24 CSS pixels unless a smaller size is essential — W3C WCAG 2.2.

### 2.7 Internationalization is non-negotiable
Responsive means responsive to *language, direction, and script* — not only to viewport. Every layout must:
- Work in LTR and RTL without code change — use logical properties (`margin-inline`, `padding-block`, `inset-inline-*`) so layout adapts via `dir="rtl"` alone — MDN CSS Logical Properties.
- Survive 30–40% text expansion (German from English; Czech, Finnish, Russian) — avoid fixed widths on label-bearing elements.
- Respect script-specific line-breaking — CJK uses `word-break`/`line-break` rules Latin doesn't.
- Mirror directional icons (arrows, chevrons, back-buttons) in RTL via `:dir(rtl)` or swapped SVGs.
- Set `lang` on the document and on language-switched subtrees so screen readers pronounce correctly and hyphenation rules apply.

### 2.8 Performance is responsiveness
Responsive means responsive to *capability, network, and resource budget*, not only viewport pixels. The reference environment is low-end Android on throttled 4G, measured at the 75th percentile of real-device data — web.dev. Core Web Vitals thresholds (LCP < 2.5s, CLS < 0.1, INP < 200ms) are hard lines, not nice-to-haves.

### 2.9 Progressive enhancement across capability axes
Container queries, `:has()`, subgrid, view transitions, cascade layers — use them, but the baseline layout must work without them. Capability is an axis of responsiveness, too.

## 3. Decisions

Each decision states the choice, the default rule, and when to deviate. Defaults are written on a single bold line so they can be lifted wholesale into code review.

### 3.1 Fluid vs stepped sizing
Media queries produce stepped UIs that feel correct at the tested widths and broken between them. Fluid primitives (`clamp()`, `min()`, `max()`, `auto-fit`, intrinsic sizing) produce continuous adaptation.

**Default:** fluid. Use `clamp()` for type/spacing and intrinsic grids (`repeat(auto-fit, minmax(min(100%, <n>rem), 1fr))`) for layout. Step only when a design token needs to snap at a content-driven breakpoint.

*When to deviate:* editorial page layouts that change meaningfully at a named breakpoint (e.g., a two-column article becoming single-column with a floated pull-quote) — use a media query, but derive the breakpoint from where the line measure stops working, not from a device width.

### 3.2 Viewport query vs container query
Viewport queries change the *page*; container queries change a *component*. A component reused at different widths (cards in a grid vs a sidebar) needs container queries to adapt correctly.

**Default:** container query (`@container`) for components reused at multiple widths. Viewport query (`@media`) for page-shell decisions — primary nav, column count, safe-area. Require an ancestor with `container-type: inline-size` or the query is silently ignored — MDN Container Queries.

*When to deviate:* single-use layout elements (site header, footer) where the whole page informs the decision — viewport query is clearer.

### 3.3 Unit selection
Units decide whether text respects user zoom, whether layout respects line-length, and whether components compose.

- `rem` for type and spacing — respects user root font-size (SC 1.4.4 Resize Text).
- `ch` for line-length / measure (target 45–75ch for body copy).
- `%` or `fr` for layout proportions.
- `cqi` / `cqb` inside `@container` contexts — sizes relative to the container.
- `dvh` / `svh` / `lvh` for viewport-coupled heights; *never bare `vh`* on mobile-visible elements (§3.7).
- Bare `px` only on content that must not scale: chart axes, 1px borders, canvas coordinates.

**Default:** `rem` for type and spacing, `ch` for measure, `%`/`fr` for layout, `cqi`/`cqb` inside containers, `dvh`/`svh`/`lvh` for viewport-coupled heights, `px` only where fixed scale is semantically correct.

### 3.4 Breakpoints
Derive from content, not from device presets. Where does the line measure break? Where does the grid gap become awkward? Name breakpoints by role (`--bp-wide`, `--bp-narrow`), not by device (`--bp-ipad`). Breakpoint lists longer than 3–4 are a smell; fluid primitives are probably the answer.

**Default:** content-derived breakpoints named by role; layout must reflow without horizontal scroll at **320 CSS pixels** wide (SC 1.4.10 Reflow).

### 3.5 Mobile-first cascade direction
Mobile-first: small-viewport styles are the base, `min-width` queries progressively enhance. Desktop-first (`max-width`) stacks overrides and produces a cascade that unwinds confusingly on narrow viewports.

**Default:** mobile-first (`min-width` queries). Desktop-first is acceptable only when the product is genuinely desktop-first (IDE tools, admin dashboards, data tables) and the decision is stated in the code.

### 3.6 Touch vs hover affordances
Assume touch by default. Hover is an enhancement on top of a layout that already works without it. Drag is never the only way to do something.

- Touch targets ≥ **24×24 CSS pixels** — SC 2.5.8. Prefer 44×44 per Apple HIG.
- Gate hover styles behind `@media (hover: hover) and (pointer: fine)` so they don't stick on touch.
- Every drag interaction (carousel, slider, reorder) has a button or keyboard alternative — SC 2.5.7.

**Default:** tap-and-reveal is the base; hover-reveal is a progressive enhancement. 24 CSS px is the floor for interactive targets; drag always has an alternative.

### 3.7 `dvh` / `svh` / `lvh` vs `vh`
On mobile Safari and Android Chrome, the URL bar appears and disappears, changing the "visible" viewport. `100vh` is equivalent to `100lvh` in modern browsers — the viewport with the URL bar hidden — so `100vh` overshoots when the URL bar is visible — MDN length units.

- `100dvh` — resizes dynamically as the UI shows/hides; best fit, but can cause layout shift.
- `100svh` — smallest possible viewport; stable, content never obscured, may leave empty space when URL bar hides.
- `100lvh` — largest viewport; stable, fills space best when URL bar hidden, content clipped when it shows.

**Default:** `svh` for guaranteed-visible layouts (forms, dialogs), `dvh` for edge-to-edge hero sections, `lvh` for scroll-driven above-fold content that expects the URL bar hidden. Never use bare `vh` on user-visible mobile elements.

### 3.8 Sticky / fixed headers and focus
A sticky header that fully covers a focused input is an SC 2.4.11 failure. Scrolling focused elements into view by default does not help if the sticky header paints on top.

**Default:** if a header is sticky, set `scroll-margin-top` on focusable landmarks to ≥ the header's computed height; or prefer non-sticky navigation on narrow viewports. A keyboard user tabbing through forms must always see their focus.

### 3.9 Logical vs physical properties
Logical properties (`margin-inline-start`, `padding-block-end`, `inset-inline-start`, `text-align: start`, `border-inline-end`) adapt automatically to `direction` and `writing-mode` — MDN CSS Logical Properties. Physical properties (`margin-left`, `padding-top`, `left`, `text-align: left`) do not.

- `width` / `height` → `inline-size` / `block-size`
- `margin-left` / `margin-right` → `margin-inline-start` / `margin-inline-end`
- `padding-top` / `padding-bottom` → `padding-block-start` / `padding-block-end`
- `top` / `right` / `bottom` / `left` (for positioning) → `inset-block-start` / `inset-inline-end` / `inset-block-end` / `inset-inline-start`
- `text-align: left` / `right` → `text-align: start` / `end`
- `border-top-left-radius` → `border-start-start-radius` (etc.)

**Default:** logical properties for every spacing/positioning property in new code. Physical properties only where the axis is semantically physical (a scroll-indicator that is visually "down" regardless of writing mode). Every physical property in new code carries a comment justifying it, or it is a smell.

### 3.10 Width sizing and text expansion
English is shorter than almost every other language. A button sized to "Save" at 64px will break for "Speichern" (German, +40%) and "Uložit změny" (Czech, +125%). Fixed widths tuned to English labels are a layout failure in every other locale.

**Default:** intrinsic sizing on interactive elements (`min-width` + intrinsic content width, or `width: fit-content`). Avoid fixed `px` or `ch` widths on label-bearing elements. Test layouts with at least one long-string locale stand-in (German is the canonical stress test).

### 3.11 Image loading strategy
Responsive images serve two masters, layout and performance. Ship appropriate resolutions per viewport and DPR; prioritize the LCP candidate; lazy-load the rest.

- `<img srcset sizes>` or `<picture>` with modern-format sources — AVIF → WebP → JPEG fallback.
- `width` and `height` attributes on every `<img>` (or `aspect-ratio` on a wrapper) — reserves space, kills CLS.
- `fetchpriority="high"` on the LCP image — MDN `<img>`.
- `loading="lazy"` on below-the-fold images — *never* on the LCP image.
- `decoding="async"` unless a synchronous paint is intentional.

**Default:** `<picture>` with AVIF + WebP sources, explicit `width`/`height`, `fetchpriority="high"` on the LCP image, `loading="lazy"` + `decoding="async"` elsewhere. Never ship a single raster for all viewports.

### 3.12 Font loading strategy
Custom fonts are the most common source of CLS. Load them so the fallback renders immediately and the swap causes minimal layout shift.

- `font-display: swap` — text renders in fallback immediately, swapped when the custom font loads — MDN `font-display`.
- `<link rel="preload" as="font" crossorigin>` for fonts used above the fold.
- `@font-face` with `size-adjust`, `ascent-override`, `descent-override` tuned so fallback metrics match the custom font — swap becomes visually silent.
- `unicode-range` subsetting — mandatory for CJK, where a naive single-file webfont can exceed 10 MB.

**Default:** `font-display: swap` + preload critical fonts + tune `size-adjust`/`ascent-override` to kill CLS + `unicode-range` subset for every non-Latin script on the site.

### 3.13 Network and capability awareness
Design for the 75th-percentile global mobile user, not the developer's fiber connection. Respect data-saver preferences where the browser exposes them; degrade gracefully on slow networks without blocking content.

- `Save-Data: on` HTTP header — sent by Chromium-family browsers when the user enables data saver. Server varies on it (`Vary: Accept-Encoding, Save-Data`) to serve smaller images, disable polling, skip autoplay — MDN Save-Data.
- `@media (prefers-reduced-data: reduce)` — the CSS analog; note that the feature is **not yet Baseline** and no major browser currently implements it — MDN `prefers-reduced-data`. Use for forward-compatibility but do not rely on it.
- `navigator.connection.effectiveType` (Network Information API) — provides `slow-2g` / `2g` / `3g` / `4g` hints. **Not Baseline**, limited to Chromium — MDN Network Information API. Use to *degrade* (lower image quality, skip video) never to block content.
- Critical-path JS budget: ≤ 170 KB compressed over the wire — empirical baseline from HTTP Archive / web.dev.

Concrete server-side branching on `Save-Data` (framework-agnostic pseudo-code):

```
# On every response that varies on data saver:
response.headers["Vary"] = "Accept-Encoding, Save-Data"

if request.headers.get("Save-Data") == "on":
    image_quality   = 60          # instead of 85
    image_max_width = 1024        # instead of 1920
    autoplay_video  = False
    poll_interval   = None        # suspend long-poll / SSE refresh
    preload_hints   = ["font-critical"]  # drop non-critical preloads
else:
    image_quality   = 85
    image_max_width = 1920
    autoplay_video  = True
    poll_interval   = 15
    preload_hints   = ["font-critical", "hero-image", "above-fold-css"]
```

**Default:** respect `Save-Data` on the server (image quality, autoplay, polling, preload count all vary on it); treat `prefers-reduced-data` and `effectiveType` as enhancements, not required signals; keep critical-path JS under ~170 KB compressed.

### 3.14 Animation and interaction performance
INP is the hard constraint on interaction. Layout-triggering animations and long JS tasks both blow past the 200ms budget.

- Prefer `transform` and `opacity` over `width`/`top`/`margin` for animation — the former compose on the compositor, the latter trigger layout.
- `content-visibility: auto` + `contain-intrinsic-size: <w> <h>` on long off-screen sections — defers paint and layout until near-viewport.
- Avoid `will-change` except during an active interaction; leaving it on promotes layers that cost memory.
- Break long tasks with `scheduler.yield()` (preferred when available — continuation runs at a boosted priority), `scheduler.postTask()`, or `requestIdleCallback` (low-priority work). `scheduler.yield()` is **Limited availability / not yet Baseline** as of 2026 — feature-detect and fall back to `postTask` or `setTimeout(0)` — MDN Scheduler. Defer non-critical JS with `<script defer>` or dynamic `import()`.
- `@media (prefers-reduced-motion: reduce)` disables non-essential motion entirely.

**Default:** transforms/opacity for motion, `content-visibility: auto` on long sections, yield work back to the browser during interactions (prefer `scheduler.yield()` where supported, fall back to `scheduler.postTask()` / `setTimeout(0)`), honour `prefers-reduced-motion: reduce`.

### 3.15 Flexbox vs Grid
Flexbox and Grid solve different problems. Flexbox distributes space along one axis; Grid positions items in a two-axis coordinate system. Using flexbox to simulate a grid (with `flex-wrap` and fixed-width children) produces a responsive layout that can't align items across rows.

- **Flex** when the layout is one-dimensional, content-sized, and wraps naturally: nav bars, tag lists, toolbars, form rows.
- **Grid** when the layout has two dimensions, fixed tracks, or items must align across both axes: page shells, card grids, dashboard layouts, gallery layouts, form grids with consistent label columns.
- **Subgrid** when children of a Grid item need to align to the parent's tracks (e.g., a row of cards whose titles all line up regardless of image height).

**Default:** Grid for two-dimensional layout and alignment across items; Flex for one-dimensional, content-driven lists. Subgrid when child components must inherit their parent's track geometry.

### 3.16 Focus management
Focus is a navigation mechanism for keyboard and screen-reader users. Responsive layouts that rearrange content, hide elements, or open overlays must manage focus explicitly — otherwise focus is lost on narrow viewports where the burger menu opens, the modal appears, the route changes, and the focus ring disappears off-screen.

- **Always-visible focus indicator** — use `:focus-visible` with an outline (not `outline: none`). SC 2.4.7 Focus Visible requires it.
- **Focus traps in modal contexts** — when a `<dialog>` or `popover` opens, focus must be contained inside until it closes. Native `<dialog>` does this automatically; custom overlays must implement it.
- **Focus restoration** — after a dialog closes, after a route change, after a disclosure menu closes, return focus to the element that triggered the change.
- **Focus not obscured** — sticky headers must not fully cover a focused element (SC 2.4.11) — see §3.8.
- **Focus appearance** — indicator area at least as large as a 2 CSS px perimeter of the unfocused control, with contrast ≥ 3:1 **between the focused and unfocused states of the same pixels** (SC 2.4.13 Focus Appearance, AAA — note that this SC's 3:1 threshold measures the *change* between states, not contrast against adjacent colour — a distinct and often-missed requirement). AAA is aspirational but worth meeting for keyboard and low-vision users.

**Default:** `:focus-visible` with a 2–3 CSS px outline and adequate contrast on every interactive element; native `<dialog>` for modals (focus trap built-in); explicit focus restoration on every close / route change.

### 3.17 Colour and contrast
Contrast requirements apply to text (SC 1.4.3 Contrast Minimum), non-text UI and graphics (SC 1.4.11 Non-text Contrast), and focus indicators (SC 2.4.13). Responsive designs must meet these in *every* theme the site supports — light, dark, high-contrast, forced-colors.

- **Text ≥ 4.5:1** against its background (≥ 3:1 for large text ≥ 18pt / 14pt bold) — SC 1.4.3.
- **UI component boundaries, state indicators, and meaningful graphics ≥ 3:1** against adjacent colors — SC 1.4.11.
- **`prefers-color-scheme: light` and `dark`** — design both; `light-dark(<light>, <dark>)` CSS function switches per theme from a single declaration.
- **`color-scheme` on `<html>`** — tells the browser which themes the page supports, enabling native form-control theming.
- **`forced-colors: active`** (Windows High Contrast) — flatten custom styles; don't rely on color alone; use `CanvasText`, `LinkText`, `ButtonFace` system colors where overrides are needed.
- **Never convey information by color alone** — pair color with icon, text, or shape (e.g., error message gets `⚠ ` prefix, not just red text).

**Default:** verify contrast in both light and dark themes at design time; use `light-dark()` + `color-scheme` for theming; pair every color-coded state with a non-color indicator; test with `forced-colors: active` before shipping.

### 3.18 Token architecture
Project assimilation reuses existing tokens (see SKILL.md). But when the project is greenfield, a token architecture decision is unavoidable — ad-hoc values accumulate into a style sheet that can't theme, can't localise, and can't be audited. Tokens are the contract between design and code.

**Two-layer naming.** Primitive tokens (`--color-blue-500`, `--space-2`, `--radius-md`) carry raw values; semantic tokens (`--color-text-primary`, `--color-surface-raised`, `--space-form-gap`) carry the *role* a value plays and reference the primitive. UI components consume *semantic* tokens only; primitives are private to the theme layer.

```css
:root {
  /* Primitives — raw scale. Private to the theme; components never use these. */
  --color-gray-0:   oklch(100% 0 0);
  --color-gray-900: oklch(15%  0 0);
  --color-blue-500: oklch(55%  0.18 255);
  --space-1: 0.25rem;  --space-2: 0.5rem;  --space-3: 0.75rem;
  --space-4: 1rem;     --space-6: 1.5rem;  --space-8: 2rem;
  --radius-sm: 0.25rem; --radius-md: 0.5rem; --radius-lg: 1rem;
  --step-0: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);  /* fluid type scale */

  /* Semantics — what components reference. Theme-swappable via light-dark(). */
  --color-text-primary:     light-dark(var(--color-gray-900), var(--color-gray-0));
  --color-text-secondary:   light-dark(oklch(40% 0 0),        oklch(70% 0 0));
  --color-surface-base:     light-dark(var(--color-gray-0),   var(--color-gray-900));
  --color-surface-raised:   light-dark(oklch(98% 0 0),        oklch(20% 0 0));
  --color-accent:           var(--color-blue-500);
  --color-focus-ring:       currentColor;

  --space-form-gap:         var(--space-4);
  --space-card-padding:     var(--space-6);
  --radius-control:         var(--radius-md);
  --radius-card:            var(--radius-lg);
}
```

**Default:** two-layer naming (primitive → semantic); semantic names describe role, not value; components consume only semantic tokens.

*When to deviate:* early-stage prototypes where the theme is volatile — a single-layer flat set is fine temporarily. Promote to two-layer before the design ships externally.

**Colour space.** Use **oklch()** (or `oklab()`) for primitive colour definitions. Oklch is perceptually uniform — a 10% lightness change looks like a 10% change regardless of hue, which sRGB famously fails at (blue at 50% lightness looks much darker than yellow at 50%). `color-mix(in oklch, ...)` generates tints and shades that read consistently across a palette. Keep a `oklch()` → sRGB fallback layer only if the project targets browsers without oklch support — Baseline 2024, so usually unnecessary in 2026.

**Dark-mode pair generation.** `light-dark(<light>, <dark>)` collapses the per-theme branch into a single declaration and is the right default. Alternatives: dual-blocked CSS (`:root { … } :root[data-theme="dark"] { … }`) when the site explicitly opts users into a theme (not `prefers-color-scheme`); CSS layers for app-level vs user-level theme overrides (`@layer theme.system, theme.user;`).

**Respecting system colours.** Semantic tokens must have a sensible fallback under `forced-colors: active`. `--color-focus-ring: currentColor` naturally coerces to the system focus colour; a hard-coded `--color-focus-ring: oklch(60% 0.18 260)` becomes whatever the system decides. Audit every semantic token for a forced-colors pass.

**Cascade layers for architecture.** `@layer reset, base, tokens, components, utilities;` — tokens live in a named layer so component-level overrides from utilities layer cleanly without specificity wars. Unlayered CSS beats layered CSS at matching specificity; keep user-authored styles in a layer even if the rest of the framework is unlayered.

**Breakpoint tokens.** Breakpoints are tokens too — name by role (`--bp-content-wide: 48rem`, `--bp-dashboard-split: 64rem`), not by device. Never hard-code `@media (min-width: 768px)` in components; reference a token via CSS custom properties or a preprocessor. Tailwind / CSS-in-JS frameworks have their own token systems — use theirs; don't layer a second one.

**Type scale.** Fluid by default (`clamp()` per §3.1); a stepped scale is a smell unless the editorial design genuinely calls for it. Token names follow modular scale conventions (`--step--1`, `--step-0`, `--step-1`, …) or semantic labels (`--font-size-body`, `--font-size-h1`). Pick one naming convention and keep it consistent across the project.

## 4. Primitives cheatsheet

Each primitive gets one-line purpose + syntax + key pitfall.

- **`clamp(min, preferred, max)`** — fluid sizing with bounds. `font-size: clamp(1rem, 2.5vw, 2rem)` — MDN `clamp()`. Pitfall: the `preferred` expression should use `vw`/`vi`/`cqi` with a `rem` floor (pure `vw` ignores user root size and violates SC 1.4.4).
- **`min()` / `max()`** — constraint logic without media queries. `width: min(100%, 40rem)` caps a fluid element at a readable width. Pitfall: composes with `clamp()` in subtle ways; test before deploying.
- **`@container` + `cqi` / `cqb` / `cqw` / `cqh` / `cqmin` / `cqmax`** — component-scoped layout — MDN Container Queries. `cqi` = 1% of the query container's inline size. Pitfall: requires an ancestor with `container-type: inline-size` (or `size`); without it, the query is ignored and container units fall back to small-viewport units.
- **`dvh` / `svh` / `lvh`** — dynamic / small / large viewport heights — MDN length units. `100dvh` resizes as the URL bar shows/hides; `100svh` is stable at the smallest possible viewport; `100lvh` is stable at the largest. Pitfall: `dvh` causes layout shift during scroll; prefer `svh` for stable layouts.
- **`@media (hover: hover)` / `@media (pointer: coarse)`** — input-modality detection. Gate hover enhancements behind `(hover: hover)`; expand tap targets under `(pointer: coarse)`. Pitfall: `any-hover`/`any-pointer` match if *any* connected input has the capability — usually not what you want.
- **`prefers-reduced-motion`**, **`prefers-color-scheme`**, **`prefers-contrast`**, **`forced-colors`** — user-preference media queries. Honour them. Pitfall: `forced-colors: active` flattens custom colors — don't rely on color as the only information channel.
- **Logical properties** — `margin-inline`, `padding-block`, `inset-inline-start`, `border-inline-end`, `text-align: start` — MDN CSS Logical Properties. Pitfall: mixing logical and physical on the same element produces unpredictable layouts — pick a lane per component.
- **`writing-mode`, `direction`, `unicode-bidi`** — script-direction primitives. `writing-mode: vertical-rl` for traditional CJK vertical text (columns right-to-left, characters top-to-bottom); `writing-mode: vertical-lr` for Mongolian / traditional columnar layouts where columns flow left-to-right. `dir="rtl"` on document or subtree for Arabic / Hebrew / Farsi / Urdu. Pitfall: mixing `writing-mode: vertical-*` with `dir="rtl"` requires careful logical-property discipline — physical properties become meaningless in a ninety-degree-rotated coordinate system.
- **`:dir(rtl)` / `:dir(ltr)`** — direction-aware styling without JS. Flip a chevron in RTL: `:dir(rtl) .chevron { transform: scaleX(-1); }`. More semantic than `[dir="rtl"]` because it follows the DOM's computed direction, including subtrees that inherit from an ancestor.
- **`:lang(en)` / `:lang(ar-SA)` / `:lang(zh-Hans)`** — language-aware styling. `:lang()` matches the language declared on the element *or any ancestor*, so `<html lang="en"><blockquote lang="fr">…</blockquote>` styles the blockquote via `:lang(fr)`. Use for per-language typography (`:lang(ar) { font-family: …; line-height: 1.75; }`), date/number patterns via `@counter-style`, or lang-specific hyphenation (`:lang(de) { hyphens: auto; }`). Pitfall: `:lang()` matches language *tags*, including region subtags — `:lang(zh)` matches `lang="zh-Hans"` and `lang="zh-TW"` both, which is usually what you want.
- **`<bdi>` element** — bidi isolation for user-generated content whose direction is unknown or may conflict with its surrounding context. `User @<bdi>محمد</bdi> commented` prevents the Arabic name from rewriting the directionality of the surrounding English. `<bdo>` overrides direction explicitly (rare, mostly for testing); `<bdi>` *isolates* it (common, the right tool for any user-display string that mixes scripts). Pitfall: `<span dir="auto">` approximates `<bdi>` in older browsers that lack `<bdi>`, but `<bdi>` is Baseline and should be preferred.
- **`srcset` + `sizes` + `<picture>`** — DPR and art-direction responsive images — MDN `<img>`. `srcset` with `w` descriptors + `sizes` media-condition list = browser picks the right resolution. Pitfall: forgetting `sizes` when using `w` descriptors makes the browser assume `100vw`.
- **`loading="lazy"` / `fetchpriority="high"` / `decoding="async"`** — image load ordering — MDN `<img>`. Pitfall: never combine `loading="lazy"` with the LCP image — that guarantees a slow LCP.
- **`@font-face` descriptors — `font-display`, `size-adjust`, `ascent-override`, `descent-override`, `unicode-range`** — font CLS control and subsetting — MDN `font-display`. Pitfall: omitting `size-adjust` + overrides means the swap visibly reflows text.
- **`@media (prefers-reduced-data: reduce)` + `Save-Data` HTTP header** — reduce payload for bandwidth-constrained users — MDN Save-Data. Pitfall: `prefers-reduced-data` is experimental and not yet implemented by any UA; `Save-Data` is the current reliable signal.
- **`navigator.connection.effectiveType`** — Network Information API — MDN. Not Baseline; Chromium-only. Use to degrade, never to block.
- **`aspect-ratio`** — reserves space for media before load. `aspect-ratio: 16 / 9` on an image wrapper or a video placeholder prevents CLS.
- **`content-visibility: auto` + `contain-intrinsic-size`** — defer paint/layout of off-screen sections. Pitfall: skipping `contain-intrinsic-size` makes scrollbar length jump as sections realise.
- **`scrollbar-gutter: stable`** — reserves scrollbar space so enabling scroll doesn't horizontally shift layout.
- **`env(safe-area-inset-top / right / bottom / left)`** — notch, gesture-bar, home-indicator insets. Use with `max()` to ensure a minimum: `padding: max(1rem, env(safe-area-inset-top))`.
- **`interactive-widget=resizes-content`** in viewport meta — virtual keyboard resizes the layout viewport, not just the visual viewport — MDN viewport meta. Pitfall: default (`resizes-visual`) causes layout jumps when the keyboard appears.
- **`text-wrap: balance` / `text-wrap: pretty`** — `balance` equalizes line lengths in short text (headings, hero text); `pretty` optimizes ragged edges and avoids orphans in body text. Both handle responsive reflow gracefully. Pitfall: `balance` applies only up to a browser-limited line count (typically 6), silently no-ops beyond.
- **`light-dark(<light>, <dark>)`** + **`color-scheme` root property** — theme-switched values from a single declaration — MDN. `html { color-scheme: light dark; }` enables native form theming; `color: light-dark(#111, #eee)` swaps with `prefers-color-scheme`. Pitfall: requires `color-scheme` on an ancestor (usually `:root`) to activate.
- **`color-mix(in <space>, <c1>, <c2> <p>%)`** and **`oklch()` / `oklab()`** — perceptually uniform color spaces and mixing — MDN. `color-mix(in oklch, var(--accent), white 20%)` builds a tint that looks right across themes. Pitfall: older libraries expect sRGB; ensure the pipeline preserves wide-gamut.
- **`:has()`** — parent and sibling selection. Responsive example: `.card:has(img) { grid-template-rows: auto 1fr; }` lets a layout adapt when content varies. Pitfall: browsers in 2026 optimize `:has()` well, but it still does more work than a simple descendant selector — reserve for cases where the alternative is JavaScript.
- **Subgrid** — `grid-template-rows: subgrid` / `grid-template-columns: subgrid` — child Grid items inherit parent tracks. Pattern: card rows whose titles, bodies, and CTAs all align across the row regardless of image height.
- **Cascade layers `@layer`** — explicit cascade ordering: `@layer reset, base, components, utilities;`. Responsive CSS scales better with layers because override specificity becomes architectural, not accidental.
- **`autocomplete`, `inputmode`, `enterkeyhint`** on form controls — instruct mobile soft keyboards (numeric pad for `inputmode="numeric"`, "Go" vs "Search" vs "Send" labels via `enterkeyhint`), and enable password-manager / address / payment autofill (`autocomplete="email"`, `"shipping street-address"`, `"cc-number"`). Pitfall: the standard `autocomplete` token list is long and exact — invented values silently fail.
- **Resource hints** — `<link rel="preload" as="font|style|image|script">`, `rel="prefetch"` for next-navigation assets, `rel="preconnect"` for third-party origins the page will hit, `rel="dns-prefetch"` for lightweight DNS warm-up. Pitfall: over-preloading competes for bandwidth with the LCP image; preload only the truly critical.
- **`aria-live="polite"` / `aria-live="assertive"` + `aria-describedby`** — announce async updates (search results, form errors, toasts) and associate help/error text with inputs. Pitfall: `aria-live` regions that are added to the DOM *at the moment of the update* don't announce — the region must exist at page load.
- **`popover` attribute** — declarative top-layer overlays without focus-trap semantics. `<button popovertarget="tips">Info</button> <div id="tips" popover>…</div>` — light-dismiss on `Esc` or outside click, `inert` on the rest of the page handled by the browser. Three values: `popover="auto"` (default — light-dismissed, closes other `auto` popovers when opened), `popover="manual"` (no light-dismiss, owner controls close, multiple may coexist — notifications, coach-marks), `popover="hint"` (light-dismissed, does not close `auto` popovers — tooltips and transient hints) — MDN `popover`. Use `<dialog>` for modal forms (focus trap); `popover` is explicitly non-modal.
- **CSS Anchor Positioning — `anchor-name`, `position-anchor`, `position-area`, `position-try-fallbacks`** — place a positioned element relative to a named anchor element via a 3×3 tile grid. `anchor-name: --trigger;` declares the anchor; `position-anchor: --trigger; position-area: block-end;` places the positioned element below the anchor. `position-try-fallbacks: flip-block, flip-inline;` lists fallback placements tried in order when the default would overflow the viewport — MDN `position-area`, `position-try-fallbacks`. **Baseline 2026** (newly available January 2026); earlier Chromium used `inset-area` and `position-try-options` for the same properties — feature-detect with `@supports (position-area: block-end)` and fall back to fixed-direction CSS or a JS positioning library.
- **View Transitions (`view-transition-name` + `@view-transition`)** — smooth cross-state transitions without manual FLIP animation. Same-document: wrap state changes in `document.startViewTransition(() => …)`, which returns a `ViewTransition` object. Cross-document (MPA): `@view-transition { navigation: auto; }` in CSS on both the outgoing and incoming documents (same origin required). Style the transition with `::view-transition-old(root)` / `::view-transition-new(root)` or per-element via `view-transition-name` — MDN View Transitions. **Limited availability / not yet Baseline** as of 2026 — feature-detect with `if ("startViewTransition" in document)` and skip the transition on unsupported browsers. View transitions run on the main thread and can dominate INP — gate non-essential transitions behind `prefers-reduced-motion: no-preference`.

## 4.5. Baseline boilerplate

A canonical `<head>` + `:root` that every responsive page should start from. Copy once, adjust theme colors and font URLs.

```html
<!doctype html>
<html lang="en" dir="ltr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#111" media="(prefers-color-scheme: dark)">
  <meta name="theme-color" content="#fff" media="(prefers-color-scheme: light)">
  <link rel="preconnect" href="https://cdn.example.com" crossorigin>
  <link rel="preload" as="font" href="/fonts/inter-var.woff2" type="font/woff2" crossorigin>
  <title>…</title>
</head>
```

```css
*, *::before, *::after { box-sizing: border-box; }
html {
  color-scheme: light dark;
  text-size-adjust: none;
  scroll-behavior: smooth;
  -webkit-tap-highlight-color: transparent;
  accent-color: var(--accent, currentColor);
}
body {
  margin: 0;
  min-block-size: 100svh;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  line-height: 1.5;
  color: light-dark(#111, #eee);
  background: light-dark(#fff, #111);
}
img, picture, svg, video { display: block; max-inline-size: 100%; block-size: auto; }
input, button, textarea, select { font: inherit; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }
}
```

What this establishes: viewport meta with `viewport-fit=cover` (enables safe-area) and `interactive-widget=resizes-content` (keyboard resizes layout viewport); `color-scheme` declared so native controls theme; `theme-color` split per `prefers-color-scheme`; a font preloaded; `box-sizing: border-box` universal; `text-size-adjust: none` to stop iOS's over-eager auto-scaling; `:root` uses `light-dark()` for theme-swapped colors; media defaults to responsive sizing; a global `prefers-reduced-motion` kill-switch. Everything else layers on top.

## 5. Patterns

Each pattern: purpose, hard requirements, implementation sketch, variations.

### 5.1 Responsive navigation
Primary nav that shows links at wide widths and collapses to a disclosure menu at narrow — no UA sniffing, keyboard-operable, `aria-expanded` correct. Tap targets ≥ 24 CSS px (SC 2.5.8); if sticky on scroll, `scroll-margin-top` on landmark targets (SC 2.4.11). Logical-property spacing so the bar mirrors cleanly in RTL; chevron/arrow icons flip via `:dir(rtl)`.

```html
<nav class="primary-nav">
  <button class="menu-toggle" aria-expanded="false" aria-controls="primary-menu">
    <span class="menu-label">Menu</span>
  </button>
  <ul id="primary-menu" class="primary-menu">
    <li><a href="/products">Products</a></li>
    <li><a href="/pricing">Pricing</a></li>
  </ul>
</nav>
```

```css
.primary-nav {
  display: flex;
  gap: 1rem;
  /* Edge-to-edge devices: outermost horizontal padding honours safe-area insets.
     max() keeps a readable minimum when the inset is 0.                      */
  padding-inline: max(clamp(1rem, 3vi, 2rem), env(safe-area-inset-left)) max(clamp(1rem, 3vi, 2rem), env(safe-area-inset-right));
  padding-block: 0.75rem;
  position: sticky;
  inset-block-start: 0;
}
.menu-toggle { min-block-size: 2.75rem; min-inline-size: 2.75rem; }
.primary-menu a { min-block-size: 2.75rem; padding-inline: 0.75rem; display: grid; place-items: center; }
@media (max-width: 40em) {
  .primary-menu { display: none; }
  [aria-expanded="true"] ~ .primary-menu { display: block; }
}
:dir(rtl) .menu-toggle .chevron { transform: scaleX(-1); }
/* Focusable elements stay clear of the sticky header when scrolled to — SC 2.4.11. */
:target, :focus-visible { scroll-margin-block-start: 5rem; }
```

### 5.2 Card grid that wraps without breakpoints, with container-aware cards
Equal-width cards that wrap from 1 to N columns with no viewport media query (Grid `auto-fit` per §3.15). Reflows at 320 CSS px (SC 1.4.10). Individual cards are *container-aware*: each card reorganises its own layout based on how wide it ends up, independently of viewport — so the same component works in a sidebar, a hero, or a three-column grid without forking CSS (§2.3, §3.2).

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
  gap: clamp(1rem, 2vw, 1.5rem);
  padding-inline: clamp(1rem, 3vw, 2rem);
}

.card {
  container-type: inline-size;
  container-name: card;
  display: grid;
  gap: 1rem;
}
.card img { inline-size: 100%; block-size: auto; aspect-ratio: 16 / 9; }

@container card (inline-size > 28rem) {
  .card {
    grid-template-columns: 40% 1fr;
    align-items: start;
  }
  .card img { aspect-ratio: 4 / 3; }
}
```

```html
<picture>
  <source type="image/avif" srcset="card-480.avif 480w, card-960.avif 960w" sizes="(min-width: 40em) 33vw, 100vw">
  <source type="image/webp" srcset="card-480.webp 480w, card-960.webp 960w" sizes="(min-width: 40em) 33vw, 100vw">
  <img src="card-960.jpg" alt="" width="960" height="540" loading="lazy" decoding="async">
</picture>
```

*What this demonstrates:* Grid `auto-fit` handles page-level wrapping; an `@container` query handles component-level layout. The card becomes horizontal (image + content) only when it has room; reused in a narrow sidebar, it stays vertical — no viewport query involved, no JS resize handler.

### 5.3 Fluid type + spacing scale
CSS custom properties computed from a single `--step-0`, all `rem`, using `clamp()` for fluidity — SC 1.4.4 Resize Text. Tolerates user text-spacing overrides (SC 1.4.12 Text Spacing) because no element hard-codes line-height in pixels.

```css
:root {
  /* vi (inline viewport) is writing-mode-aware — in vertical-rl it tracks the
     physical viewport height instead of width, keeping the scale coherent
     across writing modes. vw is the legacy equivalent and would wrong-foot
     vertical-script layouts.                                                */
  --step-0: clamp(1rem, 0.95rem + 0.25vi, 1.125rem);
  --step-1: clamp(1.125rem, 1.05rem + 0.4vi, 1.3125rem);
  --step-2: clamp(1.25rem, 1.15rem + 0.5vi, 1.5rem);
  --step-3: clamp(1.5rem, 1.3rem + 1vi, 2rem);
  --step-4: clamp(2rem, 1.7rem + 1.5vi, 3rem);
  --space-s: clamp(0.75rem, 0.7rem + 0.25vi, 1rem);
  --space-m: clamp(1rem, 0.9rem + 0.5vi, 1.5rem);
  --space-l: clamp(1.5rem, 1.3rem + 1vi, 2.5rem);
  --measure: 70ch;
}
body { font-size: var(--step-0); line-height: 1.5; }
h1 { font-size: var(--step-4); line-height: 1.2; }
p { max-inline-size: var(--measure); }
```

### 5.4 Hero with safe-area + dynamic viewport
Full-height hero that behaves on iOS through URL-bar transitions. LCP candidate, so image gets `fetchpriority="high"`, explicit dimensions, and no lazy-load. Autoplay video gated on user preferences. Must not lock orientation (SC 1.3.4).

```html
<section class="hero">
  <picture>
    <source type="image/avif" srcset="hero-1600.avif 1600w, hero-3200.avif 3200w" sizes="100vw">
    <source type="image/webp" srcset="hero-1600.webp 1600w, hero-3200.webp 3200w" sizes="100vw">
    <img src="hero-1600.jpg" alt="" width="1600" height="900" fetchpriority="high" decoding="async">
  </picture>
  <div class="hero-content">…</div>
</section>
```

```css
.hero {
  min-block-size: 100svh;
  padding-block: max(2rem, env(safe-area-inset-top)) max(2rem, env(safe-area-inset-bottom));
  padding-inline: clamp(1rem, 4vw, 3rem);
  display: grid;
  place-items: end start;
}
@media (prefers-reduced-motion: reduce) {
  .hero video { display: none; }
}
```

### 5.5 Form layout
Labels, inputs, help text that reflow gracefully. `font-size: 16px` on inputs to suppress iOS zoom-on-focus. Field widths sized in `ch` or intrinsic — tolerates translated labels. Spacing via logical properties so the form flips cleanly in RTL. Focus indicator preserved through layout changes. Error states not conveyed by color alone. Form controls carry `autocomplete` + `inputmode` + `enterkeyhint` so mobile soft-keyboards and password managers work correctly (SC 1.3.5 Identify Input Purpose, SC 3.3.8 Accessible Authentication). Help and error text are associated via `aria-describedby`; validation failures surface into a live region that already exists at page load.

```html
<!-- Single live region — created at page load, updated on validation.
     The region must pre-exist or screen readers won't announce updates. -->
<div id="form-status" role="status" aria-live="polite" aria-atomic="true"></div>

<form class="form" novalidate>
  <div class="field">
    <label for="email">Email</label>
    <input
      id="email" name="email" type="email"
      autocomplete="email" inputmode="email" enterkeyhint="next"
      required aria-describedby="email-help email-error"
    >
    <p id="email-help" class="hint">We'll send a verification link.</p>
    <p id="email-error" class="error" hidden></p>
  </div>

  <div class="field">
    <label for="password">Password</label>
    <input
      id="password" name="password" type="password"
      autocomplete="new-password" enterkeyhint="next"
      minlength="12" required aria-describedby="password-help password-error"
    >
    <p id="password-help" class="hint">At least 12 characters.</p>
    <p id="password-error" class="error" hidden></p>
  </div>

  <div class="field">
    <label for="otp">One-time code</label>
    <input
      id="otp" name="otp" type="text"
      autocomplete="one-time-code" inputmode="numeric" enterkeyhint="done"
      pattern="\d{6}" required aria-describedby="otp-error"
    >
    <p id="otp-error" class="error" hidden></p>
  </div>

  <button type="submit">Sign in</button>
</form>
```

```css
.form { display: grid; gap: var(--space-m); max-inline-size: 36rem; }
.field { display: grid; gap: 0.25rem; }
.field label { font-weight: 600; }
.field input,
.field textarea {
  font: inherit;
  /* 16 CSS px minimum prevents iOS Safari from zooming the viewport on focus. */
  font-size: max(1rem, 16px);
  padding-block: 0.5rem;
  padding-inline: 0.75rem;
  inline-size: 100%;
  /* Intrinsic minimum — tolerates translated labels, survives +35% expansion. */
  min-inline-size: 12ch;
  border: 1px solid currentColor;
  border-radius: 0.375rem;
}
.field input:focus-visible,
.field textarea:focus-visible { outline: 3px solid currentColor; outline-offset: 2px; }
.field [aria-invalid="true"] { border-color: var(--color-error); }
.field .hint { font-size: 0.875em; color: color-mix(in oklch, currentColor 70%, transparent); }
.field .error { color: var(--color-error); }
/* Icon prefix ensures the error is perceivable without colour — SC 1.4.1. */
.field .error::before { content: "⚠ "; }
```

```js
// On validation failure, populate the error node, set aria-invalid, and
// update #form-status (which already exists) so screen readers announce.
function reportError(fieldId, message) {
  const input = document.getElementById(fieldId);
  const error = document.getElementById(`${fieldId}-error`);
  input.setAttribute("aria-invalid", "true");
  error.textContent = message;
  error.hidden = false;
  document.getElementById("form-status").textContent = `Error: ${message}`;
}
```

*What this demonstrates:* `autocomplete="email|new-password|one-time-code"` + `inputmode="email|numeric"` + `enterkeyhint="next|done"` gives mobile users the right soft keyboard and the Next/Done return key that matches the form's flow. `aria-describedby` links help and error text to each input so screen readers announce them at focus. The live region exists at page load (empty) so updates are announced; creating it on demand would silently fail. The error icon prefix satisfies "not color alone" (SC 1.4.1) — the red border is redundant decoration, not the primary signal.

**Form-level error summary** (for server-rejected submissions or multi-field validation): render a summary block at the top of the form listing every error as a link to the field, move focus into the summary, and `aria-live` it so screen readers announce the count. `role="alert"` is stronger than `role="status"` — use `alert` for server validation failures that demand immediate attention; use `status` + `aria-live="polite"` for per-field errors on blur.

```html
<div id="error-summary" class="error-summary" role="alert" tabindex="-1" hidden>
  <h2>There are 2 errors in your submission</h2>
  <ul>
    <li><a href="#email">Email is required</a></li>
    <li><a href="#password">Password must be at least 12 characters</a></li>
  </ul>
</div>
```
```js
function reportErrors(errors) {
  const summary = document.getElementById("error-summary");
  summary.querySelector("h2").textContent = `There ${errors.length === 1 ? "is 1 error" : `are ${errors.length} errors`} in your submission`;
  summary.querySelector("ul").replaceChildren(...errors.map(e => {
    const li = document.createElement("li");
    const a  = document.createElement("a");
    a.href = `#${e.fieldId}`; a.textContent = e.message;
    li.appendChild(a); return li;
  }));
  summary.hidden = false;
  summary.focus();                     // move focus so keyboard users land in the summary
  summary.scrollIntoView({ block: "start", behavior: "smooth" });
}
```

`tabindex="-1"` makes the summary programmatically focusable without adding it to the tab order. Clicking a summary link moves focus to the corresponding field — the browser handles that natively via the fragment link. Clear the summary on successful submit so it doesn't persist stale errors.

**Multi-step forms (wizards).** WCAG 2.2 adds SC 3.3.7 Redundant Entry (don't make users retype information they've already provided) and SC 3.3.8 Accessible Authentication (don't require cognitive-function tests like re-typing CAPTCHAs). Applied to wizards:

- **Progress indicator** — `<ol aria-label="Progress">` with `aria-current="step"` on the active step; list positions are the step numbers. Screen readers announce "step 2 of 5."
- **Back navigation preserves state** — the Back button returns to the previous step with all fields pre-filled. `autocomplete` tokens on every field so browser autofill works on the first visit and subsequent revisits. Never discard step data when the user navigates back.
- **Save-and-resume** — persist partial submissions server-side (keyed by the user's session, or a signed resume token emailed to them) so users on flaky networks or interrupted sessions don't lose work. This directly satisfies SC 3.3.7.
- **Error handling per step** — validate on `submit` (not on `blur` during typing); show the error summary at the top of the current step and move focus into it.
- **Heading-level continuity** — the page `<h1>` names the form; each step heading is `<h2>`. Screen-reader users navigating by headings can jump between steps without extra markup.

**Accessible Authentication (SC 3.3.8).** The `otp` field in the snippet above uses `autocomplete="one-time-code"` so iOS/Android surface the SMS code inline. For non-SMS flows: `autocomplete="webauthn"` on a password field triggers the passkey prompt where available. Do not require users to solve puzzles, transcribe text, or perform cognitive operations other than recognising a code or a stored credential — that is the SC 3.3.8 bar.

### 5.6 Data-heavy content (wide tables)
Real data tables carry three concerns: semantic structure for screen readers, responsive reflow for small viewports and high zoom, and INP cost as the row count grows. Treat them as three separate problems.

**Semantic structure.** Use `<table>` + `<caption>` + `<thead>` + `<tbody>` with `<th scope="col">` / `<th scope="row">`. Tables without `<caption>` and `scope` are navigation-hostile in screen readers — rows read as anonymous cell sequences with no column context. For responsive "card-view" collapses at narrow widths, keep the `<table>` semantics and restyle via CSS (`display: grid` on `tbody`, pseudo-content from `data-label` for cell labels); don't swap to a `<div>` grid that loses table semantics.

```html
<figure class="table-wrap">
  <table>
    <caption>Orders, last 30 days <span class="count">(124 rows)</span></caption>
    <thead>
      <tr><th scope="col">Order</th><th scope="col">Customer</th><th scope="col">Placed</th><th scope="col">Total</th><th scope="col">Status</th></tr>
    </thead>
    <tbody>
      <tr>
        <th scope="row"><a href="/orders/A-1042">A-1042</a></th>
        <td data-label="Customer">Acme Corp</td>
        <td data-label="Placed"><time datetime="2026-04-12">Apr 12</time></td>
        <td data-label="Total" class="num">$1,240.00</td>
        <td data-label="Status"><span class="badge badge--shipped">Shipped</span></td>
      </tr>
      <!-- more rows -->
    </tbody>
  </table>
</figure>
```

```css
.table-wrap {
  overflow-inline: auto;
  scrollbar-gutter: stable;
  padding-block-end: 0.5rem;
}
.table-wrap table { border-collapse: collapse; inline-size: max-content; min-inline-size: 100%; }
.table-wrap :focus-visible { outline-offset: 2px; }
.table-wrap caption { caption-side: top; text-align: start; padding-block-end: 0.5rem; font-weight: 600; }
.table-wrap th, .table-wrap td { padding: 0.5rem 0.75rem; text-align: start; }
.table-wrap .num { text-align: end; font-variant-numeric: tabular-nums; }

/* Sticky column headers for long vertical scroll. */
.table-wrap thead th {
  position: sticky;
  inset-block-start: 0;
  background: light-dark(#fff, #1a1a1a);
  z-index: 1;
}

/* Sticky row header (first column) for wide horizontal scroll. */
.table-wrap tbody th {
  position: sticky;
  inset-inline-start: 0;
  background: light-dark(#fff, #1a1a1a);
}

/* Card-view collapse at narrow widths — preserves <table> semantics,
   restyles via grid + pseudo-content. */
@container (inline-size < 40rem) {
  .table-wrap table,
  .table-wrap thead,
  .table-wrap tbody,
  .table-wrap tr,
  .table-wrap th,
  .table-wrap td { display: block; }
  .table-wrap thead { position: absolute; inline-size: 1px; block-size: 1px; overflow: hidden; clip-path: inset(50%); }
  .table-wrap tr { display: grid; grid-template-columns: auto 1fr; gap: 0.25rem 0.75rem; padding-block: 0.75rem; border-block-end: 1px solid currentColor; }
  .table-wrap td::before { content: attr(data-label) ":"; font-weight: 600; }
}
```

**Reflow at zoom.** SC 1.4.10 Reflow requires the table to present without two-dimensional scrolling at 320 CSS px *or* at 400% zoom. The card-view collapse above satisfies it; the naive horizontal-scroll-only table fails at 400% zoom on narrow screens. Verify both axes — 320 px × 100% zoom **and** desktop at 400% zoom — as distinct review steps.

**Sticky headers + focus.** When column headers are sticky and a user tabs into a row, the focused cell can land *behind* the sticky header — an SC 2.4.11 Focus Not Obscured failure. Set `scroll-margin-block-start` on focusable cells to the header's computed height: `.table-wrap tbody a:focus-visible { scroll-margin-block-start: 3rem; }`. The browser will scroll the focused cell clear of the sticky header on focus.

**INP cost as rows grow.** Beyond ~500 visible rows, layout + paint + hit-testing becomes an INP hazard (tap a cell → wait for layout). Three mitigations, ordered by simplicity:

1. **`content-visibility: auto` + `contain-intrinsic-size` on each row** — the browser skips off-screen row work until the row is near the viewport. Cheapest, no JS. Pitfall: `contain-intrinsic-size` must match actual rendered height reasonably well or scrollbar-length jumps on realise.
2. **Pagination via cursor** (§3.7 / `cosmos.PAT-continuation-cursor` when backed by Cosmos) — render 25–100 rows per page; the server holds the rest. Predictable INP regardless of total-row count.
3. **Virtualization library** — only when (1) and (2) are insufficient, typically when users genuinely need to scroll thousands of rows continuously. Virtualization adds INP risk on scroll (it runs layout on every viewport update) and complicates keyboard navigation — make sure it preserves focus semantics and `aria-rowcount` / `aria-rowindex` attributes for screen readers.

**Sorting and filtering.** Add `aria-sort="ascending" | "descending" | "none"` on the active `<th>` when the column is sortable; change on click and announce via an `aria-live` region ("Sorted by Placed, ascending. 124 rows."). Keyboard users activate sort via `Enter` on a focused `<th>`-wrapped `<button>`; do not make the `<th>` itself tabbable.

### 5.7 Carousel / slider / drag interactions
Any drag gesture has a button or keyboard alternative — SC 2.5.7. Auto-advancing content has a pause/stop control. RTL-aware navigation: in `:dir(rtl)`, "next" means left-ward (reading direction).

```html
<div class="carousel" role="region" aria-label="Featured">
  <button class="prev" aria-label="Previous">‹</button>
  <ul class="slides" tabindex="0"> … </ul>
  <button class="next" aria-label="Next">›</button>
  <button class="pause" aria-label="Pause autoplay">⏸</button>
</div>
```

```css
.slides { display: flex; overflow-inline: auto; scroll-snap-type: inline mandatory; gap: 1rem; scroll-behavior: smooth; }
.slides > * { scroll-snap-align: start; flex: 0 0 min(80%, 24rem); }
.prev, .next, .pause { min-block-size: 2.75rem; min-inline-size: 2.75rem; }
:dir(rtl) .prev svg,
:dir(rtl) .next svg { transform: scaleX(-1); }

@media (prefers-reduced-motion: reduce) {
  .slides { scroll-behavior: auto; }
  /* Autoplay off entirely; the pause button becomes vestigial but harmless. */
  .carousel[data-autoplay] { animation: none; }
}
```

Autoplay and snap-animation are driven by JS; the rule above disables the smooth-scroll behavior so keyboard and programmatic navigation land without motion. The autoplay script reads `matchMedia('(prefers-reduced-motion: reduce)').matches` on init and does not start the interval if `true` — the CSS rule is the safety net, not the full implementation.

**Keyboard operation.** Arrow-key navigation, `Home` / `End` for first / last slide, `Space` to pause/resume autoplay. Tab order lands on `prev` → scrollable region → `next` → `pause`. The scrollable `<ul class="slides" tabindex="0">` is itself keyboard-scrollable once focused. Do not trap focus inside the carousel — users must be able to Tab out.

```js
const carousel = document.querySelector(".carousel");
const slides   = carousel.querySelector(".slides");
const status   = carousel.querySelector(".active-slide-status");   // aria-live region

slides.addEventListener("keydown", (e) => {
  const stride = slides.querySelector("li").getBoundingClientRect().width + 16; // gap
  if (e.key === "ArrowRight") slides.scrollBy({ left:  stride, behavior: "smooth" });
  if (e.key === "ArrowLeft")  slides.scrollBy({ left: -stride, behavior: "smooth" });
  if (e.key === "Home")       slides.scrollTo({ left: 0, behavior: "smooth" });
  if (e.key === "End")        slides.scrollTo({ left: slides.scrollWidth, behavior: "smooth" });
});

// Active-slide announcement: IntersectionObserver picks the most-visible slide,
// updates the live region. Debounce so rapid swiping doesn't flood the AT.
const io = new IntersectionObserver((entries) => {
  for (const e of entries) if (e.isIntersecting && e.intersectionRatio > 0.6) {
    const idx = [...slides.children].indexOf(e.target);
    queueMicrotask(() => status.textContent = `Slide ${idx + 1} of ${slides.children.length}`);
  }
}, { root: slides, threshold: [0.6] });
for (const li of slides.children) io.observe(li);
```

```html
<!-- Live region mirrors active slide for screen readers -->
<p class="sr-only active-slide-status" role="status" aria-live="polite" aria-atomic="true"></p>
```

**Autoplay rules (SC 2.2.2 Pause, Stop, Hide).** Any auto-updating content moving longer than 5 seconds must offer a pause / stop control. Applied to carousels:

- Autoplay is **off** by default. Opt-in by setting `data-autoplay="true"` on the container.
- When on, the `pause` button is visible and keyboard-operable; `aria-pressed` mirrors state.
- Autoplay pauses on: pointer hover, focus within the carousel, `prefers-reduced-motion: reduce`.
- On small viewports (`(pointer: coarse)`), consider defaulting autoplay off entirely — users can't hover to pause.
- Never autoplay carousels with text content users must read — SC 2.2.1 Timing Adjustable becomes harder than it's worth.

**RTL.** `scroll-snap-type: inline mandatory` + `flex` in a `:dir(rtl)` container reverse the visual order automatically (logical flow follows reading direction). The `prev` / `next` icons flip via `:dir(rtl) transform: scaleX(-1)`. Verify by loading with `<html dir="rtl">` and arrowing through — right-arrow should move visually left.

### 5.8 Dialog / modal
Use the native `<dialog>` element with `showModal()`: focus trap, backdrop, `Escape` to close, and `inert` on the rest of the page are handled by the platform. Focus is restored automatically when the dialog closes.

```html
<button type="button" class="open-dialog">Edit profile</button>
<dialog class="profile-dialog" aria-labelledby="profile-dialog-title">
  <form method="dialog">
    <h2 id="profile-dialog-title">Edit profile</h2>
    <!-- fields -->
    <div class="actions">
      <button value="cancel">Cancel</button>
      <button value="save" class="primary">Save</button>
    </div>
  </form>
</dialog>
```

```css
dialog.profile-dialog {
  max-inline-size: min(40rem, 100% - 2rem);
  max-block-size: min(80svh, 100% - 2rem);
  margin: auto;
  padding: clamp(1rem, 4vw, 2rem);
  border: none;
  border-radius: 1rem;
  background: light-dark(#fff, #1a1a1a);
  color: light-dark(#111, #eee);
}
dialog::backdrop { background: color-mix(in srgb, black 50%, transparent); backdrop-filter: blur(2px); }
dialog .actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-block-start: 1.5rem; }
dialog button { min-block-size: 2.75rem; min-inline-size: 5rem; padding-inline: 1rem; }
@media (max-width: 30em) {
  /* Full-screen on small viewports; easier to operate one-handed. */
  dialog.profile-dialog { max-inline-size: 100%; max-block-size: 100svh; border-radius: 0; }
}
```

```js
document.querySelector(".open-dialog").addEventListener("click", () => {
  document.querySelector(".profile-dialog").showModal();
});
```

*What this demonstrates:* `<dialog>` + `showModal()` gives SC 2.4.11-compliant focus handling for free. `<form method="dialog">` is a platform trick — any submit inside the form closes the dialog and sets `dialog.returnValue` to the clicked button's `value` attribute, so the caller can branch on `"cancel"` vs `"save"` without JS wiring. Prefer this over adding `@onclick`/`onclick` handlers that call `dialog.close()` manually; use manual `close()` only when the dialog body is *not* a form. Full-screen on narrow viewports because a centred 40rem dialog on a 360px phone is just a crammed small modal.

### 5.9 Skeleton / loading and empty states
Async content creates two responsive hazards: layout shift during load (CLS), and ambiguous UI when results are empty. Skeletons reserve space; empty states are announced politely; both respect `prefers-reduced-motion`.

```html
<section class="results" aria-busy="true" aria-live="polite">
  <div class="skeleton-card"><div class="skeleton skeleton-img"></div><div class="skeleton skeleton-line"></div><div class="skeleton skeleton-line short"></div></div>
  <!-- repeat skeleton-card -->
</section>
```

```css
.skeleton {
  background: linear-gradient(90deg,
    color-mix(in oklch, currentColor 10%, transparent) 25%,
    color-mix(in oklch, currentColor 20%, transparent) 37%,
    color-mix(in oklch, currentColor 10%, transparent) 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s linear infinite;
  border-radius: 0.5rem;
}
.skeleton-img { aspect-ratio: 16 / 9; }
.skeleton-line { block-size: 1em; margin-block-start: 0.5em; }
.skeleton-line.short { inline-size: 60%; }
@keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }
@media (prefers-reduced-motion: reduce) {
  .skeleton { animation: none; background: color-mix(in oklch, currentColor 15%, transparent); }
}
.empty-state {
  display: grid; place-items: center;
  padding: clamp(2rem, 6vw, 4rem);
  text-align: center;
  color: color-mix(in oklch, currentColor 70%, transparent);
}
```

*What this demonstrates:* skeletons match final content geometry (`aspect-ratio`, line heights, `short` modifier) so when real content arrives there's no CLS. `aria-busy="true"` + `aria-live="polite"` announces the load completion. Shimmer animation is disabled under `prefers-reduced-motion: reduce` and replaced with a static tint — still visible, no motion.

**The state family.** Loading is one of four states every async component has to handle; getting the transitions between them right is what distinguishes a polished UI from a janky one:

1. **Initial load** — skeleton matching final geometry. `aria-busy="true"` on the container; swap to real content on settle.
2. **Pagination / refresh** — smaller indicator (inline spinner at the trigger, or subtle dim-out via `.results[aria-busy="true"] { opacity: 0.6; }`), not a full skeleton redraw. Full skeletons on every page-change feel broken.
3. **Optimistic update + rollback** — when the user performs an action that will succeed ~always, render the expected result immediately and reconcile on server response. On failure, roll back the UI, restore the input (never silently lose it), and surface a retry affordance.
4. **Empty** — the backing query succeeded with zero results. A dedicated empty state with a localized message and (if applicable) a primary CTA to unblock the user ("Create your first invoice"). Don't collapse to nothing — users read an empty list as a bug.
5. **Error** — the request itself failed. Render a retry button, a localized short explanation, and a problem detail for support (trace-id or error code). Distinguish transient errors (auto-retry + indicator) from permanent errors (explicit retry + human-readable cause).

```html
<section class="results" aria-busy="false">
  <!-- State slots. Swap one at a time via data attribute; CSS selects which
       renders. Prevents layout-shift when transitioning between states. -->
  <ul class="state-loaded"></ul>

  <div class="state-empty" hidden>
    <!-- Empty-state illustration is decorative SVG (see §5.14). -->
    <p class="empty-title">No invoices yet</p>
    <p class="empty-body">Create your first invoice to get started.</p>
    <button type="button" class="primary">Create invoice</button>
  </div>

  <div class="state-error" role="alert" hidden>
    <p class="error-title">Couldn't load invoices</p>
    <p class="error-body">The server is not responding.</p>
    <p class="error-support">Support ref: <code>00-4bf9…e736</code></p>
    <button type="button" class="retry">Try again</button>
  </div>
</section>
```

```js
async function load(state) {
  const root = document.querySelector(".results");
  root.setAttribute("aria-busy", "true");
  try {
    const items = await fetchInvoices({ signal: state.controller.signal });
    renderLoaded(items);
    switchTo("loaded");
  } catch (e) {
    if (e.name === "AbortError") return;           // ignore cancellations
    renderError(e.problem);                        // RFC 9457 problem+json from the API
    switchTo("error");
  } finally {
    root.setAttribute("aria-busy", "false");
  }
}

async function performOptimistic(item) {
  const prev = renderInsert(item);                 // optimistic: append now
  try   { await api.create(item); }                 // server reconcile
  catch (e) { renderRemove(prev); renderRetry(item, e.problem); /* rollback + retry UI */ }
}
```

**Retry discipline.** Transient failures (408, 429, 502, 503, 504) can auto-retry *once* with backoff before surfacing an error; anything beyond that is user-visible and user-actioned. Permanent failures (400, 401, 403, 404, 409, 410, 412, 422) never auto-retry — surface the problem-detail `title` and offer the fix. On 429, honour `Retry-After` — a countdown in the retry button is a nice touch; a silent retry that ignores `Retry-After` is an amplification hazard. Cross-reference: `serverless-api-design.md` §3.10 / §3.5.

**Localized empty / error copy.** All state strings (`"No invoices yet"`, `"Create your first invoice"`, `"Couldn't load invoices"`) go through the same i18n pipeline as the rest of the UI. Test empty-state illustrations in RTL and in forced-colors — decorative SVGs that hard-code a light-mode palette become invisible in dark mode or under `forced-colors: active` (see §5.14).

### 5.10 Skip link + landmark structure
Keyboard users on narrow viewports must tab through header → nav → main on every page. A skip link lets them jump to main content. Landmarks give screen-reader users a structural map.

```html
<a class="skip-link" href="#main">Skip to main content</a>
<header>
  <nav aria-label="Primary">…</nav>
</header>
<main id="main" tabindex="-1">
  <!-- page content -->
</main>
<aside aria-label="Related">…</aside>
<footer>…</footer>
```

```css
.skip-link {
  position: absolute;
  inset-block-start: 0;
  inset-inline-start: 0;
  padding: 0.5rem 1rem;
  background: Canvas;
  color: CanvasText;
  border: 2px solid currentColor;
  transform: translateY(-100%);
  transition: transform 150ms;
}
.skip-link:focus-visible { transform: translateY(0); }
@media (prefers-reduced-motion: reduce) {
  .skip-link { transition: none; }
}
main:focus { outline: none; }
```

*What this demonstrates:* the skip link is offscreen until focused, then animates in. Uses `Canvas`/`CanvasText` system colors so it remains visible under `forced-colors: active`. The `<main id="main" tabindex="-1">` target receives focus when the link is activated. Landmark roles (`<header>`, `<nav aria-label>`, `<main>`, `<aside aria-label>`, `<footer>`) give screen readers a navigable outline.

### 5.11 Tooltip / popover
Use the native `popover` attribute for non-modal overlays — tooltips, menus, notifications, disclosure cards. The browser handles top-layer rendering, light-dismiss (`Esc` + outside click), and removes it from the tab order while closed. For modal forms, use `<dialog>` (§5.8); popovers do not trap focus.

```html
<button type="button" popovertarget="tz-info" aria-describedby="tz-info">
  Timezone
  <span aria-hidden="true">ⓘ</span>
</button>
<div id="tz-info" popover class="tooltip">
  <p>Dates display in your browser's local timezone. Change in settings to override.</p>
</div>
```

```css
.tooltip {
  margin: 0;
  max-inline-size: 28ch;
  padding: 0.75rem 1rem;
  border: 1px solid color-mix(in oklch, currentColor 35%, transparent);
  border-radius: 0.5rem;
  background: light-dark(#fff, #1a1a1a);
  color: light-dark(#111, #eee);
  box-shadow: 0 4px 12px color-mix(in oklch, currentColor 25%, transparent);
  /* Anchor positioning: place below the trigger, flip to above if no room. */
  position-area: block-end;
  position-try-fallbacks: flip-block;
}
.tooltip:popover-open { /* light fade-in, reduced-motion-aware */
  animation: tooltip-in 120ms ease-out;
}
@media (prefers-reduced-motion: reduce) {
  .tooltip:popover-open { animation: none; }
}
@keyframes tooltip-in { from { opacity: 0; transform: translateY(-2px); } }
@media (forced-colors: active) {
  .tooltip { border-color: CanvasText; background: Canvas; color: CanvasText; }
}
```

*What this demonstrates:* `popover` gives `Esc` + outside-click dismiss, top-layer stacking, and `inert` treatment of the rest of the page — all without JS. `aria-describedby` on the trigger associates the tooltip text with the control so screen readers announce it on focus. `position-area` + `position-try-fallbacks` flip the tooltip to the trigger's other side when the viewport edge is close — no JS positioning library needed. Default `popover="auto"` supports light-dismiss; `popover="hint"` is the most semantically correct for a tooltip (it does not close neighbouring `auto` popovers); `popover="manual"` is for components that own their close logic (notifications, coach-marks).

CSS Anchor Positioning (`position-area` / `position-try-fallbacks`) is **Baseline 2026** — newly available. For older browsers, feature-detect with `@supports (position-area: block-end)` and fall back to a fixed `inset-block-start: 100%` / `inset-inline-start: 0` placement, or load a JS positioning library (Floating UI, etc.). Earlier Chromium builds shipped the same properties under the names `inset-area` / `position-try-options` — both names still resolve for a short backwards-compatibility window, but new code should use the final names.

### 5.12 Search-as-you-type with live results
Per-keystroke filtering is the classic INP hazard and the classic `aria-live` use case. Debounce the work, announce the result count into a pre-existing live region, and respect `prefers-reduced-motion` in any result-list animation.

```html
<!-- <search> is the modern landmark element; equivalent to <div role="search">.
     Use the element where supported; fall back to role="search" for older ATs. -->
<search>
  <form class="search">
    <label for="q">Search movies</label>
    <input
      id="q" type="search"
      autocomplete="off" inputmode="search" enterkeyhint="search"
      aria-describedby="q-hint" aria-controls="results"
    >
    <p id="q-hint" class="hint">Matches across title, year, and director.</p>
  </form>
</search>

<!-- Pre-existing at page load — announcements won't fire if created later. -->
<p id="results-status" class="sr-only" aria-live="polite" aria-atomic="true"></p>

<ul id="results" class="results" aria-busy="false">
  <!-- results rendered here -->
</ul>
```

```css
.search { display: grid; gap: 0.25rem; max-inline-size: 36rem; }
.search input { font-size: max(1rem, 16px); padding-block: 0.5rem; padding-inline: 0.75rem; }
.results { display: grid; gap: 0.5rem; list-style: none; padding: 0; margin: 0; }
.results[aria-busy="true"] { opacity: 0.6; }
.sr-only { position: absolute; inline-size: 1px; block-size: 1px; padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
```

```js
const q = document.getElementById("q");
const list = document.getElementById("results");
const status = document.getElementById("results-status");
let controller = null;

// 200 ms debounce keeps typing responsive; INP stays well under 200 ms
// because the network / filter work is not on the keystroke path.
const DEBOUNCE = 200;
let t;
q.addEventListener("input", () => {
  clearTimeout(t);
  t = setTimeout(runSearch, DEBOUNCE);
});

async function runSearch() {
  controller?.abort();
  controller = new AbortController();
  list.setAttribute("aria-busy", "true");
  try {
    const items = await fetchResults(q.value, controller.signal);
    render(items);
    // Live region update — the region was present at page load, so this announces.
    status.textContent = items.length === 0
      ? `No results for ${q.value}.`
      : `${items.length} result${items.length === 1 ? "" : "s"} for ${q.value}.`;
  } catch (err) {
    if (err.name !== "AbortError") status.textContent = "Search failed. Try again.";
  } finally {
    list.setAttribute("aria-busy", "false");
  }
}
```

*What this demonstrates:* debounce (200 ms) keeps the keystroke handler trivial — INP stays good because the filter/network call doesn't run on the critical interaction path. `AbortController` cancels in-flight requests when the user types again, preventing out-of-order results. The `aria-live="polite"` region is in the DOM at page load and gets *updated* (not recreated) so screen-reader announcements fire correctly. `aria-busy` on the list signals to assistive tech that updates are pending. `type="search"` + `inputmode="search"` + `enterkeyhint="search"` give the right mobile soft-keyboard affordance.

### 5.13 Media — video, audio, captions, custom controls
Responsive media has three concerns that overlap but don't reduce to each other: **a11y** (captions, audio description, controls), **performance** (poster + lazy + preload trade-off), and **autoplay etiquette** (motion, data, battery). Each WCAG success criterion below maps to a specific `<track>` or attribute.

**Baseline video element.**

```html
<figure class="video">
  <video
    controls
    playsinline
    muted
    preload="metadata"
    poster="/img/intro-poster-1280.avif"
    width="1280" height="720"
    crossorigin="anonymous"
    aria-describedby="intro-summary">
    <source src="/video/intro.av1.mp4"  type='video/mp4; codecs="av01.0.05M.08"'>
    <source src="/video/intro.h264.mp4" type='video/mp4; codecs="avc1.64001F"'>
    <!-- Captions (SC 1.2.2 Captions (Prerecorded), AA) -->
    <track kind="captions"     srclang="en"    label="English"    src="/vtt/intro.en.vtt" default>
    <track kind="captions"     srclang="ar"    label="العربية"   src="/vtt/intro.ar.vtt">
    <!-- Audio description track (SC 1.2.5 Audio Description (Prerecorded), AA) -->
    <track kind="descriptions" srclang="en"    label="English AD" src="/vtt/intro.ad.en.vtt">
    <!-- Chapters for navigation (not an SC but improves UX) -->
    <track kind="chapters"     srclang="en"    label="Chapters"   src="/vtt/intro.chapters.en.vtt">
    Your browser does not support embedded video.
    <a href="/video/intro.h264.mp4">Download video</a>.
  </video>
  <figcaption id="intro-summary">Intro: how the product works in 90 seconds. <a href="/transcripts/intro">Read transcript</a>.</figcaption>
</figure>
```

**Accessibility contract.**

- **Captions (`<track kind="captions">`)** — mandatory for all prerecorded video with audio content at WCAG 2.2 AA. WebVTT, author-written (machine-generated captions from speech-to-text *can* be a starting point but require human review for proper nouns, timing, and non-speech cues).
- **Audio description (`<track kind="descriptions">`)** — mandatory at AA for video with information that isn't conveyed in the audio track (on-screen text, visual demonstrations). Implemented as a separate timed-text track; browser support for playing the description varies, so also provide a **described version of the video** as an alternative if the audience is likely to need it.
- **Transcript** — not an SC by itself, but the most robust fallback — works for deaf-blind users (via braille displays), for users on muted devices, and for search indexing. Link it from the `<figcaption>`.
- **`playsinline`** — prevents iOS Safari from forcing fullscreen on iPhone. Without it, autoplay + fullscreen is how videos bounce users out of your UI.
- **`preload="metadata"`** (not `"auto"`) — load enough to show duration and thumbnail, not the whole file. `"auto"` on an above-fold hero video competes with the LCP image for bandwidth.
- **`crossorigin="anonymous"`** — required to read WebVTT tracks from a CDN under CORS.

**Custom controls (when native controls are insufficient).** Replacing the browser's `controls` bar is a large commitment — you now own keyboard operability, focus management, labelled buttons, mobile touch targets, and screen-reader announcement. The minimum:

- Every control is a `<button>` (not a `<div>`), has a visible label or `aria-label`, and is ≥ 24×24 CSS px (SC 2.5.8).
- `Space` toggles play/pause; `Left`/`Right` seek by 5 s; `Up`/`Down` adjust volume; `M` mutes; `F` fullscreen. These are the platform defaults users expect.
- Progress bar is a `<input type="range">` with `aria-valuetext="1 minute 23 seconds of 2 minutes 45 seconds"` updated on `timeupdate`.
- Caption toggle is a `<button aria-pressed>`; updating `track.mode = "showing" | "hidden"` on the active caption track.
- Hide the native controls (`controls` attribute absent) only *after* confirming your custom controls are complete. Partial custom controls + no native fallback is worse than either alone.

**Autoplay etiquette.** Autoplay is gated by three browser conditions (muted, user-activation or site-engagement, and sometimes data-saver) plus two authoring conditions you control:

- **`muted` + `playsinline`** are required for cross-browser autoplay. Autoplay with sound is denied in every major browser without prior user gesture.
- **Gate on `prefers-reduced-motion: no-preference`** and (server-side) on `Save-Data` being absent. A marketing auto-loop video on a data-saver connection is hostile.

```js
const video = document.querySelector("video.hero");
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const saveData = document.documentElement.dataset.saveData === "on"; // set by server per Save-Data
if (!reduce && !saveData) video.play().catch(() => { /* browser blocked; leave paused */ });
```

**Media Session API.** `navigator.mediaSession.metadata` surfaces title / artwork / artist in the OS lock-screen and Bluetooth controls. Pair with `setActionHandler("play" | "pause" | "seekforward" | "previoustrack" | …)` so hardware keys work. Essential for any audio-first UI (podcasts, audiobooks); nice-to-have for hero videos.

**Picture-in-Picture.** `video.requestPictureInPicture()` is user-gesture-required; wire it to a custom control button rather than attempting it on autoplay. Respect `disablePictureInPicture` when set.

**Audio-only.** `<audio controls preload="metadata">` + the same `<track kind="captions">` (or `kind="subtitles"`) pattern. The poster concept doesn't apply; consider a static waveform image (decorative SVG per §5.14) so the element occupies space before the audio loads.

### 5.14 SVG — decorative vs informative, theming, forced-colors
SVG is leaked accessibility liability more than it is leaked performance liability. Get the semantic role right, make it theme cleanly, and keep it visible under `forced-colors: active`.

**Decorative SVG** — icons that accompany a text label, empty-state illustrations that don't convey unique information, background shapes. The text already says what the icon says; the SVG is pure ornament.

```html
<!-- Decorative: hidden from assistive tech; inherits text colour; scales with font. -->
<button type="button" class="btn-download">
  <svg class="icon" viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true" focusable="false">
    <path d="M12 3v12m0 0-4-4m4 4 4-4M4 19h16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
  Download
</button>
```

- **`aria-hidden="true"`** — the icon duplicates the "Download" text; screen readers would announce it twice otherwise.
- **`focusable="false"`** — legacy IE / EdgeHTML residual — some assistive tech still honours it; cheap insurance.
- **`stroke="currentColor"`** (or `fill="currentColor"`) — the icon themes with text, flips cleanly between light and dark, survives `forced-colors: active` (where it renders as `CanvasText`).
- **`width="1em" height="1em"`** — scales with the surrounding text, never a fixed `px` on user-scalable content.

**Informative SVG** — icons without a text label (icon-only buttons), status badges, data visualisations.

```html
<!-- Icon-only button: title via aria-label since no visible text. -->
<button type="button" aria-label="Close">
  <svg viewBox="0 0 24 24" width="1.25em" height="1.25em" aria-hidden="true" focusable="false">
    <path d="M6 6l12 12M18 6 6 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>
</button>

<!-- Standalone informative graphic: labelled as an image via role + title/desc. -->
<svg role="img" aria-labelledby="chart-title chart-desc" viewBox="0 0 400 200">
  <title id="chart-title">Monthly active users</title>
  <desc id="chart-desc">A line chart showing users rising from 1,200 in January to 3,800 in April.</desc>
  <!-- … chart paths … -->
</svg>
```

- **Icon-only buttons** — the accessible name is on the `<button>` (`aria-label`), not on the SVG. The SVG is decorative; marking it `aria-hidden` avoids double-announce.
- **Standalone informative graphics** — `role="img"` + `<title>` (short accessible name) + `<desc>` (longer description). `aria-labelledby` wires both into the accessible name/description.
- **Data visualisations** — `<title>` alone summarises the takeaway (not "a bar chart" — the actual finding); `<desc>` or an adjacent `<figcaption>` carries the narrative. Also provide a data table (`<table>` per §5.6) as an accessible fallback for users who can't parse the graphic; link it from the caption.

**Theming and forced-colors.**

- **`currentColor` everywhere the SVG should follow text colour.** Never hard-code `fill="#333"` on an icon meant to theme with the UI; it survives exactly one theme and fails the other.
- **Multi-colour illustrations** use CSS custom properties: `<path fill="var(--accent, currentColor)">` lets the illustration pick up theme tokens and adapt to light/dark via `light-dark(...)` on the custom property.
- **`forced-colors: active`** — by default, the browser coerces SVG fills and strokes to system colours. That usually works for icons (which are `currentColor` anyway). For illustrations that hard-code colour, override with system-colour-aware styling:
  ```css
  @media (forced-colors: active) {
    .illustration path { fill: CanvasText; stroke: CanvasText; }
  }
  ```
- **Decorative illustrations that must disappear in high contrast** — set `forced-color-adjust: none` cautiously, or hide them (`@media (forced-colors: active) { .decoration { display: none; } }`) if the illustration becomes meaningless when coerced.

**Viewbox and responsive scaling.**

- `viewBox` is the SVG's coordinate space; `width` / `height` are the rendered box. A responsive SVG has `viewBox="0 0 W H"` and scales via its CSS `width` / `height` (or `inline-size` / `block-size`); no intrinsic-size hazard.
- `preserveAspectRatio="xMidYMid meet"` (the default) fits the graphic inside the box without distortion. Only override when intentional cropping is the goal.

**Sprites.** Icon sprites (`<svg><use href="#icon-download">`) save requests and are fully theme-able via `currentColor`. Pitfall: sprite symbols that hard-code `fill="#123456"` lose theming — author sprites with `currentColor` from the start.

### 5.15 File upload with keyboard fallback and accessible progress
Drag-and-drop upload is a usability win for mouse users and an accessibility hazard if drag is the *only* way to do it (SC 2.5.7). The correct shape: a visible `<input type="file">` *and* a drop-zone that wraps it; both produce the same result.

```html
<form class="upload" enctype="multipart/form-data">
  <label class="drop-zone" for="attachments" id="drop-zone">
    <input
      id="attachments" name="attachments"
      type="file" multiple
      accept="image/jpeg,image/png,image/webp,application/pdf">
    <p class="drop-zone__label">
      <span class="drop-zone__primary">Drop files here</span>
      <span class="drop-zone__secondary">or <span class="drop-zone__cta">browse</span></span>
    </p>
    <p class="drop-zone__hint" id="upload-hint">Up to 10 files, 25&nbsp;MB each. JPEG, PNG, WebP, or PDF.</p>
  </label>

  <!-- Pre-existing live region for progress and per-file status announcements. -->
  <p id="upload-status" class="sr-only" role="status" aria-live="polite" aria-atomic="true"></p>

  <!-- Per-file progress list; each item is updated in place, not replaced. -->
  <ul class="upload-list" id="upload-list" aria-describedby="upload-hint"></ul>
</form>
```

```css
.drop-zone {
  display: grid;
  place-items: center;
  gap: 0.5rem;
  min-block-size: 10rem;
  padding: clamp(1rem, 3vw, 2rem);
  border: 2px dashed currentColor;
  border-radius: 0.75rem;
  cursor: pointer;
  text-align: center;
}
.drop-zone:focus-within,
.drop-zone.is-dragover { outline: 3px solid currentColor; outline-offset: 2px; background: color-mix(in oklch, currentColor 5%, transparent); }
/* The file input is visually hidden but remains in the tab order,
   so keyboard users Tab to it and activate with Space/Enter. */
.drop-zone input[type="file"] { position: absolute; inline-size: 1px; block-size: 1px; opacity: 0; }
.drop-zone__cta { text-decoration: underline; }
.upload-list { display: grid; gap: 0.5rem; margin-block-start: 1rem; padding: 0; list-style: none; }
.upload-list li { display: grid; grid-template-columns: 1fr auto; gap: 0.5rem; align-items: center; }
.upload-list progress { inline-size: 100%; }
```

```js
const zone   = document.getElementById("drop-zone");
const input  = document.getElementById("attachments");
const status = document.getElementById("upload-status");
const list   = document.getElementById("upload-list");

// Drag-and-drop delegates to the file input.
["dragenter", "dragover"].forEach(evt => zone.addEventListener(evt, e => {
  e.preventDefault(); zone.classList.add("is-dragover");
}));
["dragleave", "drop"].forEach(evt => zone.addEventListener(evt, e => {
  e.preventDefault(); zone.classList.remove("is-dragover");
}));
zone.addEventListener("drop", e => {
  input.files = e.dataTransfer.files;
  input.dispatchEvent(new Event("change", { bubbles: true }));
});

input.addEventListener("change", () => {
  const files = Array.from(input.files);
  const errors = files.flatMap(validate);
  if (errors.length) { status.textContent = errors.join(" "); return; }
  status.textContent = `Uploading ${files.length} file${files.length === 1 ? "" : "s"}.`;
  files.forEach(uploadOne);
});

function validate(file) {
  const errs = [];
  if (file.size > 25 * 1024 * 1024) errs.push(`${file.name}: exceeds 25 MB limit.`);
  if (!/^(image\/(jpeg|png|webp)|application\/pdf)$/.test(file.type)) errs.push(`${file.name}: file type not accepted.`);
  return errs;
}

async function uploadOne(file) {
  const li = renderRow(file);                              // renders <progress max=100 value=0>
  // For large files, prefer a pre-signed direct-to-blob SAS (blob.PAT-direct-upload-sas
  // in the serverless-api-design Blob Storage extension). The API returns { uploadUrl,
  // blobUri }; the browser PUTs the payload directly to Blob Storage, not the Function.
  const { uploadUrl, blobUri } = await fetch("/uploads", { method: "POST", body: JSON.stringify({ name: file.name, size: file.size, type: file.type }), headers: { "Content-Type": "application/json" } }).then(r => r.json());

  const xhr = new XMLHttpRequest();
  xhr.upload.addEventListener("progress", e => {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      li.progress.value = pct;
      li.progress.setAttribute("aria-valuetext", `${pct} percent uploaded`);
    }
  });
  xhr.addEventListener("load", () => {
    li.setStatus(xhr.status >= 200 && xhr.status < 300 ? "done" : "failed");
    status.textContent = xhr.status < 300 ? `${file.name} uploaded.` : `${file.name} failed.`;
  });
  xhr.open("PUT", uploadUrl);
  xhr.setRequestHeader("x-ms-blob-type", "BlockBlob");
  xhr.send(file);
}
```

**Key points.**

- **Visible file input inside the drop zone** — the `<label for="attachments">` wraps the input, so clicking anywhere in the zone opens the picker. Keyboard users Tab to the input (visually hidden but in the tab order) and activate with `Space` / `Enter`. SC 2.5.7 satisfied: drag is an enhancement, not the only path.
- **Validation surfaces to a pre-existing live region** — errors and progress updates go to `#upload-status`; it exists at page load so announcements fire reliably.
- **Per-file progress via `<progress>`** — native element with `max=100` and `value`, `aria-valuetext` for screen readers ("67 percent uploaded"). Update `value` on `xhr.upload.progress`; don't re-render the whole `<li>` (flickers).
- **`accept` attribute + server-side validation** — `accept` is a UX hint; clients can always submit any type. Re-validate server-side and reject with problem+json (`invalid-file-type`, `payload-too-large`) per `serverless-api-design.md` §3.11 / §3.12.
- **Direct-to-blob SAS for large payloads** — the API endpoint `POST /uploads` issues a user-delegation SAS; the browser PUTs directly to Blob Storage. Function memory / timeout no longer constrain payload size. Cross-reference `blob.PAT-direct-upload-sas` in the `serverless-api-design` Blob Storage extension.
- **`fetchpriority="high"` — not applicable here.** Upload and LCP compete if the page is media-heavy; the upload starts on explicit user gesture, so it's a deliberate choice that takes bandwidth from background loads.
- **Cancellation** — wire an `AbortController` (or `xhr.abort()`) so a "Cancel" button per row interrupts in-flight uploads. Don't silently let cancelled uploads complete — the server may still receive the payload.

## 6. Gotchas

Named failures that pass casual QA. Each item is a trap + fix.

- **iOS Safari auto-zooms form inputs with `font-size < 16px`** — set `font-size: max(1rem, 16px)` on inputs and textareas.
- **`:hover` styles stick on touch devices** — gate behind `@media (hover: hover)`.
- **`100vh` is taller than the visible viewport on mobile Safari** — use `100dvh`/`100svh`/`100lvh` per §3.7.
- **Safe-area insets ignored on iPhone / Android edge-to-edge** — `padding: max(<min>, env(safe-area-inset-*))` on the outermost layout container.
- **`forced-colors` / Windows high-contrast mode flattens custom styles** — test with `forced-colors: active`; don't rely on color as the only information channel.
- **Virtual keyboard resize causes layout jumps** — set `interactive-widget=resizes-content` in viewport meta or handle `visualViewport` events.
- **Scrollbar appearing shifts horizontal layout** — `scrollbar-gutter: stable` on the scroll container.
- **Web font FOUT/FOIT** — `font-display: swap` + `@font-face` with `size-adjust`/`ascent-override` tuned to the fallback.
- **Dialog scroll-lock fails on iOS** — `overscroll-behavior: contain` on the dialog + `position: fixed` on the body while open.
- **`vw` inside a container misbehaves after layout** — prefer `cqi`/`cqb` when inside an `@container` context.
- **RTL breaks because physical properties leaked** — replace `margin-left` / `padding-right` / `left` / `right` / `text-align: left` / `float: right` with `margin-inline-start` / `padding-inline-end` / `inset-inline-start` / `inset-inline-end` / `text-align: start` / `float: inline-end`.
- **Direction-semantic icons (arrows, chevrons, back-buttons) don't mirror in RTL** — `:dir(rtl) .icon { transform: scaleX(-1); }` or swap SVG variants.
- **Button widths tuned to English labels break in German / Czech / Finnish** — use `min-width` + intrinsic content width, not hard-coded `width`.
- **Missing `lang` attribute on the document or on language-switched subtrees** — screen readers mispronounce, hyphenation rules wrong; set `<html lang="…">` and `lang="…"` on foreign-language fragments.
- **CJK line-breaking looks wrong** — review `word-break`, `overflow-wrap`, and `line-break: strict` for CJK-specific behavior; don't apply Latin defaults globally.
- **Performance: LCP image lazy-loaded** — remove `loading="lazy"` and add `fetchpriority="high"` on the hero/LCP image; lazy-loading the LCP element guarantees a slow LCP.
- **Performance: missing `width`/`height` on images** — CLS balloons once images load; always include intrinsic dimensions (or `aspect-ratio` on a wrapper) even when the image is CSS-sized.
- **Performance: naive `@font-face` without `size-adjust`** — swap causes visible reflow; use `size-adjust` + `ascent-override` / `descent-override` to match fallback metrics.
- **Performance: autoplay hero video on Save-Data clients** — gate any auto-play on `prefers-reduced-motion: no-preference` *and* a server-side check of the `Save-Data` header (since `prefers-reduced-data` is not yet implemented).
- **Performance: webfont used for CJK without subsetting** — 10+ MB download; use `unicode-range` subsets and per-script source files.
- **Performance: INP regressions from heavy JS tap handlers** — break work with `scheduler.yield()` / `requestIdleCallback`; measure via RUM, not DevTools on a developer machine.
- **Container queries silently ignored** — an ancestor must have `container-type: inline-size` or `size`; without it, container units fall back to small-viewport units — MDN Container Queries.
- **Viewport meta with `maximum-scale=1` or `user-scalable=no`** — blocks user zoom and fails SC 1.4.4; iOS10+ ignores these by default, so the only effect is on other browsers and failing a11y audits — MDN viewport meta.
- **Dark-mode contrast regression** — a palette that passes SC 1.4.3 in light mode often fails in dark; contrast must be verified in *both* themes, not inferred from one. Use `light-dark()` or explicit `@media (prefers-color-scheme: dark)` blocks and re-run contrast checks.
- **Focus ring removed with `outline: none`** — instant SC 2.4.7 Focus Visible failure. If the default ring is ugly, replace it (`:focus-visible { outline: 2px solid …; outline-offset: 2px; }`), never delete it.
- **Custom modal without focus trap** — a div-plus-JavaScript "modal" that doesn't contain focus lets keyboard users tab into the obscured page behind it. Use native `<dialog>` with `showModal()` (§5.8) — it handles the trap.
- **Missing skip link** — keyboard users on narrow viewports must tab through every nav item on every page to reach content. Add a skip link (§5.10); it costs nothing and fixes an SC 2.4.1 Bypass Blocks failure.
- **`autocomplete` attribute missing on account / checkout forms** — breaks password-manager and address autofill, slows mobile checkout, and hurts WCAG 3.3.8 Accessible Authentication. Use the exact tokens from the spec (`email`, `current-password`, `new-password`, `shipping street-address`, `cc-number`, etc.); invented values silently fail.
- **`aria-live` region added to the DOM at update time** — the announcement doesn't fire because the region didn't exist when the screen reader built its tree. The region must be present at page load; update its contents, don't create it on demand.
- **`overflow: hidden` on `<html>` or `<body>` to "lock scroll"** — breaks iOS Safari's address-bar collapse and causes content to be clipped. Use `overflow: clip` on a wrapper, or set `position: fixed` on body during a modal and restore on close.
- **Data-density that breaks at 400% zoom** — dashboards with 8 widgets side-by-side at 1920px must reflow to a single column (or scrollable within bounded panels) at 400% zoom; otherwise SC 1.4.4 Resize Text and SC 1.4.10 Reflow both fail. Use container queries on each widget so the reflow is component-local, not tied to viewport breakpoints. Test with browser zoom pinned at 400% on a 1280×1024 display.
- **Third-party iframe embeds (video, maps, ads, widgets) break responsive flow** — iframes without an aspect-ratio wrapper collapse to 150×150 default sizing or overflow the column. Wrap in a container with `aspect-ratio: 16 / 9` (or the embed's native ratio) and set `iframe { inline-size: 100%; block-size: 100%; border: 0; }`. Add `loading="lazy"` for off-screen embeds (saves data on Save-Data clients), `title="<descriptive>"` for SC 4.1.2 Name, Role, Value, and `sandbox="allow-scripts allow-same-origin"` + `referrerpolicy="strict-origin-when-cross-origin"` for security. Cross-reference `devsecops-audit` for iframe-related CSP and `frame-ancestors` directives.

## 7. Review checklist

A "is this component done?" self-check, enforced against WCAG 2.2 AA, i18n, and Core Web Vitals. Each item names the rule it guards and tags the verification layer so reviewers know whether to reach for a grep, a browser, or a real-device fleet:

- **[static]** — inspectable from source; grep, lint, or read the HTML/CSS/JS. No browser needed.
- **[dom]** — requires a rendered DOM to verify; browser DevTools, Playwright snapshot, or an integration test.
- **[behaviour]** — requires interaction (keyboard, focus, dialog open/close, navigation); Playwright or a manual pass.
- **[visual]** — requires the item to be rendered in a specific theme or context (`forced-colors: active`, `dir="rtl"`, zoom, non-Latin script); visual regression or manual.
- **[a11y-tool]** — covered by axe-core / Pa11y / Lighthouse accessibility rules; run the tool and read the report.
- **[runtime]** — requires real-user or synthetic runtime measurement; Lighthouse-CI, CrUX, RUM. Never assertable from source alone.

**Responsive behavior**
- **[dom]** Renders correctly at 320 CSS px wide with no horizontal scroll — SC 1.4.10 Reflow.
- **[behaviour]** Reflows without loss of content or functionality at 400% browser zoom — SC 1.4.4 Resize Text.
- **[behaviour]** Works in both portrait and landscape — SC 1.3.4 Orientation.
- **[visual]** Still readable with user-overridden line-height, letter-spacing, word-spacing — SC 1.4.12 Text Spacing.
- **[static]** Uses container queries where the component is reused at different widths.
- **[static]** Flexbox vs Grid chosen deliberately — Flex for one-dimensional, Grid for two-dimensional and cross-axis alignment (§3.15).
- **[static]** `100vh` absent from any user-visible element on mobile.

**WCAG 2.2 AA (hard requirements)**
- **[a11y-tool]** Text contrast ≥ 4.5:1 (≥ 3:1 for large text) in every supported theme — SC 1.4.3 Contrast (Minimum).
- **[a11y-tool]** UI components, state indicators, focus rings, meaningful graphics ≥ 3:1 against adjacent colors — SC 1.4.11 Non-text Contrast.
- **[behaviour]** Visible focus indicator on every interactive element, never `outline: none` without a replacement — SC 2.4.7 Focus Visible. (Source grep for `outline: none` is the first pass; visual verification confirms a replacement was added.)
- **[dom]** All interactive targets ≥ 24×24 CSS px — SC 2.5.8 Target Size (Minimum).
- **[behaviour]** Sticky/fixed elements do not obscure focused content — SC 2.4.11 Focus Not Obscured (Minimum).
- **[behaviour]** Every drag interaction has a non-drag alternative — SC 2.5.7 Dragging Movements.
- **[behaviour]** Modal dialogs trap focus and restore it on close (native `<dialog>` or equivalent).
- **[static]** Skip link present, targeting `<main>` — SC 2.4.1 Bypass Blocks.
- **[static]** Page uses landmark elements (`<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`) with `aria-label` where multiple of a kind exist.
- **[static]** Viewport meta does not block zoom — no `maximum-scale=1`, no `user-scalable=no`.
- **[behaviour]** `prefers-reduced-motion: reduce` disables non-essential motion.
- **[visual]** Information not conveyed by color alone; error/status states paired with icon or text.
- **[static]** Forms with sensitive/repeat input use exact `autocomplete` tokens; numeric fields set `inputmode`.
- **[visual]** Layout verified with `forced-colors: active` — no content lost, focus ring survives.

**Internationalization (hard requirements)**
- **[static]** All spacing / positioning uses logical properties (`margin-inline`, `padding-block`, `inset-inline-*`) — no physical-property leaks.
- **[visual]** Layout renders correctly with `dir="rtl"` on the document root.
- **[visual]** Directional icons (arrows, chevrons, back-buttons) mirror in RTL via `:dir(rtl)` or swapped SVGs.
- **[visual]** No fixed-width interactive elements tuned to English labels — survives +35% text expansion. Verify with a pseudo-localization pass or a long-string locale.
- **[static]** Document has `lang` attribute; language-switched subtrees have their own `lang`.
- **[visual]** Line-break behavior verified for at least one non-Latin script (CJK or Arabic).
- **[static]** `font-family` stack includes fallbacks for every script the site targets.

**Performance (hard requirements, at 75th percentile of mobile real-device data)**
- **[runtime]** LCP ≤ 2.5s. — Lighthouse-CI on representative pages + CrUX / RUM for ground truth.
- **[runtime]** CLS ≤ 0.1. — Lighthouse-CI + CrUX / RUM.
- **[runtime]** INP ≤ 200ms. — RUM only; INP does not synthesize cleanly in Lighthouse.
- **[static]** LCP image uses `fetchpriority="high"`, is NOT `loading="lazy"`, has explicit `width`/`height`, uses a modern format (AVIF/WebP).
- **[static]** Below-the-fold images use `loading="lazy"` and either explicit dimensions or `aspect-ratio`.
- **[static]** Fonts load with `font-display: swap` + `size-adjust`/`ascent-override`/`descent-override` to kill CLS on swap.
- **[static]** CJK (or other large-script) fonts are subsetted via `unicode-range`.
- **[static]** Off-screen heavy sections use `content-visibility: auto` + `contain-intrinsic-size`.
- **[behaviour]** Server honours `Save-Data: on` — degrades images, skips autoplay, disables polling. Verify by sending the header and diffing the response.
- **[static]** No layout-triggering animation (`width`/`top`/`margin`) in the interaction path.
- **[static]** Critical-path JS ≤ ~170 KB compressed (budget, not hard line). Bundle analyzer or Lighthouse resource summary.
- **[static]** Resource hints in place: `preconnect` to critical third-party origins, `preload` for the LCP image and critical fonts, no over-preloading.
- **[visual]** Safe-area insets honoured on edge-to-edge devices.

## 8. Out of scope

Deliberately outside this reference:

- **Native mobile adaptive design** — SwiftUI size classes, Jetpack Compose `WindowSizeClass`. These are adaptive (discrete size buckets), not responsive (fluid), and live in different ecosystems.
- **Cross-platform frameworks** — React Native, Flutter, NativeScript. Responsive-adjacent, but style/layout primitives differ enough that mapping this doc across is a separate exercise.
- **Email HTML** — deeply constrained legacy rendering; almost none of the modern CSS here applies.
- **Print stylesheets** — `@media print` with `@page`, page-break rules, and fixed-unit sizing is its own subtopic.

Responsive web design in 2026 is mature enough to stand alone as a reference. Extensions to neighbouring surfaces (native, cross-platform, email, print) belong in their own documents.
