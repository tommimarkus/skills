"""Registry of canonical homes, carve-outs, and exemptions (.lean-audit.toml)."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "BUILTIN_CARVE_OUTS",
    "BUILTIN_EXEMPT",
    "OVERRIDE",
    "VERBOSE_OVERRIDE",
    "Registry",
    "VerbosityConfig",
    "carved_out",
    "has_override",
    "has_verbose_override",
    "load_registry",
    "path_captures",
    "path_exempt",
]

OVERRIDE = re.compile(r"<!--\s*lean-audit:sync-intentional:?.*?-->", re.IGNORECASE | re.DOTALL)
VERBOSE_OVERRIDE = re.compile(
    r"<!--\s*lean-audit:verbose-intentional:?.*?-->", re.IGNORECASE | re.DOTALL
)


@dataclass(frozen=True)
class VerbosityConfig:
    """Tunable thresholds for the LA-VERBOSE-1 nominator. Per-repo overrides come
    from the optional [verbosity] table in .lean-audit.toml; the defaults are the
    single source of truth (the engine reads them off the loaded Registry)."""

    enabled: bool = True
    min_tokens: int = 60
    filler_density: float = 0.09
    scaffold_min: int = 2
    repeat_ratio: float = 0.18


@dataclass(frozen=True)
class Registry:
    canonical_homes: tuple[tuple[str, str], ...]
    carve_outs: tuple[tuple[str, str], ...]
    exempt_paths: tuple[str, ...]
    verbosity: VerbosityConfig = field(default_factory=VerbosityConfig)


def _parse_verbosity(data: dict[str, object]) -> VerbosityConfig:
    # Lenient like the rest of the registry: a wrong-typed key falls back to its
    # default (never aborts the scan); a TOML syntax error is caught upstream and
    # exits 2. bool is excluded from the int/float paths (bool is an int subclass).
    d = VerbosityConfig()
    enabled = data.get("enabled", d.enabled)
    min_tokens = data.get("min_tokens", d.min_tokens)
    filler_density = data.get("filler_density", d.filler_density)
    scaffold_min = data.get("scaffold_min", d.scaffold_min)
    repeat_ratio = data.get("repeat_ratio", d.repeat_ratio)

    def _int(v: object, default: int) -> int:
        return v if isinstance(v, int) and not isinstance(v, bool) else default

    def _float(v: object, default: float) -> float:
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else default

    return VerbosityConfig(
        enabled=enabled if isinstance(enabled, bool) else d.enabled,
        min_tokens=_int(min_tokens, d.min_tokens),
        filler_density=_float(filler_density, d.filler_density),
        scaffold_min=_int(scaffold_min, d.scaffold_min),
        repeat_ratio=_float(repeat_ratio, d.repeat_ratio),
    )


def load_registry(path: Path | None) -> Registry:
    # Silent on a missing path: call sites default to root/.lean-audit.toml on
    # every run (including the PreToolUse guard hot path), so a repo without a
    # registry is routine, not a diagnostic. The missing-registry warning lives
    # at the CLI layer, gated on an explicit --registry flag (engine.py main).
    if path is None or not Path(path).is_file():
        return Registry(canonical_homes=(), carve_outs=(), exempt_paths=())
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    homes = tuple(
        (h["path"], h["heading"])
        for h in data.get("canonical_home", [])
        if "path" in h and "heading" in h
    )
    carves = tuple((c["a"], c["b"]) for c in data.get("carve_out", []) if "a" in c and "b" in c)
    exempt = tuple(data.get("exempt_paths", []))
    verbosity = _parse_verbosity(data.get("verbosity", {}))
    return Registry(
        canonical_homes=homes, carve_outs=carves, exempt_paths=exempt, verbosity=verbosity
    )


def has_override(text: str) -> bool:
    return OVERRIDE.search(text) is not None


def has_verbose_override(text: str) -> bool:
    return VERBOSE_OVERRIDE.search(text) is not None


def _glob_to_regex(pattern: str) -> str:
    out: list[str] = []
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == "{":
            j = pattern.find("}", i)
            if j == -1:
                out.append(re.escape(c))
                i += 1
            else:
                out.append(f"(?P<{pattern[i + 1 : j]}>[^/]+)")
                i = j + 1
        # Adjacent glob-token branches intentionally share consume-and-advance mechanics.
        # lean-audit:dup-intentional:begin
        elif pattern[i : i + 3] == "**/":
            out.append("(?:.*/)?")
            i += 3
        elif pattern[i : i + 2] == "**":
            out.append(".*")
            i += 2
        # lean-audit:dup-intentional:end
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return "^" + "".join(out) + "$"


def path_captures(pattern: str, path: str) -> dict[str, str] | None:
    m = re.match(_glob_to_regex(pattern), path)
    return m.groupdict() if m else None


BUILTIN_CARVE_OUTS = (("{plugin}/skills/{skill}/SKILL.md", "{plugin}/agents/{skill}.md"),)
BUILTIN_EXEMPT = (".claude/skills/**", ".agents/skills/**")


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
