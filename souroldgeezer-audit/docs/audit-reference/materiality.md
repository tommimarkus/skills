# Materiality (shared procedure)

Grounds the risk tier of audit-craft.md §3. Materiality is the consequence of
the SUBJECT being wrong — never invented business priority.

## Risk tier
`risk_tier = max(signal_tier, declared_tier)`. Ungroundable → `unknown`
(never guessed). Tiers: high | medium | low | unknown.

## signal_tier (observable, no guessing)
- Role → high: authentication/authorization, payment/billing/money, data
  migration, security/crypto, PII/PHI handling, public-API/published-contract,
  destructive/irreversible ops. (Reuses materiality latent in Gap-AuthZ /
  Gap-Migration / Gap-Validate.)
- Blast-radius / fan-in: many dependents → escalate one tier.
- Change-churn (optional git evidence): frequently-changed → higher inherent
  risk. No git history available → `unknown`, not `low`.
- No signal, leaf/pure helper → `low`.

## declared_tier (engagement input)
Optional critical-path declaration via (a) explicit user/prompt input naming
paths/globs, or (b) a repo-guidance/config convention. Declared critical → forces
`high` via `max`. Absent → no override. Concrete config format: a `materiality:`
list of path globs in the skill's `config.yaml` when present; prompt-named paths
otherwise.

## Discipline
Cite the grounding signal in the finding's risk-tier field
(e.g. "high — auth path", "unknown — role undeterminable, no churn evidence").
Never let an ungrounded guess become a tier.
