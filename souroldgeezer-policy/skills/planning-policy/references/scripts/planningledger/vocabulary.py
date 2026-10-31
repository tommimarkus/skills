"""Planning ledger vocabulary: limits, schema ids, code families, states and policies."""

from __future__ import annotations

import re

__all__ = [
    "MAX_CHECKPOINT",
    "MAX_RETURN",
    "MAX_WORKER_HANDOFF",
    "MAX_WORKER_HANDOFF_RAW",
    "MAX_REMEDIATION",
    "MAX_SERIES_HANDOFF",
    "MAX_USAGE",
    "MAX_TOKENS",
    "MAX_USAGE_TOKENS",
    "MAX_NEXT_TOKENS",
    "MAX_NEXT_ONLY_TOKENS",
    "NEXT_ID_PLACEHOLDER",
    "NEXT_ID_KEYS",
    "NEXT_ID_FLAG",
    "ID",
    "SHA",
    "SHA40",
    "COMMIT",
    "PROXY_TOKEN_RE",
    "NOTE_TYPES",
    "RETURN_STATUSES",
    "MAX_CHANGED_PATHS",
    "MAX_BLOCKERS",
    "MAX_NOTES",
    "MAX_REMAINDER",
    "MAX_BLOCKER_CODE",
    "MAX_ACCEPTANCE_SUMMARY",
    "MAX_ACCEPTANCE_EXCERPT",
    "ACCEPTANCE_TAIL_BYTES",
    "NO_ATTEMPT_ID",
    "ACCEPTANCE_LOG",
    "MAX_NOTE_MESSAGE",
    "MAX_BLOCKER_SUMMARY",
    "MAX_REMAINDER_ITEM",
    "MAX_PATH",
    "STEP_STATES",
    "WORKTREE_RESULT_FIELDS",
    "WORKTREE_RESULT_OPTIONAL",
    "BATCH_DEPENDENCY_STATES",
    "EXTERNAL_DEPENDENCY_STATES",
    "BATCH_STOPPED_STATES",
    "BATCH_ACTIVE_STATES",
    "CLOSEOUT_FIELDS",
    "AMENDMENT_FIELDS",
    "AMENDMENT_OPTIONAL",
    "MAX_AMENDMENTS",
    "MAX_AMENDMENT_PATHS",
    "MAX_AMENDED_ATTEMPTS",
    "MAX_AMENDED_COMMAND",
    "AMENDABLE_STATES",
    "SCOPE_REJECTION_REASON",
    "TERMINAL_RETRY_REASONS",
    "RETENTION_DAYS",
    "LIFECYCLE_FIELDS",
    "ESCALATING_RETRY_POLICY",
    "REGISTERED_RETURN_CODES",
    "RETURN_CODES",
    "VERIFIER_ONLY_CODES",
    "REPAIRABLE_CODES",
    "REASONING_STOPS",
    "VERIFY_POLICIES",
    "RETAINED_PIPELINE_POLICY",
    "RETAINED_PIPELINE_FIELDS",
    "RETAINED_PIPELINE_CODE",
    "MAX_CONCURRENT",
    "NON_ACTION_CATEGORIES",
    "PRECISION_POLICIES",
    "CHANGESET_BUDGET_FIELDS",
    "MAX_CHECK_OUTSIDE",
    "MAX_VERIFY_HANDOFF",
    "MAX_VERIFY_RETURN",
    "VERIFY_VERDICTS",
    "VERIFY_PASSING",
    "VERIFY_CODES",
    "VERIFY_FINDING_FIELDS",
    "VERIFY_HANDOFF_FIELDS",
    "VERIFY_HANDOFF_OPTIONAL",
    "VERIFIER_AGENTS",
    "FORWARD_SCHEMA",
    "RETIRED_RUN_SCHEMAS",
    "LAST_RETIRED_RELEASE",
    "PORTABLE_TIERS",
    "RETRY_STATE_FIELDS",
    "REMEDIATION_FIELDS",
    "SERIES_HANDOFF_SCHEMA",
    "SERIES_HANDOFF_FIELDS",
    "SERIES_HANDOFF_LIST_FIELDS",
    "USAGE_FIELDS",
    "USAGE_STAGES",
    "RAW_USAGE_FIELDS",
    "WORKER_HANDOFF_FIELDS",
    "DISPATCH_ENTRY_FIELDS",
    "MAX_WORKER_PROMPT",
]


