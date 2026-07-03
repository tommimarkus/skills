"""lean-audit per-use guard (opt-in, fail-open).

PreToolUse path: soft-blocks an Edit/Write/MultiEdit that would make a smell
code, section, or Load-Map pointer unreachable in a guarded skill's closure
(the fidelity floor). Reads PreToolUse JSON on stdin, emits a `deny` decision
on a fidelity regression.

Stop path: enumerates session-changed .md files, maps each to its owning skill,
checks the current on-disk closure against the committed baseline, and emits a
Stop-hook `decision:block` for any fidelity regression. Cost growth is advisory
and NEVER blocks in either path.

ALWAYS allows (exit 0, no stdout) on any error, non-skill path, missing
baseline, or git failure. Adds no judgment logic — inventory + closure come
from the engine."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from leanaudit import hook_envelope
from leanaudit import load_cost as slc

__all__ = ["decide", "cost_warn_decision", "post_edit_content", "run_stop_mode", "main"]


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
    for skill_md in repo_root.glob("**/SKILL.md"):
        if path.resolve() in set(slc.resolve_closure(skill_md)):
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
) -> dict[str, Any] | None:
    """Return a deny-decision dict, or None to allow. Pure; fail-open is the caller's."""
    pats = json.loads(Path(patterns).read_text(encoding="utf-8"))
    base = json.loads(Path(baseline).read_text(encoding="utf-8"))
    target_p = Path(target).resolve()
    skill_md_p = Path(skill_md)
    # Build closure with link-removal awareness (Fix C): a pending edit that
    # removes a Load-Map link actually shrinks the reachable set.
    closure = slc.resolve_closure_with_overrides(skill_md_p, {target_p: new_content})
    invs = []
    for f in closure:
        text = new_content if f.resolve() == target_p else f.read_text(encoding="utf-8")
        invs.append(slc.extract_inventory(text, pats))
    problems = slc.diff_inventory(base, slc.union_inventory(invs))
    # Also check for dangling pointers introduced by the pending edit (Fix C)
    target_inv = slc.extract_inventory(new_content, pats)
    for pointer in target_inv["pointers"]:
        tgt_file = pointer.split("#", 1)[0]
        if not tgt_file or tgt_file.startswith(("http://", "https://", "mailto:")):
            continue
        if not (target_p.parent / tgt_file).resolve().exists():
            problems.append(f"{target_p}: dangling pointer in pending edit: {pointer}")
    if not problems:
        return None
    return hook_envelope.permission_decision(
        "deny",
        "lean-audit per-use guard: fidelity regression — "
        + "; ".join(problems)
        + ". Cite the lost item or restructure; the fidelity floor must hold.",
    )


def _load_snapshot_and_scenarios(
    repo_root: Path,
) -> tuple[dict[str, int], list[dict[str, Any]]] | None:
    """Load the committed cost-snapshot + scenarios pair, or None if either is
    missing. Shared by the Stop-mode and PreToolUse cost-advisory checks (both
    filter this same pair differently — by skill vs. by target file)."""
    snap_p = repo_root / "tests" / "skill_load_cost" / "cost-snapshot.json"
    scen_p = repo_root / "tests" / "skill_load_cost" / "scenarios.json"
    if not (snap_p.exists() and scen_p.exists()):
        return None
    snap = json.loads(snap_p.read_text(encoding="utf-8"))
    scenarios = json.loads(scen_p.read_text(encoding="utf-8"))
    return snap, scenarios


def _run_stop_mode_with_changed(changed_mds: list[str], repo_root: Path) -> int:
    """Core of Stop-mode: check changed skill closure files against committed baselines.

    Outputs a Stop-hook block decision ({"decision":"block","reason":"..."}) for
    fidelity regressions. Cost growth is advisory — emitted as plain text and
    NEVER blocks. Returns 0 always (fail-open).

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

    fidelity_problems: list[str] = []
    cost_warnings: list[str] = []

    for skill_md, bl in skills_to_check.items():
        skill_name = skill_md.parent.name
        base = json.loads(Path(bl).read_text(encoding="utf-8"))
        # On-disk closure — Stop fires after all session edits are written;
        # no content override needed (the working tree already reflects them).
        closure = slc.resolve_closure(skill_md)
        existing = [f for f in closure if f.exists()]
        invs = [slc.extract_inventory(f.read_text(encoding="utf-8"), pats) for f in existing]
        problems = slc.diff_inventory(base, slc.union_inventory(invs))
        problems += slc.check_pointers(existing, pats)
        for p in problems:
            fidelity_problems.append(f"{skill_name}: {p}")

        # Cost advisory (never blocks)
        loaded = _load_snapshot_and_scenarios(repo_root)
        if loaded is not None:
            snap, scenarios = loaded
            skill_scens = [s for s in scenarios if s.get("skill") == skill_name]
            if skill_scens:
                snap_filtered = {
                    k: v for k, v in snap.items() if k in {s["id"] for s in skill_scens}
                }
                msgs = slc.cost_regressions(snap_filtered, skill_scens, repo_root, tolerance=200)
                cost_warnings.extend(msgs)

    if fidelity_problems:
        skills_str = ", ".join(sorted({p.split(":")[0] for p in fidelity_problems}))
        problems_str = "; ".join(fidelity_problems)
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        f"lean-audit per-use guard: fidelity regression in {skills_str} — "
                        f"{problems_str}. Restore the lost code/section/pointer or cite it; "
                        "the fidelity floor must hold."
                    ),
                }
            )
        )
        return 0

    if cost_warnings:
        # Cost is advisory — plain text only, never a block decision.
        print(
            "lean-audit per-use guard (advisory): per-use cost grew vs snapshot"
            " (post-edit on-disk closure vs committed cost-snapshot.json) — "
            + "; ".join(cost_warnings)
        )

    return 0


def run_stop_mode(repo_root: Path) -> int:
    """Enumerate session-changed .md files via git and run the Stop-mode check.

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
        decision = decide(target, new_content, skill_md, baseline, patterns)
        if decision is not None:
            print(json.dumps(decision))
        loaded = _load_snapshot_and_scenarios(repo_root) if decision is None else None
        if loaded is not None:
            # Measures current on-disk closure vs the committed cost snapshot.
            # At PreToolUse time this reflects pre-edit drift; at Stop time the
            # on-disk state is the post-edit truth (Stop-mode is preferred for
            # accurate cost measurement — see hook-recipe.md).
            snap, scenarios = loaded
            owned = {
                s["id"]: s
                for s in scenarios
                if str(target) in [str(repo_root / f) for f in s["files"]]
                or any((repo_root / f).resolve() == target.resolve() for f in s["files"])
            }
            msgs = slc.cost_regressions(
                {k: v for k, v in snap.items() if k in owned},
                list(owned.values()),
                repo_root,
                tolerance=200,
            )
            warn = cost_warn_decision(msgs)
            if warn is not None:
                print(json.dumps(warn))
        return 0
    except Exception as exc:
        hook_envelope.fail_open_log("load-cost-guard", "pretooluse-decide", exc)
        return 0
