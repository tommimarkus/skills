# Test Quality Audit Golden Corpus

This directory contains versioned seed cases for empirical `test-quality-audit`
accuracy checks. Run the procedure in
[../procedures/golden-corpus-evals.md](../procedures/golden-corpus-evals.md)
after changing rubric wording, dispatch, output contracts, smell catalogs, or
extensions.

The corpus must cover each high-risk rubric family that the skill changes. For
edge/gap/auth work, keep at least one positive and one negative case for:
contract-derived boundary coverage, too-narrow happy scenarios, weak SUT
references, auth/session matrix gaps, and static/delegated gap dismissals.

Add minimal original examples with expected routing, smells, positives,
boundary evidence, coverage strength, verdict, severity, and action.