# A checkpoint retains one bounded capability binding per step. Keep the
# record bounded while leaving the established 40-step summary lane viable.
MAX_CHECKPOINT = 64 * 1024


MAX_RETURN = 8 * 1024


MAX_WORKER_HANDOFF = 32 * 1024


MAX_WORKER_HANDOFF_RAW = MAX_WORKER_HANDOFF + 1024


MAX_REMEDIATION = 4 * 1024


MAX_SERIES_HANDOFF = 8 * 1024


MAX_USAGE = 4 * 1024


MAX_TOKENS = 1200


MAX_USAGE_TOKENS = 600


# A `next` block restates what the acting command just decided, so it stays far
# smaller than a summary: enough for the state and one CLI hint, never a report.
MAX_NEXT_TOKENS = 120


MAX_NEXT_ONLY_TOKENS = 240


# The `next` caps bound block structure, not identifier length: the id grammar already
# bounds identifiers, so each one is measured as this single placeholder token (#144).
NEXT_ID_PLACEHOLDER = "ID"


# Keys whose value in a `next` block or the next-only envelope is an identifier or a list of them.
NEXT_ID_KEYS = frozenset(
    {
        "agent_id",
        "attempt_id",
        "await_step_id",
        "blocked_step_ids",
        "cleanup_step_id",
        "concurrent",
        "plan_id",
        "ready_step_ids",
        "retryable_step_ids",
        "run_id",
        "step_id",
        "step_ids",
    }
)


# An identifier flag and its value inside a `next` block's command strings.
NEXT_ID_FLAG = re.compile(r"(--(?:plan|run|step|agent)-id) \S+")


ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


SHA = re.compile(r"^[0-9a-f]{64}$")


SHA40 = re.compile(r"^[0-9a-f]{40}$")


COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


PROXY_TOKEN_RE = re.compile(r"\w+|[^\w\s]")


NOTE_TYPES = {
    "finding",
    "decision_needed",
    "residual_risk",
    "untouched",
    "verification_limit",
    "extra_read",
}


# Single source for the bounded-step-return-v1 contract. Every prose restatement
# of these facts is checked against them by tests/planning_return_contract_parity_test.py.
RETURN_STATUSES = {"completed", "blocked", "failed", "oversized"}


MAX_CHANGED_PATHS = 32


MAX_BLOCKERS = 8


MAX_NOTES = 8


MAX_REMAINDER = 8


MAX_BLOCKER_CODE = 120


MAX_ACCEPTANCE_SUMMARY = 480


MAX_ACCEPTANCE_EXCERPT = 4 * 1024


# UTF-8 needs at most four bytes per character, so this window always holds the excerpt.
ACCEPTANCE_TAIL_BYTES = MAX_ACCEPTANCE_EXCERPT * 4


# Evidence directory name for a parent run of a step that has no attempt yet.
NO_ATTEMPT_ID = "no-attempt"


# One evidence log written by run-acceptance: <worker|parent>-<n>.log.
ACCEPTANCE_LOG = re.compile(r"^(worker|parent)-[1-9][0-9]*\.log$")


MAX_NOTE_MESSAGE = 480


MAX_BLOCKER_SUMMARY = 240


MAX_REMAINDER_ITEM = 240


MAX_PATH = 240


STEP_STATES = {
    "pending",
    "ready",
    "in_progress",
    "completed",
    "integrated",
    "cleaned",
    "blocked",
    "failed",
    "oversized",
    "discarded",
}


WORKTREE_RESULT_FIELDS = {
    "schema",
    "ok",
    "action",
    "repo_root",
    "target",
    "branch",
    "worktree",
    "source_commit",
    "rebased_commit",
    "parent_before",
    "parent_after",
}


# The Git-policy helper always emits `rebased_tree_changed` and adds
# `batch_source_commits` only for a batch integrate, so both stay optional here:
# a result recorded before either existed still validates.
WORKTREE_RESULT_OPTIONAL = {"rebased_tree_changed", "batch_source_commits"}


