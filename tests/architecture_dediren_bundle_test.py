import json
import platform
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCH_PLUGIN = REPO_ROOT / "souroldgeezer-architecture"
LINUX_BUNDLE = ARCH_PLUGIN / "tools" / "dediren-linux"
MACOS_BUNDLE = ARCH_PLUGIN / "tools" / "dediren-macos"
EXPECTED_DEDIREN_VERSION = "0.3.0"
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

        self.assertEqual(set(expected_versions.values()), {EXPECTED_DEDIREN_VERSION})

        for plugin_id, expected_version in expected_versions.items():
            manifest = json.loads((bundle / "plugins" / f"{plugin_id}.manifest.json").read_text(encoding="utf-8"))
            with self.subTest(plugin_id=plugin_id):
                self.assertEqual(manifest["id"], plugin_id)
                self.assertEqual(manifest["version"], expected_version)

    def test_skill_fixture_declares_current_bundle_plugins(self) -> None:
        bundle = selected_bundle()
        bundle_manifest = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
        expected_versions = {plugin["id"]: plugin["version"] for plugin in bundle_manifest["plugins"]}
        fixture_model = json.loads((FIXTURE / "model.json").read_text(encoding="utf-8"))

        fixture_versions = {plugin["id"]: plugin["version"] for plugin in fixture_model["required_plugins"]}

        self.assertEqual(fixture_versions, expected_versions)

    def test_bundle_contains_required_plugins_and_schemas(self) -> None:
        bundle = selected_bundle()
        required_paths = [
            "plugins/generic-graph.manifest.json",
            "plugins/elk-layout.manifest.json",
            "plugins/svg-render.manifest.json",
            "plugins/archimate-oef.manifest.json",
            "schemas/model.schema.json",
            "schemas/layout-request.schema.json",
            "schemas/layout-result.schema.json",
            "schemas/svg-render-policy.schema.json",
            "schemas/render-metadata.schema.json",
            "schemas/oef-export-policy.schema.json",
        ]

        for relative_path in required_paths:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((bundle / relative_path).is_file())

    def test_fixture_model_validates(self) -> None:
        result = run_dediren("validate", "--input", FIXTURE / "model.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = envelope(result)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["data"]["model_schema_version"], "model.schema.v1")

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
        self.assertEqual(envelope(project_result)["status"], "ok")

        layout_request = bundle / "fixtures" / "layout-request" / "basic.json"
        layout_result = run_dediren("layout", "--plugin", "elk-layout", "--input", layout_request)
        self.assertEqual(layout_result.returncode, 0, layout_result.stderr)
        self.assertEqual(envelope(layout_result)["status"], "ok")

        layout_result_path = bundle / "fixtures" / "layout-result" / "basic.json"
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
            FIXTURE / view["render"]["metadata"],
            "--input",
            layout_result_path,
        )
        self.assertEqual(render_result.returncode, 0, render_result.stderr)
        svg = envelope(render_result)["data"]["content"]
        self.assertIn("<svg", svg)
        self.assertIn('data-dediren-node-id="client"', svg)
        self.assertIn('data-dediren-edge-id="client-calls-api"', svg)

        export_result = run_dediren(
            "export",
            "--plugin",
            project["export"]["plugin"],
            "--policy",
            FIXTURE / project["export"]["policy"],
            "--source",
            FIXTURE / "model.json",
            "--layout",
            bundle / "fixtures" / "layout-result" / "archimate-oef-basic.json",
        )
        self.assertEqual(export_result.returncode, 0, export_result.stderr)
        self.assertEqual(envelope(export_result)["data"]["artifact_kind"], "archimate-oef+xml")


if __name__ == "__main__":
    unittest.main()
