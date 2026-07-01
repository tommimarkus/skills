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

DEFAULT_MIN_CLONE_TOKENS = 20
INTENTIONAL_MARKER = "lean-audit:dup-intentional"

# ext -> (line_comment_prefixes, block_comment_pairs, string_quotes, raw_string_quotes)
# raw_string_quotes are scanned verbatim — no backslash escapes (e.g. Go backticks).
# A run of three identical string-quote chars ("""/''' etc.) is a triple-quoted
# string emitted as one STR token, NOT stripped as a comment, so multi-line string
# VALUES (SQL, templates) and docstrings survive normalization as one token.
COMMENT_PROFILES: dict[str, tuple] = {
    ".py":    (("#",),      (),                    ('"', "'"),      ()),
    ".js":    (("//",),     (("/*", "*/"),),       ('"', "'", "`"), ()),
    ".jsx":   (("//",),     (("/*", "*/"),),       ('"', "'", "`"), ()),
    ".ts":    (("//",),     (("/*", "*/"),),       ('"', "'", "`"), ()),
    ".tsx":   (("//",),     (("/*", "*/"),),       ('"', "'", "`"), ()),
    ".java":  (("//",),     (("/*", "*/"),),       ('"',),          ()),
    ".go":    (("//",),     (("/*", "*/"),),       ('"',),          ("`",)),
    ".rs":    (("//",),     (("/*", "*/"),),       ('"',),          ()),
    ".c":     (("//",),     (("/*", "*/"),),       ('"',),          ()),
    ".h":     (("//",),     (("/*", "*/"),),       ('"',),          ()),
    ".cpp":   (("//",),     (("/*", "*/"),),       ('"',),          ()),
    ".cs":    (("//",),     (("/*", "*/"),),       ('"',),          ()),
    ".rb":    (("#",),      (("=begin", "=end"),), ('"', "'"),      ()),
    ".sh":    (("#",),      (),                    ('"', "'"),      ()),
    ".kt":    (("//",),     (("/*", "*/"),),       ('"', "'"),      ()),
    ".swift": (("//",),     (("/*", "*/"),),       ('"',),          ()),
    ".php":   (("//", "#"), (("/*", "*/"),),       ('"', "'"),      ()),
    ".scala": (("//",),     (("/*", "*/"),),       ('"', "'"),      ()),
}
GENERIC_PROFILE = ((), (), ('"', "'"), ())
DEFAULT_EXTENSIONS = tuple(COMMENT_PROFILES)


def profile_for(ext: str) -> tuple:
    return COMMENT_PROFILES.get(ext, GENERIC_PROFILE)


def _is_number(w: str) -> bool:
    """True for integer / hex / binary / octal / underscored / simple-scientific
    literals, so numeric constants normalize to a single NUM regardless of base or
    digit grouping (e.g. 0xFF, 1_000, 1e9 — not just plain decimals)."""
    s = w.replace("_", "")
    if not s:
        return False
    low = s.lower()
    if low[:2] in ("0x", "0b", "0o"):
        return len(low) > 2 and all(ch.isalnum() for ch in low[2:])
    if "e" in low:                       # <digits>e<[+/-]digits> scientific integer form
        mant, _, exp = low.partition("e")
        exp_ok = exp.isdigit() or (exp[:1] in "+-" and exp[1:].isdigit())
        return mant.isdigit() and exp_ok
    return s.isdigit()


def strip_and_tokenize(text: str, profile: tuple) -> list[tuple[str, int]]:
    line_comments, block_comments, quotes, raw_quotes = profile
    tokens: list[tuple[str, int]] = []
    i, n, line = 0, len(text), 1
    word: list[str] = []
    word_line = 1

    def flush() -> None:
        nonlocal word
        if word:
            w = "".join(word)
            tokens.append(("NUM" if _is_number(w) else w, word_line))
            word = []

    def at_line_start(pos: int) -> bool:
        return pos == 0 or text[pos - 1] == "\n"

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
        # Block comments. An opener whose first char is a letter or '=' (Ruby
        # =begin/=end) is a comment only at column 0; symbol openers like /* match
        # anywhere. Without this anchor a mid-line `=begin` swallows the rest of file.
        bpair = next(((o, cl) for o, cl in block_comments
                      if text.startswith(o, i)
                      and (not (o[:1].isalpha() or o[:1] == "=") or at_line_start(i))),
                     None)
        if bpair is not None:
            flush()
            o, cl = bpair
            j = text.find(cl, i + len(o))
            end = n if j == -1 else j + len(cl)
            line += text.count("\n", i, end)
            i = end
            continue
        if c in raw_quotes:                # verbatim string: no escapes (Go backtick)
            flush()
            start_line = line
            j = i + 1
            while j < n and text[j] != c:
                if text[j] == "\n":
                    line += 1
                j += 1
            tokens.append(("STR", start_line))
            i = j + 1 if j < n else n
            continue
        if c in quotes:
            flush()
            start_line = line
            if text.startswith(c * 3, i):  # triple-quoted string value / docstring
                close = c * 3
                j = i + 3
                while j < n and not text.startswith(close, j):
                    if text[j] == "\n":
                        line += 1
                    j += 1
                tokens.append(("STR", start_line))
                i = j + 3 if j < n else n
                continue
            j = i + 1
            while j < n and text[j] != c:
                if text[j] == "\\":        # escape: skip next char, counting a newline
                    if j + 1 < n and text[j + 1] == "\n":
                        line += 1
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


