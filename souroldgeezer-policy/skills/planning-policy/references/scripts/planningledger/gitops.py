"""Planning ledger git operations: every git and worktree-helper subprocess call."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .core import Error, WORKTREE_HELPER

__all__ = [
    "repository_top",
    "primary_checkout",
    "helper_error",
    "registered_worktrees",
    "verify_worktree_identity",
    "git_head",
    "git_output",
    "numstat_rows",
    "dirty_paths",
]


def repository_top(args):
    """The checkout relative assignment worktrees resolve against."""
    if args.repo_root:
        return Path(args.repo_root).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True
    )
    return Path(result.stdout.strip() if result.returncode == 0 else Path.cwd()).resolve()


def primary_checkout(top):
    """The checkout holding the Git common directory, so a derived worktree is never nested."""
    result = subprocess.run(
        ["git", "-C", str(top), "rev-parse", "--git-common-dir"], text=True, capture_output=True
    )
    if result.returncode:
        return top
    common = Path(result.stdout.strip())
    common = (top / common).resolve() if not common.is_absolute() else common.resolve()
    return common.parent if common.name == ".git" else top


def run_worktree_helper(*arguments):
    """Run the Git-policy helper; return its parsed result and whether it succeeded."""
    result = subprocess.run(
        [sys.executable, "-B", str(WORKTREE_HELPER), *arguments],
        text=True,
        capture_output=True,
    )
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        value = None
    if not isinstance(value, dict):
        value = {"ok": False, "error": (result.stderr or "helper produced no result").strip()[:240]}
    return value, result.returncode == 0 and value.get("ok") is True


def helper_error(value):
    return str(value.get("error", "helper failed"))[:240]


def registered_worktrees(repo):
    """Map each registered worktree path of the repository to its branch name."""
    result = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list", "--porcelain"],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise Error("cannot list git worktrees")
    entries, path = {}, None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree "):]).resolve()
            entries[path] = ""
        elif line.startswith("branch ") and path is not None:
            entries[path] = line[len("branch "):].removeprefix("refs/heads/")
    return entries


def verify_worktree_identity(repo, step, leaf, create_from):
    """Fail before any state change unless the leaf's worktree carries its branch."""
    path = Path(step["assignment"]["worktree"])
    if not path.is_absolute():
        path = repo / path
    owner = leaf["worktree_owner"]
    if not path.exists() and not path.is_symlink() and create_from:
        created = subprocess.run(
            ["git", "-C", str(repo), "worktree", "add", "-b", owner, str(path), create_from],
            text=True,
            capture_output=True,
        )
        if created.returncode:
            raise Error(f"cannot create worktree {path}: {created.stderr.strip()[:200]}")
    registry = registered_worktrees(repo)
    if path.resolve() not in registry:
        raise Error(
            f"worktree {path} is not a registered worktree of {repo}"
            + ("" if create_from else "; pass --create-from TARGET to create it")
        )
    actual = registry[path.resolve()]
    if actual != owner:
        raise Error(
            f"worktree {path} has branch {actual or 'detached'}, "
            f"expected worktree_owner {owner}"
        )


def git_head(worktree, repo):
    path = Path(worktree)
    result = subprocess.run(
        ["git", "-C", str(path if path.is_absolute() else repo / path), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise Error("cannot read worktree HEAD")
    return result.stdout.strip()


def git_output(worktree, *arguments):
    result = subprocess.run(
        ["git", "-C", str(worktree), *arguments], text=True, capture_output=True
    )
    if result.returncode:
        raise Error(f"git {arguments[0]} failed in the worktree")
    return result.stdout


def numstat_rows(worktree, base, commit):
    """Rows of (paths, changed lines); a binary row is zero lines, a rename one row."""
    tokens = git_output(worktree, "diff", "--numstat", "-z", "-M", f"{base}..{commit}").split("\0")
    rows, index = [], 0
    while index < len(tokens):
        head = tokens[index]
        index += 1
        if not head:
            continue
        added, deleted, path = head.split("\t", 2)
        paths = [path]
        if not path:
            paths = [tokens[index + 1], tokens[index]]
            index += 2
        rows.append((paths, 0 if added == "-" else int(added) + int(deleted)))
    return rows


def dirty_paths(worktree):
    entries = git_output(worktree, "status", "--porcelain", "-z", "--untracked-files=all").split("\0")
    paths, index = [], 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) > 3:
            paths.append(entry[3:])
            if entry[0] in "RC":
                index += 1
    return paths
