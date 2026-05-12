import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCH_PLUGIN = REPO_ROOT / "souroldgeezer-architecture"
ACTIVE_SURFACES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / ".claude-plugin" / "marketplace.json",
    ARCH_PLUGIN / ".claude-plugin" / "plugin.json",
    ARCH_PLUGIN / ".codex-plugin" / "plugin.json",
    ARCH_PLUGIN / "agents" / "architecture-design.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "SKILL.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "agents" / "openai.yaml",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "smell-catalog.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "red-flags.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "source-grounding.md",
    ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
    REPO_ROOT / "souroldgeezer-design" / "skills" / "app-design" / "SKILL.md",
    REPO_ROOT / "souroldgeezer-design" / "skills" / "api-design" / "SKILL.md",
    REPO_ROOT / "souroldgeezer-design" / "skills" / "infra-design" / "SKILL.md",
]
EXTRACT_GROUP_SURFACES = [
    ARCH_PLUGIN / "skills" / "architecture-design" / "SKILL.md",
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "procedures"
    / "architecture-operational-workflow.md",
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "procedures"
    / "lifting-rules-dotnet.md",
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "procedures"
    / "lifting-rules-bicep.md",
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "procedures"
    / "lifting-rules-gha.md",
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "procedures"
    / "lifting-rules-process.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl",
]
GROUPED_LAYOUT_GUARD_SURFACES = [
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "procedures"
    / "architecture-operational-workflow.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
    ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
]
EA_MODELING_FEEDBACK_SURFACES = [
    ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl",
]


class ArchitectureDedirenSurfaceTest(unittest.TestCase):
    def test_architecture_plugin_version_is_1_1_1_everywhere(self) -> None:
        marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        marketplace_entry = next(
            plugin for plugin in marketplace["plugins"] if plugin["name"] == "souroldgeezer-architecture"
        )
        claude_manifest = json.loads((ARCH_PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        codex_manifest = json.loads((ARCH_PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(marketplace_entry["version"], "1.1.2")
        self.assertEqual(claude_manifest["version"], "1.1.2")
        self.assertEqual(codex_manifest["version"], "1.1.2")
        self.assertEqual(marketplace_entry["description"], claude_manifest["description"])
        self.assertEqual(marketplace_entry["description"], codex_manifest["description"])

    def test_active_surfaces_do_not_reference_retired_arch_layout_contracts(self) -> None:
        retired_terms = [
            "arch-layout",
            "Architecture IR",
            "layout-provenance",
            "layoutPolicy",
            "route-repair",
            "global-polish",
            "validate-png",
            "rendered PNG",
            "docs/architecture/<feature>.oef.xml",
            "docs/architecture/&lt;feature&gt;.oef.xml",
        ]

        for surface in ACTIVE_SURFACES:
            content = surface.read_text(encoding="utf-8")
            for term in retired_terms:
                with self.subTest(surface=surface.relative_to(REPO_ROOT), term=term):
                    self.assertNotIn(term, content)

    def test_active_surfaces_use_dediren_package_pairing(self) -> None:
        expected_path = "docs/architecture/<feature>.dediren/"
        surfaces = [
            ARCH_PLUGIN / "skills" / "architecture-design" / "SKILL.md",
            REPO_ROOT / "souroldgeezer-design" / "skills" / "app-design" / "SKILL.md",
            REPO_ROOT / "souroldgeezer-design" / "skills" / "api-design" / "SKILL.md",
            REPO_ROOT / "souroldgeezer-design" / "skills" / "infra-design" / "SKILL.md",
        ]

        for surface in surfaces:
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                self.assertIn(expected_path, surface.read_text(encoding="utf-8"))

    def test_extract_guidance_requires_source_backed_groups(self) -> None:
        expected_phrase = "source-backed groups"

        for surface in EXTRACT_GROUP_SURFACES:
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                self.assertIn(expected_phrase, surface.read_text(encoding="utf-8"))

    def test_extract_group_guidance_names_generic_graph_model_location(self) -> None:
        expected_phrase = "model.json` under `plugins.generic-graph.views[].groups`, not `project.json`"
        surfaces = [
            ARCH_PLUGIN / "skills" / "architecture-design" / "SKILL.md",
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md",
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
        ]

        for surface in surfaces:
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                content = " ".join(surface.read_text(encoding="utf-8").split())
                self.assertIn(expected_phrase, content)

    def test_process_lifting_guidance_prevents_overgrouping_small_linear_views(self) -> None:
        expected_phrase = (
            "Do not add groups to small linear process views unless a participant, "
            "system responsibility, trust boundary, or orchestration boundary "
            "changes the architectural reading."
        )
        surfaces = [
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "lifting-rules-process.md",
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
        ]

        for surface in surfaces:
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                content = " ".join(surface.read_text(encoding="utf-8").split())
                self.assertIn(expected_phrase, content)

    def test_grouped_layout_guidance_requires_validation_fallback(self) -> None:
        expected_phrases = [
            "If grouped layout validation reports connector-through-node, invalid route, or group-boundary warnings",
            "rerun the same view without groups",
            "use the cleaner layout as evidence and report the grouped-layout regression",
        ]

        for surface in GROUPED_LAYOUT_GUARD_SURFACES:
            content = " ".join(surface.read_text(encoding="utf-8").split())
            for phrase in expected_phrases:
                with self.subTest(surface=surface.relative_to(REPO_ROOT), phrase=phrase):
                    self.assertIn(phrase, content)

    def test_lead_ea_modeling_feedback_is_documented(self) -> None:
        expected_phrases = [
            "APIs and GUIs are Application Interfaces",
            "Application Services model the functionality exposed through an interface",
            "Application Components must not realize Application Interfaces",
            "Use Triggering when the architectural claim is process sequencing",
            "define the view concern, allowed element types, and relationship types",
            "Dediren tool issues",
        ]

        for surface in EA_MODELING_FEEDBACK_SURFACES:
            content = " ".join(surface.read_text(encoding="utf-8").split())
            for phrase in expected_phrases:
                with self.subTest(surface=surface.relative_to(REPO_ROOT), phrase=phrase):
                    self.assertIn(phrase, content)

    def test_new_finding_taxonomy_is_documented_without_legacy_ad_codes(self) -> None:
        smell_catalog = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "smell-catalog.md"
        ).read_text(encoding="utf-8")

        for finding_prefix in ["ARCH-M-", "ARCH-V-", "ARCH-L-", "ARCH-R-", "ARCH-X-", "ARCH-E-", "ARCH-Q-"]:
            with self.subTest(finding_prefix=finding_prefix):
                self.assertIn(finding_prefix, smell_catalog)

        for legacy_prefix in ["AD-", "AD-Q", "AD-L", "AD-B", "AD-DR"]:
            with self.subTest(legacy_prefix=legacy_prefix):
                self.assertNotIn(legacy_prefix, smell_catalog)

    def test_old_runtime_files_are_removed(self) -> None:
        retired_paths = [
            REPO_ROOT / "tools" / "architecture-layout-java",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "bin" / "arch-layout.jar",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "scripts" / "arch-layout.sh",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "scripts" / "package-arch-layout.sh",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "scripts" / "archi-render.sh",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "scripts" / "validate-model.ajs",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "fixtures" / "architecture-ir",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "fixtures" / "rendered-png",
        ]

        for retired_path in retired_paths:
            with self.subTest(retired_path=retired_path.relative_to(REPO_ROOT)):
                self.assertFalse(retired_path.exists() or retired_path.is_symlink())


if __name__ == "__main__":
    unittest.main()
