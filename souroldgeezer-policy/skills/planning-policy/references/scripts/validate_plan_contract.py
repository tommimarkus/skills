#!/usr/bin/env python3
"""Validate the runtime-neutral planning-policy executable-plan contract."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from planningledger import plancontract as _implementation

# Callers and tests reach every module-level name, private ones included.
globals().update({k: v for k, v in vars(_implementation).items() if not k.startswith("__")})


if __name__ == "__main__":
    sys.exit(main())
