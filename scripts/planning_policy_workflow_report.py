#!/usr/bin/env python3
"""Create a bounded, offline summary of fixed planning-policy evaluation trials."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA = "planning-policy-workflow-manifest/v1"
REPORT_SCHEMA = "planning-policy-workflow-report/v1"
MAX_TRIALS = 16
MAX_RECORD_BYTES = 64 * 1024
MAX_REPORT_BYTES = 16 * 1024
USAGE_FIELDS = ("input_tokens", "output_tokens", "cached_input_tokens", "total_tokens")
FORBIDDEN_FIELDS = {"transcript", "raw_transcript", "prompt", "completion", "messages", "arguments", "raw_log"}


def _fail(message: str) -> None:
    raise ValueError(message)


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"{field} must be an object")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{field} must be a nonempty string")
    return value


def _bounded_record(value: Any, field: str) -> dict[str, Any]:
    record = _object(value, field)
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RECORD_BYTES:
        _fail(f"{field} exceeds {MAX_RECORD_BYTES} bytes")
    if _contains_forbidden_field(record):
        _fail(f"{field} includes content-bearing fields")
    return record


def _contains_forbidden_field(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in FORBIDDEN_FIELDS or _contains_forbidden_field(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_field(item) for item in value)
    return False


def _usage(value: Any, field: str) -> tuple[dict[str, int | None], bool]:
    if value is None:
        return {name: None for name in USAGE_FIELDS}, False
    raw = _object(value, field)
    result: dict[str, int | None] = {}
    complete = True
    for name in USAGE_FIELDS:
        number = raw.get(name)
        if isinstance(number, bool) or (number is not None and (not isinstance(number, int) or number < 0)):
            _fail(f"{field}.{name} must be a non-negative integer or null")
        result[name] = number
        complete = complete and isinstance(number, int)
    if complete and result["total_tokens"] != result["input_tokens"] + result["output_tokens"]:
        _fail(f"{field}.total_tokens must equal input_tokens plus output_tokens")
    return result, complete


def _conditions(value: Any) -> dict[str, Any]:
    conditions = _object(value, "conditions")
    for name in ("fixture_sha256", "oracle_sha256"):
        digest = _text(conditions.get(name), f"conditions.{name}")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            _fail(f"conditions.{name} must be a lowercase sha256")
    host = _object(conditions.get("host"), "conditions.host")
    coordinator = _object(conditions.get("coordinator"), "conditions.coordinator")
    standard = _object(_object(conditions.get("worker_mapping"), "conditions.worker_mapping").get("standard"), "conditions.worker_mapping.standard")
    for field, mapping, names in (
        ("conditions.host", host, ("name", "version", "profile")),
        ("conditions.coordinator", coordinator, ("model", "effort")),
        ("conditions.worker_mapping.standard", standard, ("model", "effort")),
    ):
        for name in names:
            _text(mapping.get(name), f"{field}.{name}")
    return conditions


def _counts(value: Any) -> dict[str, int]:
    counts = _object(value, "trial.counts")
    required = {"worker_leaves", "worker_attempts", "failed_attempts", "retries", "escalations", "dispatches"}
    if set(counts) != required:
        _fail("trial.counts has an invalid field set")
    for name, number in counts.items():
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            _fail(f"trial.counts.{name} must be a non-negative integer")
    if counts["worker_leaves"] > 2 or counts["worker_attempts"] > 4:
        _fail("trial.counts exceeds approved worker bounds")
    if counts["failed_attempts"] > counts["worker_attempts"] or counts["retries"] > counts["worker_attempts"]:
        _fail("trial.counts is internally inconsistent")
    return counts


def _sources(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        _fail("trial.sources must be a nonempty list")
    summaries: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, source_value in enumerate(value):
        source = _object(source_value, f"trial.sources[{index}]")
        if set(source) != {"path", "sha256"}:
            _fail("trial source has an invalid field set")
        path = _text(source.get("path"), "trial source path")
        digest = _text(source.get("sha256"), "trial source sha256")
        if Path(path).is_absolute() or ".." in Path(path).parts or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            _fail("trial source must have a safe relative path and lowercase sha256")
        if path in seen:
            _fail("duplicate trial source path")
        seen.add(path)
        summaries.append({"path": path, "sha256": digest})
    return summaries


def _validate_trial(value: Any, seen_trials: set[str], seen_actors: set[tuple[str, str]]) -> dict[str, Any]:
    trial = _bounded_record(value, "trial")
    trial_id = _text(trial.get("trial_id"), "trial.trial_id")
    if trial_id in seen_trials:
        _fail("duplicate trial identity")
    seen_trials.add(trial_id)
    variant = trial.get("variant")
    if variant not in {"baseline", "candidate"}:
        _fail("trial.variant must be baseline or candidate")
    if not isinstance(trial.get("sequence"), int) or trial["sequence"] < 1:
        _fail("trial.sequence must be a positive integer")
    conditions = _conditions(trial.get("conditions"))
    limits = _object(trial.get("limits"), "trial.limits")
    if limits != {"worker_leaves": 2, "worker_attempts": 4, "minutes": 15}:
        _fail("trial limits must be exactly 2 worker_leaves, 4 worker_attempts, and 15 minutes")
    counts = _counts(trial.get("counts"))
    sources = _sources(trial.get("sources"))
    actors = trial.get("actors")
    if not isinstance(actors, list) or not actors:
        _fail("trial.actors must be a nonempty list")
    actor_summaries = []
    roles: set[str] = set()
    total = 0
    complete_usage = True
    for index, actor_value in enumerate(actors):
        actor = _object(actor_value, f"trial.actors[{index}]")
        actor_id = _text(actor.get("actor_id"), "actor.actor_id")
        step_id = _text(actor.get("step_id"), "actor.step_id")
        attempt_id = _text(actor.get("attempt_id"), "actor.attempt_id")
        identity = (actor_id, attempt_id)
        if identity in seen_actors:
            _fail("duplicate actor identity")
        seen_actors.add(identity)
        role = actor.get("role")
        if role not in {"coordinator", "worker"}:
            _fail("actor.role must be coordinator or worker")
        roles.add(role)
        usage, complete = _usage(actor.get("usage"), "actor.usage")
        complete_usage = complete_usage and complete
        if complete:
            total += int(usage["total_tokens"])
        actor_summaries.append({"actor_id": actor_id, "step_id": step_id, "attempt_id": attempt_id, "role": role, "usage": usage})
    if roles != {"coordinator", "worker"}:
        _fail("trial actors must include coordinator and worker")
    execution = _object(trial.get("execution"), "trial.execution")
    outcome = execution.get("outcome")
    if outcome not in {"completed", "failed", "blocked", "oversized"}:
        _fail("execution.outcome is invalid")
    if execution.get("lifecycle") not in {"cleaned", "not_cleaned"}:
        _fail("execution.lifecycle is invalid")
    if execution.get("oracle") != "passed":
        _fail("execution.oracle must be passed; oracle failures are not admissible")
    elapsed = execution.get("elapsed_seconds")
    if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or elapsed < 0:
        _fail("execution.elapsed_seconds must be non-negative")
    return {
        "trial_id": trial_id,
        "variant": variant,
        "sequence": trial["sequence"],
        "_condition_key": json.dumps(conditions, sort_keys=True, separators=(",", ":")),
        "counts": counts,
        "evidence_source_count": len(sources),
        "actors": actor_summaries,
        "execution": {"outcome": outcome, "lifecycle": execution["lifecycle"], "oracle": "passed", "elapsed_seconds": elapsed},
        "usage": {"total_tokens": total if complete_usage else None, "complete": complete_usage},
    }


def _condition_key(trial: dict[str, Any]) -> str:
    return str(trial["_condition_key"])


def _median(values: list[int]) -> int | float:
    return statistics.median(values)


def build_report(manifest: Any) -> dict[str, Any]:
    source = _object(manifest, "manifest")
    if source.get("schema") != MANIFEST_SCHEMA:
        _fail(f"manifest.schema must be {MANIFEST_SCHEMA}")
    raw_trials = source.get("trials")
    if not isinstance(raw_trials, list) or not raw_trials or len(raw_trials) > MAX_TRIALS:
        _fail(f"manifest.trials must contain 1 through {MAX_TRIALS} records")
    seen_trials: set[str] = set()
    seen_actors: set[tuple[str, str]] = set()
    trials = [_validate_trial(value, seen_trials, seen_actors) for value in raw_trials]
    trials.sort(key=lambda item: item["sequence"])
    variants: dict[str, dict[str, Any]] = {}
    for variant in ("baseline", "candidate"):
        subset = [item for item in trials if item["variant"] == variant]
        totals = [item["usage"]["total_tokens"] for item in subset if item["usage"]["complete"]]
        variants[variant] = {"trial_count": len(subset), "successful_count": sum(item["execution"]["outcome"] == "completed" and item["execution"]["lifecycle"] == "cleaned" for item in subset), "median_total_tokens": _median(totals) if totals else None, "repeat_range_total_tokens": [min(totals), max(totals)] if totals else None}
    reasons: list[str] = []
    if any(not item["usage"]["complete"] for item in trials):
        reasons.append("missing_complete_usage")
    if len({_condition_key(item) for item in trials}) > 1:
        reasons.append("mismatched_conditions")
    if any(item["execution"]["outcome"] != "completed" or item["execution"]["lifecycle"] != "cleaned" for item in trials):
        reasons.append("non_successful_trial")
    paired_deltas: list[dict[str, int | str]] = []
    baselines = [item for item in trials if item["variant"] == "baseline"]
    candidates = [item for item in trials if item["variant"] == "candidate"]
    if not reasons:
        for pair, (baseline, candidate) in enumerate(zip(baselines, candidates), start=1):
            paired_deltas.append({"pair": pair, "baseline_trial_id": baseline["trial_id"], "candidate_trial_id": candidate["trial_id"], "total_tokens_delta": int(candidate["usage"]["total_tokens"]) - int(baseline["usage"]["total_tokens"])})
    for trial in trials:
        trial.pop("_condition_key")
    comparison = {"comparable": not reasons, "reasons": reasons, "paired_deltas": paired_deltas}
    return {"schema": REPORT_SCHEMA, "trial_count": len(trials), "trials": trials, "variants": variants, "comparison": comparison, "limits": {"max_trials": MAX_TRIALS, "max_trial_bytes": MAX_RECORD_BYTES, "max_report_bytes": MAX_REPORT_BYTES}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
        report = build_report(manifest)
        encoded = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(encoded) > MAX_REPORT_BYTES:
            _fail(f"report exceeds {MAX_REPORT_BYTES} bytes")
        arguments.output.write_bytes(encoded + b"\n")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        sys.stderr.write(f"planning-policy-workflow-report: {error}\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
