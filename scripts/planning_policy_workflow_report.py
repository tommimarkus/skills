#!/usr/bin/env python3
"""Create a bounded, offline summary of fixed planning-policy evaluation trials."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA = "planning-policy-workflow-manifest/v1"
REPORT_SCHEMA = "planning-policy-workflow-report/v1"
MAX_TRIALS = 16
MAX_RECORD_BYTES = 64 * 1024
MAX_REPORT_BYTES = 16 * 1024
MAX_MANIFEST_BYTES = MAX_TRIALS * MAX_RECORD_BYTES + 4096
USAGE_FIELDS = ("input_tokens", "output_tokens", "cached_input_tokens", "total_tokens")
FORBIDDEN_FIELDS = {"transcript", "transcripts", "raw_transcript", "prompt", "prompts", "completion", "completions", "messages", "arguments", "results", "raw_log", "raw_logs"}


def _fail(message: str) -> None:
    raise ValueError(message)


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"{field} must be an object")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 512 or any(ord(c) < 32 for c in value):
        _fail(f"{field} must be a nonempty string")
    return value


def _fields(value: dict[str, Any], allowed: set[str], field: str) -> None:
    if set(value) != allowed:
        _fail(f"{field} has an invalid field set")


def _revision(value: Any) -> str:
    text = _text(value, "policy revision")
    if len(text) not in {40, 64} or any(c not in "0123456789abcdef" for c in text):
        _fail("policy revision must be a Git object identity")
    return text


def _bounded_record(value: Any, field: str) -> dict[str, Any]:
    record = _object(value, field)
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
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
    _fields(raw, set(USAGE_FIELDS), field)
    result: dict[str, int | None] = {}
    complete = True
    for name in USAGE_FIELDS:
        number = raw.get(name)
        if isinstance(number, bool) or (number is not None and (not isinstance(number, int) or number < 0)):
            _fail(f"{field}.{name} must be a non-negative integer or null")
        result[name] = number
        complete = complete and isinstance(number, int)
    if all(result[k] is not None for k in ("input_tokens", "output_tokens", "total_tokens")) and result["total_tokens"] != result["input_tokens"] + result["output_tokens"]:
        _fail(f"{field}.total_tokens must equal input_tokens plus output_tokens")
    if result["cached_input_tokens"] is not None and result["input_tokens"] is not None and result["cached_input_tokens"] > result["input_tokens"]:
        _fail(f"{field}.cached_input_tokens exceeds input_tokens")
    return result, complete


def _conditions(value: Any) -> dict[str, Any]:
    conditions = _object(value, "conditions")
    _fields(conditions, {"fixture_sha256", "oracle_sha256", "host", "coordinator", "worker_mapping"}, "conditions")
    for name in ("fixture_sha256", "oracle_sha256"):
        digest = _text(conditions.get(name), f"conditions.{name}")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            _fail(f"conditions.{name} must be a lowercase sha256")
    host = _object(conditions.get("host"), "conditions.host")
    coordinator = _object(conditions.get("coordinator"), "conditions.coordinator")
    mapping = _object(conditions.get("worker_mapping"), "conditions.worker_mapping")
    if not mapping or set(mapping) - {"mechanical", "standard", "analytical", "deep"}:
        _fail("conditions.worker_mapping has invalid tiers")
    for tier, assignment in mapping.items():
        assignment = _object(assignment, f"worker_mapping.{tier}")
        _fields(assignment, {"model", "effort"}, f"worker_mapping.{tier}")
        for key in ("model", "effort"):
            _text(assignment[key], f"worker_mapping.{tier}.{key}")
    _fields(host, {"name", "version", "profile"}, "conditions.host")
    _fields(coordinator, {"model", "effort"}, "conditions.coordinator")
    for field, mapping, names in (
        ("conditions.host", host, ("name", "version", "profile")),
        ("conditions.coordinator", coordinator, ("model", "effort")),
    ):
        for name in names:
            _text(mapping.get(name), f"{field}.{name}")
    return conditions


def _counts(value: Any) -> dict[str, int | None]:
    counts = _object(value, "trial.counts")
    required = {"worker_leaves", "worker_attempts", "failed_attempts", "retries", "escalations", "dispatches"}
    if set(counts) != required:
        _fail("trial.counts has an invalid field set")
    for name, number in counts.items():
        if number is not None and (isinstance(number, bool) or not isinstance(number, int) or number < 0):
            _fail(f"trial.counts.{name} must be a non-negative integer or null")
    if (counts["worker_leaves"] or 0) > 2 or (counts["worker_attempts"] or 0) > 4:
        _fail("trial.counts exceeds approved worker bounds")
    if counts["worker_attempts"] is not None:
        for name in ("failed_attempts", "retries", "escalations", "worker_leaves", "dispatches"):
            if counts[name] is not None and counts[name] > counts["worker_attempts"]:
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


def _validate_trial(value: Any, seen_trials: set[str], seen_actors: set[str], revisions: dict[str, str]) -> dict[str, Any]:
    trial = _bounded_record(value, "trial")
    _fields(trial, {"trial_id", "variant", "sequence", "policy_revision", "roster_complete", "conditions", "limits", "counts", "sources", "actors", "execution"}, "trial")
    trial_id = _text(trial.get("trial_id"), "trial.trial_id")
    if trial_id in seen_trials:
        _fail("duplicate trial identity")
    seen_trials.add(trial_id)
    variant = trial.get("variant")
    if variant not in {"baseline", "candidate"}:
        _fail("trial.variant must be baseline or candidate")
    if isinstance(trial.get("sequence"), bool) or not isinstance(trial.get("sequence"), int) or trial["sequence"] < 1:
        _fail("trial.sequence must be a positive integer")
    if _revision(trial.get("policy_revision")) != revisions[variant]:
        _fail("trial policy revision conflicts with variant identity")
    if not isinstance(trial.get("roster_complete"), bool):
        _fail("trial.roster_complete must be boolean")
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
    roles: list[str] = []
    totals = {name: 0 for name in USAGE_FIELDS}
    complete_usage = trial["roster_complete"]
    mapping_matches = True
    for index, actor_value in enumerate(actors):
        actor = _object(actor_value, f"trial.actors[{index}]")
        _fields(actor, {"actor_id", "step_id", "attempt_id", "role", "model", "effort", "tier", "coverage_complete", "usage"}, "actor")
        actor_id = _text(actor.get("actor_id"), "actor.actor_id")
        step_id = _text(actor.get("step_id"), "actor.step_id")
        attempt_id = _text(actor.get("attempt_id"), "actor.attempt_id")
        if actor_id in seen_actors:
            _fail("duplicate actor identity")
        seen_actors.add(actor_id)
        role = actor.get("role")
        if role not in {"coordinator", "worker"}:
            _fail("actor.role must be coordinator or worker")
        roles.append(role)
        if not isinstance(actor["coverage_complete"], bool):
            _fail("actor.coverage_complete must be boolean")
        for name in ("model", "effort"):
            if actor[name] is not None:
                _text(actor[name], f"actor.{name}")
        if actor["tier"] is not None and actor["tier"] not in {"mechanical", "standard", "analytical", "deep"}:
            _fail("invalid actor tier")
        expected = conditions["coordinator"] if role == "coordinator" else conditions["worker_mapping"].get(actor["tier"], {})
        actor_mapping_matches = bool(expected) and all(actor[name] == expected.get(name) for name in ("model", "effort"))
        mapping_matches = mapping_matches and actor_mapping_matches
        usage, complete = _usage(actor.get("usage"), "actor.usage")
        complete_usage = complete_usage and complete and actor["coverage_complete"]
        if complete:
            for name in USAGE_FIELDS:
                totals[name] += int(usage[name])
        summary = {"actor_id": actor_id, "step_id": step_id, "attempt_id": attempt_id, "role": role, "coverage_complete": complete and actor["coverage_complete"], "usage": usage}
        if not actor_mapping_matches:
            summary["mapping_mismatch"] = {"model": actor["model"], "effort": actor["effort"]}
        actor_summaries.append(summary)
    if roles.count("coordinator") != 1:
        _fail("trial actors must include exactly one coordinator")
    complete_usage = complete_usage and roles.count("worker") == counts["worker_attempts"]
    complete_usage = complete_usage and len({a["step_id"] for a in actors if a["role"] == "worker"}) == counts["worker_leaves"]
    execution = _object(trial.get("execution"), "trial.execution")
    _fields(execution, {"outcome", "lifecycle", "oracle", "elapsed_seconds"}, "execution")
    outcome = execution.get("outcome")
    if outcome not in {"completed", "failed", "blocked", "oversized"}:
        _fail("execution.outcome is invalid")
    if execution.get("lifecycle") not in {"cleaned", "not_cleaned"}:
        _fail("execution.lifecycle is invalid")
    if execution.get("oracle") not in {"passed", "failed", "not_run", "unknown"}:
        _fail("execution.oracle is invalid")
    elapsed = execution.get("elapsed_seconds")
    if elapsed is not None and (isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0):
        _fail("execution.elapsed_seconds must be finite non-negative or null")
    return {
        "trial_id": trial_id,
        "variant": variant,
        "sequence": trial["sequence"],
        "_mapping_matches": mapping_matches,
        "_condition_key": json.dumps(conditions, sort_keys=True, separators=(",", ":")),
        "counts": counts,
        "sources": sources,
        "actors": actor_summaries,
        "execution": {"outcome": outcome, "lifecycle": execution["lifecycle"], "oracle": execution["oracle"], "elapsed_seconds": elapsed},
        "usage": {**{name: value if complete_usage else None for name, value in totals.items()}, "complete": complete_usage},
    }


def _condition_key(trial: dict[str, Any]) -> str:
    return str(trial["_condition_key"])


def _median(values: list[int]) -> int | float:
    return statistics.median(values)


def build_report(manifest: Any) -> dict[str, Any]:
    source = _object(manifest, "manifest")
    _fields(source, {"schema", "revisions", "trials"}, "manifest")
    if source.get("schema") != MANIFEST_SCHEMA:
        _fail(f"manifest.schema must be {MANIFEST_SCHEMA}")
    revisions = _object(source.get("revisions"), "revisions")
    _fields(revisions, {"baseline", "candidate"}, "revisions")
    for revision in revisions.values():
        _revision(revision)
    raw_trials = source.get("trials")
    if not isinstance(raw_trials, list) or not raw_trials or len(raw_trials) > MAX_TRIALS:
        _fail(f"manifest.trials must contain 1 through {MAX_TRIALS} records")
    seen_trials: set[str] = set()
    seen_actors: set[str] = set()
    trials = [_validate_trial(value, seen_trials, seen_actors, revisions) for value in raw_trials]
    if len({item["sequence"] for item in trials}) != len(trials):
        _fail("duplicate trial sequence")
    trials.sort(key=lambda item: item["sequence"])
    variants: dict[str, dict[str, Any]] = {}
    for variant in ("baseline", "candidate"):
        subset = [item for item in trials if item["variant"] == variant]
        totals = [item["usage"]["total_tokens"] for item in subset if item["usage"]["complete"]]
        variants[variant] = {"trial_count": len(subset), "successful_count": sum(item["execution"]["outcome"] == "completed" and item["execution"]["lifecycle"] == "cleaned" and item["execution"]["oracle"] == "passed" for item in subset), "median_total_tokens": _median(totals) if totals else None, "repeat_range_total_tokens": [min(totals), max(totals)] if totals else None}
    reasons: list[str] = []
    if any(not item["usage"]["complete"] for item in trials):
        reasons.append("missing_complete_usage")
    if len({_condition_key(item) for item in trials}) > 1:
        reasons.append("mismatched_conditions")
    if any(not item["_mapping_matches"] for item in trials):
        reasons.append("actor_mapping_mismatch")
    if any(item["execution"]["outcome"] != "completed" or item["execution"]["lifecycle"] != "cleaned" or item["execution"]["oracle"] != "passed" for item in trials):
        reasons.append("non_successful_trial")
    if any(None in item["counts"].values() or item["execution"]["elapsed_seconds"] is None for item in trials):
        reasons.append("missing_execution_evidence")
    if any((item["execution"]["elapsed_seconds"] or 0) > 900 for item in trials):
        reasons.append("trial_time_limit")
    paired_deltas: list[dict[str, int | str]] = []
    baselines = [item for item in trials if item["variant"] == "baseline"]
    candidates = [item for item in trials if item["variant"] == "candidate"]
    if not baselines or len(baselines) != len(candidates):
        reasons.append("unpaired_variants")
    if not reasons:
        for pair, (baseline, candidate) in enumerate(zip(baselines, candidates), start=1):
            paired_deltas.append({"pair": pair, "baseline_trial_id": baseline["trial_id"], "candidate_trial_id": candidate["trial_id"], "total_tokens_delta": int(candidate["usage"]["total_tokens"]) - int(baseline["usage"]["total_tokens"])})
    for trial in trials:
        trial.pop("_condition_key")
        trial.pop("_mapping_matches")
        trial.pop("sequence")  # Array order carries the validated trial sequence.
    if reasons:
        for summary in variants.values():
            summary["median_total_tokens"] = None
            summary["repeat_range_total_tokens"] = None
    comparison = {"comparable": not reasons, "reasons": reasons, "paired_deltas": paired_deltas}
    report = {"schema": REPORT_SCHEMA, "revisions": revisions, "conditions": raw_trials[0]["conditions"] if len({json.dumps(t["conditions"], sort_keys=True) for t in raw_trials}) == 1 else None, "trial_count": len(trials), "trials": trials, "variants": variants, "comparison": comparison, "limits": {"max_trials": MAX_TRIALS, "max_trial_bytes": MAX_RECORD_BYTES, "max_report_bytes": MAX_REPORT_BYTES}}
    if len(json.dumps(report, separators=(",", ":"), allow_nan=False).encode("utf-8")) + 1 > MAX_REPORT_BYTES:
        _fail(f"report exceeds {MAX_REPORT_BYTES} bytes")
    return report


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON field")
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        with arguments.manifest.open("rb") as stream:
            raw = stream.read(MAX_MANIFEST_BYTES + 1)
        if len(raw) > MAX_MANIFEST_BYTES:
            _fail("manifest exceeds bounded input size")
        manifest = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=lambda _: _fail("nonfinite JSON value"))
        report = build_report(manifest)
        encoded = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(encoded) > MAX_REPORT_BYTES:
            _fail(f"report exceeds {MAX_REPORT_BYTES} bytes")
        arguments.output.write_bytes(encoded + b"\n")
    except (OSError, ValueError, RecursionError) as error:
        sys.stderr.write(f"planning-policy-workflow-report: {error}\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
