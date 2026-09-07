"""Human guides retain reachable tasks, commands, and published skill links."""
import json
import re
import unittest
from urllib.parse import unquote, urlsplit

from tests.surface_test_lib import REPO_ROOT


GUIDES = (
    "README.md", "docs/using-skills.md", "docs/runtime-support.md",
    "docs/contributing.md", "docs/maintenance-procedures.md",
    "docs/release-checklist.md", "docs/skill-architecture.md",
    "docs/skill-evaluation.md", "PRIVACY.md", "TERMS.md", "AGENTS.md", "CLAUDE.md",
    "souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md",
    "souroldgeezer-audit/skills/lean-audit/references/hook-recipe.md",
)


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def prose(text: str) -> str:
    """Exclude fenced examples from Markdown navigation checks."""
    return re.sub(r"^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$", "", text, flags=re.M | re.S)


def anchors(text: str) -> set[str]:
    """GitHub heading anchors and explicit HTML anchors used by these guides."""
    result = set(re.findall(r'(?:id|name)=["\']([^"\']+)["\']', text))
    counts = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", prose(text), flags=re.M):
        label = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", heading)
        slug = re.sub(r"[^\w\- ]", "", label.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        result.add(f"{slug}-{count}" if count else slug)
        counts[slug] = count + 1
    return result


class ValidationSurfaceTest(unittest.TestCase):
    def test_contributor_guide_links_the_maintainer_documentation(self) -> None:
        contributing = " ".join(read("docs/contributing.md").split())
        for guide in (
            "skill-architecture.md", "skill-evaluation.md",
            "maintenance-procedures.md", "release-checklist.md",
        ):
            with self.subTest(guide=guide):
                self.assertRegex(contributing, rf"\[[^]]+\]\({re.escape(guide)}\)")
        release = " ".join(read("docs/release-checklist.md").split())
        self.assertIn("all 16 shared public skills", release)
        self.assertNotIn("docs/refactor/fragmentation-execplan.md", release)

    def test_default_validation_runs_stop_hook_regression_script(self) -> None:
        self.assertIn("bash scripts/test-stop-hooks.sh", read("scripts/validate-fragmentation.sh"))
        self.assertIn("scripts/test-stop-hooks.sh", read("README.md"))

    def test_runtime_guide_keeps_operator_and_optional_smoke_destinations(self) -> None:
        runtime = " ".join(read("docs/runtime-support.md").split())
        procedure = "../souroldgeezer-architecture/skills/architecture-design/references/procedures/dediren-install.md"
        self.assertIn(f"]({procedure})", runtime)
        self.assertIn(
            "](maintenance-procedures.md#dediren-upstream-release-adoption)", runtime,
        )
        maintenance = " ".join(read("docs/maintenance-procedures.md").split())
        for fact in (
            "DEDIREN_RUNTIME_SMOKE=1", 'DEDIREN_COMMAND="$launcher"',
            "uv run python -m unittest tests.architecture_dediren_release_test",
        ):
            with self.subTest(fact=fact):
                self.assertIn(fact, maintenance)

    def test_readme_and_usage_link_every_shipped_skill(self) -> None:
        marketplace = json.loads(read(".claude-plugin/marketplace.json"))
        skill_paths = {
            path.relative_to(REPO_ROOT).as_posix()
            for plugin in marketplace["plugins"]
            for path in (REPO_ROOT / plugin["source"] / "skills").glob("*/SKILL.md")
        }
        self.assertEqual(16, len(skill_paths), "Update the documented inventory with the marketplace")
        for guide, prefix in (("README.md", ""), ("docs/using-skills.md", "../")):
            content = read(guide)
            for path in sorted(skill_paths):
                with self.subTest(guide=guide, path=path):
                    self.assertIn(f"]({prefix}{path})", content)

    def test_readme_preserves_existing_anchors_and_reaches_task_guides(self) -> None:
        readme = read("README.md")
        self.assertTrue({
            "what-this-is", "install", "claude-code", "codex", "github-copilot-cli",
            "dediren-runtime-architecture-plugin-only", "local-development",
            "examples", "validation", "detailed-docs",
        } <= anchors(readme))
        for target in ("docs/using-skills.md", "docs/runtime-support.md", "docs/contributing.md"):
            with self.subTest(target=target):
                self.assertRegex(readme, rf"\[[^]]+\]\({re.escape(target)}\)")

    def test_scoped_guides_have_existing_local_link_targets_and_anchors(self) -> None:
        for guide in GUIDES:
            source = REPO_ROOT / guide
            for destination in re.findall(r"\[[^]\n]+\]\(([^)\s]+)\)", prose(read(guide))):
                parsed = urlsplit(destination)
                if parsed.scheme or parsed.netloc:
                    continue
                target = source.parent / unquote(parsed.path) if parsed.path else source
                with self.subTest(guide=guide, destination=destination):
                    self.assertTrue(target.exists(), f"Missing local destination: {target}")
                    if parsed.fragment and target.suffix == ".md":
                        self.assertIn(unquote(parsed.fragment), anchors(target.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
