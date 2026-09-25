#!/usr/bin/env python3
"""Opt-in fresh-context forward evaluation for planning-policy host mappings."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EVALS = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/references/evals"
FIXTURES = REPO_ROOT / "tests/planning_policy_forward"
CODEX_ADAPTER = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/extensions/codex.md"
POLICY_PLUGIN = REPO_ROOT / "souroldgeezer-policy"
MAPPINGS = {
    "claude": {
        "mechanical": ("haiku", "low"), "standard": ("sonnet", "medium"),
        "analytical": ("opus", "high"), "deep": ("opus", "xhigh"),
    },
    "codex": {
        "mechanical": ("gpt-5.6-luna", "low"), "standard": ("gpt-5.6-terra", "medium"),
        "analytical": ("gpt-5.6-sol", "high"), "deep": ("gpt-5.6-sol", "xhigh"),
    },
}
MAX_TIMEOUT_SECONDS = 180
CONTRACT_SCRIPT = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts/validate_plan_contract.py"
LEDGER_SCRIPT = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py"


def load_contract(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


plan_contract = load_contract("planning_policy_forward_plan_contract", CONTRACT_SCRIPT)
ledger = load_contract("planning_policy_forward_ledger", LEDGER_SCRIPT)

FINAL_SCHEMA = ledger.bounded_return_schema()


def bound_value(value: Any) -> Any:
    if isinstance(value, str):
        return value[:256]
    if isinstance(value, list):
        return [bound_value(item) for item in value[:20]]
    if isinstance(value, dict):
        return {str(key)[:80]: bound_value(item) for key, item in list(value.items())[:20]}
    return value


def load_cases() -> list[dict[str, Any]]:
    return [json.loads(line) for line in (EVALS / "forward-cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def synthetic_id(*parts: Any) -> str:
    """Stable valid UUID4 identity for a repeatable synthetic attempt."""
    seed = hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).digest()
    return str(uuid.UUID(bytes=seed[:16], version=4))


def handoff_for(case: dict[str, Any], harness: str, attempt: int) -> dict[str, Any]:
    """Build one complete v5 plan, binding, and assigned attempt for a host."""
    initial_tier = case.get("initial_tier", case["tier"])
    requirements = case.get("capability_requirements", {"baseline": "plan-step-base-v1", "additional": []})
    leaf = {key: case[key] for key in ("id", "dependencies", "task", "boundary", "read_set", "write_set", "settled_decisions", "size", "worktree_owner", "acceptance_command", "return_contract", "stop_conditions")}
    leaf.update(portable_tier=initial_tier, work_unit_id=f"{case['id']}-outcome", max_attempts=case["attempts"], capability_requirements=requirements)
    if initial_tier in {"analytical", "deep"}:
        leaf["irreducible_unknown_or_risk"] = case.get("irreducible_unknown_or_risk", "Synthetic fixture requires bounded evidence-led analysis.")
    plan = {"contract_version": 5, "objective": case["task"], "scope_summary": case["boundary"], "approved_decisions": ["Run only the named synthetic fixture and its acceptance check."], "work_units": [{"id": leaf["work_unit_id"], "original_size": case["size"], "cohesive_outcome": case["task"], "decomposition": {"shape": "single"}}], "leaves": [leaf]}
    if initial_tier in {"analytical", "deep"}:
        plan["analytical_heavy_exception"] = {"rationale": "This synthetic fixture isolates one evidence-led analytical outcome.", "user_approved_by": "synthetic fixture author"}
    model, effort = MAPPINGS[harness][case["tier"]]
    binding = {"schema": "planning-capability-binding-v1", "plan_sha256": plan_contract.canonical_plan_sha256(plan), "bindings": [{"step_id": case["id"], "host": harness, "executor": model, "requirements": requirements, "evidence": [f"Synthetic {harness} host mapping selects {model}/{effort} for this fixture."]}]}
    verdict = plan_contract.validate(plan, binding)
    if not verdict["dispatch_ready"]:
        raise ValueError(f"invalid synthetic assignment {case['id']}: {verdict['errors']}")
    omitted = case.get("intentionally_missing_input", [])
    assigned_leaf = {key: value for key, value in leaf.items() if key not in omitted}
    handoff = {"contract_version": 5, "plan": plan, "plan_sha256": binding["plan_sha256"], "capability_binding": binding, "run_id": synthetic_id(case["id"], harness, "run"), "step_id": case["id"], "agent_id": f"forward-{harness}-{case['id']}-{attempt}", "attempt_id": synthetic_id(case["id"], harness, attempt), "work_unit": plan["work_units"][0], "leaf": assigned_leaf, "portable_tier": case["tier"], "executor": model, "effort": effort}
    if omitted:
        handoff["intentionally_missing_input"] = omitted
    if "retry_remediation" in case:
        remediation = dict(case["retry_remediation"])
        remediation["prior_attempt_id"] = synthetic_id(case["id"], harness, attempt - 1)
        remediation["next_agent_id"] = handoff["agent_id"]
        remediation["next_harness"] = harness
        handoff["retry_remediation"] = remediation
    return handoff


def case_for_attempt(case: dict[str, Any], attempt: int) -> dict[str, Any]:
    """Apply a ledger-selected chained-attempt target without retaining history."""
    sequence = case.get("attempt_sequence")
    if sequence is None:
        return case
    selected = sequence[attempt - 1]
    derived = {key: value for key, value in case.items() if key != "attempt_sequence"}
    derived.update(selected)
    derived["initial_tier"] = case["tier"]
    return derived


def build_prompt(case: dict[str, Any], harness: str, workdir: Path, attempt: int = 1) -> str:
    adapter = CODEX_ADAPTER.read_text(encoding="utf-8") if harness == "codex" else ""
    assignment = handoff_for(case, harness, attempt)
    binding = assignment["capability_binding"]
    remediation = assignment.get("retry_remediation")
    step = {
        "id": assignment["step_id"], "status": "in_progress",
        "agent_id": assignment["agent_id"], "attempt_id": assignment["attempt_id"],
        "assignment": {"worktree": str(workdir.resolve())},
        "current_assignment": {"agent_id": assignment["agent_id"], "harness": harness,
                               "model_or_alias": assignment["executor"]},
        "current_tier": assignment["portable_tier"],
        "capability_binding": binding, "capability_binding_sha256": ledger.digest(binding),
        "retry_remediation_path": "retry.json" if remediation else "",
        "retry_remediation_sha256": ledger.digest(remediation) if remediation else "",
    }
    packet = ledger.build_worker_handoff(assignment["plan"], step, case["id"],
                                         assignment["run_id"], remediation)
    # Deliberately incomplete negative cases still omit the assigned input;
    # the missing field must not leak through a full-plan copy.
    for field in case.get("intentionally_missing_input", []):
        packet["leaf"].pop(field, None)
    packet["handoff_sha256"] = ledger.worker_handoff_digest(packet)
    contract = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    prefix = f"Shipped Codex planning-policy adapter follows:\n{adapter}\n\n" if adapter else ""
    instruction = case.get("prompt", "Complete the assigned task and its acceptance check.")
    return (f"{prefix}Execute this approved planning-policy packet in the isolated synthetic repository {workdir}:\n"
            f"{contract}\n\n{instruction} Work only in that repository. Do not use network or alter files outside it. "
            "Return only the required bounded JSON object.")


def bounded_return(value: Any, assignment: dict[str, Any]) -> dict[str, Any] | None:
    """Validate the complete host result before selecting comparison facts."""
    step = {"id": assignment["step_id"], "agent_id": assignment["agent_id"], "attempt_id": assignment["attempt_id"]}
    try:
        return ledger.valid_return(value, {}, step, assignment["plan"]["leaves"][0])
    except (ledger.Error, TypeError, ValueError):
        return None


def return_summary(returned: dict[str, Any] | None) -> dict[str, Any] | None:
    """Persist comparison facts, never a host transcript or prior-return body."""
    if returned is None:
        return None
    return {
        "status": returned["status"],
        "changed_path_count": len(returned["changed_paths"]),
        "acceptance": {key: returned["acceptance"][key] for key in ("exit_code", "summary", "evidence_path", "sha256") if key in returned["acceptance"]},
        "blocker_codes": [blocker["code"] for blocker in returned["blockers"]],
        "blocker_evidence": [{key: blocker[key] for key in ("code", "evidence_path", "sha256") if key in blocker} for blocker in returned["blockers"] if "evidence_path" in blocker],
    }


def remediation_summary(remediation: Any) -> dict[str, Any] | None:
    """Keep only the bounded ledger artifact fields needed for comparison."""
    if not isinstance(remediation, dict):
        return None
    fields = (
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
        "evidence_path",
        "sha256",
    )
    return bound_value({field: remediation[field] for field in fields if field in remediation})


def is_secure_output_dir(path: Path) -> bool:
    """Live evidence must go to an existing private, non-world-writable path."""
    try:
        mode = path.stat().st_mode
    except OSError:
        return False
    return path.is_absolute() and path.is_dir() and not (mode & 0o077)


def command_for(harness: str, model: str, effort: str, prompt: str, schema_path: Path, last_message_path: Path, claude_max_budget_usd: float) -> list[str]:
    if harness == "claude":
        agent = f"plan-step-{next(tier for tier, mapping in MAPPINGS['claude'].items() if mapping == (model, effort))}"
        return ["claude", "-p", "--plugin-dir", str(POLICY_PLUGIN), "--agent", agent, "--no-session-persistence", "--permission-mode", "acceptEdits", "--model", model, "--effort", effort, "--max-budget-usd", str(claude_max_budget_usd), "--output-format", "json", "--json-schema", json.dumps(FINAL_SCHEMA, separators=(",", ":")), prompt]
    # --approve-for-me selects the workspace-write sandbox in current Codex.
    # Passing --sandbox as well is rejected as a conflicting CLI option.
    return ["codex", "exec", "--ephemeral", "--approve-for-me", "--model", model, "-c", f'model_reasoning_effort="{effort}"', "--output-schema", str(schema_path), "--output-last-message", str(last_message_path), prompt]


def classify_host_blocker(stdout: str, stderr: str) -> str | None:
    """Classify bounded availability stops from either host output channel."""
    combined = f"{stdout}\n{stderr}".lower()
    if "weekly limit" in combined or "usage limit" in combined or "quota exceeded" in combined:
        return "blocked:host_quota"
    if "model" in combined and ("unavailable" in combined or "not available" in combined):
        return "blocked:model_unavailable"
    return None


def extract_return(harness: str, stdout: str, last_message_path: Path, assignment: dict[str, Any]) -> dict[str, Any] | None:
    try:
        if harness == "claude":
            return bounded_return(json.loads(stdout).get("structured_output"), assignment)
        return bounded_return(json.loads(last_message_path.read_text(encoding="utf-8")), assignment)
    except (OSError, json.JSONDecodeError, AttributeError):
        return None


def verify(case: dict[str, Any], workdir: Path, returned: dict[str, Any] | None) -> tuple[bool, str]:
    expected = case["expected_status"]
    if returned is None:
        return False, "host return failed bounded-step-return-v1 validation"
    if expected.startswith("blocked:"):
        matched = returned["status"] == "blocked" and any(blocker["code"] == expected for blocker in returned["blockers"])
    else:
        matched = returned["status"] == expected
    if not matched:
        return False, "return status did not match expected status"
    if case["verifier"] == "unchanged-and-return":
        return True, "bounded stop return matched"
    if case["verifier"] == "unittest":
        completed = subprocess.run([sys.executable, "-m", "unittest", "discover"], cwd=workdir, text=True, capture_output=True, timeout=30)
        return completed.returncode == 0, "unittest passed" if completed.returncode == 0 else "unittest failed"
    if case["verifier"] == "analysis-json":
        actual = workdir / "analysis.json"
        expected_path = workdir / "expected-analysis.json"
        if not actual.is_file():
            return False, "analysis.json was not created"
        return json.loads(actual.read_text(encoding="utf-8")) == json.loads(expected_path.read_text(encoding="utf-8")), "analysis.json matched expected conclusion"
    return False, "unknown verifier"


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def run_case(case: dict[str, Any], harness: str, attempt: int, output_dir: Path, execute: bool, timeout_seconds: int, claude_max_budget_usd: float) -> dict[str, Any]:
    model, effort = MAPPINGS[harness][case["tier"]]
    assignment = handoff_for(case, harness, attempt)
    result: dict[str, Any] = {"case_id": case["id"], "harness": harness, "attempt": attempt, "tier": case["tier"], "model": model, "effort": effort, "fixture": case["fixture"], "evidence_paths": [str(FIXTURES / case["fixture"])]}
    remediation = remediation_summary(assignment.get("retry_remediation"))
    if remediation is not None:
        result["remediation"] = remediation
    if not execute:
        result.update(status="not_run:execute_required", verifier="not_run", summary="Pass --execute to make a paid host call.")
        return result
    if shutil.which(harness) is None:
        result.update(status="blocked:model_unavailable", verifier="not_run", summary="host executable was unavailable; no downgrade attempted")
        return result
    runs_root = output_dir / ".forward-workdirs"
    runs_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"{harness}-{case['id']}-", dir=runs_root) as temporary:
        workdir = Path(temporary) / "repo"
        shutil.copytree(FIXTURES / case["fixture"], workdir)
        for git_args in (["git", "init", "--quiet"], ["git", "add", "--", "."], ["git", "-c", "user.name=Forward Eval", "-c", "user.email=forward-eval@example.invalid", "commit", "--quiet", "-m", "Synthetic fixture baseline"]):
            prepared = subprocess.run(git_args, cwd=workdir, text=True, capture_output=True, timeout=30)
            if prepared.returncode != 0:
                result.update(status="failed:fixture_setup", verifier="not_run", summary="could not initialize the synthetic Git fixture")
                return result
        before = tree_digest(workdir)
        schema_path = Path(temporary) / "output-schema.json"
        last_message_path = Path(temporary) / "last-message.json"
        schema_path.write_text(json.dumps(FINAL_SCHEMA, separators=(",", ":")), encoding="utf-8")
        prompt = build_prompt(case, harness, workdir, attempt)
        try:
            completed = subprocess.run(command_for(harness, model, effort, prompt, schema_path, last_message_path, claude_max_budget_usd), cwd=workdir, text=True, capture_output=True, timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            result.update(status="failed:timeout", verifier="not_run", summary=f"host exceeded {timeout_seconds}s bound")
            return result
        returned = extract_return(harness, completed.stdout, last_message_path, assignment)
        if completed.returncode != 0:
            blocker = classify_host_blocker(completed.stdout, completed.stderr)
            if blocker:
                summary = "host quota was unavailable; no downgrade attempted" if blocker == "blocked:host_quota" else "requested mapped model was unavailable; no downgrade attempted"
                result.update(status=blocker, verifier="not_run", summary=summary)
                return result
            result.update(status="failed:host_error", verifier="not_run", summary="host exited unsuccessfully without a model-unavailable signal")
            return result
        passed, detail = verify(case, workdir, returned)
        if passed and case["verifier"] == "unchanged-and-return" and tree_digest(workdir) != before:
            passed, detail = False, "stop case modified its synthetic repository"
        result.update(status="passed" if passed else "failed:verification", verifier=case["verifier"], summary=detail, return_summary=return_summary(returned))
        if returned is not None:
            result["return_sha256"] = ledger.digest(returned)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", choices=("claude", "codex", "both"), default="both", help="host mapping to evaluate")
    parser.add_argument("--output-dir", type=Path, required=True, help="directory for the bounded JSON summary")
    parser.add_argument("--execute", action="store_true", help="opt in to fresh paid host calls; without it validates the run matrix only")
    parser.add_argument("--timeout-seconds", type=int, default=120, help="per-run timeout, 1 through 180 seconds (default: 120)")
    parser.add_argument("--claude-max-budget-usd", type=float, default=0.50, help="per-Claude-run maximum budget in USD (default: 0.50)")
    args = parser.parse_args(argv)
    if not 1 <= args.timeout_seconds <= MAX_TIMEOUT_SECONDS:
        parser.error("--timeout-seconds must be between 1 and 180")
    if args.claude_max_budget_usd <= 0:
        parser.error("--claude-max-budget-usd must be positive")
    if args.execute and not is_secure_output_dir(args.output_dir):
        parser.error("--execute requires an existing absolute output directory with mode 0700 or stricter")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    harnesses = ("claude", "codex") if args.harness == "both" else (args.harness,)
    runs = []
    for case in load_cases():
        for harness in harnesses:
            prior_verified = True
            prior_result = None
            for attempt in range(1, case["attempts"] + 1):
                attempt_case = case_for_attempt(case, attempt)
                if attempt > 1 and "retry_remediation" in attempt_case and prior_result and "return_sha256" in prior_result:
                    attempt_case["retry_remediation"] = dict(attempt_case["retry_remediation"], prior_return_sha256=prior_result["return_sha256"])
                if args.execute and attempt > 1 and "attempt_sequence" in case and not prior_verified:
                    model, effort = MAPPINGS[harness][attempt_case["tier"]]
                    skipped = {
                        "case_id": case["id"], "harness": harness, "attempt": attempt,
                        "tier": attempt_case["tier"], "model": model, "effort": effort,
                        "fixture": case["fixture"], "evidence_paths": [str(FIXTURES / case["fixture"])],
                        "status": "not_run:prior_attempt_unverified", "verifier": "not_run",
                        "summary": "prior chained attempt did not verify; no retry host call was made",
                    }
                    remediation = remediation_summary(attempt_case.get("retry_remediation"))
                    if remediation is not None:
                        skipped["remediation"] = remediation
                    runs.append(skipped)
                    continue
                result = run_case(attempt_case, harness, attempt, args.output_dir, args.execute, args.timeout_seconds, args.claude_max_budget_usd)
                runs.append(result)
                prior_verified = result["status"] == "passed"
                prior_result = result
    payload = {"schema": "planning-policy-forward-eval/v1", "created_at": datetime.now(timezone.utc).isoformat(), "execute": args.execute, "runs": runs, "summary": {"total": len(runs), "passed": sum(run["status"] == "passed" for run in runs), "blocked": sum(run["status"].startswith("blocked:") for run in runs)}}
    destination = args.output_dir / "planning-policy-forward-eval.json"
    destination.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    workdirs = args.output_dir / ".forward-workdirs"
    if workdirs.exists() and not any(workdirs.iterdir()):
        workdirs.rmdir()
    print(json.dumps({"output": str(destination), "summary": payload["summary"]}, sort_keys=True, separators=(",", ":")))
    return 1 if args.execute and any(run["status"].startswith("failed:") for run in runs) else 0


if __name__ == "__main__":
    raise SystemExit(main())
