"""End-to-end tests for the PreToolUse worktree commit guard.

The guard (scripts/agent-hooks/pretooluse-worktree-commit-guard.sh) refuses
`git commit` on the PRIMARY checkout's `main` branch while linked worktrees are
active, and is fail-open otherwise. These tests drive the real script via
subprocess against real temporary git repositories, feeding it PreToolUse-shaped
JSON on stdin and asserting the decision it prints.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARD = REPO_ROOT / "scripts" / "agent-hooks" / "pretooluse-worktree-commit-guard.sh"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _run_guard(command: str, cwd: Path, tool_name: str = "Bash") -> dict | None:
    """Run the guard with a PreToolUse payload; return the parsed deny JSON or None (allow)."""
    payload = json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "session_id": "test-session",
            "cwd": str(cwd),
            "tool_name": tool_name,
            "tool_input": {"command": command},
        }
    )
    proc = subprocess.run(
        ["bash", str(GUARD)],
        input=payload,
        capture_output=True,
        text=True,
    )
    # The guard always exits 0; allow == empty stdout, deny == JSON on stdout.
    assert proc.returncode == 0, f"guard exited {proc.returncode}: {proc.stderr}"
    out = proc.stdout.strip()
    if not out:
        return None
    return json.loads(out)


@unittest.skipUnless(GUARD.exists(), "guard script missing")
@unittest.skipUnless(shutil.which("git"), "git not available")
@unittest.skipUnless(shutil.which("jq"), "jq not available")
class WorktreeCommitGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _make_repo(self, *, marketplace: bool = True) -> Path:
        primary = self.root / "primary"
        primary.mkdir()
        _git(primary, "init", "-b", "main")
        _git(primary, "config", "user.email", "test@example.com")
        _git(primary, "config", "user.name", "Test")
        if marketplace:
            (primary / ".claude-plugin").mkdir()
            (primary / ".claude-plugin" / "marketplace.json").write_text("{}\n")
        (primary / "README.md").write_text("# test\n")
        _git(primary, "add", "-A")
        _git(primary, "commit", "-m", "init")
        return primary

    def _add_worktree(self, primary: Path, name: str = "feature") -> Path:
        wt = self.root / name
        _git(primary, "worktree", "add", str(wt), "-b", name)
        return wt

    def _assert_denied(self, decision: dict | None) -> None:
        self.assertIsNotNone(decision, "expected a deny decision, got allow")
        assert decision is not None  # narrow for type checkers
        self.assertEqual(
            decision["hookSpecificOutput"]["permissionDecision"], "deny"
        )
        self.assertEqual(
            decision["hookSpecificOutput"]["hookEventName"], "PreToolUse"
        )
        self.assertTrue(
            decision["hookSpecificOutput"]["permissionDecisionReason"].strip()
        )

    # --- the failure the guard exists to stop -------------------------------

    def test_blocks_commit_on_primary_main_with_active_worktree(self) -> None:
        primary = self._make_repo()
        self._add_worktree(primary)
        self._assert_denied(_run_guard('git commit -m "wip"', primary))

    def test_blocks_commit_amend_on_primary_main_with_active_worktree(self) -> None:
        primary = self._make_repo()
        self._add_worktree(primary)
        self._assert_denied(_run_guard("git commit --amend --no-edit", primary))

    # --- allowed cases ------------------------------------------------------

    def test_allows_with_explicit_override_token(self) -> None:
        primary = self._make_repo()
        self._add_worktree(primary)
        self.assertIsNone(
            _run_guard('ALLOW_MAIN_COMMIT=1 git commit -m "deliberate integrate"', primary)
        )

    def test_allows_commit_inside_the_worktree(self) -> None:
        primary = self._make_repo()
        wt = self._add_worktree(primary)
        # cwd is the linked worktree -> not the primary checkout.
        self.assertIsNone(_run_guard('git commit -m "in worktree"', wt))

    def test_allows_git_dash_c_into_worktree(self) -> None:
        primary = self._make_repo()
        wt = self._add_worktree(primary)
        self.assertIsNone(
            _run_guard(f'git -C {wt} commit -m "targeted"', primary)
        )

    def test_allows_leading_cd_into_worktree(self) -> None:
        primary = self._make_repo()
        wt = self._add_worktree(primary)
        self.assertIsNone(
            _run_guard(f'cd {wt} && git commit -m "after cd"', primary)
        )

    def test_allows_when_no_linked_worktree(self) -> None:
        primary = self._make_repo()
        # No worktree added: authoring-in-worktree discipline does not apply.
        self.assertIsNone(_run_guard('git commit -m "solo"', primary))

    def test_allows_dry_run(self) -> None:
        primary = self._make_repo()
        self._add_worktree(primary)
        self.assertIsNone(_run_guard("git commit --dry-run", primary))

    def test_allows_non_commit_git_command(self) -> None:
        primary = self._make_repo()
        self._add_worktree(primary)
        self.assertIsNone(_run_guard("git status", primary))
        self.assertIsNone(_run_guard("git commit-graph write", primary))

    def test_allows_non_bash_tool(self) -> None:
        primary = self._make_repo()
        self._add_worktree(primary)
        self.assertIsNone(
            _run_guard('git commit -m "wip"', primary, tool_name="Edit")
        )

    def test_allows_when_not_this_marketplace_repo(self) -> None:
        # A repo without .claude-plugin/marketplace.json is out of scope.
        primary = self._make_repo(marketplace=False)
        self._add_worktree(primary)
        self.assertIsNone(_run_guard('git commit -m "wip"', primary))

    def test_allows_on_non_main_branch(self) -> None:
        primary = self._make_repo()
        self._add_worktree(primary)
        _git(primary, "checkout", "-b", "topic")
        self.assertIsNone(_run_guard('git commit -m "wip"', primary))


if __name__ == "__main__":
    unittest.main()
