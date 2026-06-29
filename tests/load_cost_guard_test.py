import importlib.util, json, tempfile
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
_p = (REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/references/scripts/load_cost_guard.py")
_spec = importlib.util.spec_from_file_location("load_cost_guard", _p)
guard = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(guard)

class PostEditContentTest(unittest.TestCase):
    def test_write_returns_full_content(self):
        self.assertEqual(guard.post_edit_content("Write", {"content": "X"}, "old"), "X")
    def test_edit_applies_replacement(self):
        self.assertEqual(
            guard.post_edit_content("Edit", {"old_string": "a", "new_string": "b"}, "a c"),
            "b c")
    def test_unknown_tool_returns_none(self):
        self.assertIsNone(guard.post_edit_content("Bash", {"command": "ls"}, ""))

class GuardDecisionTest(unittest.TestCase):
    def test_denies_when_edit_drops_a_smell_code(self):
        # Edit api-design SKILL.md to delete a code-bearing closure file's content
        # would be heavy; instead drive decide() over a synthetic skill.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "SKILL.md").write_text("# S\n[c](c.md)\nHC-1 here\n")
            (root / "c.md").write_text("## Sec\nLA-PUC-1 token\n")
            base = root / "base.json"
            base.write_text(json.dumps({"codes": ["HC-1", "LA-PUC-1"],
                                        "sections": ["S", "Sec"]}))
            patterns = root / "pat.json"
            patterns.write_text(json.dumps(["\\bHC-\\d+", "LA-PUC-\\d+"]))
            # pending edit removes the LA-PUC-1 line from c.md
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
