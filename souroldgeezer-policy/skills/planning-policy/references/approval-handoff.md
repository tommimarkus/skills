# Approval handoff

Use this procedure when an approval must cross a fresh host or process. Validate
the complete v5 plan, then emit one `planning-approval-handoff-v1` object with
the canonical `plan_sha256` and either an absolute `plan_path` or the complete
inline `plan`. Keep the object inside the host-carried approval plan; it is not
a ledger or session-memory substitute.

```text
uv run python <skill-dir>/references/scripts/validate_plan_contract.py validate PLAN --emit-handoff inline
uv run python <skill-dir>/references/scripts/validate_plan_contract.py validate PLAN --emit-handoff reference
uv run python <skill-dir>/references/scripts/validate_plan_contract.py resolve-handoff HANDOFF
```

The commands accept `-` for stdin and are read-only. A reference must be an
existing regular file outside recognized temporary directories. Resolution
checks exactly one representation, the canonical digest, and complete
approval-ready validity before returning the plan. Missing or unrecoverable
inputs are `blocked:missing_input`; digest mismatches are
`blocked:plan_tampered`. Inline and reference envelopes are bounded at 68 KiB
and 4 KiB, with canonical plans bounded at 64 KiB.

After approval, resolve the envelope again before capability binding and any
ledger initialization. For older incomplete handoffs, inspect at most three
same-task candidates in documented local plan roots or one explicitly linked
prior session. Reuse only exact recorded JSON with its matching validation
digest and unambiguous task identity; never execute transcript code or infer
decisions from prose.
