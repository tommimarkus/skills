"""Unittest discovery shim for the repo's *_test.py layout."""

from __future__ import annotations

from pathlib import Path
import unittest


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
    repo_root = Path(__file__).resolve().parent
    return loader.discover(
        start_dir=str(repo_root / "tests"),
        pattern="*_test.py",
        top_level_dir=str(repo_root),
    )
