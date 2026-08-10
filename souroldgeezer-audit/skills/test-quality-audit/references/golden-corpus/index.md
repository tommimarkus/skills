# Test Quality Audit Golden Corpus

This corpus realizes the self-measurement principle in
[audit-craft.md §8](../../../../docs/audit-reference/audit-craft.md).

This directory contains versioned seed cases for empirical `test-quality-audit`
accuracy checks. Run the procedure in
[../procedures/golden-corpus-evals.md](../procedures/golden-corpus-evals.md)
after changing rubric wording, dispatch, output contracts, smell catalogs, or
extensions.

The corpus must cover each high-risk rubric family that the skill changes. For
edge/gap/auth work, keep at least one positive and one negative case for:
contract-derived boundary coverage, too-narrow happy scenarios, weak SUT
references, auth/session matrix gaps, and static/delegated gap dismissals.
For suite-health work, cover healthy growth, costly cross-layer overlap,
missing history, unreadable result formats, selective-execution safety,
quarantine ownership, and retirement evidence.

Add minimal original examples with expected routing, smells, positives,
boundary evidence, coverage strength, verdict, severity, and action;
optionally risk tier and worklist priority.
Suite-health cases may additionally declare `expected_suite_health_smells`,
`expected_suite_health_positives`, evidence-state fields, and forbidden actions.
