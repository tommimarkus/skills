# IP Hygiene Drive-By Scope

Load this when a touched edit reaches pre-existing content that may contain or
propagate an IP-hygiene issue. A drive-by observation expands evidence only to
the neighbor needed to understand the current act; it does not silently turn a
change-scoped triage into a repository sweep.

## Criteria

- **`IP-SRC-3 Propagation`:** record whether the edit copies, modifies,
  aggregates, links/imports, or redistributes the pre-existing material. A mere
  unchanged neighbor is not caused by the edit; a new copy carries the source
  issue into the new location.
- **`IP-SRC-4 Boundary`:** inspect the source location and immediate provenance
  needed to assess the current act. Record all other potentially affected paths
  as untouched, not clean.

## Read-Only Rule

The audit is read-only by default. Emit a full finding for an issue introduced
or propagated by the current edit. For a pre-existing issue outside the
approved boundary, emit:

`deferred drive-by observation at <path:line> - <issue>; recommend separate retroactive audit [<severity>|<risk tier>]`

Do not fix it inline during an audit. If the user explicitly requests repair,
apply the approved boundary, create a separate `remediated:` record for each
changed finding, and require a fresh rerun before changing a gate or verdict.

## False-Attribution Controls

- Do not attribute a pre-existing issue to the current change merely because
  the touched file contains it.
- If the change copies affected content, report the new copy as current-scope
  and the source as a drive-by observation unless both are explicitly in scope.
- If the change only links to affected content, classify the link separately
  from copying. A citation or link records provenance but does not grant
  permission for any local reproduction.
- When the source or relationship is uncertain, mark inference and stop the
  affected decision rather than inventing lineage.
