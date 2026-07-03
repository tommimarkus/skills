#!/usr/bin/env python3
"""Entry shim — stable published path. Implementation: leanaudit.engine
(+ discovery/registry re-exported for compatibility)."""
# lean-audit:dup-intentional — mandated identical entry-shim boilerplate (published-path contract)
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from leanaudit.discovery import *  # noqa: E402,F403
from leanaudit.engine import *  # noqa: E402,F403
from leanaudit.registry import *  # noqa: E402,F403
from leanaudit.engine import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
