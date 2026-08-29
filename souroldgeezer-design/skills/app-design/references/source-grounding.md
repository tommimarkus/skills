# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases. They do not
copy external prompts, code, screenshots, diagrams, tables, examples, or
documentation.

- Source: approved app-design replacement spec,
  `docs/superpowers/specs/2026-05-06-app-design-skill-replacement-design.md`.
  Handling: local approved design input; skill wording is original and uses the
  spec as the boundary contract for the public app-design replacement.
- Source: old responsive-design workflow, reference, Blazor extension, and eval
  files moved under this skill.
  Handling: local repo-authored migration input; responsive behavior is retained
  as a mandatory app-design layer, while standalone public invocation is
  removed.
- Source: `api-design` public-skill generalization precedent in this plugin.
  Handling: local structural precedent; app-design follows the same pattern of
  broad public core plus stack-specific extensions and on-demand references.
- Source: `software-design` support-boundary decision in the approved spec.
  Handling: local boundary input; software-design supports app-design from the
  engineering side for decomposition, dependency direction, state-machine shape,
  adapter boundaries, and coupling risks without owning frontend app decisions.
- Source: React official docs, including `react.dev/reference/react`,
  `react.dev/reference/react/hooks`,
  `react.dev/reference/react/useEffect`,
  `react.dev/reference/react/useSyncExternalStore`,
  `react.dev/reference/rules/components-and-hooks-must-be-pure`,
  `react.dev/reference/rules/rules-of-hooks`,
  `react.dev/reference/react-dom/client/hydrateRoot`, and
  `react.dev/reference/react/Suspense`.
  Handling: React facts are linked as source anchors; extension wording is
  original and limited to app-design implications for components, Hooks,
  state/data ownership, rendering, hydration, browser effects, forms, and
  responsive/accessibility/performance posture.
- Source: Vite official docs, including `vite.dev/guide`,
  `vite.dev/guide/build`, `vite.dev/guide/assets`,
  `vite.dev/guide/env-and-mode`, and `vite.dev/guide/ssr`.
  Handling: Vite facts are linked as source anchors; extension wording is
  original and limited to app-design implications for dev/build/preview
  distinctions, entry topology, client-exposed environment values, assets and
  chunks, runtime boundaries, SSR, and stale-deployment recovery.
- Source: Next.js official docs, including `nextjs.org/docs`,
  `nextjs.org/docs/app`,
  `nextjs.org/docs/app/getting-started/server-and-client-components`,
  `nextjs.org/docs/app/guides/caching`,
  `nextjs.org/docs/app/api-reference/file-conventions/route-segment-config`,
  `nextjs.org/docs/app/api-reference/components`, and
  `nextjs.org/docs/app/guides/forms`.
  Handling: Next.js facts are linked as source anchors; extension wording is
  original and limited to app-design implications for routing, layouts,
  Server/Client Component boundaries, cache/freshness behavior, navigation,
  forms, metadata/assets, and sibling-skill delegation.
- Source: ASP.NET Core Blazor official docs, including
  `learn.microsoft.com/aspnet/core/blazor`,
  `learn.microsoft.com/aspnet/core/blazor/components/render-modes`,
  `learn.microsoft.com/aspnet/core/blazor/globalization-localization`,
  `learn.microsoft.com/aspnet/core/blazor/performance/app-download-size`, and
  `learn.microsoft.com/aspnet/core/blazor/javascript-interoperability`.
  Handling: Blazor facts are linked as source anchors; extension wording is
  original and limited to app-design implications for render modes, component
  contracts, state/JS interop, forms/navigation, globalization/localization, and
  responsive/accessibility/i18n/performance posture.
- Source: W3C WAI Web Accessibility Tutorials forms grouping guidance,
  `https://www.w3.org/WAI/tutorials/forms/grouping/`; GOV.UK Service Manual
  form-structure guidance, `https://www.gov.uk/service-manual/design/form-structure`;
  and Nielsen Norman Group's visual-hierarchy,
  `https://www.nngroup.com/articles/visual-hierarchy-ux-definition/`, and
  progressive-disclosure, `https://www.nngroup.com/articles/progressive-disclosure/`,
  articles.
  Handling: linked as source anchors for screen composition (§3.15); wording is
  original and limited to app-design implications for task-ordered field/section
  grouping, width-as-length signaling, single-primary-action emphasis, and
  progressive disclosure of advanced options.
