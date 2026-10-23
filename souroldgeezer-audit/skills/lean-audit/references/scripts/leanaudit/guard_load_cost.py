"""Fail-open reference guard and nonblocking inventory/cost notification.

Opt-in PreToolUse denies a broken local reference in the pending edit; code and
heading inventory changes are advisory. Stop checks changed working-tree Markdown
and reports reference defects and inventory/cost changes without blocking. It
cannot infer which session authored pre-existing changes or require remediation
outside the current task's authority. Names/counts do not prove semantic fidelity.
Errors, unguarded paths, and unavailable baselines/tools fail open.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from leanaudit import hook_envelope
from leanaudit import load_cost as slc

__all__ = ["cost_warn_decision", "decide", "main", "post_edit_content", "run_stop_mode"]


def post_edit_content(tool_name: str, tool_input: dict[str, Any], current: str) -> str | None:
    if tool_name == "Write":
        content = tool_input.get("content")
        return content if isinstance(content, str) else None
    if tool_name == "Edit":
        old, new = tool_input.get("old_string"), tool_input.get("new_string")
        if isinstance(old, str) and isinstance(new, str):
            return current.replace(old, new, 1)
        return None
    if tool_name == "MultiEdit":
        text = current
        for e in tool_input.get("edits", []) or []:
            o, n = e.get("old_string"), e.get("new_string")
            if isinstance(o, str) and isinstance(n, str):
                text = text.replace(o, n, 1)
        return text
    return None


def _owning_skill_md(path: Path, repo_root: Path) -> Path | None:
    # Include a referenced missing target when deciding ownership, so deleting a
    # closure file cannot make its owning skill disappear from the Stop check.
    target = path.resolve()
    for skill_md in repo_root.glob("**/SKILL.md"):
        if target in slc.resolve_closure_with_overrides(
            skill_md,
            {target: ""},
            source_root=repo_root,
            explicit_entry=False,
        ):
            return skill_md
    return None


def _baseline_for(skill_md: Path, repo_root: Path) -> Path | None:
    name = skill_md.parent.name
    p = repo_root / "tests" / "skill_load_cost" / "baselines" / f"{name}.json"
    return p if p.exists() else None


def cost_warn_decision(messages: list[str]) -> dict[str, Any] | None:
    if not messages:
        return None
    return hook_envelope.permission_decision(
        "allow", "lean-audit per-use guard (advisory, not blocking): " + "; ".join(messages)
    )


def decide(
    target: Path,
    new_content: str,
    skill_md: Path,
    baseline: Path,
    patterns: Path,
    source_root: Path | None = None,
) -> dict[str, Any] | None:
    """Return a reference denial, inventory advisory, or None. Pure."""
    pats = json.loads(Path(patterns).read_text(encoding="utf-8"))
    base = json.loads(Path(baseline).read_text(encoding="utf-8"))
    target_p = Path(target).resolve()
    skill_md_p = Path(skill_md)
    # Build closure with link-removal awareness (Fix C): a pending edit that
    # removes a Load-Map link actually shrinks the reachable set.
    authorized_root = source_root or skill_md_p.parent
    closure = slc.resolve_closure_with_overrides(
        skill_md_p,
        {target_p: new_content},
        source_root=authorized_root,
        explicit_entry=False,
    )
    invs = []
    for f in closure:
        text = new_content if f.resolve() == target_p else f.read_text(encoding="utf-8")
        invs.append(slc.extract_inventory(text, pats))
    inventory_changes = slc.diff_inventory(base, slc.union_inventory(invs))
    # Also check for dangling pointers introduced by the pending edit (Fix C)
    target_inv = slc.extract_inventory(new_content, pats)
    problems: list[str] = []
    for pointer in target_inv["pointers"]:
        tgt_file = pointer.split("#", 1)[0]
        if not tgt_file or tgt_file.startswith(("http://", "https://", "mailto:")):
            continue
        pointer_target = (target_p.parent / tgt_file).resolve()
        if (
            not pointer_target.is_relative_to(authorized_root.resolve())
            or not pointer_target.exists()
        ):
            problems.append(f"{target_p}: dangling pointer in pending edit: {pointer}")
    if problems:
        return hook_envelope.permission_decision(
            "deny", "lean-audit reference defect — " + "; ".join(problems)
        )
    if inventory_changes:
        return hook_envelope.permission_decision(
            "allow",
            "lean-audit inventory advisory — "
            + "; ".join(inventory_changes)
            + ". Review the intended change; names and counts do not prove semantic loss.",
        )
    return None


def _load_snapshot_and_scenarios(
    repo_root: Path,
) -> tuple[dict[str, int], list[dict[str, Any]]] | None:
    """Load the committed cost-snapshot + scenarios pair, or None if either is
    missing. Shared by the Stop-mode and PreToolUse cost-advisory checks (both
    filter this same pair differently — by skill vs. by target file)."""
    snap_p = repo_root / "tests" / "skill_load_cost" / "cost-snapshot.json"
    scenarios = _load_scenarios(repo_root)
    if not snap_p.exists() or scenarios is None:
        return None
    snap = json.loads(snap_p.read_text(encoding="utf-8"))
    return snap, scenarios


def _load_scenarios(repo_root: Path) -> list[dict[str, Any]] | None:
    scen_p = repo_root / "tests" / "skill_load_cost" / "scenarios.json"
    if not scen_p.exists():
        return None
    scenarios = json.loads(scen_p.read_text(encoding="utf-8"))
    return scenarios if isinstance(scenarios, list) else None


def _run_stop_mode_with_changed(changed_mds: list[str], repo_root: Path) -> int:
    """Core of Stop-mode: check changed skill closure files against committed baselines.

    All notices are plain text and nonblocking, including reference defects.
    Owning validation decides whether an artifact is usable. Returns 0 always.

    changed_mds: list of absolute path strings for changed .md files this session.
    repo_root: resolved Path to the repo root."""
    patterns_p = repo_root / "tests" / "skill_load_cost" / "code_patterns.json"
    if not patterns_p.exists():
        return 0
    pats = json.loads(patterns_p.read_text(encoding="utf-8"))

    # Map changed .md files to their owning skills; dedupe by skill_md path.
    skills_to_check: dict[Path, Path] = {}  # skill_md → baseline
    for md_path_str in changed_mds:
        md_path = Path(md_path_str)
        skill_md = _owning_skill_md(md_path, repo_root)
        if skill_md is None:
            continue
        bl = _baseline_for(skill_md, repo_root)
        if bl is None:
            continue
        skills_to_check[skill_md] = bl

    inventory_changes: list[str] = []
    reference_problems: list[str] = []
    cost_warnings: list[str] = []

    for skill_md, bl in skills_to_check.items():
        skill_name = skill_md.parent.name
        base = json.loads(Path(bl).read_text(encoding="utf-8"))
        # On-disk closure — Stop fires after all session edits are written;
        # no content override needed (the working tree already reflects them).
        closure = slc.resolve_closure(
            skill_md,
            source_root=repo_root,
        )
        existing = [f for f in closure if f.exists()]
        invs = [slc.extract_inventory(f.read_text(encoding="utf-8"), pats) for f in existing]
        for problem in slc.diff_inventory(base, slc.union_inventory(invs)):
            inventory_changes.append(f"{skill_name}: {problem}")
        for problem in slc.check_pointers(existing, pats):
            reference_problems.append(f"{skill_name}: {problem}")

        # Cost advisory (never blocks)
        loaded = _load_snapshot_and_scenarios(repo_root)
        if loaded is not None:
            snap, scenarios = loaded
            skill_scens = [s for s in scenarios if s.get("skill") == skill_name]
            if skill_scens:
                snap_filtered = {
                    k: v for k, v in snap.items() if k in {s["id"] for s in skill_scens}
                }
                msgs = slc.cost_regressions(snap_filtered, skill_scens, repo_root)
                cost_warnings.extend(msgs)

    if reference_problems:
        print("lean-audit reference defect — " + "; ".join(reference_problems))
    if inventory_changes:
        print("lean-audit inventory advisory — " + "; ".join(inventory_changes))

    if cost_warnings:
        # Cost is advisory — plain text only, never a block decision.
        print(
            "lean-audit per-use guard (advisory): per-use cost grew vs snapshot"
            " (post-edit on-disk closure vs committed cost-snapshot.json) — "
            + "; ".join(cost_warnings)
        )

    return 0


def run_stop_mode(repo_root: Path) -> int:
    """Enumerate working-tree .md changes via git and run the Stop-mode notice.

    Uses the union of unstaged and staged changes relative to HEAD. Any git
    failure → fail-open (return 0)."""
    changed: set[str] = set()
    for cmd in [
        ["git", "-C", str(repo_root), "diff", "--name-only", "HEAD"],
        ["git", "-C", str(repo_root), "diff", "--name-only", "--cached", "HEAD"],
    ]:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            return 0
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.endswith(".md"):
                changed.add(str((repo_root / line).resolve()))
    return _run_stop_mode_with_changed(list(changed), repo_root)


def main() -> int:
    try:
        payload = hook_envelope.read_payload()
    except Exception:
        # Routine (malformed/empty stdin JSON) — mirrors leanaudit.guard_lean's
        # identical read_payload() precedent: not a distinct execution failure,
        # so this stays silent rather than logging.
        return 0

    try:
        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input") or {}
        fp = tool_input.get("file_path")
        repo_root = Path(payload.get("cwd") or ".").resolve()
    except Exception as exc:
        hook_envelope.fail_open_log("load-cost-guard", "main-backstop", exc)
        return 0

    if not fp:
        # Stop event (no file_path) — check session-changed skill files
        try:
            return run_stop_mode(repo_root)
        except Exception as exc:
            hook_envelope.fail_open_log("load-cost-guard", "stop-mode", exc)
            return 0

    try:
        # PreToolUse path (Edit/Write/MultiEdit targeting a .md file)
        if not str(fp).endswith(".md"):
            return 0
        target = Path(fp)
        skill_md = _owning_skill_md(target, repo_root)
        if skill_md is None:
            return 0
        baseline = _baseline_for(skill_md, repo_root)
        if baseline is None:
            return 0
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        new_content = post_edit_content(tool_name, tool_input, current)
        if new_content is None:
            return 0
        patterns = repo_root / "tests" / "skill_load_cost" / "code_patterns.json"
        if not patterns.exists():
            return 0
        decision = decide(
            target,
            new_content,
            skill_md,
            baseline,
            patterns,
            source_root=repo_root,
        )
        denied = decision is not None and (
            decision["hookSpecificOutput"]["permissionDecision"] == "deny"
        )
        scenarios = None if denied else _load_scenarios(repo_root)
        if scenarios is not None:
            # PreToolUse attributes only the proposed edit's marginal increase.
            # Snapshot drift remains a Stop-mode observation and cannot make a
            # neutral or reducing pending edit look costly.
            owned = [
                scenario
                for scenario in scenarios
                if slc.scenario_uses_path(scenario, repo_root, target)
            ]
            msgs = slc.marginal_cost_regressions(
                owned,
                repo_root,
                {target.resolve(): new_content},
            )
            warn = cost_warn_decision(msgs)
            if warn is not None:
                if decision is None:
                    decision = warn
                else:
                    decision["hookSpecificOutput"]["permissionDecisionReason"] += (
                        "\n" + warn["hookSpecificOutput"]["permissionDecisionReason"]
                    )
        if decision is not None:
            print(json.dumps(decision))
        return 0
    except Exception as exc:
        hook_envelope.fail_open_log("load-cost-guard", "pretooluse-decide", exc)
        return 0
