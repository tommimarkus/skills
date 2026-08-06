#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Entry shim — stable published path. Implementation: leanaudit.workflow_cost."""

# lean-audit:dup-intentional — mandated identical entry-shim boilerplate (published-path contract)
from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info < (3, 11):  # noqa: UP036
    sys.stderr.write(
        "lean-audit: requires Python >=3.11 (found "
        f"{sys.version_info[0]}.{sys.version_info[1]}); "
        "run via 'uv run <script>' or a >=3.11 python3\n"
    )
    raise SystemExit(3)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from leanaudit.workflow_cost import *  # noqa: E402,F403
from leanaudit.workflow_cost import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
