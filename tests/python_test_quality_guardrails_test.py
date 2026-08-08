import json
import re
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT

PYTHON_ROOT = REPO_ROOT / "souroldgeezer-audit/skills/test-quality-audit"
UNIT = PYTHON_ROOT / "references/extensions/python/unit.md"
INTEGRATION = PYTHON_ROOT / "references/extensions/python/integration.md"
GROUNDING = PYTHON_ROOT / "references/source-grounding.md"
TRIGGERS = PYTHON_ROOT / "references/evals/trigger-cases.jsonl"
BEHAVIORS = PYTHON_ROOT / "references/evals/behavior-cases.jsonl"
GOLDEN = PYTHON_ROOT / "references/golden-corpus/test-quality-audit-cases.jsonl"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_jsonl(path: Path) -> dict[str, dict]:
    return {
        record["id"]: record
        for record in (json.loads(line) for line in read(path).splitlines() if line.strip())
    }


class PythonTestQualityGuardrailsTest(unittest.TestCase):
    def test_new_codes_are_addon_scoped_and_have_required_contract_fields(self) -> None:
        unit = read(UNIT)
        integration = read(INTEGRATION)

        unit_codes = set(re.findall(r"### `(python\.(?:HC|POS)-\d+)`", unit))
        integration_codes = set(re.findall(r"### `(python\.(?:I-HC-A\d+|I-POS-\d+))`", integration))
        self.assertIn("python.HC-7", unit_codes)
        self.assertIn("python.POS-6", unit_codes)
        self.assertIn("python.I-HC-A3", integration_codes)
        self.assertIn("python.I-POS-4", integration_codes)

        for code, text in (
            ("python.HC-7", unit),
            ("python.POS-6", unit),
            ("python.I-HC-A3", integration),
            ("python.I-POS-4", integration),
        ):
            with self.subTest(code=code):
                heading = text[text.index(f"### `{code}`") :]
                self.assertIn("Applies to:", heading.split("### ", 1)[0] + heading[:120])
                self.assertIn("Detection:", heading)
                self.assertIn("Rewrite:", heading)

        self.assertNotIn("python.I-HC-A3", unit)
        self.assertNotIn("python.I-POS-4", unit)
        self.assertNotIn("python.HC-7", integration)
        self.assertNotIn("python.POS-6", integration)

    def test_guidance_preserves_existing_clock_fixture_and_cleanup_boundaries(self) -> None:
        unit = read(UNIT)
        integration = read(INTEGRATION)

        self.assertIn("clock", unit)
        for phrase in ("fixture", "cleanup"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, unit)
                self.assertIn(phrase, integration)
        self.assertIn("Do not rely on a clock or scheduler\nchance", unit)
        self.assertIn("fake-clock", unit)
        self.assertIn("fixture, and cleanup", unit)
        self.assertIn("normal `finally`/fixture teardown", integration)

    def test_python_guardrails_are_source_grounded(self) -> None:
        grounding = read(GROUNDING)
        for source in (
            "docs.python.org/3/library/asyncio-task.html",
            "docs.python.org/3/reference/datamodel.html#asynchronous-context-managers-and-async-with",
            "pytest-asyncio.readthedocs.io",
            "asgi.readthedocs.io/en/latest/specs/lifespan.html",
        ):
            self.assertIn(source, grounding)
        self.assertIn("task completion/cancellation", grounding)
        self.assertIn("application startup/shutdown", grounding)

    def test_synthetic_evals_cover_activation_behavior_and_sibling_boundaries(self) -> None:
        triggers = read_jsonl(TRIGGERS)
        behaviors = read_jsonl(BEHAVIORS)

        self.assertTrue(triggers["test-quality-trigger-yes-python-async-lifecycle"]["expected_activation"])
        self.assertFalse(triggers["test-quality-trigger-no-python-design"]["expected_activation"])
        self.assertFalse(triggers["test-quality-trigger-no-python-security"]["expected_activation"])

        behavior = behaviors["test-quality-behavior-python-async-lifecycle"]
        checks = " ".join(behavior["required_checks"])
        forbidden = " ".join(behavior["forbidden_behaviors"])
        for code in ("python.HC-7", "python.POS-6", "python.I-HC-A3", "python.I-POS-4"):
            self.assertIn(code, checks)
        for phrase in ("documented runner", "clock/sleep", "fixture", "cleanup"):
            self.assertIn(phrase, checks)
        for phrase in (
            "runner with pytest",
            "new clock/sleep policy",
            "Python service",
            "TLS/SSRF",
        ):
            self.assertIn(phrase, forbidden)
        self.assertEqual("synthetic", behavior["source_kind"])
        self.assertFalse(behavior["contains_third_party_text"])

    def test_golden_corpus_has_positive_and_negative_lifecycle_cases(self) -> None:
        golden = read_jsonl(GOLDEN)
        self.assertEqual(["python.HC-7"], golden["TQA-GOLD-0020"]["expected_smells"])
        self.assertEqual(["python.POS-6"], golden["TQA-GOLD-0021"]["expected_positives"])
        self.assertEqual(["python.I-HC-A3"], golden["TQA-GOLD-0022"]["expected_smells"])
        self.assertEqual(["python.I-POS-4"], golden["TQA-GOLD-0023"]["expected_positives"])
        for case_id in ("TQA-GOLD-0020", "TQA-GOLD-0021", "TQA-GOLD-0022", "TQA-GOLD-0023"):
            self.assertEqual("python", golden[case_id]["stack"])
            self.assertIn("expected_action", golden[case_id])


if __name__ == "__main__":
    unittest.main()