def _dedupe(clones: list[Clone]) -> list[Clone]:
    """Drop a clone whose reported region is fully contained within a larger clone
    of the same file pair. Periodic/tandem repeats otherwise surface the same lines
    at multiple scales (an LA-CODE-DUP-2 nested inside an LA-CODE-DUP-1)."""
    def span(s: str) -> tuple[int, int]:
        a, b = s.split("-")
        return int(a), int(b)

    out: list[Clone] = []
    for c in clones:
        ca0, ca1 = span(c.lines)
        pair = frozenset((c.path, c.matched_path))
        subsumed = any(
            o is not c
            and frozenset((o.path, o.matched_path)) == pair
            and o.tokens > c.tokens
            and o.path == c.path
            and span(o.lines)[0] <= ca0 and ca1 <= span(o.lines)[1]
            for o in clones
        )
        if not subsumed:
            out.append(c)
    return out


def find_clones(streams: dict[str, list[tuple[str, int]]], min_tokens: int) -> list[Clone]:
    if min_tokens < 1:
        raise ValueError("min_tokens must be >= 1")
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
        if meta[i][0] != meta[i + k - 1][0]:   # seed window straddles a file boundary — skip
            i += 1
            continue
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
                            f"shared code, or add a `{INTENTIONAL_MARKER}` comment "
                            f"anywhere in either file to suppress its clones.")))
                i += length
                continue
        seen.setdefault(gram, i)
        i += 1
    return _dedupe(clones)


# Path SEGMENTS (or contiguous segment runs) that are never source of interest.
# Matched as whole segments, not substrings, so e.g. a `mydist/` dir is not caught
# by `dist`. On the non-git fallback path this is the only exclusion; in git mode
# repo_paths already drops ignored trees.
_EXCLUDE = (
    ("node_modules",), ("dist",), ("build",), ("target",), (".venv",),
    (".cache",), (".git",), (".worktrees",), (".claude", "worktrees"),
    ("docs", "superpowers"),
)


def load_config(registry_path: Path | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if registry_path is None or not Path(registry_path).is_file():
        return (), DEFAULT_EXTENSIONS
    data = tomllib.loads(Path(registry_path).read_text(encoding="utf-8"))
    exempt = tuple(data.get("exempt_paths", ()))
    exts = tuple(data.get("code_extensions", DEFAULT_EXTENSIONS))
    return exempt, exts


def _is_excluded(rel: str) -> bool:
    segs = rel.split("/")
    return any(
        any(segs[start:start + len(pat)] == list(pat)
            for start in range(len(segs) - len(pat) + 1))
        for pat in _EXCLUDE
    )


def read_sources(root: Path, exts: tuple[str, ...], exempt: tuple[str, ...]) -> dict[str, str]:
    files: dict[str, str] = {}
    in_repo = lean_engine.repo_paths(root)   # reused via sibling import (see file header)
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if in_repo is not None and rel not in in_repo:
            continue
        if _is_excluded(rel) or path.suffix not in exts:
            continue
        if any(fnmatch.fnmatch(rel, pat) for pat in exempt):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if INTENTIONAL_MARKER in text:
            continue
        files[rel] = text
    return files


def scan_dir(root: Path, min_tokens: int, registry: Path | None) -> list[Clone]:
    reg = registry if registry is not None else root / ".lean-audit.toml"
    exempt, exts = load_config(reg)
    sources = read_sources(root, exts, exempt)
    streams = {rel: strip_and_tokenize(text, profile_for(Path(rel).suffix))
               for rel, text in sources.items()}
    return find_clones(streams, min_tokens)


def _emit(clones: list[Clone], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps({"findings": [c.__dict__ for c in clones]}, indent=2))
    else:
        for c in clones:
            print(f"{c.code} [{c.severity}] {c.path}:{c.lines} == "
                  f"{c.matched_path}:{c.matched_lines} ({c.tokens} tokens) -> {c.action}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="lean-audit code-duplication lens")
    ap.add_argument("scope", help="directory to scan")
    ap.add_argument("--min-tokens", type=int, default=DEFAULT_MIN_CLONE_TOKENS)
    ap.add_argument("--registry", help="path to .lean-audit.toml")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    args = ap.parse_args(argv)
    if args.min_tokens < 1:
        print("lean-audit code_lens: --min-tokens must be >= 1", file=sys.stderr)
        return 2
    if args.registry and not Path(args.registry).is_file():
        print(f"lean-audit code_lens: --registry {args.registry} not found; "
              f"scanning with default config", file=sys.stderr)
    try:
        scope = Path(args.scope).resolve()
        root = scope if scope.is_dir() else scope.parent
        registry = Path(args.registry) if args.registry else None
        clones = scan_dir(root, args.min_tokens, registry)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        print(f"lean-audit code_lens: {exc}", file=sys.stderr)
        return 2
    _emit(clones, args.format)
    return 1 if any(c.severity == "block" for c in clones) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
