#!/usr/bin/env python3
"""Integrate and retire delegated Git worktrees without losing ancestry."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "planning-worktree-result-v1"
COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
BRANCH = re.compile(r"^(?!-)(?!.*\.\.)(?!.*(?:^|/)\.)(?!.*[~^:?*\\\[])[^\s]+$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
MAX_BATCH_COMMITS = 8


class Error(Exception):
    pass


def run(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", "-C", str(cwd), *args], text=True, capture_output=True)
    if check and result.returncode:
        raise Error(f"git {' '.join(args[:2])} failed")
    return result


def resolve_commit(cwd: Path, value: str) -> str:
    result = run(cwd, "rev-parse", "--verify", f"{value}^{{commit}}")
    commit = result.stdout.strip()
    if not COMMIT.fullmatch(commit):
        raise Error("invalid commit identity")
    return commit


def clean(cwd: Path, label: str) -> None:
    if run(cwd, "status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise Error(f"{label} worktree must be clean")


def git_path(cwd: Path, name: str) -> Path:
    value = run(cwd, "rev-parse", "--git-path", name).stdout.strip()
    path = Path(value)
    return path if path.is_absolute() else (cwd / path).resolve()


def inactive(cwd: Path, label: str) -> None:
    markers = (
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "BISECT_LOG",
        "rebase-apply",
        "rebase-merge",
    )
    if any(git_path(cwd, marker).exists() for marker in markers):
        raise Error(f"{label} worktree has an active Git operation")


def worktrees(repo: Path) -> dict[Path, str]:
    records: dict[Path, str] = {}
    current: Path | None = None
    for line in run(repo, "worktree", "list", "--porcelain").stdout.splitlines():
        if line.startswith("worktree "):
            current = Path(line.removeprefix("worktree ")).resolve()
            records[current] = ""
        elif current is not None and line.startswith("branch refs/heads/"):
            records[current] = line.removeprefix("branch refs/heads/")
    return records


def base(args: argparse.Namespace) -> tuple[Path, Path, str, str]:
    repo = Path(args.repo_root).resolve()
    leaf = Path(args.worktree).resolve()
    branch = args.branch
    target = args.target
    if not repo.is_dir() or not leaf.is_dir():
        raise Error("repository and worktree must exist")
    if not BRANCH.fullmatch(branch) or not BRANCH.fullmatch(target):
        raise Error("invalid branch or target")
    if run(repo, "rev-parse", "--show-toplevel").stdout.strip() != str(repo):
        raise Error("--repo-root must be the parent worktree root")
    if run(repo, "symbolic-ref", "--short", "HEAD").stdout.strip() != target:
        raise Error("parent worktree must be checked out on the exact target")
    registered = worktrees(repo)
    if registered.get(leaf) != branch:
        raise Error("worktree is not registered on the exact branch")
    clean(repo, "parent")
    clean(leaf, "leaf")
    inactive(repo, "parent")
    inactive(leaf, "leaf")
    upstream = run(
        leaf, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", check=False
    )
    if upstream.returncode == 0:
        raise Error("delegated branch must not have an upstream")
    return repo, leaf, branch, target


def cleanup_base(args: argparse.Namespace) -> tuple[Path, Path, str, str]:
    repo = Path(args.repo_root).resolve()
    leaf = Path(args.worktree).resolve()
    branch = args.branch
    target = args.target
    if not repo.is_dir():
        raise Error("repository must exist")
    if not BRANCH.fullmatch(branch) or not BRANCH.fullmatch(target):
        raise Error("invalid branch or target")
    if run(repo, "rev-parse", "--show-toplevel").stdout.strip() != str(repo):
        raise Error("--repo-root must be the parent worktree root")
    if run(repo, "symbolic-ref", "--short", "HEAD").stdout.strip() != target:
        raise Error("parent worktree must be checked out on the exact target")
    clean(repo, "parent")
    inactive(repo, "parent")
    return repo, leaf, branch, target


def branch_tip(repo: Path, branch: str) -> str | None:
    exists = run(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
    if exists.returncode == 1:
        return None
    if exists.returncode:
        raise Error("cannot inspect delegated branch")
    return resolve_commit(repo, f"refs/heads/{branch}")


def require_no_upstream(repo: Path, branch: str) -> None:
    upstream = run(
        repo,
        "for-each-ref",
        "--format=%(upstream)",
        f"refs/heads/{branch}",
    ).stdout.strip()
    if upstream:
        raise Error("delegated branch must not have an upstream")


def parse_batch_commits(values: list[str]) -> dict[str, str]:
    if len(values) > MAX_BATCH_COMMITS:
        raise Error(f"--batch-commit may not appear more than {MAX_BATCH_COMMITS} times")
    commits: dict[str, str] = {}
    for value in values:
        step_id, sep, sha = value.partition("=")
        if not sep or not step_id or not SHA40.fullmatch(sha):
            raise Error(f"invalid --batch-commit value: {value}")
        if step_id in commits:
            raise Error(f"duplicate --batch-commit step id: {step_id}")
        commits[step_id] = sha
    return commits


def check_batch_ancestry(leaf: Path, source: str, commits: dict[str, str]) -> None:
    for step_id, sha in commits.items():
        ancestor = run(leaf, "merge-base", "--is-ancestor", sha, source, check=False)
        if ancestor.returncode:
            raise Error(f"batch commit for step {step_id} is not an ancestor of the source commit")


def result_fields(
    repo: Path,
    leaf: Path,
    branch: str,
    target: str,
    source: str,
    rebased: str,
    parent_before: str,
    parent_after: str,
    rebased_tree_changed: bool,
    batch_source_commits: dict[str, str] | None,
) -> dict[str, object]:
    fields: dict[str, object] = {
        "schema": SCHEMA,
        "ok": True,
        "repo_root": str(repo),
        "target": target,
        "branch": branch,
        "worktree": str(leaf),
        "source_commit": source,
        "rebased_commit": rebased,
        "parent_before": parent_before,
        "parent_after": parent_after,
        "rebased_tree_changed": rebased_tree_changed,
    }
    if batch_source_commits:
        fields["batch_source_commits"] = batch_source_commits
    return fields


def integrate(args: argparse.Namespace) -> dict[str, object]:
    batch_commits = parse_batch_commits(args.batch_commit)
    repo, leaf, branch, target = base(args)
    source = resolve_commit(leaf, args.source_commit)
    if resolve_commit(leaf, "HEAD") != source or resolve_commit(repo, branch) != source:
        raise Error("returned source commit is not the exact branch tip")
    if batch_commits:
        check_batch_ancestry(leaf, source, batch_commits)
    parent_before = resolve_commit(repo, target)
    if args.require_patch_equivalent:
        cherry = run(repo, "cherry", target, branch).stdout.splitlines()
        if any(not line.startswith("- ") for line in cherry):
            raise Error("branch is not entirely patch-equivalent to target")

    rebased_run = run(leaf, "rebase", target, check=False)
    if rebased_run.returncode:
        run(leaf, "rebase", "--abort", check=False)
        if resolve_commit(leaf, "HEAD") != source:
            raise Error("rebase conflict could not restore the source branch")
        raise Error("rebase conflict; source branch retained")
    rebased = resolve_commit(leaf, "HEAD")
    if resolve_commit(repo, target) != parent_before:
        raise Error("parent target moved during rebase; rebased branch retained")
    if args.require_patch_equivalent and rebased != parent_before:
        raise Error("patch-equivalent rebase did not collapse to the parent tip")
    merged = run(repo, "merge", "--ff-only", branch, check=False)
    if merged.returncode:
        raise Error("fast-forward-only merge failed; rebased branch retained")
    parent_after = resolve_commit(repo, target)
    if parent_after != rebased:
        raise Error("fast-forward target does not equal rebased branch")
    source_tree = run(leaf, "rev-parse", f"{source}^{{tree}}").stdout.strip()
    rebased_tree = run(leaf, "rev-parse", f"{rebased}^{{tree}}").stdout.strip()
    return {
        **result_fields(
            repo,
            leaf,
            branch,
            target,
            source,
            rebased,
            parent_before,
            parent_after,
            source_tree != rebased_tree,
            batch_commits,
        ),
        "action": "integrate",
    }


def read_integrated(path: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Error("cannot read integrated helper result") from exc
    required = {
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
        "rebased_tree_changed",
    }
    optional = {"batch_source_commits"}
    if (
        not isinstance(value, dict)
        or set(value) - optional != required
        or value.get("schema") != SCHEMA
        or value.get("ok") is not True
        or value.get("action") != "integrate"
    ):
        raise Error("invalid integrated helper result")
    if any(
        not COMMIT.fullmatch(str(value.get(key, "")))
        for key in ("source_commit", "rebased_commit", "parent_before", "parent_after")
    ):
        raise Error("invalid integrated commit identities")
    if not isinstance(value.get("rebased_tree_changed"), bool):
        raise Error("invalid integrated tree-change flag")
    if "batch_source_commits" in value:
        batch = value["batch_source_commits"]
        if not isinstance(batch, dict) or not batch or any(
            not isinstance(step_id, str) or not step_id or not SHA40.fullmatch(str(sha))
            for step_id, sha in batch.items()
        ):
            raise Error("invalid integrated batch source commits")
    return value


def cleanup(args: argparse.Namespace) -> dict[str, object]:
    repo, leaf, branch, target = cleanup_base(args)
    integrated = read_integrated(args.integrated_result)
    expected = {
        "repo_root": str(repo),
        "target": target,
        "branch": branch,
        "worktree": str(leaf),
    }
    if any(integrated[key] != value for key, value in expected.items()):
        raise Error("integrated result does not own the exact branch/worktree")
    rebased = str(integrated["rebased_commit"])
    if integrated["parent_after"] != rebased:
        raise Error("integrated result does not record the fast-forward commit")

    registered = worktrees(repo)
    leaf_exists = os.path.lexists(leaf)
    leaf_registered = leaf in registered
    registered_branch = registered.get(leaf)
    branch_worktrees = [path for path, value in registered.items() if value == branch]
    if leaf_registered:
        if not leaf_exists:
            raise Error("stale worktree registration must be repaired before cleanup")
        if registered_branch != branch:
            raise Error("worktree is not registered on the exact branch")
    else:
        if leaf_exists:
            raise Error("unexpected filesystem entry exists at the owned worktree path")
        if branch_worktrees:
            raise Error("delegated branch is registered at an unexpected worktree")

    tip = branch_tip(repo, branch)
    if tip is not None:
        require_no_upstream(repo, branch)
        if tip != rebased:
            raise Error("delegated branch no longer matches the integrated commit")
    if leaf_registered:
        clean(leaf, "leaf")
        inactive(leaf, "leaf")
        if resolve_commit(leaf, "HEAD") != rebased or tip != rebased:
            raise Error("registered branch no longer matches the integrated commit")

    parent_commit = resolve_commit(repo, target)
    if run(repo, "merge-base", "--is-ancestor", rebased, target, check=False).returncode:
        raise Error("integrated commit is not merged into target")
    if tip is None:
        return {
            **integrated,
            "action": "cleanup",
            "parent_commit": parent_commit,
        }

    merged = {
        line.removeprefix("+").strip()
        for line in run(
            repo, "branch", "--merged", target, "--format=%(refname:short)"
        ).stdout.splitlines()
    }
    if branch not in merged:
        raise Error("git branch --merged did not confirm the exact branch")

    if leaf_registered:
        removed = run(repo, "worktree", "remove", str(leaf), check=False)
        if removed.returncode:
            raise Error("clean worktree removal failed; branch retained")
    run(repo, "worktree", "prune")
    deleted = run(repo, "branch", "-d", branch, check=False)
    if deleted.returncode:
        raise Error("non-force branch deletion failed; branch retained")
    if (
        branch
        in run(repo, "branch", "--list", branch, "--format=%(refname:short)").stdout.splitlines()
    ):
        raise Error("branch still exists after non-force deletion")
    return {
        **integrated,
        "action": "cleanup",
        "parent_commit": parent_commit,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("integrate", "cleanup"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", required=True)
        command.add_argument("--target", required=True)
        command.add_argument("--branch", required=True)
        command.add_argument("--worktree", required=True)
    integration = commands.choices["integrate"]
    integration.add_argument("--source-commit", required=True)
    integration.add_argument("--require-patch-equivalent", action="store_true")
    integration.add_argument("--batch-commit", action="append", default=[])
    commands.choices["cleanup"].add_argument("--integrated-result", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        value = integrate(args) if args.command == "integrate" else cleanup(args)
        print(json.dumps(value, sort_keys=True, separators=(",", ":")))
        return 0
    except Error as exc:
        print(
            json.dumps(
                {"schema": SCHEMA, "ok": False, "action": args.command, "error": str(exc)},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 3


if __name__ == "__main__":
    sys.exit(main())
