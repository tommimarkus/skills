"""Registry of canonical homes, carve-outs, and exemptions (.lean-audit.toml)."""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "BUILTIN_CARVE_OUTS",
    "BUILTIN_EXEMPT",
    "OVERRIDE",
    "Registry",
    "carved_out",
    "has_override",
    "load_registry",
    "path_captures",
    "path_exempt",
]

OVERRIDE = re.compile(r"<!--\s*lean-audit:sync-intentional:?.*?-->", re.IGNORECASE | re.DOTALL)


@dataclass(frozen=True)
class Registry:
    canonical_homes: tuple[tuple[str, str], ...]
    carve_outs: tuple[tuple[str, str], ...]
    exempt_paths: tuple[str, ...]


def load_registry(path: Path | None) -> Registry:
    # Silent on a missing path: call sites default to root/.lean-audit.toml on
    # every run (including the PreToolUse guard hot path), so a repo without a
    # registry is routine, not a diagnostic. The missing-registry warning lives
    # at the CLI layer, gated on an explicit --registry flag (engine.py main).
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
