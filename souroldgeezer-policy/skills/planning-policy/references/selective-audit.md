# Selective Audit Routing

Load only when a targeted inspection or focused test cannot resolve one bounded
question that can materially change approach or acceptance. Ordinary domain
design stays with its owning design skill.

At most one leaf may set `selective_audit`. It requires an owning audit
(`devsecops-audit`, `test-quality-audit`, `ip-hygiene`, or `lean-audit`),
`initial_inspection: true`, `domain_match: true`,
`materially_changes_approach_or_acceptance: true`,
`targeted_inspection_or_focused_tests_cannot_resolve: true`, a bounded
`question`, and an `evidence_surface`. “Review risks” and “review for risks”
are not bounded questions.
