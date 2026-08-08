# Drift Detection

Use when Review compares a package with current code, IaC, UI, API, or workflow
source.

## Checks

Classify each difference before assigning an `ARCH-*` code:

- source added or removed: `ARCH-X-1` when architecture-relevant source is not
  modeled or modeled source disappeared.
- source evidence changed: `ARCH-X-3` when labels or source facts changed but
  the architecture claim may still be intentional.
- package claim no longer has evidence: `ARCH-X-2` when lifted content has no
  current source or architect-owned basis.
- package claim may be architect intent: verify before treating it as drift;
  label as `architect-owned` or `candidate-from-source`.

Source implies omitted or reversed relationship: `ARCH-X-4`.

## Freshness And Revision Checks

Three read-only Dediren tools complement the source-drift `ARCH-X-*` checks above
(all defined in architecture §9):

- **Artifact freshness — the gate (`dediren_verify {workspaceRoot, source, artifacts}`).** The
  machine check that a package's generated output is still a pure function of its
  source. A `stale` rendered SVG or gallery is `ARCH-R-2`; a `stale` OEF/XMI export
  is `ARCH-E-4`. An `unstamped` artifact — e.g. committed evidence predating
  provenance stamping — is disclosable, not a finding.
- **Workspace freshness index (`dediren_status {workspaceRoot, dir?}`).** A read-only index of the
  models and artifacts under a directory; use it to spot which packages may have
  drifted before running `dediren_verify`. Non-gating — `dediren_verify` is the
  gate, `dediren_status` only points at it.
- **Model-revision comparison (`dediren_diff {workspaceRoot, old, new}`).** Compares two revisions
  of one package's *own* source model (added / removed / changed nodes,
  relationships, and views, with field-level changes). It surfaces what changed
  between revisions and is complementary to — and distinct from — the source-drift
  classification above; it raises no `ARCH-X-*` on its own. Use it to explain a
  revision, not to assign a drift code.

## Cross-Package Consistency

Use when Review scope spans more than one package under `docs/architecture/`,
includes the landscape package, or edits an element shared with a sibling
package (`architecture.md` §15).

1. Enumerate sibling packages (`docs/architecture/*.dediren/`) and index
   elements by `properties.identity`, then by exact element id; an explicit
   `identity` value wins over id equality.
2. Classify:
   - linked elements (shared `identity` or id) disagreeing on ArchiMate type,
     or carrying contradictory labels or evidence claims: `ARCH-X-5`
     cross-package identity conflict. Different relationship or property
     subsets are not conflicts.
   - likely-same elements — matching type and label across packages — with no
     shared id or `identity` key: `ARCH-X-6` fragmentation candidate.
   - an element shared by two or more feature packages missing from an
     existing landscape package, or a landscape element no feature package or
     architect intent backs: `ARCH-X-6` rollup gap.
3. Recommend per finding: link the identities, reconcile the conflicting
   claim, or update the landscape. Never bulk-rewrite package ids
   mechanically; id churn breaks render metadata and history.

Evidence names the package set and the shared identity or id.

## Scope Limits

Business-other, Motivation, Strategy, portfolio, cloud-quality, and Physical
content are architect-owned unless explicit source evidence exists; report
unverified intent instead of deleting it.

## Output

Report added/removed/changed/unverified counts and likely reconciliation:
update package, update source, or confirm architect-owned intent. When the
cross-package leg ran, also report conflict and fragmentation-candidate counts
and the packages compared. When the freshness checks ran, report the
`dediren_verify` stale / unstamped counts (stale mapped to `ARCH-R-2` /
`ARCH-E-4`, unstamped disclosed) and note any `dediren_diff` revision comparison
used.
