# Drift Detection

Use when Review compares a dediren package with current code, IaC, UI routes,
API definitions, or workflows.

## Inputs

- Package: `docs/architecture/<feature>.dediren/`
- Source: repo paths in scope for the request
- Existing source evidence in `model.json` properties or documentation

## Checks

- Source artifact exists but no modeled element references it:
  `ARCH-X-1`.
- Modeled source reference no longer exists or no longer defines the modeled
  component, resource, route, API, or workflow: `ARCH-X-1`.
- Lifted Business Process, Event, Interaction, API, UI route, resource, or
  workflow lacks source evidence: `ARCH-X-2`.
- Source implies a relationship that the package omits or reverses:
  `ARCH-X-4`.
- Label changed while the architecture label may be intentionally
  human-friendly: `ARCH-X-3`.

## Scope Limits

Business-other, Motivation, Strategy, and Physical content are architect-owned
unless the user supplies explicit source evidence. Report them as
unverified intent instead of inventing drift.

## Output

Include added, removed, changed, and unverified counts. Tell the user whether
the likely reconciliation is "update the package" or "update the source" when
the evidence makes that clear.
