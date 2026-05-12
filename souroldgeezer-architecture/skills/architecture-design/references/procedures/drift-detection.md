# Drift Detection

Use when Review compares a package with current code, IaC, UI, API, or workflow
source.

## Checks

- New source artifact not modeled, or modeled source missing/stale: `ARCH-X-1`.
- Lifted process/event/interaction/API/UI/resource/workflow lacks evidence:
  `ARCH-X-2`.
- Source implies omitted or reversed relationship: `ARCH-X-4`.
- Source label changed but architecture label may be intentional: `ARCH-X-3`.

## Scope Limits

Business-other, Motivation, Strategy, and Physical content are architect-owned
unless explicit source evidence exists; report unverified intent.

## Output

Report added/removed/changed/unverified counts and likely reconciliation:
update package or update source.
