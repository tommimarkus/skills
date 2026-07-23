# tests/skill_load_cost_freshness_test.py
"""The committed per-use cost-snapshot must stay fresh — within COST_TOLERANCE of a
fresh re-measurement for every scenario. This is the deterministic staleness gate #107
adds.

Why a suite test and not the runtime guard: the guard's cost path (guard_load_cost.py)
is advisory, never blocks, and runs at Stop over only the skills changed that session,
so it is structurally incapable of flagging a *globally* stale snapshot when the relevant
skill was not touched that session — the reported failure mode (the snapshot sat stale for
weeks uncaught). Re-measuring the whole committed snapshot every suite run closes that
hole: a stale committed floor fails here, forcing a deliberate `snapshot` refresh (the
review moment) instead of silent drift.

Content-based and deterministic (`measure_scenario`'s word/punct proxy over the committed
closure files) — no wall-clock, no git-commit-time heuristic, no filesystem walk — so it is
immune to time passing and to the nested-worktree topology that trips filesystem scanners.
"""
import json
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, load_script_module

SCRIPT = (REPO_ROOT / "souroldgeezer-audit" / "skills" / "lean-audit"
          / "references" / "scripts" / "skill_load_cost.py")
# Load the shim by path (repo convention, no scripts/__init__.py); `import *` re-exports
# measure_scenario and COST_TOLERANCE from leanaudit.load_cost.
slc = load_script_module("skill_load_cost_freshness", SCRIPT)

COST_DIR = REPO_ROOT / "tests" / "skill_load_cost"
SNAPSHOT = COST_DIR / "cost-snapshot.json"
SCENARIOS = COST_DIR / "scenarios.json"

_REFRESH_HINT = (
    "regenerate it:\n"
    "  uv run python souroldgeezer-audit/skills/lean-audit/references/scripts/"
    "skill_load_cost.py snapshot"
    " --scenarios tests/skill_load_cost/scenarios.json --root ."
    " --out tests/skill_load_cost/cost-snapshot.json"
)


class CostSnapshotFreshnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot: dict[str, int] = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        self.scenarios: list[dict] = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        self.by_id = {s["id"]: s for s in self.scenarios}

    def test_snapshot_ids_match_scenarios_one_to_one(self) -> None:
        """Every scenario has a snapshot entry and vice versa. A scenario added without
        snapshotting it (or a snapshot entry left behind after a scenario is removed) is
        itself staleness that the tolerance check below would skip silently — the shared
        cost engine ignores ids absent on either side."""
        self.assertEqual(
            set(self.snapshot), set(self.by_id),
            f"cost-snapshot.json and scenarios.json ids diverged — {_REFRESH_HINT}",
        )

    def test_committed_snapshot_is_within_tolerance_of_a_fresh_measurement(self) -> None:
        """The committed floor must reflect current reality: re-measure every scenario's
        closure and require |current - committed| <= COST_TOLERANCE. A snapshot that drifts
        past tolerance in either direction — an unreviewed cost climb, or a stale-high floor
        after a closure shrank — fails here, forcing a deliberate `snapshot` refresh instead
        of the silent drift #107 was about."""
        stale = []
        for sid, committed in self.snapshot.items():
            scen = self.by_id.get(sid)
            if scen is None:
                continue  # id parity is asserted separately above
            current = slc.measure_scenario(scen, REPO_ROOT)["total"]
            drift = current - committed
            if abs(drift) > slc.COST_TOLERANCE:
                stale.append(
                    f"{sid}: committed {committed} vs current {current} "
                    f"(drift {drift:+d}, tolerance {slc.COST_TOLERANCE})"
                )
        self.assertEqual(
            stale, [],
            "committed cost-snapshot is stale beyond tolerance — "
            f"{_REFRESH_HINT}\nStale scenarios:\n  " + "\n  ".join(stale),
        )


if __name__ == "__main__":
    unittest.main()
