"""lean-audit deterministic duplication engine (stdlib-only)."""
from __future__ import annotations

import fnmatch
import re
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
    must_sync: tuple[tuple[str, ...], ...]


def load_registry(path: Path | None) -> Registry:
    if path is None or not Path(path).is_file():
        return Registry(canonical_homes=(), must_sync=())
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    homes = tuple(
        (h["path"], h["heading"]) for h in data.get("canonical_home", []) if "path" in h and "heading" in h
    )
    syncs = tuple(tuple(g["globs"]) for g in data.get("must_sync", []) if g.get("globs"))
    return Registry(canonical_homes=homes, must_sync=syncs)


def has_override(text: str) -> bool:
    return OVERRIDE.search(text) is not None


def must_sync_pair(reg: Registry, a: str, b: str) -> bool:
    for globs in reg.must_sync:
        if any(fnmatch.fnmatch(a, g) for g in globs) and any(fnmatch.fnmatch(b, g) for g in globs):
            return True
    return False


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
    if must_sync_pair(reg, sec.path, best.path):
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
