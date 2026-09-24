import unittest

from tests.surface_test_lib import REPO_ROOT, load_script_module, read_jsonl


class OpsAuthorityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        report = load_script_module(
            "ops_authority_skill_architecture_report",
            REPO_ROOT / "scripts" / "skill_architecture_report.py",
        )
        cls.parse_frontmatter = staticmethod(report.parse_frontmatter)

    def test_claude_provider_agents_allow_inherited_tools(self) -> None:
        for relative in (
            "souroldgeezer-ops/agents/issue-ops.md",
            "souroldgeezer-ops/agents/pr-ops.md",
        ):
            metadata, _body = self.parse_frontmatter(REPO_ROOT / relative)
            with self.subTest(agent=relative):
                self.assertNotIn("tools", metadata)

    def test_synthetic_cases_have_valid_schema_and_required_decision_coverage(self) -> None:
        packs = (
            "souroldgeezer-ops/skills/pr-ops/references/evals/behavior-cases.jsonl",
            "souroldgeezer-ops/skills/issue-ops/references/evals/behavior-cases.jsonl",
            "internal-skills/github-issue-lifecycle/references/evals/behavior-cases.jsonl",
        )
        records = [case for pack in packs for case in read_jsonl(pack)]
        ids = [case["id"] for case in records]
        self.assertEqual(len(ids), len(set(ids)))

        required_fields = {
            "id": str,
            "prompt": str,
            "expected_artifacts": list,
            "required_checks": list,
            "forbidden_behaviors": list,
            "grader": str,
            "source_kind": str,
            "source_url": str,
            "ip_handling": str,
            "contains_third_party_text": bool,
        }
        for case in records:
            with self.subTest(case=case.get("id")):
                for field, expected_type in required_fields.items():
                    self.assertIsInstance(case.get(field), expected_type, field)
                self.assertTrue(case["id"])
                self.assertTrue(case["expected_artifacts"])
                self.assertTrue(case["required_checks"])
                self.assertTrue(case["forbidden_behaviors"])
                self.assertTrue(case["grader"])

        new_cases = {
            case["id"]: case
            for case in records
            if case["id"].startswith((
                "pr-ops-behavior-diagnosed-repair-authority",
                "pr-ops-behavior-repair-without-authority",
                "pr-ops-behavior-operation-capability-fallback",
                "issue-ops-behavior-partial-mcp-capability",
                "issue-ops-behavior-missing-cli-auth",
                "issue-ops-behavior-marker-before-auto-close",
                "github-issue-lifecycle-behavior-partial-mcp",
                "github-issue-lifecycle-behavior-auto-close-reconciliation",
            ))
        }
        expected_ids = {
            "pr-ops-behavior-diagnosed-repair-authority",
            "pr-ops-behavior-repair-without-authority",
            "pr-ops-behavior-operation-capability-fallback",
            "issue-ops-behavior-partial-mcp-capability",
            "issue-ops-behavior-missing-cli-auth",
            "issue-ops-behavior-marker-before-auto-close",
            "github-issue-lifecycle-behavior-partial-mcp",
            "github-issue-lifecycle-behavior-auto-close-reconciliation",
        }
        self.assertTrue(expected_ids.issubset(new_cases))
        required_coverage = {
            "provider_partial_capability",
            "missing_authentication",
            "repair_with_authority",
            "repair_without_authority",
            "closure_order",
            "auto_close_reconciliation",
        }
        coverage = set()
        for identifier, case in new_cases.items():
            with self.subTest(case=identifier):
                self.assertEqual(case["source_kind"], "synthetic")
                self.assertFalse(case["contains_third_party_text"])
                self.assertIsInstance(case.get("coverage"), list)
                self.assertTrue(all(isinstance(item, str) for item in case["coverage"]))
                coverage.update(case["coverage"])
        self.assertTrue(required_coverage.issubset(coverage))


if __name__ == "__main__":
    unittest.main()
