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
and the packages compared.
