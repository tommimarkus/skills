"""Resolved source-root containment for automatic Lean readers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict

__all__ = ["MAX_REPORTED_SKIPS", "SourceBoundary", "SourceSkipEvidence"]

MAX_REPORTED_SKIPS = 50


class SourceSkipEvidence(TypedDict):
    count: int
    paths: list[str]
    truncated: bool


@dataclass
class SourceBoundary:
    """Authorize reads beneath one resolved root and retain bounded skip evidence."""

    root: Path
    skipped_count: int = 0
    _skipped_paths: list[str] = field(default_factory=list)
    _skipped_seen: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.root = self.root.resolve()

    def allows(self, path: Path, *, explicit: bool = False) -> bool:
        """Whether path may be read; an explicitly selected entry is authorized itself."""
        if explicit:
            return True
        try:
            path.resolve().relative_to(self.root)
            return True
        except (OSError, ValueError):
            display = self._display(path)
            if display not in self._skipped_seen:
                self._skipped_seen.add(display)
                self.skipped_count += 1
                if len(self._skipped_paths) < MAX_REPORTED_SKIPS:
                    self._skipped_paths.append(display)
            return False

    def evidence(self) -> SourceSkipEvidence:
        return {
            "count": self.skipped_count,
            "paths": sorted(self._skipped_paths),
            "truncated": self.skipped_count > len(self._skipped_paths),
        }

    def reported_paths(self) -> tuple[str, ...]:
        return tuple(sorted(self._skipped_paths))

    def _display(self, path: Path) -> str:
        """Name the authored path without disclosing its resolved external target."""
        try:
            return path.absolute().relative_to(self.root).as_posix()
        except ValueError:
            return path.name