# A batch is one dispatch in one shared worktree, so a member's dependency on an
# earlier member is satisfied by progress rather than by that member's cleanup.
BATCH_DEPENDENCY_STATES = {"ready", "in_progress", "completed", "cleaned"}


EXTERNAL_DEPENDENCY_STATES = {"integrated", "cleaned"}


BATCH_STOPPED_STATES = {"blocked", "failed", "oversized"}


BATCH_ACTIVE_STATES = {"pending", "ready", "in_progress"}


CLOSEOUT_FIELDS = {
    "returned_commit": "",
    "integrated_commit": "",
    "integration_result_path": "",
    "integration_result_sha256": "",
    "cleanup_result_path": "",
    "cleanup_result_sha256": "",
}


# Execution-metadata amendments: a bounded per-step overlay on the approved leaf.
AMENDMENT_FIELDS = {
    "reason",
    "add_write",
    "add_read",
    "after_attempt_id",
    "after_attempt_count",
    "return_recorded",
}


AMENDMENT_OPTIONAL = {"acceptance_command", "max_attempts"}


MAX_AMENDMENTS = 4


MAX_AMENDMENT_PATHS = 8


MAX_AMENDED_ATTEMPTS = 5


MAX_AMENDED_COMMAND = 2048


AMENDABLE_STATES = {"pending", "ready", "blocked", "failed", "oversized"}


SCOPE_REJECTION_REASON = "oversized: changed path outside write_set"


TERMINAL_RETRY_REASONS = {
    "blocked:no_progress",
    "blocked:retry_exhausted",
    "blocked:retry_ceiling_reached",
}


RETENTION_DAYS = {
    "completed": 30,
    "blocked": 90,
    "abandoned": 7,
    "discarded": 7,
    "superseded": 7,
}


LIFECYCLE_FIELDS = {"run_status", "outcome", "closed_at", "purge_after"}


ESCALATING_RETRY_POLICY = "escalating_remediation_v1"


REGISTERED_RETURN_CODES = "registered_v1"


# The closed blocker-code vocabulary a registered run enforces, by return status.
RETURN_CODES = {
    "blocked": tuple(
        f"blocked:{name}"
        for name in (
            "missing_input",
            "needs_higher_tier",
            "model_unavailable",
            "capability_unavailable",
            "environment",
        )
    ),
    "failed": ("failed:acceptance", "failed:execution", "failed:verification"),
    "oversized": ("oversized:scope", "oversized:changeset"),
}


# Recorded by the ledger alone (record-verify): a worker return can never carry it.
VERIFIER_ONLY_CODES = {"failed:verification"}


# Repairable stops retry at the same tier without spending the same-tier retry.
REPAIRABLE_CODES = {"blocked:environment"}


# The stops that need reasoning rather than repair, by (status, code).
REASONING_STOPS = {
    ("failed", "failed:acceptance"),
    ("failed", "failed:verification"),
    ("blocked", "blocked:needs_higher_tier"),
}


VERIFY_POLICIES = {"leaf_verify_v1", "closeout_only"}


# Retained-run stamp of the removed provisional-start pipeline. Load accepts it;
# a run whose steps still carry stacked state refuses every mutation.
RETAINED_PIPELINE_POLICY = "provisional_v1"


RETAINED_PIPELINE_FIELDS = (
    "provisional_base",
    "upstream_stale",
    "upstream_change",
    "pending_acceptance",
)


RETAINED_PIPELINE_CODE = "blocked:upstream_changed"


MAX_CONCURRENT = 4


NON_ACTION_CATEGORIES = {
    "terminal_closed",
    "terminal_blocked",
    "validate_closeout",
    "contract_migration_required",
}


# The stamp maps to the plan's precision word; a run without it keeps the hard scope rejection.
PRECISION_POLICIES = {"standard_v1": "standard", "strict_v1": "strict"}


CHANGESET_BUDGET_FIELDS = {"max_changed_lines", "max_files", "exempt_paths", "base_commit"}


MAX_CHECK_OUTSIDE = 8


