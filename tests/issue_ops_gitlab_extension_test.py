import unittest

from tests.surface_test_lib import read, read_jsonl


class IssueOpsGitLabExtensionTest(unittest.TestCase):
    def test_issue_ops_loads_gitlab_extension_and_metadata_mentions_it(self) -> None:
        skill = read("souroldgeezer-ops/skills/issue-ops/SKILL.md")
        readme = read("souroldgeezer-ops/skills/issue-ops/extensions/README.md")
        claude_agent = read("souroldgeezer-ops/agents/issue-ops.md")

        self.assertIn("extensions/gitlab.md", skill)
        self.assertIn("gitlab.md", readme)
        for text in (skill, claude_agent):
            self.assertIn("GitLab", text)

    def test_gitlab_extension_has_required_sections_and_authoritative_sources(self) -> None:
        gitlab = read("souroldgeezer-ops/skills/issue-ops/extensions/gitlab.md")

        for heading in (
            "## State Resolution",
            "## Tooling Order",
            "## Lifecycle Status",
            "## Integration Strategies",
            "## Metadata Policy",
            "## GitLab Escalation Gates",
            "## Completion",
        ):
            self.assertIn(heading, gitlab)

        for source in (
            "docs.gitlab.com/api/rest/authentication/",
            "docs.gitlab.com/api/issues/",
            "docs.gitlab.com/api/notes/",
            "docs.gitlab.com/api/issue_links/",
            "docs.gitlab.com/api/merge_requests/",
            "docs.gitlab.com/cli/issue/",
            "docs.gitlab.com/user/project/issues/managing_issues/",
        ):
            self.assertIn(source, gitlab)

        self.assertIn("PRIVATE-TOKEN", gitlab)
        self.assertIn("issue_iid", gitlab)
        self.assertIn("URL-encoded path", gitlab)
        self.assertIn("related_merge_requests", gitlab)
        self.assertIn("closes_issues", gitlab)

    def test_gitlab_support_has_synthetic_eval_and_source_grounding(self) -> None:
        trigger_ids = {
            record["id"]
            for record in read_jsonl("souroldgeezer-ops/skills/issue-ops/references/evals/trigger-cases.jsonl")
        }
        behavior_ids = {
            record["id"]
            for record in read_jsonl("souroldgeezer-ops/skills/issue-ops/references/evals/behavior-cases.jsonl")
        }
        source_grounding = read("souroldgeezer-ops/skills/issue-ops/references/source-grounding.md")

        self.assertIn("issue-ops-trigger-yes-gitlab-url", trigger_ids)
        self.assertIn("issue-ops-behavior-gitlab-provider-selection", behavior_ids)
        self.assertIn("GitLab provider extension", source_grounding)
        self.assertIn("docs.gitlab.com", source_grounding)


if __name__ == "__main__":
    unittest.main()
