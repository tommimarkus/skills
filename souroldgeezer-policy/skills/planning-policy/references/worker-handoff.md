# Worker handoff and return preflight

Use for ledger-backed v5 delegation. The parent resolves approval and capability
binding; `dispatch` verifies the worktree identity (creating it with
`--create-from`), starts the assigned attempt and returns the packet. The generated packet transports those decisions; it grants no
approval, permission or new retry. Existing single-step manual handoffs retain
their versioned contract and must carry relevant shared decisions.

After `in_progress`, generate the packet from the current stored assignment:

```text
python3 -B "${CLAUDE_SKILL_DIR}/references/scripts/planning_ledger.py" --repo-root REPO --plan-id PLAN handoff --run-id RUN --step-id STEP
python3 -B "<skill-dir>/references/scripts/planning_ledger.py" --repo-root REPO --plan-id PLAN handoff --run-id RUN --step-id STEP
```

Claude substitutes `${CLAUDE_SKILL_DIR}`. Codex resolves `<skill-dir>` to the
absolute source directory of the loaded skill. Pass the returned `handoff`
object unchanged, inline or in an explicitly supplied persistent file, together
with the host dispatch instructions. A batch carries one packet per member. A
member whose acceptance fails only for an environmental reason commits its work,
returns `blocked:environment`, and the worker continues to the next member; any
other stop halts the batch. The parent repairs that member per the
[ledger contract](ledger-contract.md) batch rule.
Do not give a worker the whole plan or reconstruct a packet from prose.

`dispatch` also stores the packet under the run and returns its absolute
`packet_path` with a generated, host-neutral `prompt` (at most 1,200 characters)
built only from packet facts. Pass that prompt unchanged to the tier agent; a
host adapter may append host facts only. The worker may run `validate-return`
with `--return-file -` to read its return from stdin. The packet's `precision`
governs scope: under `standard` a changed path outside the write set is allowed,
recorded by the parent, and judged by the verifier, so a worker names such paths
in `changed_paths` rather than stopping; under `strict` it is a hard stop.

`planning-worker-handoff-v1` is at most 32 KiB. It carries the plan digest and
plan/run/step/agent/attempt identities, exact assigned leaf (the effective leaf, with a bounded `amendments` summary
after a parent `amend`) and work unit,
absolute worktree, current tier/host/executor and binding, bounded retry
remediation when applicable, and `return_schema` derived from ledger constants.
`plan_context` includes objective, scope and every shared approved decision;
workers may rely on these without rediscovering them. The packet's digest binds
its contents, not approval or provenance. Oversized packets fail without losing
fields; groom the task before proceeding.

Use `return_schema` with host structured output when supported. Before returning,
a worker validates its prepared JSON through the same rules used by the parent:

```text
python3 -B "${CLAUDE_SKILL_DIR}/references/scripts/planning_ledger.py" validate-return --handoff-file HANDOFF --return-file RETURN
python3 -B "<skill-dir>/references/scripts/planning_ledger.py" validate-return --handoff-file HANDOFF --return-file RETURN
```

The command reads only the two bounded files and returns identity/status/digest
facts. It never writes the ledger, repairs JSON, runs acceptance, or certifies
that reported commands were run. A worker corrects its own malformed return and
checks again. A packet missing required input stops the worker with
`blocked:missing_input`; do not manufacture its missing context to make preflight
pass. The parent records the original submitted result and any correction as
observed evidence, without inventing an execution attempt for artifact repair.

In a `leaf_verify_v1` run the packet carries `changeset_budget`
(`max_changed_lines`, `max_files`, `exempt_paths`, `base_commit`). After
committing and before returning, preflight the committed work read-only:

```text
python3 -B "${CLAUDE_SKILL_DIR}/references/scripts/planning_ledger.py" check-changeset --handoff-file HANDOFF --worktree WORKTREE [--base COMMIT]
python3 -B "<skill-dir>/references/scripts/planning_ledger.py" check-changeset --handoff-file HANDOFF --worktree WORKTREE [--base COMMIT]
```

