import json
import platform
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCH_PLUGIN = REPO_ROOT / "souroldgeezer-architecture"
LINUX_BUNDLE = ARCH_PLUGIN / "tools" / "dediren-linux"
MACOS_BUNDLE = ARCH_PLUGIN / "tools" / "dediren-macos"
EXPECTED_DEDIREN_VERSION = "0.14.8"
EXPECTED_BUNDLE_PLUGIN_IDS = {
    "generic-graph",
    "elk-layout",
    "svg-render",
    "archimate-oef",
    "uml-xmi",
}
EXPECTED_ARCHITECTURE_PROJECT_PLUGIN_IDS = {
    "generic-graph",
    "elk-layout",
    "svg-render",
    "archimate-oef",
}
FIXTURE = (
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "fixtures"
    / "dediren"
    / "basic"
)


def selected_bundle() -> Path:
    system = platform.system().lower()
    if system == "linux":
        return LINUX_BUNDLE
    if system == "darwin":
        return MACOS_BUNDLE
    return ARCH_PLUGIN / "tools" / f"dediren-{system}"


def run_dediren(*args: str | Path) -> subprocess.CompletedProcess[str]:
    bundle = selected_bundle()
    return subprocess.run(
        [bundle / "bin" / "dediren", *args],
        cwd=bundle,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def envelope(result: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"stdout was not JSON\n"
            f"returncode={result.returncode}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}"
        ) from exc


class ArchitectureDedirenBundleTest(unittest.TestCase):
    def test_current_platform_bundle_is_present_and_reports_version(self) -> None:
        bundle = selected_bundle()

        self.assertTrue(bundle.exists(), bundle)
        self.assertTrue((bundle / "bundle.json").is_file())
        self.assertTrue((bundle / "bin" / "dediren").is_file())

        result = run_dediren("--version")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("dediren", result.stdout.lower())
        self.assertIn(EXPECTED_DEDIREN_VERSION, result.stdout)

        bundle_manifest = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
        self.assertEqual(bundle_manifest["version"], EXPECTED_DEDIREN_VERSION)

    def test_bundle_plugin_manifests_match_bundle_version(self) -> None:
        bundle = selected_bundle()
        bundle_manifest = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
        expected_versions = {plugin["id"]: plugin["version"] for plugin in bundle_manifest["plugins"]}

        self.assertEqual(set(expected_versions), EXPECTED_BUNDLE_PLUGIN_IDS)
        self.assertEqual(set(expected_versions.values()), {EXPECTED_DEDIREN_VERSION})

        for plugin_id, expected_version in expected_versions.items():
            manifest = json.loads((bundle / "plugins" / f"{plugin_id}.manifest.json").read_text(encoding="utf-8"))
            with self.subTest(plugin_id=plugin_id):
                self.assertEqual(manifest["id"], plugin_id)
                self.assertEqual(manifest["version"], expected_version)

    def test_skill_fixture_declares_current_source_and_project_plugins(self) -> None:
        bundle = selected_bundle()
        bundle_manifest = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
        expected_versions = {plugin["id"]: plugin["version"] for plugin in bundle_manifest["plugins"]}
        fixture_model = json.loads((FIXTURE / "model.json").read_text(encoding="utf-8"))
        fixture_project = json.loads((FIXTURE / "project.json").read_text(encoding="utf-8"))

        fixture_versions = {plugin["id"]: plugin["version"] for plugin in fixture_model["required_plugins"]}
        project_plugin_ids = {
            fixture_project["views"][0]["projection"]["plugin"],
            fixture_project["views"][0]["metadata"]["plugin"],
            fixture_project["views"][0]["layout"]["plugin"],
            fixture_project["views"][0]["render"]["plugin"],
            fixture_project["export"]["plugin"],
        }

        self.assertEqual(fixture_versions, {"generic-graph": EXPECTED_DEDIREN_VERSION})
        self.assertEqual(fixture_model["plugins"]["generic-graph"]["semantic_profile"], "archimate")
        self.assertEqual(project_plugin_ids, EXPECTED_ARCHITECTURE_PROJECT_PLUGIN_IDS)
        self.assertTrue(project_plugin_ids.issubset(set(expected_versions)))

    def test_bundle_contains_required_plugins_and_schemas(self) -> None:
        bundle = selected_bundle()
        required_paths = [
            "plugins/generic-graph.manifest.json",
            "plugins/elk-layout.manifest.json",
            "plugins/svg-render.manifest.json",
            "plugins/archimate-oef.manifest.json",
            "plugins/uml-xmi.manifest.json",
            "schemas/model.schema.json",
            "schemas/layout-request.schema.json",
            "schemas/layout-result.schema.json",
            "schemas/svg-render-policy.schema.json",
            "schemas/render-metadata.schema.json",
            "schemas/oef-export-policy.schema.json",
            "schemas/uml-xmi-export-policy.schema.json",
            "fixtures/export-policy/default-uml-xmi.json",
            "fixtures/source/valid-uml-basic.json",
            "fixtures/source/valid-uml-complex.json",
            "docs/agent-usage.md",
            "LICENSE",
        ]

        for relative_path in required_paths:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((bundle / relative_path).is_file())

    def test_bundle_agent_usage_guide_describes_authoring_loop(self) -> None:
        bundle = selected_bundle()
        guide = (bundle / "docs" / "agent-usage.md").read_text(encoding="utf-8")

        for phrase in [
            "Minimal Source JSON",
            "Artifact Authoring Map",
            "Command Handoff Rules",
            "Repair Map",
            "layout_preferences",
            "DEDIREN_RENDER_METADATA_REQUIRED",
            "UML Profile Authoring",
            "uml-xmi",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guide)

    def test_bundle_includes_dediren_license_notice(self) -> None:
        bundle = selected_bundle()
        license_text = (bundle / "LICENSE").read_text(encoding="utf-8")

        self.assertIn("MIT License", license_text)
        self.assertIn("Dediren contributors", license_text)

    def test_fixture_model_validates(self) -> None:
        result = run_dediren("validate", "--input", FIXTURE / "model.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = envelope(result)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["data"]["model_schema_version"], "model.schema.v1")

    def test_archimate_semantic_validation_rejects_invalid_source_before_projection(self) -> None:
        def validate_model(model: dict) -> subprocess.CompletedProcess[str]:
            with tempfile.TemporaryDirectory() as temp_dir:
                model_path = Path(temp_dir) / "model.json"
                model_path.write_text(json.dumps(model), encoding="utf-8")
                return run_dediren(
                    "validate",
                    "--plugin",
                    "generic-graph",
                    "--profile",
                    "archimate",
                    "--input",
                    model_path,
                )

        base_model = {
            "model_schema_version": "model.schema.v1",
            "required_plugins": [{"id": "generic-graph", "version": EXPECTED_DEDIREN_VERSION}],
            "nodes": [
                {"id": "component", "type": "ApplicationComponent", "label": "Component", "properties": {}},
                {"id": "service", "type": "ApplicationService", "label": "Service", "properties": {}},
            ],
            "relationships": [
                {
                    "id": "component-realizes-service",
                    "type": "Realization",
                    "source": "component",
                    "target": "service",
                    "label": "realizes",
                    "properties": {},
                }
            ],
            "plugins": {
                "generic-graph": {
                    "views": [
                        {
                            "id": "main",
                            "label": "Main",
                            "nodes": ["component", "service"],
                            "relationships": ["component-realizes-service"],
                        }
                    ]
                }
            },
        }

        unsupported_type_model = json.loads(json.dumps(base_model))
        unsupported_type_model["relationships"][0]["type"] = "Bogus"
        unsupported_type = validate_model(unsupported_type_model)
        self.assertEqual(unsupported_type.returncode, 3, unsupported_type.stderr)
        unsupported_type_payload = envelope(unsupported_type)
        self.assertEqual(unsupported_type_payload["status"], "error")
        self.assertEqual(
            unsupported_type_payload["diagnostics"][0]["code"],
            "DEDIREN_ARCHIMATE_RELATIONSHIP_TYPE_UNSUPPORTED",
        )

        invalid_endpoint_model = json.loads(json.dumps(base_model))
        invalid_endpoint_model["relationships"][0]["type"] = "Access"
        invalid_endpoint = validate_model(invalid_endpoint_model)
        self.assertEqual(invalid_endpoint.returncode, 3, invalid_endpoint.stderr)
        invalid_endpoint_payload = envelope(invalid_endpoint)
        self.assertEqual(invalid_endpoint_payload["status"], "error")
        self.assertEqual(
            invalid_endpoint_payload["diagnostics"][0]["code"],
            "DEDIREN_ARCHIMATE_RELATIONSHIP_ENDPOINT_UNSUPPORTED",
        )

        legal_component_interface_realization = json.loads(json.dumps(base_model))
        legal_component_interface_realization["nodes"][1]["id"] = "interface"
        legal_component_interface_realization["nodes"][1]["type"] = "ApplicationInterface"
        legal_component_interface_realization["nodes"][1]["label"] = "Interface"
        legal_component_interface_realization["relationships"][0]["target"] = "interface"
        legal_component_interface_realization["plugins"]["generic-graph"]["views"][0]["nodes"][1] = "interface"
        legal_realization = validate_model(legal_component_interface_realization)
        self.assertEqual(legal_realization.returncode, 0, legal_realization.stderr)
        legal_realization_payload = envelope(legal_realization)
        self.assertEqual(legal_realization_payload["status"], "ok")
        self.assertEqual(
            legal_realization_payload["data"]["semantic_validation_result_schema_version"],
            "semantic-validation-result.schema.v1",
        )

    def test_uml_architecture_context_is_accepted_as_open_metadata(self) -> None:
        bundle = selected_bundle()
        source = json.loads((bundle / "fixtures" / "source" / "valid-uml-basic.json").read_text(encoding="utf-8"))
        source["nodes"][0].setdefault("properties", {}).setdefault("uml", {})["architecture_context"] = {
            "profile": "archimate",
            "element_id": "application-component-billing",
            "relationship": "elaborates",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "model.json"
            model_path.write_text(json.dumps(source), encoding="utf-8")

            schema_result = run_dediren("validate", "--input", model_path)
            semantic_result = run_dediren(
                "validate",
                "--plugin",
                "generic-graph",
                "--profile",
                "uml",
                "--input",
                model_path,
            )

        self.assertEqual(schema_result.returncode, 0, schema_result.stderr)
        self.assertEqual(envelope(schema_result)["status"], "ok")
        self.assertEqual(semantic_result.returncode, 0, semantic_result.stderr)
        semantic_payload = envelope(semantic_result)
        self.assertEqual(semantic_payload["status"], "ok")
        self.assertEqual(semantic_payload["data"]["semantic_profile"], "uml")

    def test_fixture_manifest_drives_dediren_command_smoke(self) -> None:
        bundle = selected_bundle()
        project = json.loads((FIXTURE / "project.json").read_text(encoding="utf-8"))
        view = project["views"][0]

        project_result = run_dediren(
            "project",
            "--target",
            view["projection"]["target"],
            "--plugin",
            view["projection"]["plugin"],
            "--view",
            view["id"],
            "--input",
            FIXTURE / "model.json",
        )
        self.assertEqual(project_result.returncode, 0, project_result.stderr)
        project_payload = envelope(project_result)
        self.assertEqual(project_payload["status"], "ok")

        metadata_result = run_dediren(
            "project",
            "--target",
            view["metadata"]["target"],
            "--plugin",
            view["metadata"]["plugin"],
            "--view",
            view["id"],
            "--input",
            FIXTURE / "model.json",
        )
        self.assertEqual(metadata_result.returncode, 0, metadata_result.stderr)
        metadata_payload = envelope(metadata_result)
        self.assertEqual(metadata_payload["status"], "ok")
        self.assertEqual(
            metadata_payload["data"]["render_metadata_schema_version"],
            "render-metadata.schema.v1",
        )
        self.assertEqual(metadata_payload["data"]["semantic_profile"], "archimate")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            layout_request_path = temp_path / "layout-request.json"
            layout_request_path.write_text(json.dumps(project_payload["data"]), encoding="utf-8")
            render_metadata_path = temp_path / "render-metadata.json"
            render_metadata_path.write_text(json.dumps(metadata_payload["data"]), encoding="utf-8")

            layout_result = run_dediren("layout", "--plugin", "elk-layout", "--input", layout_request_path)
            self.assertEqual(layout_result.returncode, 0, layout_result.stderr)
            layout_payload = envelope(layout_result)
            self.assertEqual(layout_payload["status"], "ok")

            layout_result_path = temp_path / "layout-result.json"
            layout_result_path.write_text(json.dumps(layout_payload["data"]), encoding="utf-8")

            validation_result = run_dediren("validate-layout", "--input", layout_result_path)
            self.assertEqual(validation_result.returncode, 0, validation_result.stderr)
            self.assertEqual(envelope(validation_result)["status"], "ok")

            render_result = run_dediren(
                "render",
                "--plugin",
                view["render"]["plugin"],
                "--policy",
                FIXTURE / view["render"]["policy"],
                "--metadata",
                render_metadata_path,
                "--input",
                layout_result_path,
            )
            self.assertEqual(render_result.returncode, 0, render_result.stderr)
            svg = envelope(render_result)["data"]["content"]
            self.assertIn("<svg", svg)
            self.assertIn('data-dediren-node-id="client"', svg)
            self.assertIn('data-dediren-edge-id="orders-service-serves-client"', svg)

            export_result = run_dediren(
                "export",
                "--plugin",
                project["export"]["plugin"],
                "--policy",
                FIXTURE / project["export"]["policy"],
                "--source",
                FIXTURE / "model.json",
                "--layout",
                layout_result_path,
            )
        self.assertEqual(export_result.returncode, 0, export_result.stderr)
        self.assertEqual(envelope(export_result)["data"]["artifact_kind"], "archimate-oef+xml")


if __name__ == "__main__":
    unittest.main()
