import re
import unittest

from tests.surface_test_lib import read, read_jsonl


def _section(markdown: str, heading: str) -> str:
    match = re.search(rf"(?ms)^{re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", markdown)
    if match is None:
        raise AssertionError(f"missing section {heading}")
    return match.group(1)


class OpsAuthorityContractTest(unittest.TestCase):
    def test_provider_route_selection_is_per_operation_and_auth_gated(self) -> None:
        for path, provider_terms in (
            ("souroldgeezer-ops/docs/provider-reference/github.md", ("GitHub MCP", "gh", "REST")),
            ("souroldgeezer-ops/docs/provider-reference/gitlab.md", ("GitLab MCP", "glab", "REST")),
        ):
            tooling = _section(read(path), "## Tooling Order")
            folded = tooling.casefold()
            self.assertRegex(folded, r"per (each )?operation|separately for each operation")
            self.assertRegex(folded, r"requested operation")
            self.assertRegex(folded, r"authentication|authenticated|auth")
            self.assertRegex(folded, r"permission|authority")
            self.assertTrue(all(term.casefold() in folded for term in provider_terms), path)

    def test_product_repair_requires_diagnosis_existing_authority_and_scope(self) -> None:
        core = read("souroldgeezer-ops/skills/pr-ops/references/core-workflow.md").casefold()
        github = read("souroldgeezer-ops/skills/pr-ops/extensions/github.md").casefold()
        gitlab = read("souroldgeezer-ops/skills/pr-ops/extensions/gitlab.md").casefold()
        for text in (core, github, gitlab):
            self.assertRegex(text, r"diagnos\w*")
            self.assertRegex(text, r"task authorit\w*|implementation authorit\w*")
            self.assertRegex(text, r"scope")
            self.assertRegex(text, r"repair plan")
        self.assertRegex(core, r"automatic fix|automatic correction|auto-fix")

    def test_issue_closure_policy_preserves_marker_order_and_reconciles_auto_close(self) -> None:
        lifecycle = read("souroldgeezer-ops/docs/provider-reference/provider-lifecycle-core.md").casefold()
        issue_core = read("souroldgeezer-ops/skills/issue-ops/references/core-workflow.md").casefold()
        github = read("souroldgeezer-ops/skills/issue-ops/extensions/github.md").casefold()
        internal = read("internal-skills/github-issue-lifecycle/SKILL.md").casefold()
        self.assertLess(lifecycle.index("verification"), lifecycle.index("final issue marker"))
        self.assertLess(lifecycle.index("final issue marker"), lifecycle.index("explicitly\nclosing"))
        for text in (lifecycle, issue_core, github, internal):
            self.assertRegex(text, r"non-closing")
            self.assertRegex(text, r"auto-closed|auto-clos\w*")
            self.assertRegex(text, r"marker followed closure|marker as a later event|actual order of events")

    def test_claude_wrappers_inherit_tools_and_can_discover_provider_tools(self) -> None:
        for path in ("souroldgeezer-ops/agents/issue-ops.md", "souroldgeezer-ops/agents/pr-ops.md"):
            text = read(path)
            frontmatter = text.split("---", 2)[1]
            self.assertNotRegex(frontmatter, r"(?m)^tools:")
            self.assertIn("deferred-tool discovery", text)
            self.assertIn("inherits the caller's available tool set", text)
            self.assertIn("does not add authority", text)

    def test_synthetic_cases_cover_partial_capability_repair_and_auto_close(self) -> None:
        packs = (
            read_jsonl("souroldgeezer-ops/skills/pr-ops/references/evals/behavior-cases.jsonl"),
            read_jsonl("souroldgeezer-ops/skills/issue-ops/references/evals/behavior-cases.jsonl"),
            read_jsonl("internal-skills/github-issue-lifecycle/references/evals/behavior-cases.jsonl"),
        )
        ids = {case["id"] for pack in packs for case in pack}
        self.assertTrue(
            {
                "pr-ops-behavior-diagnosed-repair-authority",
                "pr-ops-behavior-repair-without-authority",
                "pr-ops-behavior-operation-capability-fallback",
                "issue-ops-behavior-partial-mcp-capability",
                "issue-ops-behavior-missing-cli-auth",
                "issue-ops-behavior-marker-before-auto-close",
                "github-issue-lifecycle-behavior-partial-mcp",
                "github-issue-lifecycle-behavior-auto-close-reconciliation",
            }.issubset(ids)
        )
        for pack in packs:
            for case in pack:
                self.assertEqual(case["source_kind"], "synthetic")
                self.assertFalse(case["contains_third_party_text"])


if __name__ == "__main__":
    unittest.main()
