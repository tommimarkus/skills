"""lean-audit deterministic duplication engine (stdlib-only)."""
from __future__ import annotations

import re
from dataclasses import dataclass

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
