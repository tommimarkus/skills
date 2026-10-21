"""Implementation of the parent-owned planning ledger behind planning_ledger.py.

The entry script keeps its path and CLI; it re-exports each module's explicit
``__all__``. This file imports nothing, so loading the package never loads a module.

Module map:
- plancontract: the stdlib-only plan validator and its CLI; imports no other module, and the
  validate_plan_contract.py shim (not the ledger shim) re-exports it.
- vocabulary: constants, schema ids, return-code families, limits and policies.
- core: the shared JSON type aliases, Error, UsageError, canonical encoding and digest,
  identifiers, time, read_json, and the script path anchors derived from SCRIPTS_DIR.
- gitops: the single git helper every git call goes through, plus the worktree-helper
  subprocess call.
- store: ledger root, run layout, atomic write, event append, safe_run_contents.
- contract: plan validator seam over plancontract, leaves, amendments, effective leaves, capability
  binding and the host tier map.
- checkpoint: run integrity, the single run validator, retired-contract refusal, load_run,
  mutating_run.
- schedule: readiness, batches, retry selection, the live next block, primary_next.
- series: series handoff artifacts and the predecessor cross-check.
- returns: return validation, retry and remediation, record-return, amend.
- dispatch: worker handoff packets, dispatch and transitions.
- verify: changeset gate, verify handoff and record-verify.
- retention: list, gc, purge and run classification.
- closeout: init, land, close, reopen, validate and show.
- tracing: opt-in trace counters.
- cli: argument parsing and main.

Import order, lowest first. A module imports only an earlier group, or a same-group
module without a cycle; nothing imports cli; a helper several modules use lives in the
lowest module all of them may import (this is why run validation helpers sit in
checkpoint and the init command in closeout):
plancontract < vocabulary < core < gitops < {store, contract} < checkpoint < {schedule, series}
< {returns, dispatch, verify, retention, closeout, tracing} < cli.

Substitution seams (now in core, git and run_worktree_helper in gitops, plan_validator and
changed_path_allowed in contract) are called as owner.name() outside their owner and are
left out of ``__all__``; tests patch the owner module.
"""
