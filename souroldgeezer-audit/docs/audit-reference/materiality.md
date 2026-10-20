# Materiality (shared procedure)

Grounds the risk tier of audit-craft.md §3. Materiality is the consequence of
the SUBJECT being wrong — never invented business priority.

## Risk tier
`risk_tier = max(signal_tier, declared_tier)`. Tiers: high | medium | low |
unknown. Every subject resolves to exactly one tier through the steps below;
a tier no step yields is a guess and is never emitted. The tier rates the
subject's role, never the consequence of a finding on it.

## signal_tier (observable, no guessing)
Take the first base that applies:
1. Role → high: authentication/authorization, payment/billing/money, data
   migration, security/crypto, PII/PHI handling, public-API/published-contract
   (a published interface consumers depend on; being reachable is not enough),
   destructive/irreversible ops. (Reuses materiality latent in Gap-AuthZ /
   Gap-Migration / Gap-Validate.)
2. Role determinable from the evidence but none of the above → `low`, naming
   the role (a leaf/pure helper, a build step, a public-content handler).
3. Role not determinable from the evidence → `unknown`.

Then escalate, the only route to `medium`: cited blast-radius / fan-in evidence
(many dependents) or change-churn evidence (frequently changed, from git
history) raises a `low` base to `medium`; `high` and `unknown` bases do not
move. Missing evidence never lowers a tier or makes it `unknown`: without git
history there is no churn escalation, disclosed as a limit.

## declared_tier (engagement input)
Optional critical-path declaration via (a) explicit user/prompt input naming
paths/globs, or (b) a repo-guidance/config convention. Declared critical → forces
`high` via `max`. Absent → no override. Concrete config format: a `materiality:`
list of path globs in the skill's `config.yaml` when present; prompt-named paths
otherwise.

## Discipline
Cite the grounding signal in the finding's risk-tier field
(e.g. "high — auth path", "low — public-content handler; no high-tier role",
"medium — low base; fan-in: imported by 40 modules", "unknown — role
undeterminable from the fragment"). Never let an ungrounded guess become a tier.
