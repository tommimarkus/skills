#!/usr/bin/env python3
"""Expand one template and a JSONL rule index into v5 plan slices for a plan series."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from planningledger import expand as _implementation
from planningledger.expand import main

# Callers and tests reach every module-level name, private ones included.
globals().update({k: v for k, v in vars(_implementation).items() if not k.startswith("__")})


if __name__ == "__main__":
    sys.exit(main())
