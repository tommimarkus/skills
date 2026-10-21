# IP Hygiene Remediation

Load this only when the user explicitly requests a repair, per
[SKILL.md § Finding And Remediation Contract](../../SKILL.md). Audits stay
read-only without that request.

## Remediation Record

Only an explicit fix request authorizes repairs. Keep audit findings unchanged,
make the requested bounded repair, and add a separate `remediated:` record with
the finding ID, changed location, action, authority used, and verification. A
fresh rerun is required for a new gate or verdict. Do not reuse a pre-fix result.
The former `fixed: <path:line> - <remedy summary> [<severity>|<risk tier>];
consequence: <effect if unaddressed>` form is retired in favor of `remediated:`.

## Drive-By Observations

For an out-of-bound drive-by issue, preserve the compact observation:
`deferred drive-by observation at <path:line> - <issue>; recommend separate retroactive audit [<severity>|<risk tier>]`,
and include its full finding data.
