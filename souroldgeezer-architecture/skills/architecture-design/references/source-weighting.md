# Source Evidence Evaluator

Use before first-pass Extract analysis when source evidence maps to ArchiMate
element, relationship, or view choices. Start with the heaviest applicable
evidence lane; confirm with local evidence, architect intent, and semantic
validation.

Decision loop:

1. Identify the source fact.
2. List plausible ArchiMate candidates.
3. Pick the heaviest applicable evidence lane.
4. Reject semantically invalid candidates.
5. Select the narrowest useful relationship and view.
6. Label confidence.
7. Record the rejected alternative for non-obvious choices.

Do not manufacture Business, Motivation, Strategy, ownership, lifecycle, or
cloud-quality claims from code/IaC names. Use `source-backed`,
`candidate-from-source`, `architect-owned`, `weak-evidence`, or `overlay-only`
when confidence matters.

Details: `../../../docs/architecture-reference/source-weighting.md`.
