# Plan Expansion

Load only when authoring a plan series from a rule index (index-driven
authoring); nothing else in the reference set changes. `expand_plan.py` is a
deterministic, stdlib-only authoring aid: one JSON template plus a JSONL rule
index become v5 plan slices. Series mechanics stay in [plan series](plan-series.md)
and approval in [approval handoff](approval-handoff.md).

## Template

`schema: "planning-expansion-template-v1"`; start from
[templates/expansion-template-v1.json](templates/expansion-template-v1.json).
Required: `objective`, `scope_summary`, `approved_decisions`, `owner_prefix`
(`owner_prefix` + rule id must form a valid branch name), `series`, `types`;
optional `precision` (default `strict`) and `verification`.

- `series`: `series_id`, `end_verification_commands`, `max_leaves` (default and
  ceiling 12).
- Each type: `task`, `boundary`, `write_set`, `read_set_extra`,
  `acceptance_command`, `size`, `portable_tier`, `max_attempts`,
  `settled_decisions`, `capability_requirements`, `batch`; optional
  `irreducible_unknown_or_risk` (required for `analytical`/`deep`, forbidden
  otherwise) and `exemplar`.
- Text fields may use `{id}`, `{type}`, `{spec}`; `{{` and `}}` are literal
  braces. Unknown placeholders, format specs or conversions, and a value that
  renders empty are refused.

## Index

JSONL, one rule per line: `id`, `type`, `deps` (rule ids), `spec` and `refs`
(repository-relative paths); `exemplar: true` is optional. An `id` is a stable
identifier (lowercase, digits, `-`/`_`, at most 64 characters). Blank lines,
duplicate ids, unknown types or dependencies, self-dependencies, a second
`exemplar: true` for one type, and `exemplar: true` on a type without `exemplar`
are refused with the line number; a cycle is refused naming its rules.

## Partition

Order is topological and stable by index order; exemplars and their transitive
dependencies come first. Slices take at most `max_leaves` rules and shrink until
the canonical plan is within 64 KiB. `partition` prints the bounded summary the
owner approves: `generator_sha256` (expander version, template, index),
`series_id`, rule and slice counts, exemplars, and per-slice ids. It renders
every rule and validates every slice (worst-case predecessor stub past slice 1),
so an approved summary never hides a refusable slice; errors are prefixed
`slice <k>: `.

## Slices

Each rule is one work unit and one leaf. `read_set` is `spec`, `refs`, then
`read_set_extra`. `dependencies` keep only same-slice rules; earlier-slice
dependencies are already landed. Each leaf's `worktree_owner` is `owner_prefix`
plus its id. Adjacent same-type `mechanical`/`standard` leaves with
`batch: true`, never an exemplar, form `batch` groups of 2 to 8 that share
`owner_prefix` plus the batch id. The
`series` block carries `slice`, `final`, and `end_verification_commands`; past
slice 1 `predecessor` is filled read-only from the closed previous run. The
plan is validated again before it is emitted.

## Exemplars

A type with `exemplar` lands one rule first — the rule marked `exemplar: true`,
otherwise its type's first rule in dependency order — at the exemplar's own tier
(`standard`, or `analytical` with `irreducible_unknown_or_risk`). The type's
own `portable_tier: "mechanical"` is the follower tier; followers get the
exemplar's landed `write_set` in `read_set`, an `exemplar_pattern` settled
decision (do not set one yourself), and a same-slice dependency on the exemplar.
A rule the order would place before its exemplar is refused ("ordered before its
exemplar"; reachable only via an explicit `exemplar: true`): choose another
exemplar or adjust deps. Mechanical leaves may not require a skill, since Claude
mechanical wrappers lack the `Skill` tool. No new plan field is added; if the
work needs one, stop and report.

## Commands

```text
python3 -B "${CLAUDE_SKILL_DIR}/references/scripts/expand_plan.py" partition --template T --index I
python3 -B "<skill-dir>/references/scripts/expand_plan.py" partition --template T --index I
python3 -B "${CLAUDE_SKILL_DIR}/references/scripts/expand_plan.py" slice --template T --index I --slice 1 --out PLAN
python3 -B "<skill-dir>/references/scripts/expand_plan.py" slice --template T --index I --slice 1 --out PLAN
```

Claude substitutes `${CLAUDE_SKILL_DIR}`; Codex resolves `<skill-dir>` to the
loaded skill's absolute source directory. For `--slice N` above 1 add
`--predecessor-plan-id` and `--predecessor-run-id` (optionally `--repo-root`,
`--ledger-root`); slice 1 takes none. `--out` writes the canonical plan and
prints `{"ok", "slice", "final", "plan_sha256", "out"}`; without it the plan goes
to stdout. Exit 0 succeeds, 1 is an input or validation refusal printing
`{"ok": false, "errors": [...]}` (at most 40), 2 is a usage error.

## Workflow per slice

Emit, then `validate --pin-roots`, the approval handoff, `init-v5` with its
predecessor cross-check, and execution; close with a series handoff, then emit
the next slice with the closed run's plan id and run id, read-only (an unclosed
run, another series, or a wrong slice number is refused). The aid changes no
validator, ledger, approval, or series semantics.

## Reproducibility and limits

Output is byte-identical for the same template, index, and predecessor. The
`generator_sha256` covers the expander version, template, and index, not the
predecessor. Each slice is approved separately: there is no inherited approval
(a separate pending proposal could bind to the digest). The expander never
writes the ledger. Bounds: template 256 KiB, index 8 MiB, `max_leaves` 12, summary
and each plan 64 KiB canonical. It refuses rather than emits an invalid plan.
