import importlib.util, json, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_p = (REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/references/scripts/load_cost_guard.py")
_spec = importlib.util.spec_from_file_location("load_cost_guard", _p)
guard = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(guard)

GUARD_SCRIPT = str(_p)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run_guard(payload):
    """Run the guard script as a subprocess, return (exit_code, stdout_lines)."""
    result = subprocess.run(
        [sys.executable, GUARD_SCRIPT],
        input=json.dumps(payload),
        capture_output=True, text=True,
    )
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    return result.returncode, lines


def _init_git_repo(root: Path):
    """Initialise a git repo in root, add all files, and make one commit."""
    for cmd in [
        ["git", "init"],
        ["git", "config", "user.email", "test@test.com"],
        ["git", "config", "user.name", "Test"],
        ["git", "add", "-A"],
        ["git", "commit", "-m", "init"],
    ]:
        subprocess.run(cmd, cwd=str(root), check=True,
                       capture_output=True, text=True)


# ---------------------------------------------------------------------------
# post_edit_content
# ---------------------------------------------------------------------------

class PostEditContentTest(unittest.TestCase):
    def test_write_returns_full_content(self):
        self.assertEqual(guard.post_edit_content("Write", {"content": "X"}, "old"), "X")

    def test_edit_applies_replacement(self):
        self.assertEqual(
            guard.post_edit_content("Edit", {"old_string": "a", "new_string": "b"}, "a c"),
            "b c")

    def test_unknown_tool_returns_none(self):
        self.assertIsNone(guard.post_edit_content("Bash", {"command": "ls"}, ""))

    def test_multiedit_applies_edits_sequentially(self):
        edits = [
            {"old_string": "foo", "new_string": "bar"},
            {"old_string": "baz", "new_string": "qux"},
        ]
        result = guard.post_edit_content("MultiEdit", {"edits": edits}, "foo baz")
        self.assertEqual(result, "bar qux")

    def test_multiedit_empty_edits_returns_current(self):
        result = guard.post_edit_content("MultiEdit", {"edits": []}, "unchanged")
        self.assertEqual(result, "unchanged")


# ---------------------------------------------------------------------------
# decide() — unit tests
# ---------------------------------------------------------------------------

class GuardDecisionTest(unittest.TestCase):
    def test_denies_when_edit_drops_a_smell_code(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "SKILL.md").write_text("# S\n[c](c.md)\nHC-1 here\n")
            (root / "c.md").write_text("## Sec\nLA-PUC-1 token\n")
            base = root / "base.json"
            base.write_text(json.dumps({"codes": ["HC-1", "LA-PUC-1"],
                                        "sections": ["S", "Sec"]}))
            patterns = root / "pat.json"
            patterns.write_text(json.dumps(["\\bHC-\\d+", "LA-PUC-\\d+"]))
            decision = guard.decide(
                target=root / "c.md", new_content="## Sec\n(removed)\n",
                skill_md=root / "SKILL.md", baseline=base, patterns=patterns)
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allows_when_nothing_unreachable(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "SKILL.md").write_text("# S\n[c](c.md)\n")
            (root / "c.md").write_text("## Sec\nLA-PUC-1 token\n")
            base = root / "base.json"
            base.write_text(json.dumps({"codes": ["LA-PUC-1"], "sections": ["S", "Sec"]}))
            patterns = root / "pat.json"; patterns.write_text(json.dumps(["LA-PUC-\\d+"]))
            self.assertIsNone(guard.decide(
                target=root / "c.md", new_content="## Sec\nLA-PUC-1 still here\n",
                skill_md=root / "SKILL.md", baseline=base, patterns=patterns))

    def test_denies_when_edit_orphans_linked_file_by_removing_link(self):
        """Removing a Load-Map link from SKILL.md must shrink the closure and
        cause codes in the orphaned file to become unreachable (Fix C)."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "SKILL.md").write_text("# S\n[c](c.md)\nHC-1 here\n")
            (root / "c.md").write_text("## Sec\nLA-PUC-2 token\n")
            base = root / "base.json"
            base.write_text(json.dumps({"codes": ["HC-1", "LA-PUC-2"],
                                        "sections": ["S", "Sec"]}))
            patterns = root / "pat.json"
            patterns.write_text(json.dumps(["\\bHC-\\d+", "LA-PUC-\\d+"]))
            # edit removes the link to c.md → LA-PUC-2 becomes orphaned
            decision = guard.decide(
                target=root / "SKILL.md",
                new_content="# S\nHC-1 here\n(no link to c.md)\n",
                skill_md=root / "SKILL.md", baseline=base, patterns=patterns)
            self.assertIsNotNone(decision,
                "expected deny when link removal orphans a code-bearing file")
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_denies_when_edit_introduces_dangling_pointer(self):
        """An edit introducing a dangling pointer must deny (Fix C)."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "SKILL.md").write_text("# S\n")
            base = root / "base.json"
            base.write_text(json.dumps({"codes": [], "sections": ["S"]}))
            patterns = root / "pat.json"
            patterns.write_text(json.dumps([]))
            # edit adds a pointer to a non-existent file
            decision = guard.decide(
                target=root / "SKILL.md",
                new_content="# S\n[broken](does-not-exist.md)\n",
                skill_md=root / "SKILL.md", baseline=base, patterns=patterns)
            self.assertIsNotNone(decision,
                "expected deny when edit introduces a dangling pointer")
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")


# ---------------------------------------------------------------------------
# cost_warn_decision
# ---------------------------------------------------------------------------

class GuardCostWarnTest(unittest.TestCase):
    def test_warn_payload_allows_and_names_scenario(self):
        out = guard.cost_warn_decision(["lookup-functions: per-use cost grew 900 tokens"])
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "allow")
        self.assertIn("lookup-functions", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_no_warn_returns_none(self):
        self.assertIsNone(guard.cost_warn_decision([]))


# ---------------------------------------------------------------------------
# main() integration — subprocess-driven
# ---------------------------------------------------------------------------

class MainIntegrationTest(unittest.TestCase):
    """Integration tests driving main() via subprocess with real stdin JSON."""

    def _mk_skill(self, root: Path, skill_name: str = "myskill"):
        """Create a minimal skill structure under root/<skill_name>/."""
        skill_dir = root / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("# S\n[c](c.md)\nHC-1 here\n")
        (skill_dir / "c.md").write_text("## Sec\nLA-PUC-1 token\n")
        tests_dir = root / "tests" / "skill_load_cost"
        tests_dir.mkdir(parents=True, exist_ok=True)
        baselines_dir = tests_dir / "baselines"
        baselines_dir.mkdir(exist_ok=True)
        (tests_dir / "code_patterns.json").write_text(
            json.dumps(["\\bHC-\\d+", "LA-PUC-\\d+"]))
        (baselines_dir / f"{skill_name}.json").write_text(
            json.dumps({"codes": ["HC-1", "LA-PUC-1"], "sections": ["S", "Sec"]}))
        return skill_dir

    # -- PreToolUse: deny when code is dropped --

    def test_pretooluse_deny_drops_code(self):
        """PreToolUse payload that drops a code → deny decision on stdout, exit 0."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            skill_dir = self._mk_skill(root)
            payload = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(skill_dir / "c.md"),
                    "old_string": "LA-PUC-1 token",
                    "new_string": "(removed)",
                },
                "cwd": str(root),
            }
            code, lines = _run_guard(payload)
            self.assertEqual(code, 0, "guard must exit 0 (fail-open contract)")
            self.assertTrue(lines, "expected at least one output line")
            out = json.loads(lines[0])
            self.assertEqual(
                out["hookSpecificOutput"]["permissionDecision"], "deny",
                f"expected deny, got: {lines}")

    # -- PreToolUse: non-skill path → no output --

    def test_pretooluse_non_skill_fail_open(self):
        """PreToolUse to a non-skill .md → no deny output, exit 0."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "README.md").write_text("# README\n")
            tests_dir = root / "tests" / "skill_load_cost"
            tests_dir.mkdir(parents=True)
            (tests_dir / "code_patterns.json").write_text(json.dumps([]))
            payload = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(root / "README.md"),
                    "old_string": "# README",
                    "new_string": "# Changed",
                },
                "cwd": str(root),
            }
            code, lines = _run_guard(payload)
            self.assertEqual(code, 0)
            # Must not emit a deny decision
            for line in lines:
                try:
                    out = json.loads(line)
                    self.assertNotEqual(
                        out.get("hookSpecificOutput", {}).get("permissionDecision"), "deny",
                        "non-skill path must not produce a deny")
                except (json.JSONDecodeError, AttributeError):
                    pass

    # -- Stop-mode: fidelity block when code is removed from disk --

    def test_stop_mode_fidelity_block(self):
        """Stop event with session-changed file dropping a baseline code → block."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            skill_dir = self._mk_skill(root, "lean-skill")

            # Commit the initial state so git diff HEAD can see the change
            _init_git_repo(root)

            # Now remove LA-PUC-1 from c.md on disk (not committed)
            (skill_dir / "c.md").write_text("## Sec\n(code removed)\n")

            # Stop payload — no tool_input.file_path
            payload = {"cwd": str(root)}
            code, lines = _run_guard(payload)

            self.assertEqual(code, 0, "guard must exit 0 even on block")
            self.assertTrue(lines, "expected block output")
            out = json.loads(lines[0])
            self.assertEqual(out["decision"], "block",
                             f"expected Stop-mode block decision, got: {lines}")
            self.assertIn("fidelity", out["reason"].lower())

    # -- Stop-mode: fail-open when no git repo --

    def test_stop_mode_fail_open_no_git_repo(self):
        """Stop event in a non-git directory → no output, exit 0 (fail-open)."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            # No git init → git diff will fail → fail-open
            payload = {"cwd": str(root)}
            code, lines = _run_guard(payload)
            self.assertEqual(code, 0)
            # No block decision must be emitted
            for line in lines:
                try:
                    out = json.loads(line)
                    self.assertNotEqual(out.get("decision"), "block",
                                        "no-git case must not block")
                except (json.JSONDecodeError, AttributeError):
                    pass


if __name__ == "__main__":
    unittest.main()
