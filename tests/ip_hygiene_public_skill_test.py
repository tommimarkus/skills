import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SKILL = REPO_ROOT / "souroldgeezer-audit" / "skills" / "ip-hygiene"
INTERNAL_SKILL = REPO_ROOT / ".claude" / "skills" / "ip-hygiene"
PUBLIC_SKILL_PATH = "souroldgeezer-audit/skills/ip-hygiene/SKILL.md"
INTERNAL_SKILL_PATH = ".claude/skills/ip-hygiene/SKILL.md"
AUDIT_DESCRIPTION = (
    "Rubric-driven audits for DevSecOps posture, test quality, IP hygiene, and "
    "duplication/waste (Lean), with per-stack extensions, matching Claude Code "
    "subagents, and Codex skill metadata."
)


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


class PublicIpHygieneSkillTest(unittest.TestCase):
    def test_internal_ip_hygiene_skill_removed(self) -> None:
        self.assertFalse(INTERNAL_SKILL.exists(), f"{INTERNAL_SKILL} should not remain")

    def test_public_skill_files_exist(self) -> None:
        expected = [
            "SKILL.md",
            "agents/openai.yaml",
            "references/authority-index.md",
            "references/copyright.md",
            "references/drive-by.md",
            "references/evals/behavior-cases.jsonl",
            "references/evals/trigger-cases.jsonl",
            "references/fence-posts.md",
            "references/ip-hygiene-reference.md",
            "references/licence-assets.md",
            "references/source-grounding.md",
            "references/trademark.md",
        ]
        missing = [path for path in expected if not (PUBLIC_SKILL / path).is_file()]
        self.assertEqual(missing, [])

    def test_public_skill_contract_is_focused_configurable_and_terse(self) -> None:
        skill = read(PUBLIC_SKILL_PATH)
        self.assertIn("target repo guidance", skill)
        self.assertIn("General repo-wide IP hygiene is future scope", skill)
        self.assertIn("not legal advice", skill)
        self.assertIn("nothing to check", skill)
        self.assertIn("checked: <bucket list>; no IP hygiene changes needed", skill)
        self.assertIn("fixed: <path:line> - <remedy summary>", skill)
        self.assertIn(
            "deferred drive-by observation at <path:line> - <issue>; recommend separate retroactive audit",
            skill,
        )

    def test_runtime_entrypoints_exist_and_point_to_public_skill(self) -> None:
        claude_agent = read("souroldgeezer-audit/agents/ip-hygiene.md")
        codex_agent = read(".codex/agents/ip-hygiene.toml")
        openai_yaml = read("souroldgeezer-audit/skills/ip-hygiene/agents/openai.yaml")

        self.assertIn("name: ip-hygiene", claude_agent)
        self.assertIn("Invoke the `ip-hygiene` skill", claude_agent)
        self.assertIn(PUBLIC_SKILL_PATH, claude_agent)
        self.assertNotIn(INTERNAL_SKILL_PATH, claude_agent)
        self.assertIn('name = "ip-hygiene"', codex_agent)
        self.assertIn(PUBLIC_SKILL_PATH, codex_agent)
        self.assertIn('display_name: "IP Hygiene"', openai_yaml)
        self.assertIn("$ip-hygiene", openai_yaml)

    def test_audit_plugin_version_and_description_are_synchronized(self) -> None:
        marketplace = json.loads(read(".claude-plugin/marketplace.json"))
        claude_manifest = json.loads(read("souroldgeezer-audit/.claude-plugin/plugin.json"))
        codex_manifest = json.loads(read("souroldgeezer-audit/.codex-plugin/plugin.json"))
        audit_entry = next(
            plugin for plugin in marketplace["plugins"] if plugin["name"] == "souroldgeezer-audit"
        )

        # The marketplace entry is the in-test source of truth for the version; the
        # manifests must agree with it. The value is deliberately not pinned to a
        # literal — the CalVer stamp is assigned at integration on main and owned by
        # scripts/version_stamp.py, so a pin here would just be a sixth sync cell to
        # hand-edit every bump. The description stays pinned because it is content.
        canonical = audit_entry["version"]
        self.assertRegex(canonical, r"^\d{4}\.\d{2}\.\d+$")
        for surface in (audit_entry, claude_manifest, codex_manifest):
            self.assertEqual(surface["version"], canonical)
            self.assertEqual(surface["description"], AUDIT_DESCRIPTION)

        prompts = codex_manifest["interface"]["defaultPrompt"]
        self.assertEqual(codex_manifest["interface"]["websiteURL"], "https://github.com/tommimarkus/skills")
        self.assertEqual(
            codex_manifest["interface"]["privacyPolicyURL"],
            "https://github.com/tommimarkus/skills/blob/main/PRIVACY.md",
        )
        self.assertEqual(
            codex_manifest["interface"]["termsOfServiceURL"],
            "https://github.com/tommimarkus/skills/blob/main/TERMS.md",
        )
        self.assertLessEqual(len(prompts), 3)
        self.assertTrue(any("IP hygiene" in prompt or "ip-hygiene" in prompt for prompt in prompts))

    def test_repo_guidance_and_hooks_reference_public_skill(self) -> None:
        checked_paths = [
            "README.md",
            "CLAUDE.md",
            "AGENTS.md",
            "internal-skills/github-issue-lifecycle/SKILL.md",
            "scripts/agent-hooks/stop-ip-hygiene.sh",
            "scripts/test-stop-plugin-eval-hooks.sh",
        ]
        for path in checked_paths:
            content = read(path)
            self.assertIn(PUBLIC_SKILL_PATH, content, path)
            self.assertNotIn(INTERNAL_SKILL_PATH, content, path)

        readme = read("README.md")
        self.assertIn("[ip-hygiene](souroldgeezer-audit/skills/ip-hygiene/SKILL.md)", readme)

        claude = read("CLAUDE.md")
        # CLAUDE.md was slimmed (0d28964); it now states the migration in prose
        # rather than the old bolded "(plugin ...)" list format.
        self.assertIn("now a public skill in `souroldgeezer-audit`", claude)
        self.assertNotIn("**`ip-hygiene`** at [.claude/skills/ip-hygiene/SKILL.md]", claude)


if __name__ == "__main__":
    unittest.main()
