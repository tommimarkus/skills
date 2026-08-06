#!/usr/bin/env python3
"""Deterministic secret scan for the lesson loop (Plan 4).

Implements the DSO-POS-9 pre-commit control: before any lesson graduates to a
committed file, scan its text / the staged diff for well-known secret shapes.
Specific patterns only (not an entropy heuristic) to avoid noisy false positives
in a repo full of git SHAs and example text. Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import sys

# (label, pattern): specific, well-known secret shapes only.
SECRET_PATTERNS = (
    ("github-token", r"\bgh[posru]_[A-Za-z0-9]{30,}\b"),
    ("openai-key", r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    ("aws-access-key-id", r"\bAKIA[0-9A-Z]{16}\b"),
    ("slack-token", r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    ("google-api-key", r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ("private-key-block", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    ("jwt", r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    ("secret-assignment",
     r"(?i)\b(?:secret|token|password|passwd|api[_-]?key|access[_-]?key)\b"
     r"\s*[:=]\s*['\"]?[A-Za-z0-9/+_-]{16,}"),
)


def scan_text(text: str) -> list[str]:
    """Return sorted labels of secret shapes found in the text."""
    return sorted({label for label, pattern in SECRET_PATTERNS if re.search(pattern, text)})


def scan_diff(diff: str) -> list[str]:
    """Scan only the added lines of a unified diff (ignore context/removed/headers)."""
    added = "\n".join(
        line[1:] for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    return scan_text(added)


# lean-audit:dup-intentional:begin -- sibling lesson CLIs keep local parsers
# because their argument sets and exit meanings are independent contracts.
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="lessons_secret_scan")
    parser.add_argument("--diff", action="store_true",
                        help="treat input as a unified diff; scan only added lines")
    parser.add_argument("--text", help="scan this string instead of stdin")
    args = parser.parse_args(argv)
    data = args.text if args.text is not None else sys.stdin.read()
    labels = scan_diff(data) if args.diff else scan_text(data)
    for label in labels:
        print(label)
    return 1 if labels else 0
# lean-audit:dup-intentional:end


if __name__ == "__main__":
    raise SystemExit(main())