Verdicts are `pass`, `oversized:changeset`, and `outside_write_set` (an
uncommitted path counts as outside; under `standard` precision a committed
outside path is listed in `outside` and the verdict stays `pass`). A batch follower's `base_commit` is empty;
pass `--base` with the previous member's commit. Budget pressure resolves by
stopping `oversized:changeset` with the unstarted remainder, never by deleting
required content. A worker never returns `failed:verification`; only the ledger
synthesizes it from a verifier reject, and the verifier procedure lives in
[verify handoff](verify-handoff.md).

The parent still calls `record-return` on the current run. An old packet may be
internally valid while its attempt has been superseded; local preflight cannot
establish live freshness. Acceptance, retry, integration and cleanup remain owned
by the existing ledger and Git-policy procedures.

## Worker obligations

Every tier agent loads and follows this section once; the agents keep only their
tier-specific judgment, escalation, size-band and acceptance wording.

- **Packet use.** For a generated `planning-worker-handoff-v1` packet, preserve
  its shared `plan_context` decisions and use its `return_schema`. The packet
  never grants additional authority; the parent remains responsible for
  current-attempt validation and integration.
- **Contract version and binding.** Before any inspection or tool use,
  establish the assigned contract version. Assignments use v5. Require the exact
  resolved `planning-capability-binding-v1` with the plan digest, this `step_id`,
  assigned executor, and `capability_requirements`, alongside the assigned
  plan/step/attempt identity. If it is missing or does not exactly match, return
  `blocked:capability_unavailable`; do not probe for, substitute, drop, or defer
  a replacement capability.
- **Required inputs.** Before work, require the step's task and boundary, size
  band, named inputs and prior decisions, acceptance check, return shape, and the
  assigned work unit's `cohesive_outcome` and `decomposition` context. If a
  required field is missing, stop and return `blocked:missing_input` naming the
  missing fields; do not proceed under an assumption.
- **Retry remediation.** On a retry, accept only the ledger-supplied bounded
  `retry-remediation-v1` material. The ledger alone chose the target tier and
  whether this is a reuse or fresh executor; honor both without reading raw
  history or selecting another tier. If the settled task genuinely needs more
  reasoning, return `blocked:needs_higher_tier` with bounded evidence so the
  ledger decides whether to retry.
- **Changeset budget.** Stay inside the packet's `changeset_budget`: make only
  the assigned task, with no drive-by refactors, reformatting, or renames, and
  patch rather than regenerate. Run `check-changeset` before returning
  `completed`. If the work cannot fit, stop `oversized:changeset`; never shrink
  it by deleting required content.
- **Return.** Return exactly one UTF-8 JSON object using
  `"schema": "bounded-step-return-v1"`, with no Markdown, prose outside the
  object, or raw logs. Echo the assigned `step_id`, `agent_id` and
  helper-generated `attempt_id`; the parent supplies `run_id`, so do not return
  it. Status is exactly `completed`, `blocked`, `failed`, or `oversized`; blocker
  codes such as `blocked:missing_input` carry the detail. Note types are exactly
  `finding`, `decision_needed`, `residual_risk`, `untouched`, or
  `verification_limit`. Blocker evidence is an optional pair: supply a relative
  path and digest together, or omit both when the stop has no evidence artifact.
  Use `completed` only when the acceptance command exits `0`. Completed changed work needs a
  commit hash, as does any other status whose changed paths are non-empty. Blocked, failed, and oversized returns require a blocker;
  oversized also needs remainder. Prefer stopping before you change anything;
  when the stop only becomes clear after work began, commit the finished slice
  and name it in `commit_hash`, or revert to a clean tree and report no changed
  paths; never leave edits uncommitted. Do not invent a decision. Your
  verification covers only your own drafting; say plainly what you did not check.
  Before returning, validate the prepared return read-only with `validate-return`,
  as described above in this file.
  The packet's `return_schema` and `validate-return` own every count, length and
  size limit.
