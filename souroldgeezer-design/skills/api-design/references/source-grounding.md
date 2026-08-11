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
- Source: `extensions/python.md` and its `python/{build,review}.md` lanes.
  Handling: Python's primary ASGI, WSGI, asyncio, and serverless references are
  linked in the extension; eval cases use original synthetic Python gateway
  scenarios and do not reproduce those sources' text or examples.
- Source: `../app-design` public-skill boundary.
  Handling: local sibling-skill boundary; hosted Next.js API guidance keeps
  Route Handlers, Pages API routes, and API-like Server Actions in api-design
  while frontend route/layout/screen/component behavior delegates to app-design.
- Source: `references/procedures/surface-architecture.md` and the API reference
  surface-architecture rule.
  Handling: repo-authored HTTP contract portfolio guidance; synthetic cases
  exercise evidence-bound keep/separate/standardize/aggregate/consolidate/
  deprecate decisions without asserting traffic, latency, ownership, or runtime
  benefit from static contracts.

Mode-routing evals are original synthetic cases. They assert that factual
Extract stays core-only, explicit debt/compliance Extract adds only Review,
Build excludes Review, Review excludes Build, and Lookup remains bounded to an
anchored core rule plus at most one relevant stack lane.
