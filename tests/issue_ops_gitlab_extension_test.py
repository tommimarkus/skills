import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def read_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


class IssueOpsGitLabExtensionTest(unittest.TestCase):
    def test_issue_ops_loads_gitlab_extension_and_metadata_mentions_it(self) -> None:
        skill = read("souroldgeezer-ops/skills/issue-ops/SKILL.md")
        readme = read("souroldgeezer-ops/skills/issue-ops/extensions/README.md")
        openai = read("souroldgeezer-ops/skills/issue-ops/agents/openai.yaml")
        claude_agent = read("souroldgeezer-ops/agents/issue-ops.md")
        codex_agent = read(".codex/agents/issue-ops.toml")

        self.assertIn("extensions/gitlab.md", skill)
        self.assertIn("gitlab.md", readme)
        for text in (skill, openai, claude_agent, codex_agent):
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
