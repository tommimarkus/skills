#!/usr/bin/env python3
"""lean-audit per-use PreToolUse guard (opt-in, fail-open).

Soft-blocks an Edit/Write/MultiEdit that would make a smell code or section
unreachable in a guarded skill's Load-Map closure (the fidelity floor). Reads
PreToolUse JSON on stdin, emits a `deny` decision on a fidelity regression, and
ALWAYS allows (exit 0, no stdout) on any error, non-skill path, or missing
baseline. Adds no judgment logic — the inventory + closure come from the engine."""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_load_cost as slc  # noqa: E402


def post_edit_content(tool_name, tool_input, current):
    if tool_name == "Write":
        c = tool_input.get("content"); return c if isinstance(c, str) else None
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


def owning_skill_md(path, repo_root):
    for skill_md in repo_root.glob("**/SKILL.md"):
        if path.resolve() in set(slc.resolve_closure(skill_md)):
            return skill_md
    return None


def baseline_for(skill_md, repo_root):
    name = skill_md.parent.name
    p = repo_root / "tests" / "skill_load_cost" / "baselines" / f"{name}.json"
    return p if p.exists() else None


def decide(target, new_content, skill_md, baseline, patterns):
    """Return a deny-decision dict, or None to allow. Pure; fail-open is the caller's."""
    pats = json.loads(Path(patterns).read_text())
    base = json.loads(Path(baseline).read_text())
    invs = []
    for f in slc.resolve_closure(Path(skill_md)):
        text = new_content if f.resolve() == Path(target).resolve() \
            else f.read_text(encoding="utf-8")
        invs.append(slc.extract_inventory(text, pats))
    problems = slc.diff_inventory(base, slc.union_inventory(invs))
    if not problems:
        return None
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason":
            "lean-audit per-use guard: fidelity regression — " + "; ".join(problems)
            + ". Cite the lost item or restructure; the fidelity floor must hold."}}


def main():
    try:
        payload = json.load(sys.stdin)
        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input", {}) or {}
        fp = tool_input.get("file_path")
        if not fp or not str(fp).endswith(".md"):
            return 0
        target = Path(fp)
        repo_root = Path(payload.get("cwd") or ".").resolve()
        skill_md = owning_skill_md(target, repo_root)
        if skill_md is None:
            return 0
        baseline = baseline_for(skill_md, repo_root)
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
        return 0
    except Exception:
        return 0  # fail-open


if __name__ == "__main__":
    raise SystemExit(main())
