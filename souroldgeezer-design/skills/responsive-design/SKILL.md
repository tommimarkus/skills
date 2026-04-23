---
name: responsive-design
description: Use when building, reviewing, or looking up modern responsive web UI — components, pages, or features in HTML/CSS/JS and Blazor WASM. Applies the bundled reference at souroldgeezer-design/docs/ui-reference/responsive-design.md, enforcing WCAG 2.2 AA, internationalization (LTR + RTL + text expansion), and Core Web Vitals as hard baselines. Supports build, review, and lookup modes with a matching subagent and Blazor-WASM extension.
---

# Responsive Design

## Overview

Help Claude produce and review responsive web UI that is correct by construction across viewport, container, input modality, user preference, language/direction, capability, and network. The central problem, from §1 of the reference:

> Presence vs. efficacy — a site rendering at 375×667 is not the same as a site that works for the Arabic-speaking user on a 2019 Android with Save-Data on, or the low-vision user at 400% zoom, or the keyboard user stuck behind a sticky header.

**The reference is [../../docs/ui-reference/responsive-design.md](../../docs/ui-reference/responsive-design.md)** (bundled with the plugin). This skill is the *workflow* for applying it. Generated code embodies the reference's defaults; review output cites reference sections and WCAG SCs by reference; the skill never duplicates reference prose.

## Non-goals

- **General code quality** → out of scope; produce working responsive code, don't lint surrounding logic.
- **Verification of runtime metrics** (LCP/CLS/INP) → static signals only. Real CWV numbers need RUM + CrUX + Lighthouse-CI; surface this honestly.
- **Native mobile adaptive design, cross-platform frameworks, email HTML, print stylesheets** — reference §8 out-of-scope; decline and redirect.
- **Design-system creation from scratch** — use existing tokens; don't invent a theme unless the user asks.

## Modes

### Build mode (primary)

**Use for:** creating a new component, page, section, or full feature.

**Triggers:** "build a …", "design a …", "create a responsive …", "make me a …", "how should I structure …", "implement this UI".

### Review mode

**Use for:** reviewing existing UI code against the reference checklist.

**Triggers:** "review this component", "is this responsive", "audit this UI", "does this meet WCAG", "check this against the checklist", "responsive review".

### Lookup mode

**Use for:** a specific, narrow question — which unit, which media query, which primitive.

**Triggers:** "which unit for X", "how do I do Y", "what is the default for Z", "should I use @container or @media here".

**Default:** If the request is ambiguous, ask the user which mode they want.

## Extensions

The core workflow is framework-neutral. Extensions are per-stack packs loaded on demand:

| Extension | Applies to | Loaded when target matches |
|---|---|---|
| `extensions/blazor-wasm.md` | Blazor WebAssembly components — both **standalone** (`blazorwasm` template) and **Blazor Web App `.Client` projects** | `*.razor` / `*.razor.css` / `*.razor.cs` files, OR `.csproj` with `Sdk="Microsoft.NET.Sdk.BlazorWebAssembly"` (standalone), OR a server `.csproj` using `AddInteractiveWebAssemblyComponents()` / `AddInteractiveWebAssemblyRenderMode()` with a sibling `.Client` project (Blazor Web App), OR `wwwroot/index.html` referencing `blazor.webassembly.js` / `blazor.web.js`, OR `@rendermode` directives in `.razor` files |

Multiple extensions may load. Unknown stacks proceed with only the core reference. See `extensions/README.md` for adding a new extension.

Extensions **never override** core rules. They add stack-specific primitives, patterns, and smells (namespaced `<ext>.HC-N` / `<ext>.POS-N`), or carve out false positives for idiomatic stack patterns. Carve-outs win only for the exact pattern described.

## Pre-flight (build & review)

Before writing or reviewing code, confirm the following. If the user hasn't supplied them, ask — don't invent answers:

