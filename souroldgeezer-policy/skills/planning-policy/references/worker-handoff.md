# Worker handoff and return preflight

Use for ledger-backed v5 delegation. The parent resolves approval and capability
binding, creates the worktree and starts the assigned attempt through the normal
ledger lifecycle. The generated packet transports those decisions; it grants no
approval, permission or new retry. Existing single-step or legacy manual
handoffs retain their versioned contract and must carry relevant shared decisions.

After `in_progress`, generate the packet from the current stored assignment:

```text
python3 -B "${CLAUDE_SKILL_DIR}/references/scripts/planning_ledger.py" --repo-root REPO --plan-id PLAN handoff --run-id RUN --step-id STEP
python3 -B "<skill-dir>/references/scripts/planning_ledger.py" --repo-root REPO --plan-id PLAN handoff --run-id RUN --step-id STEP
```

Claude substitutes `${CLAUDE_SKILL_DIR}`. Codex resolves `<skill-dir>` to the
absolute source directory of the loaded skill. Pass the returned `handoff`
object unchanged, inline or in an explicitly supplied persistent file, together
with the host dispatch instructions. A batch carries one packet per member.
Do not give a worker the whole plan or reconstruct a packet from prose.

`planning-worker-handoff-v1` is at most 32 KiB. It carries the plan digest and
plan/run/step/agent/attempt identities, exact assigned leaf and work unit,
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

The parent still calls `record-return` on the current run. An old packet may be
internally valid while its attempt has been superseded; local preflight cannot
establish live freshness. Acceptance, retry, integration and cleanup remain owned
by the existing ledger and Git-policy procedures.
