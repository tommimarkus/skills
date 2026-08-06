"""lean-audit code-duplication lens (stdlib-only).

Detects mechanical copy-paste clones in source via token-window seed-and-extend.
Sibling to leanaudit.engine (markdown waste); reuses leanaudit.discovery.repo_paths
for git-aware discovery via the repo's sibling-import pattern (see the lean_guard.py
shim).
"""

from __future__ import annotations

# Engine import scaffolding intentionally mirrors the markdown engine.
# lean-audit:dup-intentional:begin
import argparse
import dataclasses
import fnmatch
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from leanaudit.cli import add_shared_flags
from leanaudit.discovery import repo_paths
# lean-audit:dup-intentional:end

# (line_comment_prefixes, block_comment_pairs, string_quotes, raw_string_quotes)
CommentProfile = tuple[
    tuple[str, ...], tuple[tuple[str, str], ...], tuple[str, ...], tuple[str, ...]
]

__all__ = [
    "COMMENT_PROFILES",
    "Clone",
    "CommentProfile",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_MIN_CLONE_TOKENS",
    "GENERIC_PROFILE",
    "INTENTIONAL_MARKER",
    "find_clones",
    "load_config",
    "main",
    "profile_for",
    "read_sources",
    "scan_dir",
    "strip_and_tokenize",
]

DEFAULT_MIN_CLONE_TOKENS = 20
INTENTIONAL_MARKER = "lean-audit:dup-intentional"

# The marker only counts inside a LINE COMMENT of the file's own language, mirroring
# how the markdown side anchors its override to an HTML comment (registry.OVERRIDE).
# A bare string assignment of the marker text — such as the line just above, in this
# very module — is NOT a declaration; anchoring is what stops the engine from
# silently exempting its own source from its own corpus.
#
# Two scopes:
#   whole file  <line-comment> <marker> [— rationale]        (drops the file in read_sources)
#   region      <line-comment> <marker>:begin … :end         (post-filtered in scan_dir)
# An unrecognized suffix degrades to the whole-file form (the backward-compatible read).
#
# 1-based inclusive (first_line, last_line) spans, in source order.
_LineSpans = tuple[tuple[int, int], ...]
_MARKER_RE_CACHE: dict[tuple[str, ...], re.Pattern[str] | None] = {}


def _marker_re(line_comments: tuple[str, ...]) -> re.Pattern[str] | None:
    """Compiled marker matcher for a language whose line-comment openers are
    `line_comments`; None when the language has none (GENERIC_PROFILE), which can
    therefore carry no marker. Group `scope` is `begin`/`end`, or None for the
    whole-file form."""
    if line_comments not in _MARKER_RE_CACHE:
        opener = "|".join(re.escape(p) for p in line_comments)
        _MARKER_RE_CACHE[line_comments] = (
            re.compile(
                rf"(?:{opener})[^\n]*?{re.escape(INTENTIONAL_MARKER)}"
                rf"(?::(?P<scope>begin|end))?(?![\w-])"
            )
            if line_comments
            else None
        )
    return _MARKER_RE_CACHE[line_comments]


def _has_whole_file_marker(text: str, profile: CommentProfile) -> bool:
    """True when a line comment declares the file-wide (suffix-less) marker."""
    rx = _marker_re(profile[0])
    return rx is not None and any(m.group("scope") is None for m in rx.finditer(text))


def _marked_regions(text: str, profile: CommentProfile) -> _LineSpans:
    """1-based inclusive line spans of `:begin` … `:end` marker regions.

    A RAW-TEXT line scan: markers live in comments, which strip_and_tokenize removes
    before the token stream exists (pinned by ledger case LCD-T0002). Clone.lines /
    Clone.matched_lines are source line ranges, so these spans intersect directly.

    Defined behaviour at the edges: nesting is depth-counted, so an inner pair does
    not close the outer region; a `:begin` that is never closed runs to end of file
    (declaring intent conservatively rather than silently doing nothing); a `:end`
    with no open region is ignored.
    """
    rx = _marker_re(profile[0])
    if rx is None:
        return ()
    lines = text.splitlines()
    regions: list[tuple[int, int]] = []
    depth, start = 0, 1
    for no, line in enumerate(lines, start=1):
        match = rx.search(line)
        if match is None:
            continue
        scope = match.group("scope")
        if scope == "begin":
            if depth == 0:
                start = no
            depth += 1
        elif scope == "end" and depth:
            depth -= 1
            if depth == 0:
                regions.append((start, no))
    if depth:
        regions.append((start, max(len(lines), start)))
    return tuple(regions)


