"""Planning ledger checkpoint: run integrity, the single run validator, load and mutation guards."""

from __future__ import annotations

import json
from pathlib import Path

from . import contract
from .contract import (
    checkpoint_binding,
    effective_leaves,
    host_tiers,
    leaves_by_id,
    valid_stored_binding,
    validate_amendment_events,
)
from .core import (
    Error,
    canon,
    dependency_order,
    digest,
    ident,
    parent,
    read_json,
    rel,
    require_sha256,
    required_file,
    retained_until,
    timestamp,
    uuid4,
)
from .store import plan_dir, run_dir, safe_run_contents
from .vocabulary import (
    CLOSEOUT_FIELDS,
    COMMIT,
    ESCALATING_RETRY_POLICY,
    FORWARD_SCHEMA,
    LAST_RETIRED_RELEASE,
    LIFECYCLE_FIELDS,
    MAX_CHECKPOINT,
    MAX_REMEDIATION,
    MAX_SERIES_HANDOFF,
    PORTABLE_TIERS,
    PRECISION_POLICIES,
    REGISTERED_RETURN_CODES,
    REMEDIATION_FIELDS,
    RETAINED_PIPELINE_CODE,
    RETAINED_PIPELINE_FIELDS,
    RETAINED_PIPELINE_POLICY,
    RETIRED_RUN_SCHEMAS,
    RETRY_STATE_FIELDS,
    SCOPE_REJECTION_REASON,
    SERIES_HANDOFF_FIELDS,
    SERIES_HANDOFF_LIST_FIELDS,
    SERIES_HANDOFF_SCHEMA,
    SHA,
    STEP_STATES,
    VERIFY_POLICIES,
)

__all__ = [
    "retained_pipeline_steps",
    "require_no_retained_pipeline",
    "scope_rejection_state",
    "lifecycle",
    "active_run",
    "validate_steps",
    "validate_events",
    "retired_contract",
    "refuse_retired",
    "validate_run",
    "load_run",
    "mutating_run",
    "valid_remediation",
    "valid_series_handoff",
    "read_series_handoff",
    "validate_series_handoff",
    "validate_retry_artifacts",
]


def retained_pipeline_steps(data):
    """Steps still carrying state from the removed provisional-start pipeline."""
    return [
        sid
        for sid, step in sorted(data["steps"].items())
        if any(step.get(field) is not None for field in RETAINED_PIPELINE_FIELDS)
        or any(
            isinstance(blocker, dict) and blocker.get("code") == RETAINED_PIPELINE_CODE
            for blocker in step.get("blockers") or ()
        )
    ]


def require_no_retained_pipeline(data):
    """Refuse to mutate a retained provisional_v1 run whose steps carry stacked state."""
    stacked = retained_pipeline_steps(data)
    if stacked:
        raise Error(
            "blocked:contract_migration_required: steps "
            + ", ".join(stacked[:8])
            + " carry state from the removed provisional-start pipeline; "
            "show, list and gc still work"
        )


def scope_rejection_state(step):
    """A step stopped on write_set alone, with no stored return, is repairable."""
    return (
        step["status"] == "oversized"
        and step["reason"] == SCOPE_REJECTION_REASON
        and not step["return_path"]
        and not step["return_sha256"]
    )


def lifecycle(data):
    """Validate lifecycle fields, reading a checkpoint without them as active, in memory."""
    present = LIFECYCLE_FIELDS.intersection(data)
    if not present:
        data.update(run_status="active", outcome=None, closed_at=None, purge_after=None)
    elif present != LIFECYCLE_FIELDS:
        raise Error("invalid run lifecycle fields")
    status = data["run_status"]
    if status == "active":
        if any(data[key] is not None for key in ("outcome", "closed_at", "purge_after")):
            raise Error("active run has terminal lifecycle fields")
    elif status == "closed":
        outcome = data["outcome"]
        if outcome not in {"completed", "blocked", "abandoned"}:
            raise Error("invalid closed run outcome")
        timestamp(data["closed_at"], "closed_at")
        timestamp(data["purge_after"], "purge_after")
        if data["purge_after"] != retained_until(data["closed_at"], outcome):
            raise Error("invalid closed run retention")
    else:
        raise Error("invalid run_status")
    reason = data.setdefault("close_reason", "")
    if not isinstance(reason, str) or len(reason) > 480:
        raise Error("invalid close_reason")
    return data


def active_run(data):
    if lifecycle(data)["run_status"] != "active":
        raise Error("run is closed")


