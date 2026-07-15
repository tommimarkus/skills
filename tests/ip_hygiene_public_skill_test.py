import json
import unittest

from tests.surface_test_lib import REPO_ROOT, read

PUBLIC_SKILL = REPO_ROOT / "souroldgeezer-audit" / "skills" / "ip-hygiene"
INTERNAL_SKILL = REPO_ROOT / ".claude" / "skills" / "ip-hygiene"
PUBLIC_SKILL_PATH = "souroldgeezer-audit/skills/ip-hygiene/SKILL.md"
INTERNAL_SKILL_PATH = ".claude/skills/ip-hygiene/SKILL.md"
AUDIT_DESCRIPTION = (
    "Rubric-driven audits for DevSecOps posture, test quality, IP hygiene, and "
    "duplication/waste (Lean), with per-stack extensions and matching Claude Code "
    "subagents."
)


class PublicIpHygieneSkillTest(unittest.TestCase):
    def test_internal_ip_hygiene_skill_removed(self) -> None:
        self.assertFalse(INTERNAL_SKILL.exists(), f"{INTERNAL_SKILL} should not remain")

    def test_public_skill_files_exist(self) -> None:
        expected = [
            "SKILL.md",
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

        self.assertIn("name: ip-hygiene", claude_agent)
        self.assertIn("Invoke the `ip-hygiene` skill", claude_agent)
        self.assertIn("../skills/ip-hygiene/SKILL.md", claude_agent)
        self.assertNotIn(INTERNAL_SKILL_PATH, claude_agent)

    def test_audit_plugin_version_and_description_are_synchronized(self) -> None:
        marketplace = json.loads(read(".claude-plugin/marketplace.json"))
        claude_manifest = json.loads(read("souroldgeezer-audit/.claude-plugin/plugin.json"))
        audit_entry = next(
            plugin for plugin in marketplace["plugins"] if plugin["name"] == "souroldgeezer-audit"
        )

        # plugin.json#version is the sole version authority (Claude Code always
        # resolves it over a marketplace-entry copy without warning, so a mirrored
        # copy is a silent drift risk); the manifest is the in-test source of truth
        # and the marketplace entry must not carry a competing version key. The
        # value is deliberately not pinned to a literal — the CalVer stamp is
        # assigned at integration on main and owned by scripts/version_stamp.py, so
        # a pin here would just be a hand-edited sync cell every bump. The
        # description stays pinned because it is content, and stays synchronized
        # across both surfaces.
        canonical = claude_manifest["version"]
        self.assertRegex(canonical, r"^\d{4}\.\d{2}\.\d+$")
        self.assertNotIn("version", audit_entry)
        self.assertEqual(audit_entry["description"], AUDIT_DESCRIPTION)
        self.assertEqual(claude_manifest["description"], AUDIT_DESCRIPTION)

    def test_repo_guidance_and_hooks_reference_public_skill(self) -> None:
        checked_paths = [
            "README.md",
            "CLAUDE.md",
            "internal-skills/github-issue-lifecycle/SKILL.md",
            "scripts/agent-hooks/stop-ip-hygiene.sh",
            "scripts/test-stop-hooks.sh",
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
