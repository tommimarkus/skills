#!/usr/bin/env python3
"""Parent-owned checkpoint ledger with byte-compatible legacy commands."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from planningledger.vocabulary import *  # noqa: F403
from planningledger.core import *  # noqa: F403
from planningledger.store import *  # noqa: F403
from planningledger.gitops import *  # noqa: F403
from planningledger.contract import *  # noqa: F403
from planningledger.checkpoint import *  # noqa: F403
from planningledger.legacy import *  # noqa: F403
from planningledger.schedule import *  # noqa: F403
from planningledger.series import *  # noqa: F403
from planningledger.returns import *  # noqa: F403
from planningledger.dispatch import *  # noqa: F403
from planningledger.verify import *  # noqa: F403
from planningledger.retention import *  # noqa: F403
from planningledger.closeout import *  # noqa: F403
from planningledger.tracing import *  # noqa: F403
from planningledger.cli import *  # noqa: F403


if __name__ == "__main__":
    sys.exit(main())
