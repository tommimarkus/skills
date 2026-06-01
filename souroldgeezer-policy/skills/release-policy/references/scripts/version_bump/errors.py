"""Stable error contract for the version-bump CLI."""

from __future__ import annotations


class VersionBumpError(ValueError):
    def __init__(self, message: str, code: str = "invalid-policy", exit_code: int = 3):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def invalid_policy(message: str) -> VersionBumpError:
    return VersionBumpError(message, "invalid-policy", 3)


def source_read(message: str) -> VersionBumpError:
    return VersionBumpError(message, "source-read", 4)


def source_write(message: str) -> VersionBumpError:
    return VersionBumpError(message, "source-write", 5)