# A clone window dominated by normalized literals/punctuation is data shape
# (an __all__ list, a path table), not copied logic. Require a minimum number
# of DISTINCT identifier tokens before a window may be reported. Private
# tuning knob (leanaudit convention: non-`__all__` names carry a `_` prefix).
_MIN_DISTINCT_IDENTIFIERS = 4

_IDENTIFIER_RE = re.compile(r"[A-Za-z_]\w*\Z")


def _identifier_diverse(window: list[str]) -> bool:
    idents = {t for t in window if t not in ("STR", "NUM") and _IDENTIFIER_RE.match(t)}
    return len(idents) >= _MIN_DISTINCT_IDENTIFIERS


# ext -> (line_comment_prefixes, block_comment_pairs, string_quotes, raw_string_quotes)
# raw_string_quotes are scanned verbatim — no backslash escapes (e.g. Go backticks).
# A run of three identical string-quote chars ("""/''' etc.) is a triple-quoted
# string emitted as one STR token, NOT stripped as a comment, so multi-line string
# VALUES (SQL, templates) and docstrings survive normalization as one token.
COMMENT_PROFILES: dict[str, CommentProfile] = {
    ".py": (("#",), (), ('"', "'"), ()),
    ".js": (("//",), (("/*", "*/"),), ('"', "'", "`"), ()),
    ".jsx": (("//",), (("/*", "*/"),), ('"', "'", "`"), ()),
    ".ts": (("//",), (("/*", "*/"),), ('"', "'", "`"), ()),
    ".tsx": (("//",), (("/*", "*/"),), ('"', "'", "`"), ()),
    ".java": (("//",), (("/*", "*/"),), ('"',), ()),
    ".go": (("//",), (("/*", "*/"),), ('"',), ("`",)),
    ".rs": (("//",), (("/*", "*/"),), ('"',), ()),
    ".c": (("//",), (("/*", "*/"),), ('"',), ()),
    ".h": (("//",), (("/*", "*/"),), ('"',), ()),
    ".cpp": (("//",), (("/*", "*/"),), ('"',), ()),
    ".cs": (("//",), (("/*", "*/"),), ('"',), ()),
    ".rb": (("#",), (("=begin", "=end"),), ('"', "'"), ()),
    ".sh": (("#",), (), ('"', "'"), ()),
    ".kt": (("//",), (("/*", "*/"),), ('"', "'"), ()),
    ".swift": (("//",), (("/*", "*/"),), ('"',), ()),
    ".php": (("//", "#"), (("/*", "*/"),), ('"', "'"), ()),
    ".scala": (("//",), (("/*", "*/"),), ('"', "'"), ()),
}
GENERIC_PROFILE = ((), (), ('"', "'"), ())
DEFAULT_EXTENSIONS = tuple(COMMENT_PROFILES)


def profile_for(ext: str) -> CommentProfile:
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
    if "e" in low:  # <digits>e<[+/-]digits> scientific integer form
        mant, _, exp = low.partition("e")
        exp_ok = exp.isdigit() or (exp[:1] in "+-" and exp[1:].isdigit())
        return mant.isdigit() and exp_ok
    return s.isdigit()


def _scan_string(
    text: str, n: int, start: int, close: str, line: int, escapes: bool
) -> tuple[int, int]:
    """Advance past a string body that begins at `start` and runs to the next `close`.

    Returns `(index just past the string, line number at that index)`. The three
    string forms strip_and_tokenize handles differ only in these two parameters:
    `close` is the terminator (a quote char, or a `\"\"\"`-style run), and `escapes`
    says whether a backslash consumes the next character — raw strings (Go
    backticks) and triple-quoted strings scan verbatim, single-quoted ones do not.

    An UNTERMINATED string runs to EOF and returns `n`, so a stray quote costs the
    rest of the file's tokens rather than desynchronising the stream. Newlines
    crossed (including one hidden behind a backslash escape) are counted, because
    the caller's `("STR", start_line)` token and every token after it carry source
    line numbers that the region-marker suppression intersects against.
    """
    j = start
    while j < n and not text.startswith(close, j):
        if escapes and text[j] == "\\":  # escape: skip next char, counting a newline
            if j + 1 < n and text[j + 1] == "\n":
                line += 1
            j += 2
            continue
        if text[j] == "\n":
            line += 1
        j += 1
    return (j + len(close) if j < n else n), line