def validate_steps(data, leafs):
    if data.get("retry_policy") != ESCALATING_RETRY_POLICY:
        raise Error("invalid run retry policy")
    if data.get("return_codes") not in {None, REGISTERED_RETURN_CODES}:
        raise Error("invalid run return codes")
    steps = data.get("steps")
    if not isinstance(steps, dict) or set(steps) != set(leafs):
        raise Error("blocked:plan_tampered")
    for sid, step in steps.items():
        if (
            not isinstance(step, dict)
            or step.get("id") != sid
            or step.get("status") not in STEP_STATES
            or step.get("dependencies") != leafs[sid]["dependencies"]
            or step.get("max_attempts") != leafs[sid]["max_attempts"]
            or not isinstance(step.get("attempt_count"), int)
            or isinstance(step.get("attempt_count"), bool)
            or not 0 <= step["attempt_count"] <= step["max_attempts"]
            or not isinstance(step.get("retry_allowed"), bool)
        ):
            raise Error("blocked:plan_tampered")
        assignment = step.get("current_assignment")
        assignment_fields = {"agent_id", "harness", "model_or_alias"}
        if (
            not RETRY_STATE_FIELDS.issubset(step)
            or step.get("current_tier") not in PORTABLE_TIERS
            or PORTABLE_TIERS.index(step["current_tier"])
            < PORTABLE_TIERS.index(leafs[sid]["portable_tier"])
            or not isinstance(step.get("same_tier_retry_used"), bool)
            or not isinstance(assignment, dict)
            or set(assignment) != assignment_fields
            or assignment.get("agent_id") != step.get("agent_id")
            or not isinstance(assignment.get("harness"), str)
            or not 1 <= len(assignment["harness"]) <= 160
            or not assignment["harness"].strip()
            or not isinstance(step.get("retry_remediation_path"), str)
            or not isinstance(step.get("retry_remediation_sha256"), str)
            or bool(step["retry_remediation_path"]) != bool(step["retry_remediation_sha256"])
        ):
            raise Error("blocked:plan_tampered")
        binding = step.get("capability_binding")
        if (
            not isinstance(assignment.get("model_or_alias"), str)
            or not 1 <= len(assignment["model_or_alias"]) <= 160
            or not assignment["model_or_alias"].strip()
            or not isinstance(binding, dict)
            or digest(binding) != step.get("capability_binding_sha256")
            or not valid_stored_binding(
                binding,
                data.get("plan_hash"),
                sid,
                leafs[sid],
                assignment,
            )
        ):
            raise Error("blocked:plan_tampered")
        if step["retry_remediation_path"]:
            rel(step["retry_remediation_path"], "retry remediation path")
            require_sha256(
                step["retry_remediation_sha256"],
                "blocked:plan_tampered",
            )
    # Retained provisional_v1 state stays well-formed so read-only commands can load it.
    for step in steps.values():
        for field, keys in (
            ("upstream_stale", {"step_id", "commit"}),
            ("upstream_change", {"old", "new"}),
            ("pending_acceptance", {"old", "new"}),
        ):
            value = step.get(field)
            if value is not None and not (
                isinstance(value, dict)
                and set(value) == keys
                and all(isinstance(item, str) for item in value.values())
                and all(COMMIT.fullmatch(item) or item in steps for item in value.values())
            ):
                raise Error("blocked:plan_tampered")
        base = step.get("provisional_base")
        if base is not None and not (
            isinstance(base, dict)
            and set(base) == {"step_id", "commit"}
            and base["step_id"] in steps
            and base["step_id"] in step["dependencies"]
            and isinstance(base["commit"], str)
            and COMMIT.fullmatch(base["commit"])
        ):
            raise Error("blocked:plan_tampered")
    dependency_order(steps)


def validate_events(directory, data):
    path = required_file(directory, "events.jsonl", "run events.jsonl does not exist")
    previous = 0
    # "restack" is accepted only in the history of a retained provisional_v1 run.
    actions = {
        "init-v5",
        "transition-v5",
        "record-return",
        "close-v5",
        "reopen-v5",
        "amend-v5",
        "verify-handoff",
        "record-verify",
        "record-changeset",
        "restack",
    }
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        raise Error("invalid run events") from exc
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Error("invalid run event") from exc
        if (
            not isinstance(value, dict)
            or value.get("sequence") != previous + 1
            or value.get("actor") != "parent"
            or value.get("plan_id") != data["plan_id"]
            or value.get("run_id") != data["run_id"]
            or value.get("action") not in actions
            or not isinstance(value.get("at"), str)
        ):
            raise Error("invalid run event")
        previous += 1
    if previous != data.get("event_sequence"):
        raise Error("run event sequence mismatch")


def retired_contract(directory, plan_level=False):
    """(retired, version) for a retained ledger directory of a retired contract (1-4).

    Version 1 kept checkpoint.json directly in its plan directory, so a plan-level
    checkpoint is retired whatever it holds; versions 2-4 stamp `schema` in a run
    directory's checkpoint. `version` is the recorded version, or None when it
    cannot be read. Nothing deeper is read: such a run is refused, listed and kept.
    """
    path = directory / "checkpoint.json"
    if directory.is_symlink() or path.is_symlink() or not path.is_file():
        return False, None
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        value = None
    if plan_level:
        return True, 1 if isinstance(value, dict) and value.get("schema_version") == 1 else None
    version = value.get("schema") if isinstance(value, dict) else None
    retired = isinstance(version, int) and version in RETIRED_RUN_SCHEMAS
    return retired, version if retired else None


