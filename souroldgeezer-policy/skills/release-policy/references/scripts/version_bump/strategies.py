from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .errors import invalid_policy
from .strategy_calver import bump_calver, calver_default
from .strategy_pep440 import bump_pep440
from .strategy_semver import bump_semver


@dataclass(frozen=True)
class BumpRequest:
    current: str | None
    bump: str | None
    pre_label: str
    scheme: str
    date: str | None
    existing_tags: list[str]


@dataclass(frozen=True)
class Strategy:
    name: str
    aliases: tuple[str, ...]
    bump: Callable[[BumpRequest], str]
    default_bump: Callable[[BumpRequest], str]


def patch_default(request: BumpRequest) -> str:
    return request.bump or "patch"


def resolve_strategy(value: str) -> Strategy:
    normalized = value.lower().replace("-", "")
    for strategy in STRATEGIES:
        if normalized in strategy.aliases:
            return strategy
    raise invalid_policy(f"unsupported strategy: {value}")


STRATEGIES = (
    Strategy("semver", ("semantic", "semver"), bump_semver, patch_default),
    Strategy("calver", ("calendar", "calver"), bump_calver, calver_default),
    Strategy("pep440", ("pep440", "python"), bump_pep440, patch_default),
)
