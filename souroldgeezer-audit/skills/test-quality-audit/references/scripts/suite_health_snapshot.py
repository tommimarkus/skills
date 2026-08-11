"""Summarize one JUnit XML document without retaining test output bodies."""

from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as element_tree
from pathlib import Path
from typing import Any

OUTPUT_LIMIT_BYTES = 16 * 1024
SLOW_TESTCASE_LIMIT = 20
IDENTITY_LIMIT = 256
PERCENTILES = (50, 90, 95, 99)
RUNTIME_SHARE_PERCENTS = (1, 5, 10)


def nonnegative_duration(value: str | None) -> float:
    """Return a finite nonnegative JUnit duration, treating invalid values as zero."""
    try:
        duration = float(value) if value is not None else 0.0
    except ValueError:
        return 0.0
    return duration if math.isfinite(duration) and duration > 0 else 0.0


def bounded_identity(value: str | None) -> str:
    """Keep names useful while reserving output space for the rest of the snapshot."""
    return (value or "")[:IDENTITY_LIMIT]


def testcase_status(testcase: element_tree.Element) -> str:
    """Classify a testcase without reading any failure or captured-output body."""
    child_names = {child.tag.rsplit("}", 1)[-1] for child in testcase}
    if "error" in child_names:
        return "error"
    if "failure" in child_names:
        return "failed"
    if "skipped" in child_names or "disabled" in child_names:
        return "skipped"
    return "passed"


def nearest_rank(sorted_values: list[float], percentile: int) -> float:
    """Calculate a nearest-rank percentile from one non-empty ascending sequence."""
    index = max(0, math.ceil(percentile / 100 * len(sorted_values)) - 1)
    return sorted_values[index]


def parse_junit(content: str) -> element_tree.Element:
    """Parse one supported JUnit document and reject empty/unsupported roots."""
    try:
        root = element_tree.fromstring(content)
    except element_tree.ParseError as error:
        raise ValueError("malformed JUnit XML") from error
    root_name = root.tag.rsplit("}", 1)[-1]
    if root_name not in {"testsuite", "testsuites"}:
        raise ValueError("JUnit root must be testsuite or testsuites")
    if not any(element.tag.rsplit("}", 1)[-1] == "testcase" for element in root.iter()):
        raise ValueError("JUnit document contains no testcase elements")
    return root


def snapshot(root: element_tree.Element) -> dict[str, Any]:
    """Build numeric facts and bounded testcase identities from parsed JUnit XML."""
    statuses = {"total": 0, "passed": 0, "skipped": 0, "failed": 0, "error": 0}
    durations: list[float] = []
    testcases: list[tuple[float, str, str]] = []
    suite_time = 0.0
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "testsuite":
            suite_time += nonnegative_duration(element.get("time"))
        elif tag == "testcase":
            duration = nonnegative_duration(element.get("time"))
            statuses["total"] += 1
            statuses[testcase_status(element)] += 1
            durations.append(duration)
            testcases.append(
                (
                    duration,
                    bounded_identity(element.get("classname")),
                    bounded_identity(element.get("name")),
                )
            )

    ordered_durations = sorted(durations)
    total_duration = sum(ordered_durations)
    percentiles = {
        f"p{percentile}": nearest_rank(ordered_durations, percentile) for percentile in PERCENTILES
    }
    percentiles["max"] = ordered_durations[-1]
    runtime_shares = {
        f"top_{percent}_percent": (
            sum(
                sorted(ordered_durations, reverse=True)[
                    : math.ceil(len(ordered_durations) * percent / 100)
                ]
            )
            / total_duration
            if total_duration
            else 0.0
        )
        for percent in RUNTIME_SHARE_PERCENTS
    }
    slow_testcases = [
        {"classname": classname, "name": name, "time_seconds": duration}
        for duration, classname, name in sorted(testcases, reverse=True)[:SLOW_TESTCASE_LIMIT]
    ]
    return {
        "schema": "suite-health-snapshot-v1",
        "testcase_statuses": statuses,
        "reported_suite_time_seconds": suite_time,
        "testcase_time_seconds": total_duration,
        "testcase_duration_percentiles_seconds": percentiles,
        "testcase_runtime_shares": runtime_shares,
        "slow_testcases": slow_testcases,
    }


def render_snapshot(root: element_tree.Element) -> str:
    """Render one bounded UTF-8 JSON object."""
    rendered = json.dumps(
        snapshot(root), ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    if len(rendered.encode("utf-8")) > OUTPUT_LIMIT_BYTES:
        raise ValueError("snapshot exceeds 16 KiB output limit")
    return rendered


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--junit", action="append", type=Path, required=True, help="path to one JUnit XML document"
    )
    try:
        options = parser.parse_args(arguments)
    except SystemExit as error:
        return error.code if isinstance(error.code, int) else 2
    try:
        if len(options.junit) != 1:
            raise ValueError("exactly one --junit path is required")
        root = parse_junit(options.junit[0].read_text(encoding="utf-8"))
        print(render_snapshot(root))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"suite-health snapshot: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
