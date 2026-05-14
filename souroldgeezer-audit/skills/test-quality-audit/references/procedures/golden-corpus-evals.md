# Golden-Corpus Evals

**When this runs:** run after changing `test-quality-audit` rubric wording,
dispatch rules, output contracts, extension files, smell catalogs, or examples.
This is an empirical guardrail for audit accuracy; it complements
`scripts/skill-architecture-report.sh .`, which validates skill architecture.

## Inputs

- Seed corpus:
  [../golden-corpus/test-quality-audit-cases.jsonl](../golden-corpus/test-quality-audit-cases.jsonl)
- Current `SKILL.md`, selected rubric references, smell catalog, and affected
  extensions.
- The exact skill change being evaluated.

## Stable Manual Eval Prompt

For each quick-mode corpus case, start a fresh audit context and use this prompt:

```text
Use test-quality-audit in quick mode. Audit only the supplied test snippet.
Report the selected rubric, sub-lane if any, smell codes, positive signal codes,
boundary evidence, coverage strength, gap relevance, verdict, severity, and
recommended action. Focus on edge cases, too-narrow happy scenarios, and tests
that only name or reach a SUT surface without asserting its contract. Do not
suggest code fixes beyond the recommended action field.
```

Provide only the corpus case's `test_snippet`, `stack`, and any declared
`supporting_context`. Do not provide `expected_*` fields to the auditor.

## Deep-Mode Gap Eval Prompt

For corpus cases that include `sut_snippet` or `deep_mode_context`, start a
fresh audit context and use this prompt:

```text
Use test-quality-audit in deep mode. Audit the supplied SUT snippet and test
snippet together. Report the selected rubric, loaded stack extension, gap
class, coverage state (`covered-strong`, `referenced-weak`,
`referenced-incidental`, `not-referenced`, `probable-static`, or
`confirmed-static-or-delegated`), smell codes, positive signal codes, verdict,
severity, and recommended action. Pay special attention to happy-path-only
tests, narrow happy scenarios, edge cases, auth/session matrix gaps, and weak
references that should not suppress a gap.
```

## Scoring

Compare output with the corpus entry:

- **Routing pass:** selected `rubric` and E2E `sub_lane` match.
- **Smell pass:** every `expected_smells` code appears; no `forbidden_smells`
  code appears.
- **Positive pass:** every `expected_positives` code appears when the case
  expects positives.
- **Boundary pass:** `expected_boundary_evidence`, when present, matches.
- **Coverage-strength pass:** `expected_coverage_strength`, when present,
  matches.
- **Gap-state pass:** `expected_gap_state`, when present, matches.
- **Verdict pass:** `expected_verdict`, `expected_severity`, and
  `expected_action` match.
- **False-positive note:** any extra smell code must be justified by evidence
  in the snippet. Record unjustified extras.
- **False-negative note:** any missing expected code is a regression unless the
  changed rubric intentionally retired or renamed it.

## Output

Record results in the change discussion or closeout notes:

```markdown
### Golden-corpus eval

- **Corpus version:** <value from corpus metadata or file commit>
- **Cases run:** <N>
- **Routing:** <passed>/<N>
- **Expected smells:** <passed>/<N>
- **Expected positives:** <passed>/<N or n/a>
- **Verdict/action:** <passed>/<N>
- **False positives:** <case ids and codes, or none>
- **False negatives:** <case ids and codes, or none>
- **Intentional expectation updates:** <case ids and reason, or none>
```

## Updating The Corpus

- Add cases one at a time.
- Keep snippets minimal and original to this repository.
- Include at least `id`, `stack`, `rubric`, `test_type`, `test_snippet`,
  `expected_smells`, `expected_positives`, `expected_verdict`,
  `expected_severity`, and `expected_action`.
- Include `expected_boundary_evidence`, `expected_coverage_strength`,
  `expected_gap_state`, or `deep_mode_context` when the case is about boundary
  or gap behavior.
- Use `forbidden_smells` to pin known false-positive regressions.
- When changing expected outcomes, state whether the change reflects a rubric
  improvement or a deliberate behavior change.
