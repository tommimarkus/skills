"""software-design's per-stack test-code lane: six guidance-only files reached
through one SKILL.md route, with test adequacy left to test-quality-audit."""
import unittest

from tests.surface_test_lib import compact, eval_ids, read

SD = "souroldgeezer-design/skills/software-design"
LINE_CAP = 75
SECTIONS = (
    "## Shared test support",
    "## Setup lifetime",
    "## Time, randomness, and ambient environment",
    "## Isolation and parallel runs",
    "## Lanes and durations",
)
CLOSING = "Adds no key codes; findings cite core `SD-*`; test adequacy → `test-quality-audit`."
# stack -> (one robust test-code fact, production-side ambient-environment markers)
STACKS = {
    "csharp": ("IClassFixture", ("CA1305", "TimeProvider")),
    "java": ("@BeforeAll", ("Locale.ROOT", "Clock")),
    "python": ("conftest.py", ("encoding=", "EncodingWarning", "PEP 686")),
    "rust": ("tests/common", ("chrono::Local",)),
    "shell-script": ("setup_file", ("LC_ALL=C",)),
    "typescript": ("TZ", ("Intl", "localeCompare")),
}


class SoftwareDesignTestCodeLaneTest(unittest.TestCase):
    def test_each_test_code_file_has_the_required_shape_and_no_key_codes(self) -> None:
        for stack, (fact, _) in STACKS.items():
            with self.subTest(stack=stack):
                text = read(f"{SD}/extensions/{stack}/test-code.md")
                lines = text.splitlines()
                self.assertRegex(lines[0], r"^# .+ Test-Code Lane$")
                self.assertRegex(text, r"(?m)^Sources: .*https://")
                positions = [text.find(section) for section in SECTIONS]
                self.assertNotIn(-1, positions)
                self.assertEqual(positions, sorted(positions))
                self.assertEqual(compact(lines[-1]), CLOSING)
                self.assertLessEqual(len(lines), LINE_CAP)
                self.assertIn(fact, text)
                self.assertNotIn("Key codes", text)
                self.assertNotRegex(text, r"\b[a-z-]+\.SD-[A-Z]-\d")

    def test_skill_routes_every_test_code_file_and_names_the_escalation(self) -> None:
        skill = read(f"{SD}/SKILL.md")
        flat_skill = compact(skill)
        for stack in STACKS:
            with self.subTest(stack=stack):
                self.assertIn(f"(extensions/{stack}/test-code.md)", skill)
        for phrase in (
            "security/test adequacy",
            "tdd-policy",
            "production-design claims",
            "escalate to Build/Review",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, flat_skill)

    def test_stack_cores_narrow_delegation_and_own_ambient_environment(self) -> None:
        for stack, (_, markers) in STACKS.items():
            with self.subTest(stack=stack):
                core = read(f"{SD}/extensions/{stack}.md")
                flat_core = compact(core)
                self.assertIn("test adequacy", flat_core)
                self.assertIn("test-code lane (Load Map)", flat_core)
                self.assertNotRegex(core, r"\]\([^)]*test-code\.md\)")
                for marker in markers:
                    self.assertIn(marker, core)

    def test_core_reference_owns_ambient_environment_seams(self) -> None:
        reference = read("souroldgeezer-design/docs/software-reference/software-design.md")
        section = compact(reference.split("### 3.10", 1)[1].split("### 3.11", 1)[0])
        for phrase in (
            "locale",
            "timezone",
            "invariant culture",
            "explicit encoding",
            "explicit culture",
            "SD-B-5",
            "Test code is code",
            "adequacy",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, section)

    def test_authoring_procedure_and_evals_cover_every_test_code_file(self) -> None:
        authoring = read(f"{SD}/references/procedures/extension-authoring.md")
        behavior = eval_ids(f"{SD}/references/evals/behavior-cases.jsonl")
        self.assertIn("software-design-behavior-machine-format-invariant-culture", behavior)
        self.assertIn("test-code", read(f"{SD}/references/source-grounding.md"))
        for stack in STACKS:
            with self.subTest(stack=stack):
                self.assertIn(f"{stack}/test-code.md", authoring)
                self.assertIn(f"software-design-behavior-test-code-{stack}", behavior)


if __name__ == "__main__":
    unittest.main()
