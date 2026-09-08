"""Git-aware repo enumeration (tracked+untracked, exclusions). The git block is
intentionally duplicated with scripts/skill_architecture_report.py (packaging
boundary; pinned by GitEnumerationParityTest)."""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

__all__ = ["git_worktree_root", "is_guarded", "read_repo", "repo_paths"]

_GUARD_GLOBS = (
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    # Top-level authoring/governance docs are listed explicitly (like the root
    # files above): a `docs/*.md` glob would slurp the whole `docs/notes/**`
    # draft tree because fnmatch '*' crosses '/'. Add new authoritative
    # top-level docs here by name.
    "docs/skill-architecture.md",
    "docs/skill-evaluation.md",
    "docs/release-checklist.md",
    "SKILL.md",
    "agents/*.md",
    "commands/**/*.md",
    "commands/*.md",
    "references/**/*.md",
    "references/*.md",
    "extensions/**/*.md",
    "extensions/*.md",
    "**/SKILL.md",
    "**/agents/*.md",
    "**/docs/*-reference/**/*.md",
    "**/docs/*-reference/*.md",
    "**/references/**/*.md",
    "**/references/*.md",
    "**/extensions/**/*.md",
    "**/extensions/*.md",
)
_EXCLUDE = (".worktrees/", "docs/superpowers/", ".cache/", ".git/", "node_modules/")


def is_guarded(rel: str) -> bool:
    """True if rel is a guarded-markdown path (matches a guard glob and isn't
    under an excluded tree)."""
    if any(seg in rel for seg in _EXCLUDE):
        return False
    return any(fnmatch.fnmatch(rel, g) for g in _GUARD_GLOBS)


def _is_excluded(rel: str) -> bool:
    return any(seg in rel for seg in _EXCLUDE)


def repo_paths(root: Path) -> frozenset[str] | None:
    """Paths git treats as part of root's own work tree (tracked plus
    untracked-not-ignored), or None when root is not the top of a git work tree
    or git is unavailable. Nested worktrees live in a separate work tree, so git
    never lists them here; when None, callers fall back to the static _EXCLUDE
    walk so non-git target repos still work."""
    # Git subprocess shapes are deliberate twins required by the parity contract.
    # lean-audit:dup-intentional:begin
    # fmt: off
    # Kept byte-identical (modulo the naming/typing differences the parity test
    # already tolerates) to scripts/skill_architecture_report.py's copy, which
    # ruff's formatter never touches (outside [tool.ruff] include) — see
    # GitEnumerationParityTest.
    try:
        toplevel = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    if Path(toplevel).resolve() != root.resolve():
        return None
    try:
        listing = subprocess.run(
            ["git", "-C", str(root), "ls-files",
             "--cached", "--others", "--exclude-standard", "-z"],
            check=True, capture_output=True, text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return frozenset(entry for entry in listing.split("\0") if entry)
    # fmt: on
    # lean-audit:dup-intentional:end


def git_worktree_root(path: Path) -> Path | None:
    """Return the owning worktree root for a path, if Git can identify one."""
    try:
        toplevel = subprocess.run(
            [
                "git",
                "-C",
                str(path if path.is_dir() else path.parent),
                "rev-parse",
                "--show-toplevel",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return Path(toplevel).resolve()


def read_repo(root: Path, scope: Path, *, include: Path | None = None) -> dict[str, str]:
    # Source readers deliberately share the git-membership/read loop shape.
    # lean-audit:dup-intentional:begin
    files: dict[str, str] = {}
    base = scope if scope.is_dir() else scope.parent
    repo_root = git_worktree_root(base) or root
    in_repo = repo_paths(repo_root)
    for path in sorted(path for path in base.rglob("*") if path.suffix.lower() == ".md"):
        rel = path.relative_to(root).as_posix()
        git_rel = path.relative_to(repo_root).as_posix()
        scope_rel = path.relative_to(base).as_posix()
        if _is_excluded(rel):
            continue
        if in_repo is not None and git_rel not in in_repo:
            continue
        if is_guarded(rel) or is_guarded(scope_rel) or path == include:
            files[rel] = path.read_text(encoding="utf-8", errors="replace")
    return files
    # lean-audit:dup-intentional:end
