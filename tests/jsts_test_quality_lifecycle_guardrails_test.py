import json
import re
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT


ROOT = REPO_ROOT / "souroldgeezer-audit/skills/test-quality-audit"
CORE = ROOT / "references/extensions/nodejs/core.md"
UNIT = ROOT / "references/extensions/nodejs/unit.md"
INTEGRATION = ROOT / "references/extensions/nodejs/integration.md"
GROUNDING = ROOT / "references/source-grounding.md"
TRIGGERS = ROOT / "references/evals/trigger-cases.jsonl"
BEHAVIORS = ROOT / "references/evals/behavior-cases.jsonl"
GOLDEN = ROOT / "references/golden-corpus/test-quality-audit-cases.jsonl"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_jsonl(path: Path) -> dict[str, dict]:
    return {
        record["id"]: record
        for record in (json.loads(line) for line in read(path).splitlines() if line.strip())
    }


class JsTsReactLifecycleGuardrailsTest(unittest.TestCase):
    def test_lifecycle_codes_are_addon_scoped_and_require_observable_outcomes(self) -> None:
        core = read(CORE)
        unit = read(UNIT)
        integration = read(INTEGRATION)

        self.assertIn("nodejs.HC-8", core)
        self.assertIn("nodejs.POS-8", core)
        self.assertIn("nodejs.HC-U2", unit)
        self.assertIn("nodejs.POS-U2", unit)
        self.assertIn("nodejs.I-HC-A4", integration)
        self.assertIn("nodejs.I-POS-4", integration)

        for code, text in (
            ("nodejs.HC-8", core),
            ("nodejs.POS-8", core),
            ("nodejs.HC-U2", unit),
            ("nodejs.POS-U2", unit),
            ("nodejs.I-HC-A4", integration),
            ("nodejs.I-POS-4", integration),
        ):
            with self.subTest(code=code):
                heading = text[text.index(f"### `{code}`") :]
                section = heading.split("\n---", 1)[0]
                self.assertIn("Applies to:", section)
                self.assertIn("Detection:", section)
                self.assertIn("Rewrite", section)
                self.assertIn("observable", section.lower())

        self.assertNotIn("nodejs.HC-U2", core)
        self.assertNotIn("nodejs.POS-U2", core)
        self.assertNotIn("nodejs.I-HC-A4", core)
        self.assertNotIn("nodejs.I-POS-4", core)
        self.assertNotIn("nodejs.HC-8", unit)
        self.assertNotIn("nodejs.POS-8", unit)
        self.assertNotIn("nodejs.I-HC-A4", unit)
        self.assertNotIn("nodejs.I-POS-4", unit)
        self.assertNotIn("nodejs.HC-8", integration)
        self.assertNotIn("nodejs.POS-8", integration)
        self.assertNotIn("nodejs.HC-U2", integration)
        self.assertNotIn("nodejs.POS-U2", integration)

    def test_node_and_react_lifecycle_guidance_is_source_grounded(self) -> None:
        grounding = read(GROUNDING)
        for source in ("https://nodejs.org/api/test.html", "https://react.dev/reference/react/useEffect"):
            self.assertIn(source, grounding)
        self.assertIn("detached work", grounding)
        self.assertIn("React Effect", grounding)
        self.assertIn("cleanup facts", grounding)
        self.assertIn("application lifecycle ownership", grounding)

    def test_synthetic_evals_preserve_audit_and_sibling_boundaries(self) -> None:
        triggers = read_jsonl(TRIGGERS)
        behaviors = read_jsonl(BEHAVIORS)

        self.assertTrue(triggers["test-quality-trigger-yes-node-react-lifecycle"]["expected_activation"])
        self.assertFalse(triggers["test-quality-trigger-no-node-react-design"]["expected_activation"])
        self.assertFalse(triggers["test-quality-trigger-no-node-react-security"]["expected_activation"])

        behavior = behaviors["test-quality-behavior-node-react-lifecycle"]
        checks = " ".join(behavior["required_checks"])
        forbidden = " ".join(behavior["forbidden_behaviors"])
        for code in (
            "nodejs.HC-8",
            "nodejs.POS-8",
            "nodejs.HC-U2",
            "nodejs.POS-U2",
            "nodejs.I-HC-A4",
            "nodejs.I-POS-4",
        ):
            self.assertIn(code, checks)
        for phrase in ("API-name", "observable", "runner", "cleanup"):
            self.assertIn(phrase, forbidden + " " + checks)
        self.assertEqual("synthetic", behavior["source_kind"])
        self.assertFalse(behavior["contains_third_party_text"])

    def test_golden_corpus_has_negative_and_positive_lifecycle_cases(self) -> None:
        golden = read_jsonl(GOLDEN)
        expected = {
            "TQA-GOLD-0024": (["nodejs.HC-8"], []),
            "TQA-GOLD-0025": ([], ["nodejs.POS-8"]),
            "TQA-GOLD-0026": (["nodejs.HC-U2"], []),
            "TQA-GOLD-0027": ([], ["nodejs.POS-U2"]),
            "TQA-GOLD-0028": (["nodejs.I-HC-A4"], []),
            "TQA-GOLD-0029": ([], ["nodejs.I-POS-4"]),
        }
        for case_id, (smells, positives) in expected.items():
            with self.subTest(case_id=case_id):
                self.assertEqual("nodejs", golden[case_id]["stack"])
                self.assertEqual(smells, golden[case_id]["expected_smells"])
                self.assertEqual(positives, golden[case_id]["expected_positives"])
                self.assertIn("expected_action", golden[case_id])


if __name__ == "__main__":
    unittest.main()
