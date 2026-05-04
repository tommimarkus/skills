# Skill Evaluation Evidence

Use this document when creating or reviewing skill behavioral evidence. Keep
evidence files one hop from `SKILL.md` and load them only when the task changes
trigger metadata, workflow behavior, model-family extensions, source grounding,
or high-risk rejection gates.

## Source Hygiene

Evaluation artifacts are repo-authored evidence, not mirrors of benchmark
repositories or vendor docs.

- Prefer synthetic prompts derived from observed failure modes.
- Link external source material by URL or local path; do not copy third-party
  prompt text, examples, code, fixtures, tables, schemas, diagrams, logos, or
  screenshots.
- Use original paraphrase when recording a lesson from a source.
- Set `contains_third_party_text` to `false` for cases that are safe to bundle.
- If a case cannot be made safe without copying protected material, keep only a
  URL reference in `references/source-grounding.md` and do not add it to JSONL.

## Trigger Cases

Path: `references/evals/trigger-cases.jsonl`.

Each line is one JSON object:

```json
{"id":"api-design-trigger-yes-001","prompt":"Design a POST endpoint for order creation.","expected_activation":true,"reason":"Direct HTTP API build request.","source_kind":"synthetic","source_url":"","ip_handling":"original synthetic prompt; no third-party text","contains_third_party_text":false}
```

Required fields:

- `id`: stable local case identifier.
- `prompt`: synthetic or originally paraphrased user prompt.
- `expected_activation`: boolean.
- `reason`: why the skill should or should not activate.
- `source_kind`: `synthetic`, `local-trace`, `issue`, `review`, `runbook`, or
  another narrow provenance label.
- `source_url`: URL or local path when the case comes from a source; empty for
  synthetic cases.
- `ip_handling`: short source-hygiene note.
- `contains_third_party_text`: must be `false` for bundled cases.

A trigger pack needs at least one `expected_activation: true` case and one
`expected_activation: false` case.

## Behavior Cases

Path: `references/evals/behavior-cases.jsonl`.

Each line is one JSON object:

```json
{"id":"api-design-behavior-001","prompt":"Review a route handler for missing problem+json errors.","expected_artifacts":["per-finding report"],"required_checks":["load the API reference","cite file evidence"],"forbidden_behaviors":["claim runtime SLI evidence from static code"],"grader":"rubric: output cites evidence and separates static from runtime verification","source_kind":"synthetic","source_url":"","ip_handling":"original synthetic prompt; no third-party text","contains_third_party_text":false}
```

Required fields:

- `id`: stable local case identifier.
- `prompt`: synthetic or originally paraphrased task prompt.
- `expected_artifacts`: non-empty list of outputs the skill should produce.
- `required_checks`: non-empty list of checks the agent must perform.
- `forbidden_behaviors`: non-empty list of behaviors that should fail the case.
- `grader`: deterministic check, rubric, or manual review note.
- `source_kind`, `source_url`, `ip_handling`,
  `contains_third_party_text`: same meaning as trigger cases.

## Model Pressure

Path: `references/evals/model-pressure.md`.

Use this only when a model-family or runtime-specific extension exists because
generic wording failed. Record:

- pressure prompt id,
- model family or runtime tested,
- observed failure,
- accepted extension rule,
- retest command or prompt set,
- merge-back condition.

## Source Grounding

Path: `references/source-grounding.md`.

Use this when a skill encodes lessons from real traces, issues, reviews,
runbooks, or correction history. A useful entry names:

- source URL or local path,
- source type,
- lesson extracted in original wording,
- bundled material decision: `idea-only`, `paraphrase-with-citation`, or
  `URL-only`,
- licence or trademark note when relevant.
