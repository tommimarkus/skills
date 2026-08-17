# lean-audit:dup-intentional — parallel per-case test bodies kept literal for readability
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, read_jsonl

ARCH_PLUGIN = REPO_ROOT / "souroldgeezer-architecture"
ACTIVE_SURFACES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / ".claude-plugin" / "marketplace.json",
    ARCH_PLUGIN / ".claude-plugin" / "plugin.json",
    ARCH_PLUGIN / "agents" / "architecture-design.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "SKILL.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "notations" / "archimate.md",
    ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "notations" / "uml.md",
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
def compact_file(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class ArchitectureDedirenSurfaceTest(unittest.TestCase):
    def _assert_phrase_in_surfaces(self, surfaces: list, phrase: str) -> None:
        """One phrase, checked (compacted) across a list of surfaces."""
        for surface in surfaces:
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                content = " ".join(surface.read_text(encoding="utf-8").split())
                self.assertIn(phrase, content)

    def _assert_phrases_in_surfaces(self, surfaces: list, phrases: list) -> None:
        """Every phrase in `phrases`, checked (compacted) across every surface in
        `surfaces` — the nested surfaces x phrases coverage shape used below."""
        for surface in surfaces:
            content = " ".join(surface.read_text(encoding="utf-8").split())
            for phrase in phrases:
                with self.subTest(surface=surface.relative_to(REPO_ROOT), phrase=phrase):
                    self.assertIn(phrase, content)

    def _assert_phrases_per_surface(self, expectations: dict) -> None:
        """For each surface -> [phrases] mapping, assert every phrase is present in
        that surface's compacted content. Shared shape for the per-surface phrase
        coverage checks below."""
        for surface, phrases in expectations.items():
            content = compact_file(surface)
            for phrase in phrases:
                with self.subTest(surface=surface.relative_to(REPO_ROOT), phrase=phrase):
                    self.assertIn(phrase, content)

    def test_architecture_plugin_version_is_synchronized_everywhere(self) -> None:
        marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        marketplace_entry = next(
            plugin for plugin in marketplace["plugins"] if plugin["name"] == "souroldgeezer-architecture"
        )
        claude_manifest = json.loads((ARCH_PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))

        # plugin.json#version is the sole version authority (Claude Code always
        # resolves it over a marketplace-entry copy without warning, so a mirrored
        # copy is a silent drift risk); the manifest is the in-test source of truth,
        # the marketplace entry must not carry a competing version key, and the
        # README table cell must agree with the manifest. The value is *not* pinned
        # here — the calendar stamp is assigned at integration on main and owned by
        # scripts/version_stamp.py, so pinning a literal would only add an
        # undocumented sibling-sync cell. This test enforces the cross-surface
        # invariant; well-formedness is checked too.
        canonical = claude_manifest["version"]
        self.assertRegex(canonical, r"^\d{4}\.\d{2}\.\d+$")
        self.assertNotIn("version", marketplace_entry)
        self.assertEqual(marketplace_entry["description"], claude_manifest["description"])
        self.assertIn(
            f"| `souroldgeezer-architecture` | `{canonical}` |",
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
        )

    def test_host_manifests_use_runtime_specific_dediren_mcp_adapters(self) -> None:
        """Each host loads the shared router through its native MCP adapter.

        An inline ``mcpServers`` object is valid Claude packaging but leaves the
        Codex plugin enabled without registering any Dediren tools. Each adapter
        also has to hand the launcher that host's own writable plugin data
        directory, since the runtime refuses to guess one.
        """
        claude_manifest = json.loads(
            (ARCH_PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        claude_dediren = claude_manifest["mcpServers"]["dediren"]
        self.assertEqual(
            claude_dediren["command"],
            "${CLAUDE_PLUGIN_ROOT}/skills/architecture-design/references/scripts/dediren-mcp.sh",
        )
        self.assertEqual(
            claude_dediren["env"], {"DEDIREN_HOME": "${CLAUDE_PLUGIN_DATA}/dediren"}
        )

        codex_manifest = json.loads(
            (ARCH_PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(codex_manifest["mcpServers"], "./mcp/codex.mcp.json")

        mcp_config = json.loads(
            (ARCH_PLUGIN / "mcp" / "codex.mcp.json").read_text(encoding="utf-8")
        )
        dediren = mcp_config["dediren"]
        self.assertEqual(
            dediren["command"],
            "./skills/architecture-design/references/scripts/dediren-mcp.sh",
        )
        self.assertEqual(dediren["args"], [])
        self.assertEqual(dediren["cwd"], ".")
        # The legacy Codex adapter passes MCP fields literally, so it can carry
        # no data-directory substitution at all; that is exactly why the Agent
        # Plugins lane below exists, and why this one keeps its timeout.
        self.assertNotIn("env", dediren)
        self.assertNotIn("codex plugin", json.dumps(dediren))
        self.assertNotIn("${PLUGIN_", json.dumps(dediren))
        self.assertGreaterEqual(dediren["startup_timeout_sec"], 120)

        # Current Codex lane: the Agent Plugins manifest and its mandated
        # sibling mcp.json, the one place ${PLUGIN_DATA} actually interpolates.
        agent_manifest = json.loads((ARCH_PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(
            agent_manifest["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        self.assertEqual(
            agent_manifest["extensions"]["com.openai"]["interface"],
            codex_manifest["interface"],
        )
        agent_config = json.loads((ARCH_PLUGIN / "mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(
            agent_config["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
        )
        agent_dediren = agent_config["mcpServers"]["dediren"]
        self.assertEqual(agent_dediren["type"], "stdio")
        self.assertEqual(
            agent_dediren["command"],
            "./skills/architecture-design/references/scripts/dediren-mcp.sh",
        )
        # Deliberately minimal. Copilot CLI also consumes this file once the root
        # manifest declares the Agent Plugins $schema — verified live, it reports
        # sourcePluginSpec and ignores mcp/copilot.mcp.json — but it does not
        # interpolate ${PLUGIN_ROOT} / ${PLUGIN_DATA} here, so a declared env or
        # cwd would reach one host expanded and the other verbatim. Both hosts
        # instead export PLUGIN_DATA (and Copilot COPILOT_PLUGIN_DATA) into the
        # child as absolute paths, which is what the resolver reads. The format
        # defines no timeout for a stdio server either.
        self.assertEqual(set(agent_dediren), {"type", "command"})

        copilot_manifest = agent_manifest
        self.assertEqual(copilot_manifest["name"], codex_manifest["name"])
        self.assertEqual(copilot_manifest["version"], codex_manifest["version"])
        self.assertEqual(copilot_manifest["description"], codex_manifest["description"])
        self.assertEqual(copilot_manifest["skills"], "./skills/")
        self.assertEqual(copilot_manifest["mcpServers"], "./mcp/copilot.mcp.json")
        copilot_config = json.loads(
            (ARCH_PLUGIN / "mcp" / "copilot.mcp.json").read_text(encoding="utf-8")
        )
        copilot_dediren = copilot_config["dediren"]
        self.assertEqual(
            copilot_dediren["command"],
            "${PLUGIN_ROOT}/skills/architecture-design/references/scripts/dediren-mcp.sh",
        )
        self.assertEqual(copilot_dediren["args"], [])
        self.assertEqual(copilot_dediren["tools"], ["*"])
        self.assertNotIn("cwd", copilot_dediren)
        self.assertEqual(
            copilot_dediren["env"], {"DEDIREN_HOME": "${COPILOT_PLUGIN_DATA}/dediren"}
        )
        self.assertNotIn("codex plugin", json.dumps(copilot_dediren))
        launcher = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "scripts"
            / "dediren-mcp.sh"
        ).read_text(encoding="utf-8")
        # Resolution and provisioning belong to dediren_runtime.py, so the shell
        # launcher carries neither a runtime override nor an install lane of its
        # own; a second copy of either would drift from the tested one.
        self.assertIn("dediren_runtime.py", launcher)
        self.assertIn("--exec-upstream", launcher)
        self.assertNotIn("DEDIREN_COMMAND", launcher)
        self.assertNotIn("--ensure-bundle", launcher)

    def test_codex_mcp_adapter_resolves_the_installed_launcher_without_nested_codex(self) -> None:
        """Codex resolves relative MCP cwd from the installed plugin root.

        Tool calls carry their own absolute ``workspaceRoot``, so the adapter no
        longer needs a nested ``codex plugin list`` process merely to preserve the
        caller's cwd.
        """
        mcp_config = json.loads(
            (ARCH_PLUGIN / "mcp" / "codex.mcp.json").read_text(encoding="utf-8")
        )
        dediren = mcp_config["dediren"]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            plugin_root = temp_path / "installed plugin with spaces"
            launcher = plugin_root / dediren["command"].removeprefix("./")
            launcher.parent.mkdir(parents=True)
            launcher.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$PWD\"\n", encoding="utf-8")
            launcher.chmod(0o755)
            result = subprocess.run(
                [dediren["command"], *dediren["args"]],
                cwd=plugin_root / dediren["cwd"],
                check=False,
                text=True,
                capture_output=True,
                timeout=10,
                env=os.environ,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(plugin_root))

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
        expected_phrase = "model.json` under `plugins.generic-graph.views[].groups`, not `package.json`"
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

        self._assert_phrase_in_surfaces(surfaces, expected_phrase)

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

        self._assert_phrase_in_surfaces(surfaces, expected_phrase)

    def test_grouped_layout_guidance_requires_validation_fallback(self) -> None:
        # The grouped-layout validation fallback prose lives canonically in
        # architecture.md §9. output-format.md and the operational workflow cite
        # that section instead of duplicating the prose (refactor ad4db28).
        canonical = ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md"
        self._assert_phrases_in_surfaces([canonical], [
            "If grouped layout validation still reports connector-through-node, invalid route, or group-boundary warnings",
            "rerun the same view without groups",
            "use the cleaner layout as evidence and report the grouped-layout regression",
        ])

        self._assert_phrases_in_surfaces(
            [
                ARCH_PLUGIN
                / "skills"
                / "architecture-design"
                / "references"
                / "procedures"
                / "architecture-operational-workflow.md",
                ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
            ],
            ["architecture.md` §9", "grouped-layout fallback", "report the regression"],
        )

    def test_lead_ea_modeling_feedback_is_documented(self) -> None:
        # The lead-EA modeling feedback lives canonically in architecture.md §5 and
        # is exercised by the behavioral evals. output-format.md cites §5 rather
        # than duplicating the prose (refactor ad4db28).
        canonical_surfaces = [
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl",
        ]
        canonical_phrases = [
            "APIs and GUIs are Application Interfaces",
            "Application Services model the functionality exposed through an interface",
            "Application Component to Application Interface Realization",
            "do not report it as endpoint-illegal",
            "Prefer Composition or Aggregation for component-interface ownership",
            "Use Triggering when the architectural claim is process sequencing",
            "define the view concern, allowed element types, and relationship types",
            "Dediren tool issues",
        ]
        self._assert_phrases_in_surfaces(canonical_surfaces, canonical_phrases)

        output_format = " ".join(
            (ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md")
            .read_text(encoding="utf-8")
            .split()
        )
        for phrase in [
            "architecture.md` §5",
            "interface/service semantics",
            "component-interface ownership",
            "Triggering for process sequencing",
            "define the view concern, allowed element types, and relationship types",
        ]:
            with self.subTest(surface="output-format.md", phrase=phrase):
                self.assertIn(phrase, output_format)

    def test_application_interface_guidance_allows_realization_but_prefers_ownership(self) -> None:
        # The realization-vs-ownership guidance lives canonically in
        # architecture.md §5 and the behavioral evals; the operational workflow
        # and output-format cite §5 component-interface ownership rather than
        # restating it (refactor ad4db28). The forbidden phrasing is barred
        # everywhere.
        canonical_surfaces = [
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl",
        ]
        for surface in canonical_surfaces:
            content = " ".join(surface.read_text(encoding="utf-8").split())
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                self.assertIn("Application Component to Application Interface Realization", content)
                self.assertIn("do not report it as endpoint-illegal", content)
                self.assertIn(
                    "Prefer Composition or Aggregation for component-interface ownership",
                    content,
                )
                self.assertNotIn("Application Components must not realize Application Interfaces", content)

        citing_surfaces = [
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md",
        ]
        for surface in citing_surfaces:
            content = " ".join(surface.read_text(encoding="utf-8").split())
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                self.assertIn("architecture.md` §5", content)
                self.assertIn("component-interface ownership", content)
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
            "schema plus semantic-profile validation",
            architecture_reference,
        )
        self.assertIn(
            'dediren_validate {workspaceRoot, source, profile: "archimate"}',
            architecture_reference,
        )
        # self-check.md drives semantic validation through the MCP tool with a profile.
        self.assertIn("dediren_validate", self_check)
        self.assertIn('profile: "archimate"', self_check)
        # output-format.md cites architecture.md §9 for the source-valid tools
        # rather than restating them.
        self.assertIn("`source-valid` validation", output_format)
        self.assertIn("`architecture.md` §9", output_format)
        self.assertIn("The standards review notes are local, ignored working notes", source_grounding)
        self.assertIn("agent-friendly extracted ArchiMate 3.2 reference", source_grounding)

    def test_dediren_external_runtime_contract_is_documented(self) -> None:
        expectations = {
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md": [
                "tested Dediren runtime enforces ArchiMate® 3.2 relationship endpoint",
                "`Node`, not `TechnologyNode`",
                "close parallel route channels during layout validation",
                "`dediren_build` call walks its views through projection",
            ],
            # The operational workflow and output-format cite architecture.md §9
            # for endpoint/Node/route semantics instead of restating them.
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md": [
                "pinned checksum-verified install",
                "plugins.generic-graph.semantic_profile",
                "architecture.md` §9",
                "endpoint legality",
                "`Node` naming",
                "in-build layout",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md": [
                "which Dediren lane ran",
                "Runtime semantics",
                "are defined in `architecture.md` §9",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "source-grounding.md": [
                "tested Dediren runtime enforces ArchiMate® 3.2 relationship endpoint legality",
                "`Node`, not `TechnologyNode`",
                "reports close parallel route channels",
                "plugins.generic-graph.semantic_profile",
                "runs projection, layout, layout validation, and rendering inside each `dediren_build` call",
            ],
            # Compatibility evidence is independent from runtime selection.
            REPO_ROOT / "docs" / "maintenance-procedures.md": [
                "version in repo fixtures is a compatibility evidence baseline",
            ],
        }

        self._assert_phrases_per_surface(expectations)

    def test_dediren_host_adapter_and_generic_local_client_contract_is_documented(self) -> None:
        """The shared router stays harness-neutral while host configuration differs."""
        expectations = {
            REPO_ROOT / "AGENTS.md": [
                "shared launcher/router has no harness detection",
                "Generic local-client compatibility",
                "absolute `workspaceRoot` on every tool call",
                "Streamable HTTP is future work only",
                "authentication, origin validation, port and service lifecycle, session isolation, and workspace authorization",
                "Preserve the legacy verified-release-cache fallback",
            ],
            REPO_ROOT / "CLAUDE.md": [
                "shared launcher/router has no harness detection",
                "Generic local-client compatibility",
                "absolute `workspaceRoot`",
                "Streamable HTTP is future work only",
                "`startup_timeout_sec` is seconds",
                "`timeout` is milliseconds",
            ],
            REPO_ROOT / "README.md": [
                "shared launcher/router has no harness detection",
                "Generic local-client compatibility",
                "absolute `workspaceRoot` per tool call",
                "Streamable HTTP is future work only",
                "`startup_timeout_sec`: seconds",
                "`timeout`: milliseconds",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "SKILL.md": [
                "shared launcher/router has no harness detection",
                "Generic local-client compatibility",
                "absolute `workspaceRoot` per tool call",
                "Streamable HTTP is future work only",
                "legacy verified-release-cache fallback",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "procedures" / "self-check.md": [
                "shared launcher/router has no harness detection",
                "Generic local-client compatibility",
                "absolute `workspaceRoot` per tool call",
                "Streamable HTTP is future work only",
                "Codex `startup_timeout_sec` are seconds",
                "Copilot `timeout` is milliseconds",
                "legacy verified-release-cache fallback",
            ],
        }

        self._assert_phrases_per_surface(expectations)

    def test_guidance_avoids_hard_coded_dediren_version_numbers(self) -> None:
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
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "source-grounding.md",
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl",
            REPO_ROOT / "CLAUDE.md",
        ]

        for surface in surfaces:
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                content = surface.read_text(encoding="utf-8")
                for version in ["0.10.0", "0.11.1", "0.11.2"]:
                    self.assertNotIn(version, content)

    def test_self_check_documents_mcp_tool_calls(self) -> None:
        self_check = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "self-check.md"
        ).read_text(encoding="utf-8")
        expected_phrases = [
            'dediren_validate {workspaceRoot: "/abs/project", source: "<pkg>/model.json", profile: "archimate"}',
            "dediren_build",
            'dediren_guide {workspaceRoot: "/abs/project", topic: "source-json"}',
            # The native package lane: one call, artifacts at their declared paths.
            "package",
            "package-build-result",
            '"$DEDIREN" build --package <pkg>/package.json',
        ]

        for phrase in expected_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self_check)
        # The consumer-side orchestration is retired with the package lane: no staging
        # dir, no plan/map remap, no per-view export fan-out, and no bundled build
        # helper. The CLI fallback drives the selected host executable directly.
        for absent in [
            "layout --plugin elk-layout",
            "project --target layout-request",
            "dediren-build.py",
            ".dediren-build",
        ]:
            with self.subTest(absent=absent):
                self.assertNotIn(absent, self_check)

    def test_guidance_points_to_dediren_guide_tool(self) -> None:
        self_check = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "self-check.md"
        ).read_text(encoding="utf-8")
        architecture_reference = (
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md"
        ).read_text(encoding="utf-8")

        for content in [self_check, architecture_reference]:
            with self.subTest():
                normalized = " ".join(content.split())
                self.assertIn("dediren_guide", content)
                self.assertIn("Minimal Source JSON", normalized)
                self.assertIn("Command Handoff", normalized)
                self.assertIn("Repair Rules", normalized)

    def test_multi_notation_scope_includes_archimate_and_uml(self) -> None:
        expectations = {
            # CLAUDE.md carries multi-notation scope at orientation level only;
            # profile commands and uml-xmi depth live in the skill surfaces below.
            REPO_ROOT / "CLAUDE.md": [
                "ArchiMate® 3.2 + UML®",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "SKILL.md": [
                "ArchiMate® and UML® dediren packages",
                "cross-notation handoff links",
                "references/notations/uml.md",
            ],
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md": [
                "ArchiMate and UML are supported profiles",
                "uml-xmi",
                "Cross-notation links",
            ],
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "self-check.md": [
                'profile: "uml"',
                "uml-xmi",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "source-grounding.md": [
                "ArchiMate and UML are supported `generic-graph` semantic profiles",
                'dediren_validate {workspaceRoot, profile: "uml"}',
                "uml-xmi",
                "uml-sequence",
            ],
            # output-format.md surfaces notation in its footer; profile commands
            # live in self-check.md, not here.
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md": [
                "Notation: archimate | uml | mixed",
                "Cross-notation links",
            ],
        }

        self._assert_phrases_per_surface(expectations)

    def test_notation_references_define_archimate_uml_boundary(self) -> None:
        archimate_ref = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "notations" / "archimate.md"
        ).read_text(encoding="utf-8")
        uml_ref = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "notations" / "uml.md"
        ).read_text(encoding="utf-8")

        archimate_phrases = [
            "ArchiMate frames the architectural concern",
            'dediren_validate {workspaceRoot, profile: "archimate"}',
            "archimate-oef",
            "relationship connectors and junctions unsupported",
        ]
        uml_phrases = [
            "UML elaborates one bounded part",
            'dediren_validate {workspaceRoot, profile: "uml"}',
            'kind: "uml-sequence"',
            "uml-xmi",
            "properties.uml.architecture_context",
            "relationship: elaborates",
            "Do not infer cross-notation links from matching labels alone",
        ]

        for phrase in archimate_phrases:
            with self.subTest(reference="archimate", phrase=phrase):
                self.assertIn(phrase, archimate_ref)
        for phrase in uml_phrases:
            with self.subTest(reference="uml", phrase=phrase):
                self.assertIn(phrase, uml_ref)

    def test_uml_sequence_guidance_is_adopted(self) -> None:
        # The full UML kind enumeration lives in the skill surfaces below; lean
        # CLAUDE.md keeps only orientation-level "ArchiMate® 3.2 + UML®" scope
        # (asserted in test_multi_notation_scope_includes_archimate_and_uml).
        expectations = {
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "notations" / "uml" / "sequence.md": [
                'kind: "uml-sequence"',
                "Interaction",
                "Lifeline",
                "Message",
                "properties.uml.sequence",
                "message_sort",
                "valid-uml-sequence-basic.json",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "source-grounding.md": [
                "uml-sequence",
                "Interaction",
                "Lifeline",
                "Message",
                "properties.uml.sequence",
                "message_sort",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl": [
                "architecture-design-behavior-uml-sequence-view",
                "properties.uml.sequence",
                "message_sort",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "trigger-cases.jsonl": [
                "architecture-design-trigger-yes-uml-sequence",
                "uml-sequence",
            ],
        }

        self._assert_phrases_per_surface(expectations)

    def test_output_contract_reports_notation_and_cross_notation_links(self) -> None:
        output_format = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md"
        ).read_text(encoding="utf-8")

        expected_phrases = [
            "Notation: archimate | uml | mixed | unsupported",
            "Cross-notation links: none | UML elaborates ArchiMate",
            "Export readiness: not requested | OEF ready (<coverage>) | XMI ready (<coverage>; view/count; omissions; represented content; XMI envelope only | UML-content schema | importer validated) | blocked",
            "Handoff boundary: architecture/design model | companion material required | delegated to <skill>",
        ]

        for phrase in expected_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, output_format)

    def test_uml_handoff_eval_cases_exist(self) -> None:
        behavior_cases = read_jsonl(
            "souroldgeezer-architecture/skills/architecture-design/references/evals/behavior-cases.jsonl"
        )
        trigger_cases = read_jsonl(
            "souroldgeezer-architecture/skills/architecture-design/references/evals/trigger-cases.jsonl"
        )
        behavior_ids = {case["id"]: case for case in behavior_cases}
        trigger_ids = {case["id"]: case for case in trigger_cases}

        self.assertIn("architecture-design-behavior-uml-archimate-handoff-links", behavior_ids)
        self.assertIn("architecture-design-trigger-yes-uml-handoff", trigger_ids)
        behavior = behavior_ids["architecture-design-behavior-uml-archimate-handoff-links"]
        self.assertIn("Cross-notation links field", behavior["expected_artifacts"])
        self.assertIn(
            "verify referenced ArchiMate ids exist in the package's ArchiMate model "
            "(the archimate entry in package.json models[]) before claiming cross-notation readiness",
            behavior["required_checks"],
        )
        self.assertIn(
            "do not infer cross-notation links from matching labels alone",
            behavior["required_checks"],
        )
        self.assertTrue(trigger_ids["architecture-design-trigger-yes-uml-handoff"]["expected_activation"])

    def test_package_generation_guidance_documents_metadata_and_layout_concurrency(self) -> None:
        expectations = {
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md": [
                "generated/render-metadata",
                "render-metadata",
                "Layout runs inside each `dediren_build` call",
                "hand-authored",
                "reproducible output",
                "plugins.generic-graph.semantic_profile",
                "semantic_profile",
                "archimate-oef",
                "OEF export is requested",
            ],
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md": [
                "generated/render-metadata",
                "render-metadata",
                "run inside one `dediren_build` call",
                "reproducible output",
                "plugins.generic-graph.semantic_profile",
                "archimate-oef",
                "requested ArchiMate OEF export",
            ],
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "self-check.md": [
                "render-metadata",
                "plugins.generic-graph.semantic_profile",
                "archimate-oef",
                "OEF export is requested",
            ],
            # output-format.md cites architecture.md §9 for layout concurrency
            # rather than restating the per-view/serial-rerun detail (ad4db28).
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md": [
                "`package.json` declares bindings and paths",
                "runtime owns projection, layout, rendering, and export execution",
                "`architecture.md` §9",
                "reproducible output",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl": [
                "generated/render-metadata",
                "render-metadata",
                "bundled dediren MCP server",
                "dediren_build",
                "hand-authored",
                "reproducible output",
                "plugins.generic-graph.semantic_profile",
                "semantic_profile",
                "archimate-oef",
            ],
        }

        self._assert_phrases_per_surface(expectations)

    def test_visual_readiness_guidance_flags_dense_valid_renders(self) -> None:
        expectations = {
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md": [
                "ARCH-L-3",
                "ARCH-R-3",
                "ARCH-Q-2",
                "hub fanout",
                "mixed audience concerns",
            ],
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "professional-readiness.md": [
                "ARCH-L-3",
                "ARCH-R-3",
                "ARCH-Q-2",
                "dense",
                "hub-heavy",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "smell-catalog.md": [
                "ARCH-L-3",
                "ARCH-R-3",
                "ARCH-Q-2",
                "hub fanout",
                "mixed concerns",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md": [
                "layout-valid is not visually clean",
                "ARCH-L-3",
                "ARCH-R-3",
                "ARCH-Q-2",
                "hub fanout",
                "mixed concerns",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl": [
                "layout-valid versus visually clean distinction",
                "ARCH-L-3",
                "ARCH-R-3",
                "ARCH-Q-2",
                "hub fanout",
                "mixed concerns",
            ],
        }

        self._assert_phrases_per_surface(expectations)

    def test_implementation_readiness_reference_is_routed(self) -> None:
        procedure = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "implementation-readiness-review.md"
        )
        skill = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "SKILL.md"
        ).read_text(encoding="utf-8")
        workflow = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md"
        ).read_text(encoding="utf-8")
        architecture_reference = (
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md"
        ).read_text(encoding="utf-8")

        self.assertTrue(procedure.exists())
        procedure_content = " ".join(procedure.read_text(encoding="utf-8").split())

        for surface in [skill, workflow, architecture_reference]:
            with self.subTest(surface=surface[:40]):
                self.assertIn("implementation-readiness review", surface)

        expected_phrases = [
            "implementation-readiness verdict",
            "architecture-documentation findings",
            "other source material",
            "ArchiMate equivalence",
            "Implementation impact",
            "candidate-from-source",
            "runtime/package readiness claims are separate from implementation-handoff completeness claims",
        ]
        for phrase in expected_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, procedure_content)

    def test_implementation_readiness_output_contract_and_codes_are_documented(self) -> None:
        output_format = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md"
        ).read_text(encoding="utf-8")
        smell_catalog = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "smell-catalog.md"
        ).read_text(encoding="utf-8")

        output_phrases = [
            "implementation-readiness verdict",
            "architecture-documentation findings",
            "other source material findings",
            "skill/package issue classification",
            "ArchiMate equivalence",
            "Implementation impact",
            "do not duplicate API, UI, auth, IaC, test, or code internals",
        ]
        for phrase in output_phrases:
            with self.subTest(surface="output-format", phrase=phrase):
                self.assertIn(phrase, output_format)

        code_phrases = [
            "`ARCH-Q-3`: implementation-readiness claim exceeds evidence",
            "`ARCH-X-2`: required architecture evidence is absent",
            "`ARCH-V-4`: supported implementation-handoff diagram kind is absent",
            "`ARCH-M-4`: architect-owned content is presented as extracted fact",
        ]
        for phrase in code_phrases:
            with self.subTest(surface="smell-catalog", phrase=phrase):
                self.assertIn(phrase, smell_catalog)

    def test_implementation_readiness_eval_and_source_grounding_exist(self) -> None:
        behavior_cases_path = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "evals"
            / "behavior-cases.jsonl"
        )
        trigger_cases_path = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "evals"
            / "trigger-cases.jsonl"
        )
        behavior_cases = [
            json.loads(line)
            for line in behavior_cases_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        trigger_cases = [
            json.loads(line)
            for line in trigger_cases_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        behavior_ids = {case["id"]: case for case in behavior_cases}
        trigger_ids = {case["id"]: case for case in trigger_cases}
        self.assertIn(
            "architecture-design-behavior-implementation-readiness-review",
            behavior_ids,
        )
        self.assertIn(
            "architecture-design-trigger-yes-implementation-readiness",
            trigger_ids,
        )
        self.assertIn("architecture-design-trigger-no-api-wire-contracts", trigger_ids)
        behavior_case = behavior_ids[
            "architecture-design-behavior-implementation-readiness-review"
        ]

        self.assertIn("implementation handoff", behavior_case["prompt"])
        self.assertIn("implementation-readiness verdict", behavior_case["expected_artifacts"])
        self.assertIn("architecture-documentation findings", behavior_case["expected_artifacts"])
        self.assertIn("other source material findings", behavior_case["expected_artifacts"])
        self.assertIn(
            "include ArchiMate equivalence for every architecture-documentation finding",
            behavior_case["required_checks"],
        )
        self.assertIn(
            "route API wire contracts UI behavior auth mechanics IaC parameters tests and code internals to owning source material",
            behavior_case["required_checks"],
        )
        self.assertIn(
            "treat architecture docs as a complete implementation specification",
            behavior_case["forbidden_behaviors"],
        )
        self.assertFalse(behavior_case["contains_third_party_text"])

        self.assertTrue(
            trigger_ids["architecture-design-trigger-yes-implementation-readiness"]["expected_activation"]
        )
        self.assertFalse(
            trigger_ids["architecture-design-trigger-no-api-wire-contracts"]["expected_activation"]
        )

        source_grounding = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "source-grounding.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "implementation-readiness review notes are local, ignored working notes",
            source_grounding,
        )
        self.assertIn("synthetic implementation-readiness eval", source_grounding)

    def test_source_weighting_reference_has_operational_extraction_contract(self) -> None:
        source_weighting = (
            ARCH_PLUGIN / "docs" / "architecture-reference" / "source-weighting.md"
        ).read_text(encoding="utf-8")
        required_phrases = [
            "## Use During Extract",
            "## Source-To-ArchiMate Selection Matrix",
            "## Relationship Selection Ladder",
            "## View Recipes",
            "## Evidence Labels",
            "## Anti-Patterns",
            "Application Interface",
            "Application Service",
            "Application Component",
            "Business Process candidate",
            "No Business Capability/Goal/Product by default",
            "Association is a disclosed fallback",
            "overlay-only",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source_weighting)

    def test_extract_mode_loads_source_weighting_by_default_for_mapping(self) -> None:
        skill = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "SKILL.md"
        ).read_text(encoding="utf-8")
        expected = (
            "In Extract mode, load "
            "[`references/source-weighting.md`](references/source-weighting.md) "
            "before selecting ArchiMate element, relationship, or view types "
            "unless the task is a purely mechanical update to an existing "
            "package."
        )

        self.assertIn(expected, " ".join(skill.split()))

    def test_skill_local_source_weighting_pointer_has_decision_loop(self) -> None:
        pointer = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "source-weighting.md"
        ).read_text(encoding="utf-8")
        required_phrases = [
            "Identify the source fact",
            "List plausible ArchiMate candidates",
            "Pick the heaviest applicable evidence lane",
            "Reject semantically invalid candidates",
            "Select the narrowest useful relationship and view",
            "Label confidence",
            "Record the rejected alternative",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, pointer)

    def test_lifting_rules_have_source_family_mapping_examples(self) -> None:
        checks = {
            "lifting-rules-dotnet.md": [
                "`*.sln` is repository/package context",
                "Deployable `*.csproj`",
                "route or GUI surface",
                "handler/orchestrator behavior",
                "Business Process candidates only when outcome and participant context are clear",
                "ASP.NET Core evidence is additive",
                "Azure Functions evidence is additive",
                "Blazor evidence is additive",
                "EF Core evidence is additive",
                "Worker and hosted service evidence is additive",
            ],
            "lifting-rules-java.md": [
                "Generic Java first",
                "Multi-module Maven or Gradle build",
                "Deployable JAR, WAR, service, CLI, or worker",
                "Spring-specific evidence is additive",
                "Spring Boot auto-configuration",
                "Actuator endpoints",
                "Quarkus-specific evidence is additive",
                "Quarkus extensions and build steps",
                "Dev Services",
            ],
            "lifting-rules-bicep.md": [
                "Azure resource type decides platform/technology context",
                "App settings, connection strings, identities, RBAC, and diagnostics",
                "Resource groups/modules/environments",
                "Tags, parameter names, and SKU names do not create Motivation, Capability, or lifecycle claims",
            ],
            "lifting-rules-gha.md": [
                "Workflow files are Work Package candidates only when delivery architecture is in scope",
                "Jobs can be implementation steps",
                "Artifacts and deployment packages can be Deliverables",
                "Routine CI stays out",
            ],
            "lifting-rules-process.md": [
                "UI/API sequence can be Application Process by default",
                "Business Process stays candidate",
                "Timers, callbacks, messages, and deploy/release occurrences are events",
                "A small linear process should remain ungrouped",
            ],
        }

        procedures = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "procedures"
        )
        for filename, phrases in checks.items():
            content = (procedures / filename).read_text(encoding="utf-8")
            for phrase in phrases:
                with self.subTest(file=filename, phrase=phrase):
                    self.assertIn(phrase, content)

    def test_view_output_drift_and_runtime_guidance_have_decision_rules(self) -> None:
        procedures = (
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "procedures"
        )
        checks = {
            procedures / "seed-views.md": [
                "Typical elements",
                "Typical relationships",
                "Split trigger",
            ],
            procedures / "process-view-emission.md": [
                "Keep Application Process",
                "Emit Business Process Cooperation",
                "Consolidate duplicate process drill-downs",
            ],
            procedures / "professional-readiness.md": [
                "Valid But Not Useful",
                "layout-valid evidence can still fail the audience",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md": [
                "Source-weighted choices",
                "Notable choices",
                "low-confidence",
                "architect-owned",
            ],
            procedures / "drift-detection.md": [
                "source added or removed",
                "source evidence changed",
                "package claim no longer has evidence",
                "package claim may be architect intent",
            ],
            procedures / "implementation-readiness-review.md": [
                "Architecture-owned evidence",
                "Companion material",
            ],
            procedures / "self-check.md": [
                "Reading tool results",
                "dediren_build",
                "dediren_validate",
            ],
            procedures / "architecture-operational-workflow.md": [
                "The MCP tool call flow lives in `self-check.md`",
            ],
        }

        for path, phrases in checks.items():
            content = path.read_text(encoding="utf-8")
            for phrase in phrases:
                with self.subTest(path=path.relative_to(REPO_ROOT), phrase=phrase):
                    self.assertIn(phrase, content)

    def test_source_weighted_behavior_eval_cases_exist(self) -> None:
        behavior_path = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "evals"
            / "behavior-cases.jsonl"
        )
        cases = [
            json.loads(line)
            for line in behavior_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        ids = {case["id"] for case in cases}
        expected_ids = {
            "architecture-design-behavior-source-weighted-api-service-interface",
            "architecture-design-behavior-source-weighted-cloud-overlay",
            "architecture-design-behavior-source-weighted-business-terms",
            "architecture-design-behavior-source-weighted-relationship-ladder",
            "architecture-design-behavior-source-weighted-view-split",
            "architecture-design-behavior-dotnet-lifting-specificity",
            "architecture-design-behavior-dotnet-framework-evidence-specificity",
            "architecture-design-behavior-java-lifting-specificity",
            "architecture-design-behavior-java-framework-evidence-specificity",
            "architecture-design-behavior-bicep-trust-access-path",
            "architecture-design-behavior-gha-delivery-architecture",
            "architecture-design-behavior-drift-architect-owned-intent",
            "architecture-design-behavior-readiness-companion-material",
        }

        self.assertTrue(expected_ids.issubset(ids), expected_ids - ids)

    def test_source_grounding_mentions_refreshed_weighting_without_local_paths(self) -> None:
        source_grounding = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "source-grounding.md"
        ).read_text(encoding="utf-8")
        required_phrases = [
            "standards/method sources for semantic and viewpoint defaults",
            "practitioner sources for app-layer and relationship defaults",
            "enterprise-practice sources for business-claim evidence gates",
            "portfolio/cloud sources for overlay-only guidance",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, source_grounding)

        self.assertNotIn("/home/souroldgeezer/Documents", source_grounding)
        self.assertNotIn("~/Documents", source_grounding)

    def test_repo_guidance_documents_plugin_runtime_provisioning(self) -> None:
        """Adopting a Dediren release is a plugin release procedure now.

        The plugin provisions its own pinned runtime, so the maintenance guidance
        has to carry the pin, the floor, the resolution order that decides when
        provisioning even runs, and the air-gapped opt-out. What stays true is
        that the runtime is upstream-owned: no vendored tree, and no revival of
        the deleted downloader by name.
        """
        maintenance_guidance = (
            REPO_ROOT / "docs" / "maintenance-procedures.md"
        ).read_text(encoding="utf-8")

        self.assertIn("pinned, checksum-verified", maintenance_guidance)
        self.assertIn("DEDIREN_VERSION_DEFAULT", maintenance_guidance)
        self.assertIn("DEDIREN_VERSION_FLOOR", maintenance_guidance)
        self.assertIn("DEDIREN_AUTO_INSTALL=0", maintenance_guidance)
        self.assertIn("Java is\nnever downloaded", maintenance_guidance)
        # Java stays a host prerequisite, and the runtime is still not ours to
        # modify or vendor.
        self.assertNotIn("dediren-release.sh", maintenance_guidance)
        self.assertNotRegex(maintenance_guidance, r"(?m)^tools/dediren-(linux|macos)/")

    def test_dediren_operator_guidance_matches_the_adopted_schema_fetcher(self) -> None:
        install_guidance = (
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "dediren-install.md"
        ).read_text(encoding="utf-8")
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        for surface in (install_guidance, readme):
            with self.subTest():
                normalized = " ".join(surface.split())
                self.assertIn("Java HTTP client", normalized)
                self.assertIn("ALL_PROXY", normalized)
        normalized_install = " ".join(install_guidance.split())
        self.assertIn("`curl` or `wget`", normalized_install)
        self.assertIn("release downloads", normalized_install)

    def test_current_dediren_pin_is_synchronized_across_runtime_guidance(self) -> None:
        pin = "2026.08.5"
        expectations = {
            REPO_ROOT / "AGENTS.md": f"pin `{pin}`",
            REPO_ROOT / "CLAUDE.md": f"pin `{pin}`",
            REPO_ROOT / "README.md": f"(`{pin}`, support floor",
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md": f"(`{pin}`)",
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "self-check.md": f"`{pin}` release",
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "dediren-install.md": f"pinned release **{pin}**",
        }

        for surface, phrase in expectations.items():
            with self.subTest(surface=surface.relative_to(REPO_ROOT)):
                self.assertIn(phrase, surface.read_text(encoding="utf-8"))

    def test_dediren_host_runtime_is_marked_upstream_owned(self) -> None:
        expectations = {
            # The don't-patch rule lives in the Dediren upstream compatibility
            # procedure, which relocated from CLAUDE.md to
            # docs/maintenance-procedures.md.
            REPO_ROOT / "docs" / "maintenance-procedures.md": [
                "Never patch a host installation from this repo",
                "report Dediren defects upstream",
            ],
            ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md": [
                "upstream distribution artifact",
                "Do not patch",
                "Dediren tool issues",
            ],
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "architecture-operational-workflow.md": [
                "imported upstream evidence",
                "do not patch the host installation",
                "Dediren tool issues",
            ],
            ARCH_PLUGIN
            / "skills"
            / "architecture-design"
            / "references"
            / "procedures"
            / "self-check.md": [
                # The runtime is upstream-owned whichever lane produced it, so
                # the don't-touch rule survives the plugin gaining an installer:
                # provisioning a pinned release is not licence to modify one.
                "upstream runtime, whether the launcher",
                "Do not patch, hand-download, or downgrade",
                "Dediren tool issues",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md": [
                "Dediren tool issues",
            ],
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "evals" / "behavior-cases.jsonl": [
                "upstream Dediren issue reference",
                "do not edit cached schemas manifests binaries Java helpers fixtures or bundle.json",
                "Dediren tool issues footer",
            ],
        }

        self._assert_phrases_per_surface(expectations)

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

    def test_standards_guidance_preserves_evidence_and_notation_boundaries(self) -> None:
        """Public guidance must not turn envelope-only XMI into UML conformance."""
        architecture = compact_file(ARCH_PLUGIN / "docs" / "architecture-reference" / "architecture.md")
        output = compact_file(ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "output-format.md")
        source_grounding = compact_file(
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "source-grounding.md"
        )
        uml_hub = compact_file(
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "notations" / "uml.md"
        )
        data = compact_file(
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "notations" / "uml" / "data.md"
        )
        deployment = compact_file(
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "notations" / "uml" / "deployment.md"
        )
        self_check = compact_file(
            ARCH_PLUGIN / "skills" / "architecture-design" / "references" / "procedures" / "self-check.md"
        )

        self.assertIn("Quality level: not assessed", output)
        self.assertIn("schema plus semantic-profile validation", architecture)
        self.assertIn("XMI envelope only", output)
        self.assertIn("UML-content schema", output)
        self.assertIn("importer validated", output)
        self.assertIn("view/count", output)
        self.assertIn("omissions", output)
        self.assertIn("represented content", output)
        self.assertIn("Dediren issue #71", source_grounding)
        self.assertIn("export-result.schema.v2", source_grounding)
        self.assertIn(".data.assurance", source_grounding)
        self.assertIn("kind_taxonomy", source_grounding)
        self.assertIn("validation_evidence", source_grounding)
        self.assertIn("independently verifies", source_grounding)
        self.assertIn("package-build-result does not surface assurance", source_grounding)
        self.assertIn("active structure -> behavior", architecture)
        self.assertNotIn("or vice versa", architecture)
        self.assertIn(
            "Physical active/passive structure extends the Technology layer", architecture
        )
        self.assertIn(
            "Motivation spans the layers as a cross-cutting aspect", architecture
        )
        self.assertIn("Motivation is not a layer", architecture)
        self.assertNotIn("Motivation is not an ArchiMate layer or aspect", architecture)
        self.assertIn("stakeholders, concerns, purpose, scope/abstraction", architecture)
        self.assertIn("allowed elements/relationships, conventions, audience, quality target", architecture)
        self.assertIn("`Device` is physical", deployment)
        self.assertIn("`ExecutionEnvironment` is software/runtime", deployment)
        self.assertIn("`Node` is a generic computational resource", deployment)
        self.assertIn("Dediren-local classifier-structure view", data)
        self.assertIn("not a UML Annex A diagram kind", uml_hub)
        self.assertIn("root `mcp.json` deliberately declares no `env` or `cwd`", self_check)
        self.assertIn("legacy Copilot lane explicitly sets `DEDIREN_HOME`", self_check)
        self.assertIn("package.json declares bindings and paths", architecture)
        self.assertIn("runtime owns projection, layout, rendering, and export execution", architecture)

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
