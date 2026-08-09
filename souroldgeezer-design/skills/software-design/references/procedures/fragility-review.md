# Fragility Review

Load when Review assesses changed code for hidden preconditions or whether a
nearby change could miss a volatile design decision. Fragility review checks
whether code that works today introduces hidden assumptions or scatters one
design decision across places that a nearby future change could miss, causing
regressions or repeated refactoring. It is not style review, speculative
abstraction, analyzer enforcement, or development-method enforcement.

## Evidence

For `SD-E-6` (latent precondition), inspect indexed access, first/last,
lookups, casts, and similar partial operations in changed code. Report a finding
only when the required invariant is not proven by a fixed-shape or non-empty
type, a validated boundary, a dominating guard, or a deliberate fail-fast
contract. Tests, comments, and sample data alone do not prove safety. A
deliberate fail-fast contract is sufficient only when the caller-visible
precondition and failure are intentional and local to the boundary.

For structural fragility, run this adjacent-change probe:

1. Name the volatile decision that a nearby change would alter.
2. Name its intended owner.
3. List every site that must change together.

Multiple files alone are not a finding. Report structural fragility only for
accidental duplication, divergent ownership, or unrelated coordinated edits;
reuse the applicable coupling, ownership, boundary, or semantic `SD-*` code.
Do not prescribe an abstraction because a future change is merely imaginable.

Native analyzer, type-checker, linter, or similar results are evidence
candidates, not conclusions. Load `native-tool-evidence.md` only under the
core skill's stated condition; absence of optional tooling does not prevent a
source-based review.

## Completion Gate

Return exactly one completion state when fragility review materially applies:

| State | Use when |
|---|---|
| `pass` | Changed code has no supported fragility finding, or the relevant invariant and ownership evidence is present. |
| `warn` | Evidence supports a plausible adjacent-change or maintainability risk, but consequence or confidence does not justify blocking. |
| `block` | Changed code introduces high-confidence fragility with credible crash, corruption, partial-application, or silent-divergence consequences. |
| `not-assessed` | Necessary source or evidence scope is unavailable. Do not use for absent optional tooling. |

For every finding, state a plain-language title beside its internal `SD-*` code,
the changed location, verification layer, evidence, consequence, and smallest
coherent action. A tool finding alone is insufficient to select `warn` or
`block`.
