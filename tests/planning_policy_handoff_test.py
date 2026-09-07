import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts/validate_plan_contract.py"
FIXTURE = ROOT.parent / "planning-policy-approval-handoff-evidence/plan.json"


class PlanningPolicyHandoffTest(unittest.TestCase):
    def run_cli(self, *args, input_text=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=input_text, text=True, capture_output=True)

    def test_inline_round_trip(self):
        result = self.run_cli("validate", str(FIXTURE), "--emit-handoff", "inline")
        self.assertEqual(result.returncode, 0, result.stderr)
        handoff = json.loads(result.stdout)["handoff"]
        resolved = self.run_cli("resolve-handoff", "-", input_text=json.dumps(handoff))
        self.assertEqual(resolved.returncode, 0, resolved.stderr)
        self.assertEqual(json.loads(resolved.stdout)["validation"]["plan_sha256"], handoff["plan_sha256"])

    def test_tampered_inline_is_rejected(self):
        result = self.run_cli("validate", str(FIXTURE), "--emit-handoff", "inline")
        handoff = json.loads(result.stdout)["handoff"]
        handoff["plan"]["objective"] = "tampered"
        resolved = self.run_cli("resolve-handoff", "-", input_text=json.dumps(handoff))
        self.assertEqual(resolved.returncode, 1)
        self.assertIn("blocked:plan_tampered", resolved.stdout)

    def test_reference_round_trip(self):
        result = self.run_cli("validate", str(FIXTURE), "--emit-handoff", "reference")
        self.assertEqual(result.returncode, 0, result.stderr)
        handoff = json.loads(result.stdout)["handoff"]
        resolved = self.run_cli("resolve-handoff", "-", input_text=json.dumps(handoff))
        self.assertEqual(resolved.returncode, 0, resolved.stderr)


if __name__ == "__main__":
    unittest.main()
