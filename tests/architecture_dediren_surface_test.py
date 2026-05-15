import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCH_PLUGIN = REPO_ROOT / "souroldgeezer-architecture"
EXPECTED_ARCHITECTURE_PLUGIN_VERSION = "1.3.1"
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
    def test_architecture_plugin_version_is_synchronized_everywhere(self) -> None:
        marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        marketplace_entry = next(
            plugin for plugin in marketplace["plugins"] if plugin["name"] == "souroldgeezer-architecture"
        )
        claude_manifest = json.loads((ARCH_PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        codex_manifest = json.loads((ARCH_PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(marketplace_entry["version"], EXPECTED_ARCHITECTURE_PLUGIN_VERSION)
        self.assertEqual(claude_manifest["version"], EXPECTED_ARCHITECTURE_PLUGIN_VERSION)
        self.assertEqual(codex_manifest["version"], EXPECTED_ARCHITECTURE_PLUGIN_VERSION)
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
            "If grouped layout validation still reports connector-through-node, invalid route, or group-boundary warnings",
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
            "Application Component to Application Interface Realization",
            "do not report it as endpoint-illegal",
            "Prefer Composition or Aggregation for component-interface ownership",
            "Use Triggering when the architectural claim is process sequencing",
            "define the view concern, allowed element types, and relationship types",
            "Dediren tool issues",
        ]

        for surface in EA_MODELING_FEEDBACK_SURFACES:
            content = " ".join(surface.read_text(encoding="utf-8").split())
            for phrase in expected_phrases:
                with self.subTest(surface=surface.relative_to(REPO_ROOT), phrase=phrase):
                    self.assertIn(phrase, content)

    def test_application_interface_guidance_allows_realization_but_prefers_ownership(self) -> None:
        surfaces = [
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl",
        ]

        for surface in surfaces:
            content = " ".join(surface.read_text(encoding="utf-8").split())
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                self.assertIn("Application Component to Application Interface Realization", content)
                self.assertIn("do not report it as endpoint-illegal", content)
                self.assertIn(
                    "Prefer Composition or Aggregation for component-interface ownership",
                    content,
                )
                self.assertNotIn("Application Components must not realize Application Interfaces", content)

    def test_basic_fixture_uses_application_interface_service_split(self) -> None:
        fixture_model = json.loads(
            (
                ARCH_PLUGIN
                / "skills"
                / "architecture-design"
                / "references"
                / "fixtures"
                / "dediren"
                / "basic"
                / "model.json"
            ).read_text(encoding="utf-8")
        )
        nodes = {node["id"]: node["type"] for node in fixture_model["nodes"]}
        relationships = {relationship["id"]: relationship for relationship in fixture_model["relationships"]}
        view = fixture_model["plugins"]["generic-graph"]["views"][0]

        self.assertEqual(nodes["orders-api"], "ApplicationInterface")
        self.assertEqual(nodes["orders-service"], "ApplicationService")
        self.assertNotIn("api", nodes)
        self.assertEqual(
            set(view["nodes"]),
            {"client", "orders-component", "orders-api", "orders-service"},
        )
        self.assertEqual(relationships["orders-component-provides-api"]["type"], "Composition")
        self.assertEqual(relationships["orders-component-provides-api"]["source"], "orders-component")
        self.assertEqual(relationships["orders-component-provides-api"]["target"], "orders-api")
        self.assertEqual(relationships["orders-component-realizes-service"]["type"], "Realization")
        self.assertEqual(relationships["orders-component-realizes-service"]["target"], "orders-service")
        self.assertEqual(relationships["orders-service-serves-client"]["type"], "Serving")

    def test_business_layer_guidance_names_representation(self) -> None:
        architecture_reference = (
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Representation", architecture_reference)

    def test_grouping_connectors_viewpoints_and_customization_guidance_is_documented(self) -> None:
        architecture_reference = (
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md"
        ).read_text(encoding="utf-8")
        workflow = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md"
        ).read_text(encoding="utf-8")
        seed_views = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "seed-views.md"
        ).read_text(encoding="utf-8")
        output_format = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md"
        ).read_text(encoding="utf-8")
        behavior_cases = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl"
        ).read_text(encoding="utf-8")

        for content in [architecture_reference, workflow, output_format, behavior_cases]:
            normalized = " ".join(content.split())
            lowered = normalized.lower()
            self.assertIn("layout-only groups are not archimate grouping elements", lowered)
            self.assertIn("semantic-boundary", lowered)
            self.assertIn("semantic_source_id", lowered)
            self.assertIn("relationship connectors and junctions", lowered)
            self.assertIn("unsupported in dediren package source", lowered)

        for content in [architecture_reference, seed_views, behavior_cases]:
            normalized = " ".join(content.split())
            self.assertIn(
                "Seed diagram kinds are starter coverage, not the full ArchiMate viewpoint mechanism",
                normalized,
            )
            self.assertIn("Custom viewpoint path", normalized)

        for content in [architecture_reference, output_format, behavior_cases]:
            normalized = " ".join(content.split())
            self.assertIn("Customization profile", normalized)

        for content in [architecture_reference, behavior_cases]:
            normalized = " ".join(content.split())
            self.assertIn("profile, attribute, and specialization choices", normalized)

    def test_archimate_32_conformance_boundary_and_source_valid_semantics(self) -> None:
        architecture_reference = (
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md"
        ).read_text(encoding="utf-8")
        workflow = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md"
        ).read_text(encoding="utf-8")
        self_check = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "self-check.md"
        ).read_text(encoding="utf-8")
        output_format = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md"
        ).read_text(encoding="utf-8")
        source_grounding = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "source-grounding.md"
        ).read_text(encoding="utf-8")

        self.assertIn("ArchiMate-aware modeling skill", architecture_reference)
        self.assertIn("not a certified or complete conforming ArchiMate tool", architecture_reference)
        self.assertIn(
            "schema validation plus ArchiMate semantic validation",
            architecture_reference,
        )
        self.assertIn("validate --plugin generic-graph --profile archimate", architecture_reference)
        self.assertIn("validate --plugin generic-graph --profile archimate", workflow)
        self.assertIn("validate --plugin generic-graph --profile archimate", self_check)
        self.assertIn("source-valid requires schema plus ArchiMate semantic validation", output_format)
        self.assertIn("The standards review notes are local, ignored working notes", source_grounding)
        self.assertIn("agent-friendly extracted ArchiMate 3.2 reference", source_grounding)

    def test_dediren_0_8_3_runtime_contract_is_documented(self) -> None:
        expected_phrases = [
            "bundled dediren 0.8.3 runtime",
            "ArchiMate® 3.2 relationship endpoint legality",
            "`Node`, not `TechnologyNode`",
            "close parallel route channels",
            "serial",
        ]
        surfaces = [
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "source-grounding.md",
            REPO_ROOT / "CLAUDE.md",
        ]

        combined = " ".join(
            surface.read_text(encoding="utf-8") for surface in surfaces
        )
        combined = " ".join(combined.split())
        for phrase in expected_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_package_generation_guidance_documents_metadata_and_serial_layout(self) -> None:
        expected_phrases = [
            "generated/render-metadata",
            "render-metadata",
            "layout commands serially",
            "hand-authored",
            "reproducible output",
        ]
        surfaces = [
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
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
            / "self-check.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl",
        ]

        combined = " ".join(
            surface.read_text(encoding="utf-8") for surface in surfaces
        )
        combined = " ".join(combined.split())
        for phrase in expected_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_visual_readiness_guidance_flags_dense_valid_renders(self) -> None:
        expected_phrases = [
            "layout-valid is not visually clean",
            "ARCH-L-3",
            "ARCH-R-3",
            "ARCH-Q-2",
            "hub fanout",
            "mixed concerns",
        ]
        surfaces = [
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "professional-readiness.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "smell-catalog.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl",
        ]

        combined = " ".join(
            surface.read_text(encoding="utf-8") for surface in surfaces
        )
        combined = " ".join(combined.split())
        for phrase in expected_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_repo_guidance_uses_plugin_scoped_dediren_bundle_path(self) -> None:
        claude_guidance = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

        self.assertIn("souroldgeezer-architecture/tools/dediren-linux/", claude_guidance)
        self.assertNotRegex(claude_guidance, r"(?m)^tools/dediren-(linux|macos)/")

    def test_dediren_bundle_is_marked_upstream_owned(self) -> None:
        expected_phrases = [
            "imported upstream",
            "Do not patch",
            "issue-filing mechanics",
            "Dediren tool issues",
        ]
        surfaces = [
            REPO_ROOT / "AGENTS.md",
            REPO_ROOT / "CLAUDE.md",
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
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
            / "self-check.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "source-grounding.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl",
        ]

        combined = " ".join(surface.read_text(encoding="utf-8") for surface in surfaces)
        combined = " ".join(combined.split())
        for phrase in expected_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

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
