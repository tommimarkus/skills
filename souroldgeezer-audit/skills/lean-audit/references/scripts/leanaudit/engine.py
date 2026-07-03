"""lean-audit deterministic duplication engine (stdlib-only)."""

from __future__ import annotations

import argparse
import dataclasses
import json
import posixpath
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from leanaudit.discovery import read_repo
from leanaudit.registry import (
    Registry,
    carved_out,
    has_override,
    load_registry,
    path_exempt,
)

__all__ = [
    "BLOAT_BUDGET_LINES",
    "DEFAULT_K",
    "Finding",
    "HIGH_BAND",
    "MID_BAND",
    "MIN_TOKENS",
    "Section",
    "build_index",
    "containment",
    "evaluate_added_block",
    "find_dead_refs",
    "link_targets",
    "main",
    "normalize",
    "scan",
    "scan_bloat",
    "scan_stale_refs",
    "score_section",
    "shingle_set",
    "slugify",
    "split_sections",
    "strip_frontmatter",
]

_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]*`")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_WORD = re.compile(r"[a-z0-9]+")
_HEADING = re.compile(r"^#{1,6}\s+(.*)$")

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


def containment(added: frozenset[tuple[str, ...]], other: frozenset[tuple[str, ...]]) -> float:
    return len(added & other) / len(added) if added else 0.0


@dataclass(frozen=True)
class Section:
    path: str
    heading: str
    body: str
    shingles: frozenset[tuple[str, ...]]


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
            return Finding(
                "LA-DUP-2",
                "block",
                sec.path,
                sec.heading,
                round(best_c, 3),
                best.path,
                best.heading,
                f'Cite {best.path} §"{best.heading}" instead of restating it.',
            )
        return Finding(
            "LA-DUP-1",
            "block",
            sec.path,
            sec.heading,
            round(best_c, 3),
            best.path,
            best.heading,
            f'Duplicates {best.path} §"{best.heading}" — cite it or mark sync-intentional.',
        )
    return Finding(
        "LA-DUP-1",
        "info",
        sec.path,
        sec.heading,
        round(best_c, 3),
        best.path,
        best.heading,
        f'Overlaps {best.path} §"{best.heading}" (advisory).',
    )


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


def scan_stale_refs(files: dict[str, str], root: Path | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for path, text in files.items():
        parent = posixpath.dirname(path)
        for target in link_targets(text):
            if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith(("<", "//")):
                continue
            rel, _, anchor = target.partition("#")
            if rel == "":
                if anchor and slugify(anchor) not in _heading_slugs(text):
                    findings.append(
                        Finding(
                            "LA-STALE-1",
                            "warn",
                            path,
                            "",
                            0.0,
                            "",
                            "",
                            f"Anchor '#{anchor}' not found in this file.",
                        )
                    )
                continue
            resolved = posixpath.normpath(posixpath.join(parent, rel))
            present = resolved in files or (root is not None and (Path(root) / resolved).exists())
            if not present:
                findings.append(
                    Finding(
                        "LA-STALE-1",
                        "warn",
                        path,
                        "",
                        0.0,
                        "",
                        "",
                        f"Broken reference: {target} does not resolve.",
                    )
                )
            elif (
                anchor
                and resolved in files
                and slugify(anchor) not in _heading_slugs(files[resolved])
            ):
                findings.append(
                    Finding(
                        "LA-STALE-1",
                        "warn",
                        path,
                        "",
                        0.0,
                        "",
                        "",
                        f"Broken anchor: '#{anchor}' not found in {resolved}.",
                    )
                )
    return findings


def find_dead_refs(files: dict[str, str]) -> list[Finding]:
    """Flag references/ or extensions/ files whose basename no other guarded file
    mentions — likely dead weight nothing loads."""
    findings: list[Finding] = []
    for path in files:
        if "/references/" not in path and "/extensions/" not in path:
            continue
        name = posixpath.basename(path)
        if not any(name in text for other, text in files.items() if other != path):
            findings.append(
                Finding(
                    "LA-DEAD-1",
                    "info",
                    path,
                    "",
                    0.0,
                    "",
                    "",
                    f"No other guarded file mentions {name}; possibly dead weight.",
                )
            )
    return findings


BLOAT_BUDGET_LINES = 250


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[end + 4 :].lstrip("\n")
    return text


def scan_bloat(files: dict[str, str]) -> list[Finding]:
    """Flag SKILL.md bodies (frontmatter stripped) that exceed BLOAT_BUDGET_LINES."""
    findings: list[Finding] = []
    for path, text in files.items():
        if posixpath.basename(path) != "SKILL.md":
            continue
        lines = len(strip_frontmatter(text).splitlines())
        if lines > BLOAT_BUDGET_LINES:
            findings.append(
                Finding(
                    "LA-BLOAT-1",
                    "warn",
                    path,
                    "",
                    0.0,
                    "",
                    "",
                    f"SKILL.md body is {lines} lines (> {BLOAT_BUDGET_LINES}); "
                    "move heavy detail to references/.",
                )
            )
    return findings


def _emit(findings: list[Finding], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps({"findings": [dataclasses.asdict(f) for f in findings]}, indent=2))
    else:
        for f in findings:
            print(
                f'{f.code} [{f.severity}] {f.path} §"{f.heading}" '
                f"(containment={f.containment}) -> {f.action}"
            )


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
    if args.registry and not Path(args.registry).is_file():
        print(
            f"lean-audit: --registry {args.registry} not found; scanning with default config",
            file=sys.stderr,
        )

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
            findings = (
                scan(files, reg)
                + scan_stale_refs(files, root)
                + find_dead_refs(files)
                + scan_bloat(files)
            )
    except (OSError, tomllib.TOMLDecodeError, re.error) as exc:
        print(f"lean-audit: {exc}", file=sys.stderr)
        return 2

    _emit(findings, args.format)
    return 1 if any(f.severity == "block" for f in findings) else 0