def strip_and_tokenize(text: str, profile: CommentProfile) -> list[tuple[str, int]]:
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
            flush()
            line += 1
            i += 1
            continue
        lc = next((p for p in line_comments if text.startswith(p, i)), None)
        if lc is not None:
            flush()
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        # Block comments. An opener whose first char is a letter or '=' (Ruby
        # =begin/=end) is a comment only at column 0; symbol openers like /* match
        # anywhere. Without this anchor a mid-line `=begin` swallows the rest of file.
        bpair = next(
            (
                (o, cl)
                for o, cl in block_comments
                if text.startswith(o, i)
                and (not (o[:1].isalpha() or o[:1] == "=") or at_line_start(i))
            ),
            None,
        )
        if bpair is not None:
            flush()
            o, cl = bpair
            j = text.find(cl, i + len(o))
            end = n if j == -1 else j + len(cl)
            line += text.count("\n", i, end)
            i = end
            continue
        if c in raw_quotes:  # verbatim string: no escapes (Go backtick)
            flush()
            start_line = line
            i, line = _scan_string(text, n, i + 1, c, line, escapes=False)
            tokens.append(("STR", start_line))
            continue
        if c in quotes:
            flush()
            start_line = line
            # A run of three identical quotes opens a triple-quoted string value /
            # docstring, which — like a raw string — is scanned verbatim.
            triple = text.startswith(c * 3, i)
            close = c * 3 if triple else c
            i, line = _scan_string(text, n, i + len(close), close, line, escapes=not triple)
            tokens.append(("STR", start_line))
            continue
        if c.isalnum() or c == "_":
            if not word:
                word_line = line
            word.append(c)
            i += 1
            continue
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


def _span(s: str) -> tuple[int, int]:
    """A `"<first>-<last>"` line range as an inclusive (first, last) pair."""
    a, b = s.split("-")
    return int(a), int(b)


def _dedupe(clones: list[Clone]) -> list[Clone]:
    """Drop a clone whose reported region is fully contained within a larger clone
    of the same file pair. Periodic/tandem repeats otherwise surface the same lines
    at multiple scales (an LA-CODE-DUP-2 nested inside an LA-CODE-DUP-1)."""
    out: list[Clone] = []
    for c in clones:
        ca0, ca1 = _span(c.lines)
        pair = frozenset((c.path, c.matched_path))
        subsumed = any(
            o is not c
            and frozenset((o.path, o.matched_path)) == pair
            and o.tokens > c.tokens
            and o.path == c.path
            and _span(o.lines)[0] <= ca0
            and ca1 <= _span(o.lines)[1]
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
    meta: list[tuple[str, int]] = []  # (path, local_index)
    per_file: dict[str, list[tuple[str, int]]] = {}
    for path in sorted(streams):
        toks = streams[path]
        per_file[path] = toks
        for li in range(len(toks)):
            seq.append(toks[li][0])
            meta.append((path, li))
    n = len(seq)
    clones: list[Clone] = []
    seen: dict[tuple[str, ...], int] = {}
    i = 0
    while i + k <= n:
        if meta[i][0] != meta[i + k - 1][0]:  # seed window straddles a file boundary — skip
            i += 1
            continue
        gram = tuple(seq[i : i + k])
        if gram in seen:
            j = seen[gram]
            length = k
            while (
                i + length < n
                and j + length < i
                and seq[i + length] == seq[j + length]
                and meta[i + length][0] == meta[i][0]
                and meta[j + length][0] == meta[j][0]
            ):
                length += 1
            pj, lj = meta[j]
            pi, li = meta[i]
            overlap = pj == pi and lj + length > li
            if not overlap:
                window_tokens = seq[i : i + length]  # matched window's token texts
                if not _identifier_diverse(window_tokens):
                    i += 1  # declarative literal/punctuation shape, not copied logic
                    continue
                j0, j1 = per_file[pj][lj][1], per_file[pj][lj + length - 1][1]
                i0, i1 = per_file[pi][li][1], per_file[pi][li + length - 1][1]
                severity = "block" if length >= 2 * min_tokens else "info"
                code = "LA-CODE-DUP-1" if severity == "block" else "LA-CODE-DUP-2"
                clones.append(
                    Clone(
                        code=code,
                        severity=severity,
                        path=pj,
                        lines=f"{j0}-{j1}",
                        matched_path=pi,
                        matched_lines=f"{i0}-{i1}",
                        tokens=length,
                        action=(
                            f"Clone of {pj}:{j0}-{j1} ({length} tokens) — extract "
                            f"shared code, or declare it intentional in a line "
                            f"comment in either file: wrap just this span in "
                            f"`{INTENTIONAL_MARKER}:begin` / "
                            f"`{INTENTIONAL_MARKER}:end` (preferred), or put a bare "
                            f"`{INTENTIONAL_MARKER} — <rationale>` comment anywhere "
                            f"in the file to exempt the whole file."
                        ),
                    )
                )
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
    ("node_modules",),
    ("dist",),
    ("build",),
    ("target",),
    (".venv",),
    (".cache",),
    (".git",),
    (".worktrees",),
    (".claude", "worktrees"),
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
        any(
            segs[start : start + len(pat)] == list(pat) for start in range(len(segs) - len(pat) + 1)
        )
        for pat in _EXCLUDE
    )


