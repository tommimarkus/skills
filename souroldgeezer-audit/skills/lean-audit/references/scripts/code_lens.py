"""lean-audit code-duplication lens (stdlib-only).

Detects mechanical copy-paste clones in source via token-window seed-and-extend.
Sibling to lean_engine.py (markdown waste); reuses lean_engine.repo_paths for
git-aware discovery via the repo's sibling-import pattern (see lean_guard.py:18).
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lean_engine  # noqa: E402  (repo sibling-import pattern; see lean_guard.py:18)

DEFAULT_MIN_CLONE_TOKENS = 50
INTENTIONAL_MARKER = "lean-audit:dup-intentional"

# ext -> (line_comment_prefixes, block_comment_pairs, string_quotes)
COMMENT_PROFILES: dict[str, tuple] = {
    ".py":   (("#",), (('"""', '"""'), ("'''", "'''")), ('"', "'")),
    ".js":   (("//",), (("/*", "*/"),), ('"', "'", "`")),
    ".jsx":  (("//",), (("/*", "*/"),), ('"', "'", "`")),
    ".ts":   (("//",), (("/*", "*/"),), ('"', "'", "`")),
    ".tsx":  (("//",), (("/*", "*/"),), ('"', "'", "`")),
    ".java": (("//",), (("/*", "*/"),), ('"',)),
    ".go":   (("//",), (("/*", "*/"),), ('"', "`")),
    ".rs":   (("//",), (("/*", "*/"),), ('"',)),
    ".c":    (("//",), (("/*", "*/"),), ('"',)),
    ".h":    (("//",), (("/*", "*/"),), ('"',)),
    ".cpp":  (("//",), (("/*", "*/"),), ('"',)),
    ".cs":   (("//",), (("/*", "*/"),), ('"',)),
    ".rb":   (("#",),  (("=begin", "=end"),), ('"', "'")),
    ".sh":   (("#",),  (), ('"', "'")),
}
GENERIC_PROFILE = ((), (), ('"', "'"))
DEFAULT_EXTENSIONS = tuple(COMMENT_PROFILES) + (".kt", ".swift", ".php", ".scala")


def profile_for(ext: str) -> tuple:
    return COMMENT_PROFILES.get(ext, GENERIC_PROFILE)


def strip_and_tokenize(text: str, profile: tuple) -> list[tuple[str, int]]:
    line_comments, block_comments, quotes = profile
    tokens: list[tuple[str, int]] = []
    i, n, line = 0, len(text), 1
    word: list[str] = []
    word_line = 1

    def flush() -> None:
        nonlocal word
        if word:
            w = "".join(word)
            tokens.append(("NUM" if w.isdigit() else w, word_line))
            word = []

    while i < n:
        c = text[i]
        if c == "\n":
            flush(); line += 1; i += 1; continue
        lc = next((p for p in line_comments if text.startswith(p, i)), None)
        if lc is not None:
            flush()
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        bpair = next(((o, cl) for o, cl in block_comments if text.startswith(o, i)), None)
        if bpair is not None:
            flush()
            o, cl = bpair
            j = text.find(cl, i + len(o))
            end = n if j == -1 else j + len(cl)
            line += text.count("\n", i, end)
            i = end
            continue
        if c in quotes:
            flush()
            start_line = line
            j = i + 1
            while j < n and text[j] != c:
                if text[j] == "\\":
                    j += 2; continue
                if text[j] == "\n":
                    line += 1
                j += 1
            tokens.append(("STR", start_line))
            i = j + 1 if j < n else n
            continue
        if c.isalnum() or c == "_":
            if not word:
                word_line = line
            word.append(c); i += 1; continue
        flush()
        if not c.isspace():
            tokens.append((c, line))
        i += 1
    flush()
    return tokens


@dataclass(frozen=True)
class Clone:
    code: str
    severity: str
    path: str
    lines: str
    matched_path: str
    matched_lines: str
    tokens: int
    action: str


def find_clones(streams: dict[str, list[tuple[str, int]]], min_tokens: int) -> list[Clone]:
    k = min_tokens
    seq: list[str] = []
    meta: list[tuple[str, int]] = []          # (path, local_index)
    per_file: dict[str, list[tuple[str, int]]] = {}
    for path in sorted(streams):
        toks = streams[path]
        per_file[path] = toks
        for li in range(len(toks)):
            seq.append(toks[li][0]); meta.append((path, li))
    n = len(seq)
    clones: list[Clone] = []
    seen: dict[tuple, int] = {}
    i = 0
    while i + k <= n:
        gram = tuple(seq[i:i + k])
        if gram in seen:
            j = seen[gram]
            length = k
            while (i + length < n and j + length < i
                   and seq[i + length] == seq[j + length]
                   and meta[i + length][0] == meta[i][0]
                   and meta[j + length][0] == meta[j][0]):
                length += 1
            pj, lj = meta[j]
            pi, li = meta[i]
            overlap = pj == pi and lj + length > li
            if not overlap:
                j0, j1 = per_file[pj][lj][1], per_file[pj][lj + length - 1][1]
                i0, i1 = per_file[pi][li][1], per_file[pi][li + length - 1][1]
                severity = "block" if length >= 2 * min_tokens else "info"
                code = "LA-CODE-DUP-1" if severity == "block" else "LA-CODE-DUP-2"
                clones.append(Clone(
                    code=code, severity=severity,
                    path=pj, lines=f"{j0}-{j1}",
                    matched_path=pi, matched_lines=f"{i0}-{i1}",
                    tokens=length,
                    action=(f"Clone of {pj}:{j0}-{j1} ({length} tokens) — extract "
                            f"shared code or mark // {INTENTIONAL_MARKER}.")))
                i += length
                continue
        seen.setdefault(gram, i)
        i += 1
    return clones
