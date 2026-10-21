"""Planning ledger tracing: opt-in trace counters."""

from __future__ import annotations

import uuid

from . import contract, core
from .vocabulary import MAX_USAGE, MAX_USAGE_TOKENS
from .core import Error, digest, parent, proxy_tokens, read_json
from .store import valid_usage_summary, write
from .checkpoint import active_run, load_run

__all__ = [
    "usage_path",
    "trace_run",
    "trace_result",
    "trace_init",
    "trace_record",
    "trace_show",
    "trace_close",
]


def usage_path(directory):
    return directory / "usage"


def trace_run(args, require_usage=True, require_open=False):
    parent(args.actor)
    directory, data, plan, leafs = load_run(args)
    usage = usage_path(directory)
    if require_usage and not usage.exists():
        raise Error("trace-init is required")
    metadata = read_json(usage / "trace.json", "invalid usage trace") if usage.exists() else None
    if require_open and metadata and metadata.get("closed_at"):
        raise Error("usage trace is closed")
    return directory, data, plan, leafs, usage, metadata


def trace_result(action, data, **facts):
    return {
        "ok": True,
        "action": action,
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        **facts,
    }


def trace_init(args):
    directory, data, _plan, _leafs, usage, _metadata = trace_run(args, require_usage=False)
    active_run(data)
    if usage.exists():
        raise Error("tracing is already initialized")
    write(
        usage / "trace.json",
        {"schema": "planning-usage-trace-v1", "initialized_at": core.now(), "closed_at": ""},
        MAX_USAGE,
    )
    return trace_result("trace-init", data)


def trace_record(args):
    directory, data, _plan, _leafs, _usage, _metadata = trace_run(args, require_open=True)
    value = valid_usage_summary(read_json(args.usage_file, "cannot read usage file"))
    supplied_identity = (value["run_id"],)
    checkpoint_identity = (data["run_id"],)
    if supplied_identity == checkpoint_identity:
        pass
    else:
        raise Error("usage run identity mismatch")
    parent_identity = value["step_id"] == "parent" and value["attempt_id"] == "run"
    if value["actor"] == "parent" and not parent_identity:
        raise Error("parent usage identity must be parent/run")
    if value["actor"] == "worker":
        step = data["steps"].get(value["step_id"])
        if step is None or not step["attempt_id"] or value["attempt_id"] != step["attempt_id"]:
            raise Error("worker usage attempt identity mismatch")
        assignment = step["current_assignment"]
        if value["harness"] != assignment["harness"]:
            raise Error("worker usage harness provenance mismatch")
        if value["model"] != step["assignment"]["model_or_alias"]:
            raise Error("worker usage model provenance mismatch")
    if value["actor"] not in {"parent", "worker"}:
        raise Error("usage actor must be parent or worker")
    record_id = str(uuid.uuid4())
    relative = f"usage/records/{record_id}.json"
    write(directory / relative, value, MAX_USAGE)
    return trace_result(
        "trace-record",
        data,
        record_path=relative,
        record_sha256=digest(value),
    )


def trace_show(args):
    _directory, data, plan, _leafs, usage, _metadata = trace_run(args)
    records_dir = usage / "records"
    values = (
        []
        if not records_dir.exists()
        else [
            valid_usage_summary(read_json(path, "invalid usage record"))
            for path in sorted(records_dir.iterdir())
        ]
    )
    stages = {}
    cycles = set()
    totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    provenance = set()
    for value in values:
        stage = stages.setdefault(value["stage"], {"records": 0, "total_tokens": 0})
        stage["records"] += 1
        stage["total_tokens"] += value["total_tokens"]
        cycles.add((value["step_id"], value["attempt_id"]))
        provenance.add((value["harness"], value["model"]))
        for key in totals:
            totals[key] += value[key]
    forecast = contract.plan_validator()(plan)["cost_advisory"]
    comparison = "indeterminate:forecast"
    findings = []
    declared = plan.get("execution_cost", {}).get("declared_model_tokens", {})
    worker_ranges = declared.get("worker_attempts") if isinstance(declared, dict) else None
    if (
        values
        and all(value["actor"] == "worker" for value in values)
        and isinstance(worker_ranges, dict)
    ):
        cycle_keys = {(value["step_id"], value["attempt_id"]) for value in values}
        ranges = [worker_ranges.get(step_id) for step_id, _attempt_id in cycle_keys]
        if all(
            isinstance(value, dict)
            and set(value) == {"low", "expected", "high"}
            and all(isinstance(value[key], int) for key in value)
            for value in ranges
        ):
            low = sum(value["low"] for value in ranges)
            high = sum(value["high"] for value in ranges)
            observed = totals["total_tokens"]
            comparison = {"lane": "worker_attempts", "low": low, "observed": observed, "high": high}
            if observed < low or observed > high:
                findings.append("PLANCOST-COMPARABLE-OBSERVED-DRIFT")
    result = {
        "ok": True,
        "schema": "planning-usage-advisory-v1",
        "mode": "advisory",
        "plan_id": data["plan_id"],
        "run_id": data["run_id"],
        "records": len(values),
        "cycles": len(cycles),
        "stages": stages,
        "provider_measured": totals,
        "provenance": [
            {"harness": harness, "model": model} for harness, model in sorted(provenance)
        ],
        "forecast_comparison": (
            comparison
            if comparison != "indeterminate:forecast"
            else (
                "indeterminate:provenance"
                if forecast.get("declared_total_run") is not None
                else comparison
            )
        ),
        "findings": findings,
    }
    while proxy_tokens(result) > MAX_USAGE_TOKENS and result["provenance"]:
        result["provenance"].pop()
    result["summary_proxy_tokens"] = proxy_tokens(result)
    return result


def trace_close(args):
    _directory, data, _plan, _leafs, usage, metadata = trace_run(args)
    if metadata.get("closed_at"):
        raise Error("usage trace is already closed")
    metadata["closed_at"] = core.now()
    write(usage / "trace.json", metadata, MAX_USAGE)
    return trace_result("trace-close", data)
