import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timezone
from pathlib import Path


SCRIPT = Path("souroldgeezer-design/skills/software-design/references/scripts/tool_state.py")


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, text=True, capture_output=True)


def run(repo: Path, *args: str) -> dict:
    result = subprocess.run(
        ["python3", str(SCRIPT.resolve()), "--repo-root", str(repo), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


class SoftwareDesignToolStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "clone"
        self.linked = Path(self.temporary.name) / "linked"
        self.other = Path(self.temporary.name) / "other"
        for repo in (self.root, self.other):
            repo.mkdir()
            git(repo, "init")
            git(repo, "config", "user.email", "test@example.invalid")
            git(repo, "config", "user.name", "Test User")
            (repo / "README.md").write_text("fixture\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "fixture")
        git(self.root, "branch", "linked")
        git(self.root, "worktree", "add", str(self.linked), "linked")
        git(self.root, "config", "--local", "unrelated.keep", "unchanged")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_put_get_and_clear_are_clone_local_and_keep_unrelated_config(self) -> None:
        put = run(self.root, "put", "typescript-index", "--tool", "tsc", "--reported-version", "5.8", "--source", "package.json", "--validated-on", "2026-01-01")
        self.assertEqual("ok", put["status"])
        self.assertEqual("2026-01-31", put["record"]["refresh-after"])
        self.assertEqual("2026-03-02", put["record"]["purge-after"])
        visible = run(self.linked, "get", "typescript-index")
        self.assertEqual("expired", visible["status"])
        self.assertEqual("absent", run(self.other, "get", "typescript-index")["status"])
        self.assertEqual("ok", run(self.linked, "clear", "typescript-index")["status"])
        self.assertEqual("absent", run(self.root, "get", "typescript-index")["status"])
        self.assertEqual("unchanged", git(self.root, "config", "--local", "--get", "unrelated.keep").stdout.strip())

    def test_stale_gc_and_decision_lifecycle_are_utc_calendar_based(self) -> None:
        run(self.root, "put", "format", "--tool", "black", "--reported-version", "24", "--source", "pyproject.toml", "--validated-on", "2026-08-01")
        stale = run(self.root, "stale", "format", "--stale-on", "2026-08-02")
        self.assertEqual("2026-08-09", stale["record"]["purge-after"])
        git(self.root, "config", "--local", "softwaredesign.tool-decision-format", "defer-until:2026-08-09")
        spec = importlib.util.spec_from_file_location("tool_state", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = module.utc_today
        module.utc_today = lambda: module.parse_date("2026-08-09")
        try:
            captured = io.StringIO()
            with redirect_stdout(captured):
                self.assertEqual(0, module.main(["--repo-root", str(self.root), "gc", "--dry-run"]))
            simulated = json.loads(captured.getvalue())
            self.assertEqual(["cache:format", "decision:format"], simulated["removed"])
        finally:
            module.utc_today = original

    def test_malformed_and_unknown_schema_are_report_only(self) -> None:
        git(self.root, "config", "--local", "softwaredesign.tool-cache-bad.schema-version", "2")
        git(self.root, "config", "--local", "softwaredesign.tool-cache-bad.tool", "bad")
        self.assertEqual("unknown_schema", run(self.root, "clear", "bad")["status"])
        listed = run(self.root, "list")["records"]
        self.assertEqual("unknown_schema", listed[0]["status"])
        self.assertIn("softwaredesign.tool-cache-bad.schema-version", git(self.root, "config", "--local", "--get-regexp", "^softwaredesign\\.tool-cache-bad").stdout)

    def test_list_and_clear_all_have_bounded_kind_scopes(self) -> None:
        run(self.root, "put", "formatter", "--tool", "black", "--reported-version", "24", "--source", "pyproject.toml", "--validated-on", date.today().isoformat())
        git(self.root, "config", "--local", "softwaredesign.tool-decision-formatter", "defer-until:2099-01-01")
        listed = run(self.root, "list")
        self.assertEqual(["formatter"], [record["capability"] for record in listed["records"]])
        self.assertEqual([{"capability": "formatter", "status": "deferred"}], listed["decisions"])
        decisions = run(self.root, "clear-all", "--kind", "decisions")
        self.assertEqual(["decision:formatter"], decisions["cleared"])
        self.assertEqual("valid", run(self.root, "get", "formatter")["status"])
        cache = run(self.root, "clear-all", "--kind", "cache")
        self.assertEqual(["cache:formatter"], cache["cleared"])
        self.assertEqual("absent", run(self.root, "get", "formatter")["status"])

    def test_capability_is_not_a_path(self) -> None:
        result = subprocess.run(["python3", str(SCRIPT.resolve()), "put", "../bad", "--tool", "x", "--reported-version", "x", "--source", "x"], text=True, capture_output=True)
        self.assertNotEqual(0, result.returncode)

    def test_utc_clock_and_collection_results_are_bounded(self) -> None:
        spec = importlib.util.spec_from_file_location("tool_state", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class FixedDateTime:
            @staticmethod
            def now(tz):
                self.assertIs(timezone.utc, tz)
                return datetime(2026, 8, 9, 0, 30, tzinfo=timezone.utc)

        original_datetime = module.datetime
        module.datetime = FixedDateTime
        try:
            self.assertEqual(date(2026, 8, 9), module.utc_today())
        finally:
            module.datetime = original_datetime

        for index in range(101):
            git(
                self.root,
                "config",
                "--local",
                f"softwaredesign.tool-cache-item-{index:03}.schema-version",
                "2",
            )
        listed = run(self.root, "list")
        self.assertEqual(100, len(listed["records"]))
        self.assertEqual(1, listed["omitted_count"])
        self.assertTrue(listed["truncated"])
        cleared = run(self.root, "clear-all", "--kind", "cache")
        self.assertEqual(100, len(cleared["reported"]))
        self.assertEqual(1, cleared["reported_omitted_count"])
        self.assertTrue(cleared["truncated"])
        collected = run(self.root, "gc", "--dry-run")
        self.assertEqual(100, len(collected["reported"]))
        self.assertEqual(1, collected["reported_omitted_count"])
        self.assertTrue(collected["truncated"])

    def test_oversized_write_or_stored_value_is_not_echoed(self) -> None:
        oversized = "x" * 513
        rejected = subprocess.run(
            ["python3", str(SCRIPT.resolve()), "put", "format", "--tool", oversized, "--reported-version", "1", "--source", "x"],
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(0, rejected.returncode)
        self.assertNotIn(oversized, rejected.stderr)
        git(self.root, "config", "--local", "softwaredesign.tool-cache-oversized.schema-version", "1")
        git(self.root, "config", "--local", "softwaredesign.tool-cache-oversized.tool", oversized)
        listing = run(self.root, "list")
        record = listing["records"][0]
        self.assertEqual("malformed", record["status"])
        self.assertEqual("<omitted:oversized-value>", record["record"]["tool"])
        self.assertNotIn(oversized, json.dumps(listing))


if __name__ == "__main__":
    unittest.main()
