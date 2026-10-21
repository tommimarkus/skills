"""Planning ledger git operations: every git and worktree-helper subprocess call."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .core import WORKTREE_HELPER, Error

__all__ = [
    "git_common_dir",
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


def git(*arguments, cwd=None):
    """Run git, in `cwd` when given; return the completed process. The only git invocation."""
    command = ["git", *(["-C", str(cwd)] if cwd is not None else []), *arguments]
    return subprocess.run(command, text=True, capture_output=True)


def repository_top(args):
    """The checkout relative assignment worktrees resolve against."""
    if args.repo_root:
        return Path(args.repo_root).resolve()
    result = git("rev-parse", "--show-toplevel")
    return Path(result.stdout.strip() if result.returncode == 0 else Path.cwd()).resolve()


def git_common_dir(repo):
    """The absolute Git common directory of `repo`, or None when it is not in a repository."""
    result = git("rev-parse", "--git-common-dir", cwd=repo)
    if result.returncode:
        return None
    common = Path(result.stdout.strip())
    return (repo / common).resolve() if not common.is_absolute() else common.resolve()


def primary_checkout(top):
    """The checkout holding the Git common directory, so a derived worktree is never nested."""
    common = git_common_dir(top)
    if common is None:
        return top
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
    result = git("worktree", "list", "--porcelain", cwd=repo)
    if result.returncode:
        raise Error("cannot list git worktrees")
    entries, path = {}, None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree ") :]).resolve()
            entries[path] = ""
        elif line.startswith("branch ") and path is not None:
            entries[path] = line[len("branch ") :].removeprefix("refs/heads/")
    return entries


def verify_worktree_identity(repo, step, leaf, create_from):
    """Fail before any state change unless the leaf's worktree carries its branch."""
    path = Path(step["assignment"]["worktree"])
    if not path.is_absolute():
        path = repo / path
    owner = leaf["worktree_owner"]
    if not path.exists() and not path.is_symlink() and create_from:
        created = git("worktree", "add", "-b", owner, str(path), create_from, cwd=repo)
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
            f"worktree {path} has branch {actual or 'detached'}, expected worktree_owner {owner}"
        )


def git_head(worktree, repo):
    path = Path(worktree)
    result = git("rev-parse", "HEAD", cwd=path if path.is_absolute() else repo / path)
    if result.returncode:
        raise Error("cannot read worktree HEAD")
    return result.stdout.strip()


def git_output(worktree, *arguments):
    result = git(*arguments, cwd=worktree)
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
    entries = git_output(worktree, "status", "--porcelain", "-z", "--untracked-files=all").split(
        "\0"
    )
    paths, index = [], 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) > 3:
            paths.append(entry[3:])
            if entry[0] in "RC":
                index += 1
    return paths
