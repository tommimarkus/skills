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