1. **Locale scope.** LTR only? LTR + RTL? Which scripts (Latin, CJK, Arabic, Hebrew)? Assume LTR + RTL + text expansion unless told otherwise.
2. **Theme scope.** Light only? Light + dark? `forced-colors`? Default: light + dark + forced-colors resilient.
3. **Framework / stack.** Plain HTML/CSS, or a framework? Detect Blazor via file globs; otherwise ask.
4. **Target viewport floor.** Default: 320 CSS px (SC 1.4.10 Reflow). Do not accept a higher floor without a written reason.
5. **Performance posture.** Is there a CWV target or a team SLO? Default: web.dev Core Web Vitals at mobile p75.

If any answer changes a decision's default (e.g., desktop-first product dashboard → §3.5 default flips), state the deviation explicitly.

## Project assimilation (before build & review)

**Direction is one-way: the project is assimilated to the reference, not the reference to the project.** The reference's WCAG 2.2 AA, i18n, and Core Web Vitals baselines are non-negotiable; its decision defaults (§3) are the target state. Assimilation means discovering what the project ships so output (a) reuses compliant infrastructure instead of duplicating it, and (b) surfaces non-compliant infrastructure as legacy debt rather than silently extending it.

Before emitting code or opening a review on an existing project, run the discovery pass below. Keep detection lightweight — canonical locations only. If nothing found, assume greenfield and emit the §4.5 boilerplate.

### Framework-agnostic discovery

Do this pass every time, regardless of stack:

1. **Tokens** — grep `:root` + `--<name>:` in `*.css` / `*.scss` / `index.css` / `app.css` / `global.css` / `theme.css` / `tokens.css`. Record color variables, spacing scale, type scale, theme variants.
2. **Breakpoints** — grep `@media (min-width:` and `@media (max-width:` across the project. List distinct thresholds and their names. More than 4 un-aligned thresholds → flag as a project-level §3.4 deviation.
3. **Host boilerplate** — read `index.html` / root layout. Check for §4.5 elements: viewport meta (`viewport-fit=cover`, `interactive-widget=resizes-content`), `color-scheme` meta, `theme-color` per scheme, resource hints, preloaded fonts.
4. **Landmarks + skip** — grep for `<main`, `<nav`, `<aside`, `<footer`, `.skip-link`, `role="search"`, `<search`. Record presence/absence.
5. **Modern primitives already adopted** — grep `<dialog`, `popover=`, `aria-live`, `@container`, `light-dark(`, `dvh`, `svh`, `inset-inline-`, `margin-inline`. Presence tells you the project's baseline is modern; absence tells you migration is part of the work.
6. **Manifest signals only** — read `package.json` / `.csproj` / equivalent to *identify* the framework, UI library, router, image component, icon set. Do **not** parse stack-specific config files here — that's the extension's job.

### Stack-specific discovery

Delegated to the matching extension. Each extension covers its own stack's token config and component library catalog — `tailwind.config.*`, Sass `_tokens.scss`, CSS-in-JS configs (`stitches.config.*`, `panda.config.*`, `vanilla-extract/*.css.ts`), Blazor `MainLayout.razor` + component libraries (MudBlazor, FluentUI Blazor, Radzen, Blazorise), React component libraries (Radix, Headless UI, shadcn, MUI, Chakra, Mantine), framework image/head/router components. See the loaded extension's **Project assimilation** section.

### Mapping existing infrastructure to reference rules

Reuse is conditional on **substantive compliance**, not presence. For each discovered asset, judge it against the reference before deciding whether to reuse or replace:

