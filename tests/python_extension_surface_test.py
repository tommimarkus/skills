import re
import unittest

from tests.surface_test_lib import (
    assert_software_design_loads_stack_extension,
    compact,
    read,
    read_jsonl,
)


class PythonExtensionSurfaceTest(unittest.TestCase):
    def test_software_design_loads_python_extension_and_keeps_scope(self) -> None:
        assert_software_design_loads_stack_extension(self, "python", "Python®")

        python = read("souroldgeezer-design/skills/software-design/extensions/python.md")
        for marker in (
            "pyproject.toml",
            "requires-python",
            "First assimilate the project",
            "resource-lifetime",
            "sync/async",
            "contextvars",
            "py.typed",
            "supported prior release",
            "public-API or type-compatibility check",
            "bounded manual or generated diff",
            "release-policy",
            "profile",
            "api-design",
            "devsecops-audit",
            "test-quality-audit",
        ):
            self.assertIn(marker, compact(python))

        for core_code in ("SD-C-6", "SD-S-5", "SD-Q-4"):
            self.assertIn(core_code, python)
        self.assertNotRegex(python, r"python\.SD-(?:C-6|S-5|Q-4)")

    def test_python_guidance_is_grounded_in_authoritative_docs(self) -> None:
        python = read("souroldgeezer-design/skills/software-design/extensions/python.md")
        grounding = read("souroldgeezer-design/skills/software-design/references/source-grounding.md")

        for source in (
            "docs.python.org/3/reference/import.html",
            "packaging.python.org",
            "peps.python.org/pep-0561/",
            "docs.python.org/3/library/asyncio-task.html",
            "docs.python.org/3/library/asyncio-runner.html",
            "docs.python.org/3/library/contextvars.html",
            "docs.python.org/3/library/typing.html",
            "docs.python.org/3/library/profile.html",
            "docs.astral.sh/uv/",
        ):
            with self.subTest(source=source):
                self.assertIn(source, python)
                self.assertIn(source, grounding)

    def test_python_support_has_project_first_and_core_code_eval_coverage(self) -> None:
        trigger_ids = {
            record["id"]
            for record in read_jsonl("souroldgeezer-design/skills/software-design/references/evals/trigger-cases.jsonl")
        }
        behavior = {
            record["id"]: record
            for record in read_jsonl("souroldgeezer-design/skills/software-design/references/evals/behavior-cases.jsonl")
        }

        for case_id in (
            "software-design-trigger-yes-python-async-boundaries",
            "software-design-trigger-yes-python-public-contract",
        ):
            self.assertIn(case_id, trigger_ids)

        expected = {
            "software-design-behavior-python-project-first-assimilation":
                ("verify Python floor/framework/conventions/tools first", "prescribe uv"),
            "software-design-behavior-python-async-resource-ownership":
                ("SD-C-6", "prescribe one async framework"),
            "software-design-behavior-python-context-local-state":
                ("contextvars from thread-local and globals", "mandate contextvars"),
            "software-design-behavior-python-failure-and-performance-contracts":
                ("SD-S-5", "recommend an optimization from intuition alone"),
            "software-design-behavior-python-typed-contract-compatibility":
                ("supported prior release or named baseline", "prescribe a particular checker"),
        }
        for case_id, (required, forbidden) in expected.items():
            with self.subTest(case_id=case_id):
                checks = " ".join(behavior[case_id]["required_checks"])
                forbidden_behaviors = " ".join(behavior[case_id]["forbidden_behaviors"])
                self.assertIn(required, checks)
                self.assertIn(forbidden, forbidden_behaviors)

    def test_python_extension_does_not_introduce_new_smell_code_family(self) -> None:
        python = read("souroldgeezer-design/skills/software-design/extensions/python.md")
        codes = set(re.findall(r"python\.SD-[A-Z]-\d+", python))
        self.assertEqual(
            codes,
            {
                "python.SD-B-1", "python.SD-B-4", "python.SD-C-1",
                "python.SD-C-2", "python.SD-C-3", "python.SD-S-1",
                "python.SD-S-2", "python.SD-S-3", "python.SD-E-1",
            },
        )


if __name__ == "__main__":
    unittest.main()
