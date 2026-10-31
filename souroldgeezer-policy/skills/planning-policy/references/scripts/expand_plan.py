#!/usr/bin/env python3
"""Expand one template and a JSONL rule index into v5 plan slices for a plan series."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from planningledger.expand import main

if __name__ == "__main__":
    sys.exit(main())
