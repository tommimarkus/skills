# Architecture Design Finding Catalog

Compact lookup table for finding codes emitted by the skill. The rubric lives
in [../../../docs/architecture-reference/architecture.md](../../../docs/architecture-reference/architecture.md).
Findings cite codes from this catalog and keep the action concrete.

## Rules

1. Use one code and one severity per finding: `block`, `warn`, or `info`.
2. Cite package source, view id, node id, relationship id, command output, SVG
   artifact, or supplied downstream evidence.
3. Prefer the narrowest code. Use the broader quality codes only when the
   problem is audience/readiness rather than structural correctness.

## Model Findings

| Code | Default | Meaning |
|---|---:|---|
| `ARCH-M-1` | block | Relationship type invalid for the source/target ArchiMate element types. |
| `ARCH-M-2` | block | Source-grounded element points to nonexistent or stale source evidence. |
| `ARCH-M-3` | warn | Element type, label, or layer assignment contradicts its documented architecture role. |
| `ARCH-M-4` | warn | Architect-owned content is presented as extracted fact without an authority marker. |

## View Findings

| Code | Default | Meaning |
|---|---:|---|
| `ARCH-V-1` | block | View listed in `project.json` cannot be projected by its configured plugin/target. |
| `ARCH-V-2` | warn | View omits the primary relationship needed to answer its architecture question. |
| `ARCH-V-3` | warn | Viewpoint or diagram kind does not match the audience concern. |
| `ARCH-V-4` | info | Supported diagram kind is absent and should be reported as missing, not stubbed. |

## Layout Findings

| Code | Default | Meaning |
|---|---:|---|
| `ARCH-L-1` | block | Layout command fails or returns an error envelope. |
| `ARCH-L-2` | warn | Layout validation reports overlap, connector-through-node, invalid route, or group-boundary warnings. |
| `ARCH-L-3` | warn | Layout is technically valid but too dense, tiny, or poorly framed for review. |
| `ARCH-L-4` | info | Layout policy weakens a requested grouping, direction, or route preference. |

## Render Findings

| Code | Default | Meaning |
|---|---:|---|
| `ARCH-R-1` | block | SVG render command fails or returns an error envelope. |
| `ARCH-R-2` | block | SVG is blank, misses expected `data-dediren-node-id` / `data-dediren-edge-id` markers, or has an incoherent `viewBox`. |
| `ARCH-R-3` | warn | SVG renders but labels, icons, or relationship markers obscure the architecture message. |
| `ARCH-R-4` | info | Render policy is usable but visually inconsistent with the intended audience. |

## Extraction And Drift Findings

| Code | Default | Meaning |
|---|---:|---|
| `ARCH-X-1` | warn | Extracted model no longer matches source, IaC, UI routes, APIs, or workflows. |
| `ARCH-X-2` | warn | Lifted Business Process/Event/Interaction/API/UI route/resource/workflow lacks source evidence. |
| `ARCH-X-3` | info | Source label changed while the architecture label may be intentionally human-friendly. |
| `ARCH-X-4` | warn | Source implies a relationship that the package omits or reverses. |

## Export Findings

| Code | Default | Meaning |
|---|---:|---|
| `ARCH-E-1` | block | OEF export fails or returns an error envelope. |
| `ARCH-E-2` | warn | Exported OEF fails downstream import, schema, or conformant-tool validation evidence supplied by the user. |
| `ARCH-E-3` | info | OEF export was requested but no export policy exists yet. |
| `ARCH-E-4` | warn | Export policy names a view, model id, or viewpoint that no longer matches `project.json`. |

## Quality Findings

| Code | Default | Meaning |
|---|---:|---|
| `ARCH-Q-1` | block | Package is not review-ready because a blocking finding remains. |
| `ARCH-Q-2` | warn | View is too dense, audience-incoherent, or unclear about its architecture question. |
| `ARCH-Q-3` | warn | Package claims a quality level not supported by the recorded dediren evidence. |
| `ARCH-Q-4` | info | Diagram-kind coverage is incomplete but honestly disclosed. |

## Severity Guidance

- Use `block` for invalid source, failed projection/layout/render/export, or
  claims that cannot be supported by evidence.
- Use `warn` for review-quality defects, source drift, incomplete realization,
  and optional export problems.
- Use `info` for disclosed gaps, cosmetic issues, and intentional architect
  choices that should be revisited later.
