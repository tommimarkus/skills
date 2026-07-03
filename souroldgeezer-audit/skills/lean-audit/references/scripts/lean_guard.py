#!/usr/bin/env python3
"""Entry shim — stable published path. Implementation: leanaudit.guard_lean."""

# lean-audit:dup-intentional — mandated identical entry-shim boilerplate (published-path contract)
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from leanaudit.guard_lean import *  # noqa: E402,F403
from leanaudit.guard_lean import main  # noqa: E402

if __name__ == "__main__":
    main()
