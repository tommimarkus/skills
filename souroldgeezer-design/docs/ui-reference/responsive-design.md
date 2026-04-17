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

## 4. Primitives cheatsheet

Each primitive gets one-line purpose + syntax + key pitfall.

- **`clamp(min, preferred, max)`** — fluid sizing with bounds. `font-size: clamp(1rem, 2.5vw, 2rem)` — MDN `clamp()`. Pitfall: the `preferred` expression should use `vw`/`vi`/`cqi` with a `rem` floor (pure `vw` ignores user root size and violates SC 1.4.4).
- **`min()` / `max()`** — constraint logic without media queries. `width: min(100%, 40rem)` caps a fluid element at a readable width. Pitfall: composes with `clamp()` in subtle ways; test before deploying.
- **`@container` + `cqi` / `cqb` / `cqw` / `cqh` / `cqmin` / `cqmax`** — component-scoped layout — MDN Container Queries. `cqi` = 1% of the query container's inline size. Pitfall: requires an ancestor with `container-type: inline-size` (or `size`); without it, the query is ignored and container units fall back to small-viewport units.
- **`dvh` / `svh` / `lvh`** — dynamic / small / large viewport heights — MDN length units. `100dvh` resizes as the URL bar shows/hides; `100svh` is stable at the smallest possible viewport; `100lvh` is stable at the largest. Pitfall: `dvh` causes layout shift during scroll; prefer `svh` for stable layouts.
- **`@media (hover: hover)` / `@media (pointer: coarse)`** — input-modality detection. Gate hover enhancements behind `(hover: hover)`; expand tap targets under `(pointer: coarse)`. Pitfall: `any-hover`/`any-pointer` match if *any* connected input has the capability — usually not what you want.
- **`prefers-reduced-motion`**, **`prefers-color-scheme`**, **`prefers-contrast`**, **`forced-colors`** — user-preference media queries. Honour them. Pitfall: `forced-colors: active` flattens custom colors — don't rely on color as the only information channel.
- **Logical properties** — `margin-inline`, `padding-block`, `inset-inline-start`, `border-inline-end`, `text-align: start` — MDN CSS Logical Properties. Pitfall: mixing logical and physical on the same element produces unpredictable layouts — pick a lane per component.
- **`writing-mode`, `direction`, `unicode-bidi`** — script-direction primitives. `writing-mode: vertical-rl` for traditional CJK vertical text; `dir="rtl"` on document or subtree for Arabic/Hebrew.
- **`:dir(rtl)` / `:dir(ltr)`** — direction-aware styling without JS. Flip a chevron in RTL: `:dir(rtl) .chevron { transform: scaleX(-1); }`.
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

### 5.6 Data-heavy content (wide tables)
Tables and wide content use a horizontal scroll container with an uncropped focus ring. Vertical-scroll content must reflow under 1280 CSS px tall; horizontal-scroll content under 320 CSS px wide (SC 1.4.10).

```css
.table-wrap {
  overflow-inline: auto;
  scrollbar-gutter: stable;
  padding-block-end: 0.5rem;
}
.table-wrap table { border-collapse: collapse; inline-size: max-content; min-inline-size: 100%; }
.table-wrap :focus-visible { outline-offset: 2px; }
```

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
