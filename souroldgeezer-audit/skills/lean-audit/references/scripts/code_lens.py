#!/usr/bin/env python3
"""Entry shim — stable published path. Implementation: leanaudit.clones."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from leanaudit.clones import *  # noqa: E402,F403
from leanaudit.clones import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