def refuse_retired(args):
    """Refuse a command aimed at a retained run of a retired contract, before any load."""
    plan = plan_dir(args)
    retired, version = retired_contract(plan, plan_level=True)
    if not retired and args.run_id:
        retired, version = retired_contract(run_dir(args))
    if retired:
        raise Error(
            f"blocked:contract_migration_required: this run uses retired contract version "
            f"{version or 'unknown'}; finish or close it with {LAST_RETIRED_RELEASE} or earlier"
        )


def validate_run(directory, data, plan_id, run_id):
    """The single run validator for load_run, classify_run and load_predecessor_run.

    Everything but the event log: callers read their checkpoint, map errors to
    their own codes, and validate events once on their own path. Steps are
    checked against amendment-aware effective leaves, so an amended run is never
    reported as tampered.
    """
    if data.get("schema") != FORWARD_SCHEMA:
        raise Error("unknown checkpoint schema")
    if (
        data.get("plan_id") != plan_id
        or data.get("run_id") != run_id
        or data.get("retry_policy") != ESCALATING_RETRY_POLICY
        or data.get("return_codes") not in {None, REGISTERED_RETURN_CODES}
        or data.get("verify_policy") not in {None, *VERIFY_POLICIES}
        or data.get("precision_policy") not in {None, *PRECISION_POLICIES}
        or data.get("pipeline_policy") not in {None, RETAINED_PIPELINE_POLICY}
        or (data.get("host") is not None and data["host"] not in host_tiers().get("hosts", {}))
    ):
        raise Error("invalid run checkpoint")
    if len(canon(data) + b"\n") > MAX_CHECKPOINT:
        raise Error("run checkpoint exceeds bounded limit")
    plan = read_json(directory / "plan.json", "blocked:plan_tampered")
    if digest(plan) != data.get("plan_hash") or not SHA.fullmatch(data.get("plan_hash", "")):
        raise Error("blocked:plan_tampered")
    plan_result = contract.plan_validator()(
        plan, capability_binding=checkpoint_binding(data), admission=False
    )
    if (
        not plan_result.get("dispatch_ready")
        or plan_result.get("contract_version") != FORWARD_SCHEMA
    ):
        raise Error("blocked:plan_tampered")
    if set(data.get("steps", {})) != set(leaves_by_id(plan)):
        raise Error("blocked:plan_tampered")
    validate_amendment_events(directory, data)
    leafs = effective_leaves(plan, data)
    for step in data["steps"].values():
        for field, default in CLOSEOUT_FIELDS.items():
            step.setdefault(field, default)
    validate_steps(data, leafs)
    validate_retry_artifacts(directory, data)
    validate_series_handoff(directory, data, plan)
    for name in ("returns", "retry-remediations"):
        folder = directory / name
        if folder.exists() and any(
            step_dir.name not in data["steps"] for step_dir in folder.iterdir()
        ):
            raise Error(f"unexpected {name} step")
    lifecycle(data)
    return plan, leafs


def load_run(args):
    refuse_retired(args)
    parent_directory = plan_dir(args)
    if parent_directory.is_symlink() or not parent_directory.is_dir():
        raise Error("unknown run id")
    directory = run_dir(args)
    if directory.is_symlink() or not directory.is_dir():
        raise Error("unknown run id")
    safe_run_contents(directory)
    path = required_file(directory, "checkpoint.json", "unknown run id")
    data = read_json(path, "invalid run checkpoint")
    try:
        plan, leafs = validate_run(directory, data, args.plan_id, args.run_id)
    except Error as exc:
        if str(exc) == "unknown checkpoint schema":
            raise Error("invalid run checkpoint") from exc
        raise
    return directory, data, plan, leafs


def mutating_run(args):
    parent(args.actor)
    loaded = load_run(args)
    validate_events(loaded[0], loaded[1])
    active_run(loaded[1])
    require_no_retained_pipeline(loaded[1])
    return loaded