| Discovered in project | Reuse when | Replace / migrate when |
|---|---|---|
| Spacing / type-scale tokens (§3.3) | Tokens are in `rem`, respect user root size, and fluid where appropriate | Hard-coded `px` on user-scalable content, or a rigid stepped scale with no fluid option |
| Breakpoint names (§3.4) | Derived from content (e.g. Tailwind `sm/md/lg`, `--bp-narrow`, role-named) — just adopt the names | Device-named (`--bp-ipad`, `--bp-iphone`), more than 4 un-aligned thresholds, or desktop-first `max-width` stacks |
| Theme system (§3.17) | Existing `prefers-color-scheme` block + token-swap passes contrast in both themes, respects `forced-colors` | Light-mode only, dark-mode regressions, or palette fails SC 1.4.3 / 1.4.11 in either theme |
| Dialog primitive (§5.8) | UI library's dialog traps focus, handles `Esc`, restores focus, uses top-layer (native `<dialog>` or equivalent) | Div-plus-JS "modal", no focus trap, no `inert` on the page behind |
| Popover / tooltip primitive (§5.11) | Light-dismissed, top-layer, `aria-describedby` wired, keyboard-operable | Hover-only, no `Esc`, no focus return, no screen-reader association |
| Responsive image component (§3.11) | Emits `srcset` + `sizes` + explicit dimensions + `fetchpriority` on LCP | Plain `<img src>` wrappers or one-resolution raster |
| Layout shell (landmarks, skip link, focus restore) | `<main id tabindex="-1">` + skip link + `LocationChanged`-driven focus | Div-soup root, no skip link, focus left on trigger after navigation |

**Name adoption is always fine.** If the project calls it `--space-md` and the reference example calls it `--space-m`, use `--space-md` — the rule is the unit and scale, not the spelling.

**Substantive non-compliance is never fine.** If the project's tokens are `px`-based on user-scalable content, or the breakpoints are device-named, or the modal has no focus trap, reuse is not an option: the rule is broken, and reuse propagates the break.

### Conflict handling

When the project's existing approach violates a reference rule:

1. **Flag it** — cite the reference rule (§n.m and SC number), the file/line evidence, and classify it as *legacy debt* (pre-existing) or *would-be-new-code* (about to be added or reviewed).
2. **Pick a path** based on task scope and which class the conflict is in:
   - **New code must comply.** Emit reference-compliant output for anything the current task is adding. There is no "match the broken pattern" option for new code.
   - **Legacy debt: scope-dependent.**
     - If the task explicitly includes migration, fix in place and show the diff.
     - If the task does not include migration, leave the legacy untouched and add a `Legacy debt` entry to the footer naming file/line + the violated rule. Do not extend the legacy pattern into new files.
     - If the legacy is load-bearing for the task (e.g. the new component sits inside a desktop-first parent), halt and ask the user which scope to take.
3. **Never silently propagate a violation.** If existing tokens violate SC 1.4.3, generating new code that uses them quietly is worse than flagging them loudly. Output a warning block; let the user decide.

### Footer additions

Both build-mode and review-mode footers gain a `Project assimilation:` block listing: compliant infrastructure reused, non-compliant infrastructure flagged as legacy debt (with the violated rule cited), and any migration the task performed. Example:

```
Project assimilation:
  Tokens:        --color-*, --space-*, --step-* (tokens.css) — compliant, reused
  Breakpoints:   sm=30em, md=48em, lg=64em (Tailwind theme.screens) — compliant, adopted
  UI library:    shadcn/ui (Radix under) — Dialog, Popover compliant, reused; Skeleton generated fresh
  Boilerplate:   §4.5 present in index.html
  Legacy debt (not migrated in this task):
    - desktop-first cascade in legacy.css — violates §3.5 — 6 occurrences
    - bare px font-sizes in old-styles.css — violates SC 1.4.4 — 12 occurrences
  Migrations performed:
    - components/Modal.tsx: replaced div-based modal with <Dialog> from shadcn — fixes §5.8 / SC 2.4.11
```

The legacy-debt list is the record of what the project violates; it is not a list of "matched conventions." New code in the same task is always reference-compliant regardless of what the legacy looks like.

## Build mode workflow

0. **Dispatch.** Confirm build mode. Run the pre-flight above. Detect stack; announce which extensions load.

