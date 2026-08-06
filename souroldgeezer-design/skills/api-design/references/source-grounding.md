# Source Grounding

This skill's behavioral evals are synthetic, repo-authored cases derived from
the local API design workflow and its bundled reference. They do not copy
external prompt text, code, examples, fixtures, schemas, diagrams, logos, or
screenshots.

- Source: `../../../docs/api-reference/api-design.md`.
  Handling: local bundled reference owned by this repo; eval prompts are
  original synthetic scenarios that exercise the workflow's mode selection,
  verification-layer disclosure, and extension composition.
- Source: `extensions/*.md`, `extensions/*/build.md`, and
  `extensions/*/review.md`.
  Handling: local mode-sliced extension load conditions, implementation
  patterns, and smell-code behavior; eval cases mention stack names only as
  nominative context and do not reproduce external documentation examples.
- Source: `../app-design` public-skill boundary.
  Handling: local sibling-skill boundary; hosted Next.js API guidance keeps
  Route Handlers, Pages API routes, and API-like Server Actions in api-design
  while frontend route/layout/screen/component behavior delegates to app-design.

Mode-routing evals are original synthetic cases. They assert that factual
Extract stays core-only, explicit debt/compliance Extract adds only Review,
Build excludes Review, Review excludes Build, and Lookup remains bounded to an
anchored core rule plus at most one relevant stack lane.