def read_sources(root: Path, exts: tuple[str, ...], exempt: tuple[str, ...]) -> dict[str, str]:
    files: dict[str, str] = {}
    in_repo = repo_paths(root)  # reused via sibling import (see file header)
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
        # Only the whole-file marker form drops a file here. A file carrying just
        # region markers stays in the corpus; scan_dir post-filters its clones.
        if _has_whole_file_marker(text, profile_for(path.suffix)):
            continue
        files[rel] = text
    return files


def _region_suppressed(clone: Clone, regions: dict[str, _LineSpans]) -> bool:
    """CONTAINMENT, both sides: a clone is suppressed when EITHER of its two sides
    lies wholly inside ONE marked region of that side's own file. Either-side
    mirrors the whole-file marker (a declaration in one file suppresses the pair);
    containment (not overlap) keeps a one-line marked touch from killing a long
    clone, and requiring a single region keeps two adjacent regions from jointly
    covering a span that neither of them declared."""

    def inside(lines: str, path: str) -> bool:
        lo, hi = _span(lines)
        return any(r0 <= lo and hi <= r1 for r0, r1 in regions.get(path, ()))

    return inside(clone.lines, clone.path) or inside(clone.matched_lines, clone.matched_path)


def scan_dir(root: Path, min_tokens: int, registry: Path | None) -> list[Clone]:
    reg = registry if registry is not None else root / ".lean-audit.toml"
    exempt, exts = load_config(reg)
    sources = read_sources(root, exts, exempt)
    streams: dict[str, list[tuple[str, int]]] = {}
    regions: dict[str, _LineSpans] = {}
    for rel, text in sources.items():
        profile = profile_for(Path(rel).suffix)
        streams[rel] = strip_and_tokenize(text, profile)
        regions[rel] = _marked_regions(text, profile)
    # Region suppression is a POST-filter, not a read_sources filter: read_sources is
    # a published re-export (see the scripts/README shim contract), so narrowing what
    # it returns would be a breaking change; dropping clones here is additive.
    return [c for c in find_clones(streams, min_tokens) if not _region_suppressed(c, regions)]


# The two engines preserve parallel, engine-specific emitters instead of a generic CLI layer.
# lean-audit:dup-intentional:begin
def _emit(clones: list[Clone], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps({"findings": [dataclasses.asdict(c) for c in clones]}, indent=2))
    else:
        for c in clones:
            print(
                f"{c.code} [{c.severity}] {c.path}:{c.lines} == "
                f"{c.matched_path}:{c.matched_lines} ({c.tokens} tokens) -> {c.action}"
            )
# The published engine CLIs intentionally keep parallel local argument/error flows too;
# one region covers the token run that crosses this emitter-to-main boundary.
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="lean-audit code-duplication lens")
    ap.add_argument("scope", help="directory to scan")
    ap.add_argument("--min-tokens", type=int, default=DEFAULT_MIN_CLONE_TOKENS)
    add_shared_flags(ap)
    args = ap.parse_args(argv)
    if args.min_tokens < 1:
        print("lean-audit code_lens: --min-tokens must be >= 1", file=sys.stderr)
        return 2
    if args.registry and not Path(args.registry).is_file():
        print(
            f"lean-audit code_lens: --registry {args.registry} not found; "
            f"scanning with default config",
            file=sys.stderr,
        )
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
# lean-audit:dup-intentional:end