1. **Principles scan.** Read reference [§2 Principles](../../docs/ui-reference/responsive-design.md#2-principles). The skill's output must not violate any principle silently — violations require an explicit, justified deviation in a comment.

2. **Decision defaults.** For each layout / interaction choice the component needs, pull the corresponding default from reference §3:
   - Sizing → §3.1 fluid, §3.3 unit selection, §3.10 width + text expansion.
   - Query scope → §3.2 viewport vs container.
   - Breakpoints → §3.4 content-derived.
   - Cascade → §3.5 mobile-first.
   - Interaction → §3.6 touch/hover, §3.8 sticky + focus, §3.16 focus management.
   - Direction → §3.9 logical properties only in new code.
   - Loading → §3.11 image, §3.12 font.
   - Network → §3.13.
   - Motion → §3.14.
   - Layout primitive → §3.15 Flexbox vs Grid.
   - Colour → §3.17.

3. **Start from the boilerplate.** If the output is a full page or a new project, open with §4.5 Baseline boilerplate. If it's a snippet that will drop into an existing page, skip the boilerplate but assume its behaviour.

4. **Compose with primitives (§4) and patterns (§5).** Pick the closest §5 pattern as the structural template — §5.1 responsive nav, §5.2 container-aware card grid, §5.3 fluid type + spacing scale, §5.4 hero with safe-area + dvh, §5.5 form layout with `autocomplete`/`inputmode`/`enterkeyhint` + `aria-live`, §5.6 wide tables, §5.7 carousel/slider, §5.8 `<dialog>` modal, §5.9 skeleton + empty state, §5.10 skip link + landmarks, §5.11 `popover` tooltip (with CSS Anchor Positioning), §5.12 search-as-you-type (with `<search>` element, debounce, `AbortController`, `aria-live` results region). Cite and adapt; do not reinvent.

5. **Apply the extension.** If Blazor-WASM loaded, layer its additions on top. Distinguish hosting model: standalone Blazor WebAssembly (`Microsoft.NET.Sdk.BlazorWebAssembly`) has no `@rendermode` — every component runs on the client after WASM boot; Blazor Web App `.Client` projects do use `@rendermode` with `InteractiveAuto` / `InteractiveWebAssembly`. Common regardless of hosting: component-isolated CSS (logical properties in `*.razor.css`), `ElementReference.FocusAsync()` after `NavigationManager.LocationChanged`, JS-interop modules for `matchMedia` / `visualViewport` / Web Vitals, native `<dialog>` via a JS helper module (not `showModal.call`), `LazyAssemblyLoader.LoadAssembliesAsync` with `.wasm` Webcil packaging, and the extension's POS signals.

6. **Self-check against §7 before declaring done.** Each checklist item carries a verification-layer tag (`[static]`, `[dom]`, `[behaviour]`, `[visual]`, `[a11y-tool]`, `[runtime]`). Walk the four buckets — Responsive behaviour, WCAG 2.2 AA, Internationalization, Performance — and:
   - `[static]` items: verify against the code you wrote; pass/fail with confidence.
   - `[dom]` / `[behaviour]` / `[visual]` items: verify the source-level preconditions are right (attributes present, structure correct, properties logical), then mark as "source-aligned; final verification requires a browser at <condition>" (400% zoom, `dir="rtl"`, `forced-colors: active`, etc.).
   - `[a11y-tool]` items (contrast, non-text contrast): state the expected pass and point at axe-core / Pa11y / Lighthouse to confirm.
   - `[runtime]` items (LCP, CLS, INP): **never** claim a pass from static analysis; report as "not statically verifiable — run Lighthouse-CI; use CrUX / RUM for ground truth."
   If any `[static]` item fails, fix it and re-check.

7. **Emit footer disclosure.**

## Review mode workflow

0. **Dispatch.** Confirm review mode. Run pre-flight. Detect stack; announce extensions.

1. **Structural scan.** Read the target file(s). Identify whether you're reviewing a component, a page, or a full feature.

2. **Walk §7 checklist bucket by bucket.** For each item, inspect the code and record: pass / fail / not-applicable / not-statically-verifiable. Failures become findings.

3. **Per-finding format.** Match the devsecops-audit style:

   ```
   [<code>] <file>:<line>
     bucket:   responsive | wcag-2.2-aa | i18n | performance
     sc:       <SC ref when applicable>
     severity: block | warn | info
     evidence: <quoted snippet or grep match>
     action:   <suggested fix template>
     ref:      responsive-design.md §<n.m>
   ```

   Codes are drawn from the extensions (`blazor.HC-1`, etc.) and from generic responsive-design labels (`RD-*` when a finding matches a specific named gotcha in reference §6). Core findings without a code cite reference section + SC.

4. **Performance is layer-capped.** Static signals only — attribute presence (`fetchpriority`, `loading`, `decoding`, explicit dimensions), font-loading descriptors, unicode-range subsetting, `content-visibility`, resource hints. **Never assert LCP/CLS/INP numbers without RUM.** Flag this in the footer.

5. **Rollup.** After per-finding output, one paragraph per bucket summarising severity counts and the top fix.

6. **Emit footer disclosure.**

## Lookup mode workflow

0. **Dispatch.** Confirm lookup.

1. **Locate.** Grep reference for the concept (unit, primitive, pattern, SC number). Load only the matched section plus its immediate context.

2. **Answer concisely.** One or two sentences, citing the reference section. Include the default rule if it's a §3 decision.

3. **Footer disclosure** (single line in lookup mode).

## Output format

### Build mode

```
<code blocks — HTML / CSS / JS / Razor as applicable>

Self-check:
  Responsive behaviour:  <n>/<n>  [static verified]
                         <n> item(s) need browser ([dom] | [behaviour] | [visual])
  WCAG 2.2 AA:           <n>/<n>  [static verified]
                         <n> item(s) need axe-core / Pa11y / Lighthouse
                         <n> item(s) need browser (focus, dialog, reduced-motion)
  Internationalization:  <n>/<n>  [static verified]
                         <n> item(s) need dir="rtl" / pseudo-localization / non-Latin pass
  Performance:           <n>/<n>  [static verified]
                         <n> item(s) require Lighthouse-CI / CrUX / RUM (LCP, CLS, INP)
Deviations from defaults (if any): <list with reason>
```

### Review mode

Per-finding block for each failure, then rollup. All findings cite reference section + SC where applicable. Each finding includes a `layer:` field so the reader knows how to confirm: `static` (grep / lint / source inspection), `dom` (DevTools, Playwright snapshot), `behaviour` (keyboard / focus / modal / navigation interaction), `visual` (RTL / theme / zoom / non-Latin script), `a11y-tool` (axe / Pa11y / Lighthouse), `runtime` (RUM / CrUX / Lighthouse-CI). Only `static` findings are definitively pass/fail from the review alone; the rest are "source-aligned, verification deferred to <layer>".

### Lookup mode

Two to four lines of prose + one footer line.

### Footer (all modes)

```
Mode: build | review | lookup
Extensions loaded: blazor-wasm | (none)
Reference: souroldgeezer-design/docs/ui-reference/responsive-design.md
Self-check: pass | <n failures> | n/a
Runtime-verified metrics: none — use Lighthouse-CI / CrUX for LCP, CLS, INP
```

## Red flags — stop and re-run

Output contains any of the following? Stop; fix before delivering:

- Physical properties in new code — `margin-left`, `margin-right`, `padding-top`, `padding-bottom`, `top:`, `right:`, `bottom:`, `left:` (for positioning), `text-align: left`, `text-align: right`, `float: left`, `float: right`. Replace with logical equivalents per §3.9.
- Bare `vh` on any user-visible mobile element. Use `dvh`/`svh`/`lvh` per §3.7.
- `<img>` without `width`/`height` attributes, or without `srcset`/`sizes` / `<picture>` for content images. Fix per §3.11.
- LCP image with `loading="lazy"` or missing `fetchpriority="high"`. Fix per §3.11.
- `outline: none` on a focusable element without a `:focus-visible` replacement. Fix per §3.16, SC 2.4.7.
- `:hover` styling not gated behind `@media (hover: hover)`. Fix per §3.6.
- Motion/transition/animation without a `@media (prefers-reduced-motion: reduce)` guard. Fix per §3.14.
- Fixed-width button / chip / tab sized to an English label. Fix per §3.10.
- Custom div-based modal. Replace with `<dialog>` + `showModal()` per §5.8.
- No `color-scheme` on `<html>` on a page-level output. Fix per §3.17 and §4.5 boilerplate.
- Viewport meta with `maximum-scale=1` or `user-scalable=no`. Fix per §6.
- `@media (max-width: …)` as the *first* query in a new stylesheet. Desktop-first is a smell unless the product is genuinely desktop-first and stated.
- Claiming "LCP/CLS/INP pass" from a static review. Fix: restate as "static signals aligned; runtime metrics require RUM."
- Using a non-Baseline primitive as the only path — `scheduler.yield()`, `@view-transition` / `document.startViewTransition`, CSS Anchor Positioning (`position-area`, `position-try-fallbacks`, `anchor-name`, `position-anchor`) — without a feature-detection fallback. Fix: wrap in `@supports (position-area: block-end)` / `if ("startViewTransition" in document)` / `"yield" in scheduler` and provide a working fallback.
- Custom div + hover tooltip. Replace with `popover` attribute (use `popover="hint"` for tooltips) per §5.11; tooltips must respect `Esc` / light-dismiss and carry `aria-describedby` on the trigger.
- Live region (`aria-live`) created at the moment of update. The region must exist at page load; updates work by setting `textContent`, not by inserting the region into the DOM on demand. Fix per reference §6.

## Complementary skills

- `devsecops-audit` (plugin `souroldgeezer-audit`) — CSP, CORS, cookie attributes, and supply-chain concerns that surface in browser-facing code live there.
- `test-quality-audit` (plugin `souroldgeezer-audit`) — if asked to write tests that verify responsive/a11y behaviour, E2E sub-lane A covers the test-quality rules; this skill does not author E2E tests.
- `serverless-api-design` (same plugin `souroldgeezer-design`) — if the UI consumes a serverless HTTP API, that skill enforces the API contract (OpenAPI 3.1, RFC 9457 problem+json, RFC 9110 ETag), security (Entra ID / managed identities / Key Vault / data-plane RBAC), reliability (idempotency, 429 + `Retry-After`), and observability (structured logs, W3C `traceparent`). The two skills compose; neither duplicates the other.

## Honest limits

- **Runtime Core Web Vitals (LCP, CLS, INP) cannot be asserted from static analysis.** Static signals (attribute presence, font-loading descriptors, resource hints, no layout-triggering animation) are necessary but not sufficient. Point at Lighthouse-CI and CrUX / RUM.
- **Verification layers `[dom]` / `[behaviour]` / `[visual]` / `[a11y-tool]` / `[runtime]` are deferred from the skill itself** to a browser, an accessibility tool, or a RUM pipeline. The skill reports "source-aligned; final verification requires <layer>" rather than claiming unverified passes.
- **`forced-colors: active` rendering, RTL rendering, and CJK line-breaking need live visual verification**; this skill's review step flags *likely* failures, not confirmed ones.
- **`prefers-reduced-data` is experimental and not yet UA-implemented** — the reference's treatment is forward-compatible only. `Save-Data` HTTP header is the current reliable signal; server-side branching is required to act on it.
- **Primitive availability is not uniform.** The reference covers features with different Baseline status:
  - Baseline 2024: `light-dark()` (May), `text-wrap: balance/pretty` (March), `:has()` broadly shipped.
  - Baseline 2025: `overflow-inline` (September).
  - Baseline 2026: CSS Anchor Positioning (`position-area`, `position-try-fallbacks`, `anchor-name`, `position-anchor`) — January 2026.
  - **Limited availability / not yet Baseline:** `scheduler.yield()`, View Transitions (`@view-transition`, `document.startViewTransition`, `view-transition-name`), `@media (prefers-reduced-data: reduce)`, `navigator.connection.effectiveType`.
  Non-Baseline primitives must be feature-detected with a fallback; do not ship them as the only path on public-facing code.
- In older browsers that predate `@container`, `dvh`, `:has()`, `light-dark()`, logical properties, or `<dialog>`, the reference's baseline assumptions break — this skill declines to target those browsers without an explicit user directive.

Review-mode reports include the honest-limits line in the footer.