MAX_VERIFY_HANDOFF = 16 * 1024


MAX_VERIFY_RETURN = 4 * 1024


VERIFY_VERDICTS = {"pass", "reject", "inconclusive"}


VERIFY_PASSING = {"pass", "inconclusive"}


VERIFY_CODES = {
    "verify:coverage",
    "verify:decision",
    "verify:regression",
    "verify:scope_creep",
    "verify:acceptance_gap",
}


VERIFY_FINDING_FIELDS = {"code", "path", "line", "clause", "summary"}


VERIFY_HANDOFF_FIELDS = {
    "schema",
    "packet_sha256",
    "plan_id",
    "run_id",
    "plan_sha256",
    "step_id",
    "attempt_id",
    "agent_id",
    "verify_id",
    "verifier_tier",
    "task",
    "boundary",
    "settled_decisions",
    "approved_decisions",
    "write_set",
    "acceptance_command",
    "cohesive_outcome",
    "acceptance_exit_code",
    "base_commit",
    "returned_commit",
    "budget",
    "changeset",
    "prior_verify",
    "return_schema",
}


# Added to a packet only for a run stamped with a precision policy.
VERIFY_HANDOFF_OPTIONAL = {"outside_write_set", "outside_write_set_count"}


# The verifier is read-only: mechanical and standard builds get the standard
# verifier, analytical and deep builds the analytical one.
VERIFIER_AGENTS = {
    "mechanical": "plan-verify-standard",
    "standard": "plan-verify-standard",
    "analytical": "plan-verify-analytical",
    "deep": "plan-verify-analytical",
}


FORWARD_SCHEMA = 5


# Contract versions 1-4 are retired. A retained run of one is refused, listed and never
# collected: version 1 by its plan-level checkpoint, versions 2-4 by the `schema` stamp.
RETIRED_RUN_SCHEMAS = {2, 3, 4}


LAST_RETIRED_RELEASE = "souroldgeezer-policy 2026.10.9"


PORTABLE_TIERS = ("mechanical", "standard", "analytical", "deep")


RETRY_STATE_FIELDS = {
    "current_tier",
    "same_tier_retry_used",
    "current_assignment",
    "retry_remediation_path",
    "retry_remediation_sha256",
}


REMEDIATION_FIELDS = {
    "schema",
    "step_id",
    "prior_attempt_id",
    "prior_return_sha256",
    "diagnosis",
    "remediation_action",
    "executor_mode",
    "next_agent_id",
    "next_harness",
    "target_portable_tier",
}


SERIES_HANDOFF_SCHEMA = "planning-series-handoff-v1"


SERIES_HANDOFF_FIELDS = {
    "schema",
    "plan_id",
    "run_id",
    "series_id",
    "slice",
    "landed",
    "decisions",
    "assumptions_to_revalidate",
    "remaining_scope",
}


SERIES_HANDOFF_LIST_FIELDS = (
    "landed",
    "decisions",
    "assumptions_to_revalidate",
    "remaining_scope",
)


USAGE_FIELDS = {
    "schema",
    "run_id",
    "step_id",
    "attempt_id",
    "actor",
    "stage",
    "harness",
    "model",
    "input_tokens",
    "output_tokens",
    "total_tokens",
}


USAGE_STAGES = {
    "prepare",
    "implement",
    "validate",
    "integrate",
    "final_verify",
    "unknown",
}


RAW_USAGE_FIELDS = {
    "prompt",
    "completion",
    "arguments",
    "results",
    "raw_log",
    "messages",
    "content",
}


WORKER_HANDOFF_FIELDS = {
    "schema",
    "contract_version",
    "handoff_sha256",
    "plan_id",
    "run_id",
    "plan_sha256",
    "step_id",
    "agent_id",
    "attempt_id",
    "plan_context",
    "leaf",
    "work_unit",
    "worktree",
    "portable_tier",
    "host",
    "executor",
    "capability_binding",
    "retry_remediation",
    "return_schema",
}


# Added to a dispatch entry beside the packet; never part of the packet's digest.
DISPATCH_ENTRY_FIELDS = {"packet_path", "prompt"}


MAX_WORKER_PROMPT = 1200
