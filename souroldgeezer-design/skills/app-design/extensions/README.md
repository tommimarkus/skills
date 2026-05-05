# App-Design Extensions

Per-stack packs loaded on demand by the app-design skill. The core workflow in
`../SKILL.md` is framework-neutral; extensions add stack-specific app
architecture, routing, component, state/data, rendering, browser-runtime,
responsive/accessibility, positive-signal, and carve-out guidance.

## Load Order

1. The skill detects stack signals from file types, manifests, host files,
   runtime setup, and framework-specific syntax.
2. Every matching extension is loaded.
3. Extension guidance augments the app-design reference and adds namespaced
   finding codes.
4. Extensions never override core app-design rules. A carve-out only suppresses
   a core smell when the exact stack pattern still satisfies the core rule.

## Required Sections

Each extension should cover:

- name, scope, and detection signals;
- app architecture, route/layout ownership, and rendering boundaries;
- component architecture, state/data ownership, forms, navigation, browser
  runtime behavior, and storage;
- responsive, accessibility, i18n, and performance details specific to the
  stack;
- project assimilation signals and reusable compliant primitives;
- positive signals, smell codes, and carve-outs;
- sibling-skill delegation boundaries.

Use `<prefix>.APP-*` for app-design findings and `<prefix>.POS-*` for positive
signals. Keep examples synthetic and minimal; do not copy vendor documentation
or framework sample code into an extension.

## Current Extensions

| File | Applies to | Notes |
|---|---|---|
| `blazor-wasm.md` | Blazor WebAssembly applications and components, including standalone WASM and Blazor Web App `.Client` projects | Route/layout ownership, render modes, component contracts, state containers, event callbacks, JS interop, API-client delegation, focus/navigation/forms/storage, and responsive/accessibility/i18n/performance posture |

## Adding a New Extension

1. Start from a real stack pressure case that the generic core cannot cover
   precisely.
2. Pick a short stable prefix such as `react`, `nextjs`, `vue`, or `tailwind`.
3. Write unambiguous detection signals.
4. Add only stack-specific app-design guidance; cite the core reference for
   generic responsive, accessibility, i18n, and performance rules.
5. Add extension finding codes under `<prefix>.APP-*`.
6. Add the extension to the `SKILL.md` extension table with a concrete load
   condition.
