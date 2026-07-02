"""Git-aware repo enumeration (tracked+untracked, exclusions). The git block is
intentionally duplicated with scripts/skill_architecture_report.py (packaging
boundary; pinned by GitEnumerationParityTest)."""
from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

__all__ = ["is_guarded", "read_repo", "repo_paths"]

_GUARD_GLOBS = (
    "CLAUDE.md", "AGENTS.md", "README.md",
    # Top-level authoring/governance docs are listed explicitly (like the root
    # files above): a `docs/*.md` glob would slurp the whole `docs/notes/**`
    # draft tree because fnmatch '*' crosses '/'. Add new authoritative
    # top-level docs here by name.
    "docs/skill-architecture.md", "docs/skill-evaluation.md",
    "docs/release-checklist.md",
    "**/SKILL.md", "**/agents/*.md",
    "**/docs/*-reference/**/*.md", "**/docs/*-reference/*.md",
    "**/references/**/*.md", "**/references/*.md",
    "**/extensions/**/*.md", "**/extensions/*.md",
)
_EXCLUDE = (".worktrees/", "docs/superpowers/", ".cache/", ".git/", "node_modules/")


def is_guarded(rel: str) -> bool:
    if any(seg in rel for seg in _EXCLUDE):
        return False
    return any(fnmatch.fnmatch(rel, g) for g in _GUARD_GLOBS)


def repo_paths(root: Path) -> frozenset[str] | None:
    """Paths git treats as part of root's own work tree (tracked plus
    untracked-not-ignored), or None when root is not the top of a git work tree
    or git is unavailable. Nested worktrees live in a separate work tree, so git
    never lists them here; when None, callers fall back to the static _EXCLUDE
    walk so non-git target repos still work."""
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


def read_repo(root: Path, scope: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    base = scope if scope.is_dir() else scope.parent
    in_repo = repo_paths(root)
    for path in sorted(base.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        if in_repo is not None and rel not in in_repo:
            continue
        if is_guarded(rel):
            files[rel] = path.read_text(encoding="utf-8", errors="replace")
    return files
