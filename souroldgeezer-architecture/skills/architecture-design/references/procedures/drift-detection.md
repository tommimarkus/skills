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

## Scope Limits

Business-other, Motivation, Strategy, portfolio, cloud-quality, and Physical
content are architect-owned unless explicit source evidence exists; report
unverified intent instead of deleting it.

## Output

Report added/removed/changed/unverified counts and likely reconciliation:
update package, update source, or confirm architect-owned intent.