def valid_remediation(value):
    if not isinstance(value, dict) or len(canon(value)) > MAX_REMEDIATION:
        raise Error("retry-remediation-v1 exceeds 4 KiB")
    optional = {"evidence_path", "sha256"}
    if (
        set(value) - (REMEDIATION_FIELDS | optional)
        or REMEDIATION_FIELDS - set(value)
        or value.get("schema") != "retry-remediation-v1"
        or value.get("executor_mode") not in {"reuse", "fresh"}
        or value.get("target_portable_tier") not in PORTABLE_TIERS
    ):
        raise Error("invalid retry-remediation-v1 schema")
    ident(value["step_id"], "remediation step id")
    uuid4(value["prior_attempt_id"], "prior attempt id")
    require_sha256(value["prior_return_sha256"], "invalid prior return sha256")
    for field in ("diagnosis", "remediation_action"):
        if not isinstance(value[field], str) or not value[field] or len(value[field]) > 480:
            raise Error(f"retry remediation requires bounded {field}")
    if (
        not isinstance(value["next_agent_id"], str)
        or not 1 <= len(value["next_agent_id"]) <= 128
        or not value["next_agent_id"].strip()
    ):
        raise Error("retry remediation requires bounded next_agent_id")
    if (
        not isinstance(value["next_harness"], str)
        or not 1 <= len(value["next_harness"]) <= 160
        or not value["next_harness"].strip()
    ):
        raise Error("retry remediation requires bounded next_harness")
    if ("evidence_path" in value) != ("sha256" in value):
        raise Error("retry remediation evidence digest pair required")
    if "evidence_path" in value:
        rel(value["evidence_path"], "retry remediation evidence")
        require_sha256(value["sha256"], "invalid retry remediation evidence sha256")
    return value


def valid_series_handoff(value):
    if not isinstance(value, dict) or len(canon(value)) > MAX_SERIES_HANDOFF:
        raise Error("planning-series-handoff-v1 exceeds 8 KiB")
    if set(value) != SERIES_HANDOFF_FIELDS or value.get("schema") != SERIES_HANDOFF_SCHEMA:
        raise Error("invalid planning-series-handoff-v1 schema")
    ident(value["plan_id"], "series handoff plan id")
    uuid4(value["run_id"], "series handoff run id")
    ident(value["series_id"], "series handoff series id")
    slice_value = value["slice"]
    if not isinstance(slice_value, int) or isinstance(slice_value, bool) or slice_value < 1:
        raise Error("series handoff slice must be an integer >= 1")
    for field in SERIES_HANDOFF_LIST_FIELDS:
        items = value[field]
        if not isinstance(items, list) or len(items) > 16:
            raise Error(f"series handoff {field} must be a bounded array")
        for item in items:
            if not isinstance(item, str) or not 1 <= len(item) <= 480:
                raise Error(f"series handoff {field} entries must be bounded non-empty strings")
    return value


def read_series_handoff(path):
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Error("invalid planning-series-handoff-v1") from exc
    if len(raw) > MAX_SERIES_HANDOFF:
        raise Error("planning-series-handoff-v1 exceeds 8 KiB")
    return valid_series_handoff(value)


def validate_series_handoff(directory, data, plan):
    """Sibling of validate_retry_artifacts: re-verify a stamped handoff artifact.

    `load_run` calls this but not `validate_events`, so a plain event-fact record
    of the stamp alone would skip tamper detection; the file's own bytes are
    hashed and re-checked against the checkpoint stamp every load.
    """
    path = data.get("series_handoff_path", "")
    sha256 = data.get("series_handoff_sha256", "")
    if bool(path) != bool(sha256):
        raise Error("series handoff stamp requires both path and sha256")
    artifact = directory / "series-handoff.json"
    file_exists = artifact.is_file() and not artifact.is_symlink()
    if file_exists and not path:
        raise Error("series handoff artifact present without a checkpoint stamp")
    if path and not file_exists:
        raise Error("series handoff checkpoint stamp has no artifact")
    if not path:
        return
    if path != "series-handoff.json":
        raise Error("series handoff path must name the run-level artifact")
    series = plan.get("series")
    if series is None:
        raise Error("series handoff stamp present on a run whose plan has no series block")
    value = read_series_handoff(artifact)
    if (
        digest(value) != sha256
        or value["plan_id"] != data["plan_id"]
        or value["run_id"] != data["run_id"]
        or value["series_id"] != series.get("series_id")
        or value["slice"] != series.get("slice")
    ):
        raise Error("series handoff artifact digest or identity mismatch")


def validate_retry_artifacts(directory, data):
    for step in data["steps"].values():
        path = step["retry_remediation_path"]
        if not path:
            continue
        value = read_json(directory / path, "missing retry remediation artifact")
        valid_remediation(value)
        expected_path = (
            Path("retry-remediations") / step["id"] / f"{value['prior_attempt_id']}.json"
        )
        if (
            value["step_id"] != step["id"]
            or path != str(expected_path)
            or value["target_portable_tier"] != step["current_tier"]
            or value["next_agent_id"] != step["current_assignment"]["agent_id"]
            or value["next_harness"] != step["current_assignment"]["harness"]
            or digest(value) != step["retry_remediation_sha256"]
        ):
            raise Error("retry remediation artifact digest mismatch")
