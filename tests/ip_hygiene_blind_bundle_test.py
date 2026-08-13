import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT


BUILDER = (
    REPO_ROOT
    / "souroldgeezer-audit"
    / "skills"
    / "ip-hygiene"
    / "references"
    / "scripts"
    / "build_ip_hygiene_blind_bundle.py"
)


class IpHygieneBlindBundleTest(unittest.TestCase):
    def build_bundle(self, output: Path) -> Path:
        result = subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                "--repo-root",
                str(REPO_ROOT),
                "--output",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return output

    def test_builder_creates_deterministic_allowlisted_blind_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self.build_bundle(root / "first")
            second = self.build_bundle(root / "second")

            first_manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
            second_manifest = json.loads((second / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(first_manifest, second_manifest)
            self.assertEqual(first_manifest["schema_version"], "ip-hygiene-blind-bundle.v1")

            paths = [entry["path"] for entry in first_manifest["files"]]
            self.assertEqual(paths, sorted(paths))
            self.assertIn("EVALUATOR_INSTRUCTIONS.md", paths)
            self.assertIn("cases.jsonl", paths)
            self.assertIn("validate_ip_hygiene_actual.py", paths)
            self.assertFalse(any(path.endswith("/cases.jsonl") for path in paths))
            self.assertFalse(any(path.endswith("/validate_ip_hygiene_actual.py") for path in paths))
            self.assertIn("souroldgeezer-audit/skills/ip-hygiene/SKILL.md", paths)
            self.assertIn("souroldgeezer-audit/docs/audit-reference/audit-craft.md", paths)
            self.assertIn("souroldgeezer-audit/docs/audit-reference/materiality.md", paths)
            self.assertFalse(any("expected.jsonl" in path for path in paths))
            self.assertFalse(any("score_ip_hygiene_eval.py" in path for path in paths))
            self.assertFalse(any("source-grounding.md" in path for path in paths))
            self.assertFalse(any(path.startswith(".git/") for path in paths))
            self.assertFalse(any("/tests/" in path or path.startswith("tests/") for path in paths))

            for entry in first_manifest["files"]:
                content = (first / entry["path"]).read_bytes()
                self.assertEqual(entry["sha256"], hashlib.sha256(content).hexdigest())

            instructions = (first / "EVALUATOR_INSTRUCTIONS.md").read_text(encoding="utf-8")
            self.assertIn("blocked:contaminated", instructions)
            self.assertIn("only assigned bundle", instructions)
            self.assertIn("structure only", instructions)
            self.assertIn("Parent", instructions)


if __name__ == "__main__":
    unittest.main()
