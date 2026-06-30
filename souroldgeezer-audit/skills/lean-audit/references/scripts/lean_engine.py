"""lean-audit deterministic duplication engine (stdlib-only)."""
from __future__ import annotations

import argparse
import fnmatch
import json
import posixpath
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]*`")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_WORD = re.compile(r"[a-z0-9]+")
_HEADING = re.compile(r"^#{1,6}\s+(.*)$")
OVERRIDE = re.compile(r"<!--\s*lean-audit:sync-intentional:?.*?-->", re.IGNORECASE | re.DOTALL)

DEFAULT_K = 4


def normalize(text: str) -> list[str]:
    text = _FENCE.sub(" ", text)
    text = _LINK.sub(r"\1", text)
    text = _INLINE_CODE.sub(" ", text)
    return _WORD.findall(text.lower())


def shingle_set(tokens: list[str], k: int = DEFAULT_K) -> set[tuple[str, ...]]:
    if len(tokens) < k:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def containment(added: set, other: set) -> float:
    return len(added & other) / len(added) if added else 0.0


@dataclass(frozen=True)
class Section:
    path: str
    heading: str
    body: str
    shingles: frozenset


def split_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            sections.append((m.group(1).strip(), []))
        else:
            sections[-1][1].append(line)
    out = []
    for heading, lines in sections:
        body = "\n".join(lines).strip()
        if heading or body:
            out.append((heading, body))
    return out


def build_index(files: dict[str, str]) -> list[Section]:
    index: list[Section] = []
    for path, text in files.items():
        for heading, body in split_sections(text):
            shingles = frozenset(shingle_set(normalize(body)))
            index.append(Section(path=path, heading=heading, body=body, shingles=shingles))
    return index


@dataclass(frozen=True)
class Registry:
    canonical_homes: tuple[tuple[str, str], ...]
    carve_outs: tuple[tuple[str, str], ...]
    exempt_paths: tuple[str, ...]


def load_registry(path: Path | None) -> Registry:
    if path is None or not Path(path).is_file():
        return Registry(canonical_homes=(), carve_outs=(), exempt_paths=())
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    homes = tuple(
        (h["path"], h["heading"]) for h in data.get("canonical_home", []) if "path" in h and "heading" in h
    )
    carves = tuple((c["a"], c["b"]) for c in data.get("carve_out", []) if "a" in c and "b" in c)
    exempt = tuple(data.get("exempt_paths", []))
    return Registry(canonical_homes=homes, carve_outs=carves, exempt_paths=exempt)


def has_override(text: str) -> bool:
    return OVERRIDE.search(text) is not None


HIGH_BAND = 0.60
MID_BAND = 0.35
MIN_TOKENS = 25


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    path: str
    heading: str
    containment: float
    matched_path: str
    matched_heading: str
    action: str


def _is_home(reg: Registry, path: str, heading: str) -> bool:
    return (path, heading) in reg.canonical_homes


def score_section(sec: Section, index: list[Section], reg: Registry) -> Finding | None:
    if len(normalize(sec.body)) < MIN_TOKENS:
        return None
    if has_override(sec.body):
        return None
    if path_exempt(reg, sec.path):
        return None
    best = None
    best_c = 0.0
    for other in index:
        if other.path == sec.path:
            continue
        c = containment(sec.shingles, other.shingles)
        if c > best_c:
            best, best_c = other, c
    if best is None or best_c < MID_BAND:
        return None
    if path_exempt(reg, best.path) or carved_out(reg, sec.path, best.path):
        return None
    if best_c >= HIGH_BAND:
        if _is_home(reg, best.path, best.heading):
            return Finding("LA-DUP-2", "block", sec.path, sec.heading, round(best_c, 3),
                           best.path, best.heading,
                           f'Cite {best.path} §"{best.heading}" instead of restating it.')
        return Finding("LA-DUP-1", "block", sec.path, sec.heading, round(best_c, 3),
                       best.path, best.heading,
                       f'Duplicates {best.path} §"{best.heading}" — cite it or mark sync-intentional.')
    return Finding("LA-DUP-1", "info", sec.path, sec.heading, round(best_c, 3),
                   best.path, best.heading,
                   f'Overlaps {best.path} §"{best.heading}" (advisory).')


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


def evaluate_added_block(
    root: Path, source: str, block: str, registry: Path | None
) -> list[Finding]:
    """Score one added/edited block against the guarded-markdown corpus.

    Shared by the --added-text CLI path and the PreToolUse guard hook. `source`
    is repo-relative; `registry=None` defaults to `root/.lean-audit.toml`.
    Carve-outs and the sync-intentional override are honoured via score_section.
    """
    reg = load_registry(registry if registry is not None else root / ".lean-audit.toml")
    files = read_repo(root, root)
    files[source] = block
    index = build_index(files)
    targets = [s for s in index if s.path == source]
    return [f for f in (score_section(s, index, reg) for s in targets) if f is not None]


def scan(files: dict[str, str], reg: Registry) -> list[Finding]:
    index = build_index(files)
    findings = []
    for sec in index:
        f = score_section(sec, index, reg)
        if f is not None:
            findings.append(f)
    return findings


def slugify(heading: str) -> str:
    s = re.sub(r"[^\w\s-]", "", heading.strip().lower())
    return re.sub(r"\s+", "-", s)


def link_targets(text: str) -> list[str]:
    text = _INLINE_CODE.sub(" ", _FENCE.sub(" ", text))
    return [m.group(1) for m in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text)]


def _heading_slugs(text: str) -> set[str]:
    return {slugify(h) for h, _ in split_sections(text) if h}


def scan_stale_refs(files: dict[str, str], root=None) -> list[Finding]:
    findings: list[Finding] = []
    for path, text in files.items():
        parent = posixpath.dirname(path)
        for target in link_targets(text):
            if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith(("<", "//")):
                continue
            rel, _, anchor = target.partition("#")
            if rel == "":
                if anchor and slugify(anchor) not in _heading_slugs(text):
                    findings.append(Finding("LA-STALE-1", "warn", path, "", 0.0, "", "",
                        f"Anchor '#{anchor}' not found in this file."))
                continue
            resolved = posixpath.normpath(posixpath.join(parent, rel))
            present = resolved in files or (root is not None and (Path(root) / resolved).exists())
            if not present:
                findings.append(Finding("LA-STALE-1", "warn", path, "", 0.0, "", "",
                    f"Broken reference: {target} does not resolve."))
            elif anchor and resolved in files and slugify(anchor) not in _heading_slugs(files[resolved]):
                findings.append(Finding("LA-STALE-1", "warn", path, "", 0.0, "", "",
                    f"Broken anchor: '#{anchor}' not found in {resolved}."))
    return findings


def find_dead_refs(files: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        if "/references/" not in path and "/extensions/" not in path:
            continue
        name = posixpath.basename(path)
        if not any(name in text for other, text in files.items() if other != path):
            findings.append(Finding("LA-DEAD-1", "info", path, "", 0.0, "", "",
                f"No other guarded file mentions {name}; possibly dead weight."))
    return findings


BLOAT_BUDGET_LINES = 250


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[end + 4:].lstrip("\n")
    return text


def scan_bloat(files: dict[str, str]) -> list[Finding]:
    findings: list[Finding] = []
    for path, text in files.items():
        if posixpath.basename(path) != "SKILL.md":
            continue
        lines = len(strip_frontmatter(text).splitlines())
        if lines > BLOAT_BUDGET_LINES:
            findings.append(Finding("LA-BLOAT-1", "warn", path, "", 0.0, "", "",
                f"SKILL.md body is {lines} lines (> {BLOAT_BUDGET_LINES}); move heavy detail to references/."))
    return findings


def _glob_to_regex(pattern: str) -> str:
    out: list[str] = []
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == "{":
            j = pattern.find("}", i)
            if j == -1:
                out.append(re.escape(c)); i += 1
            else:
                out.append(f"(?P<{pattern[i + 1:j]}>[^/]+)")
                i = j + 1
        elif pattern[i:i + 3] == "**/":
            out.append("(?:.*/)?"); i += 3
        elif pattern[i:i + 2] == "**":
            out.append(".*"); i += 2
        elif c == "*":
            out.append("[^/]*"); i += 1
        elif c == "?":
            out.append("[^/]"); i += 1
        else:
            out.append(re.escape(c)); i += 1
    return "^" + "".join(out) + "$"


def path_captures(pattern: str, path: str) -> dict | None:
    m = re.match(_glob_to_regex(pattern), path)
    return m.groupdict() if m else None


BUILTIN_CARVE_OUTS = (("{plugin}/skills/{skill}/SKILL.md", "{plugin}/agents/{skill}.md"),)
BUILTIN_EXEMPT = (".claude/skills/**",)


def _pair_matches(a: str, b: str, x: str, y: str) -> bool:
    for pa, pb in ((a, b), (b, a)):
        ca = path_captures(pa, x)
        cb = path_captures(pb, y)
        if ca is not None and cb is not None:
            if all(ca[k] == cb[k] for k in (set(ca) & set(cb))):
                return True
    return False


def carved_out(reg: Registry, x: str, y: str) -> bool:
    if x == y:
        return False
    for a, b in BUILTIN_CARVE_OUTS + reg.carve_outs:
        if _pair_matches(a, b, x, y):
            return True
    return False


def path_exempt(reg: Registry, path: str) -> bool:
    return any(path_captures(p, path) is not None for p in BUILTIN_EXEMPT + reg.exempt_paths)


def _emit(findings: list[Finding], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps({"findings": [f.__dict__ for f in findings]}, indent=2))
    else:
        for f in findings:
            print(f"{f.code} [{f.severity}] {f.path} §\"{f.heading}\" "
                  f"(containment={f.containment}) -> {f.action}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="lean-audit duplication engine")
    ap.add_argument("scope", nargs="?", help="file or directory to scan")
    ap.add_argument("--added-text", metavar="-", help="read one block from stdin ('-')")
    ap.add_argument("--source", help="repo-relative path the stdin block belongs to")
    ap.add_argument("--corpus-root", default=".", help="repo root for the corpus")
    ap.add_argument("--registry", help="path to .lean-audit.toml")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    args = ap.parse_args(argv)

    if args.added_text is not None and args.added_text != "-":
        ap.error("--added-text only accepts '-' (read the block from stdin)")

    try:
        if args.added_text == "-":
            if not args.source:
                ap.error("--added-text requires --source")
            root = Path(args.corpus_root).resolve()
            registry = Path(args.registry) if args.registry else None
            block = sys.stdin.read()
            findings = evaluate_added_block(root, args.source, block, registry)
        else:
            if not args.scope:
                ap.error("scope is required")
            scope = Path(args.scope).resolve()
            root = scope if scope.is_dir() else scope.parent
            reg = load_registry(Path(args.registry) if args.registry else root / ".lean-audit.toml")
            files = read_repo(root, scope)
            findings = (scan(files, reg) + scan_stale_refs(files, root)
                        + find_dead_refs(files) + scan_bloat(files))
    except (OSError, tomllib.TOMLDecodeError, re.error) as exc:
        print(f"lean-audit: {exc}", file=sys.stderr)
        return 2

    _emit(findings, args.format)
    return 1 if any(f.severity == "block" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
