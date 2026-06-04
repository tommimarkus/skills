import json
import os
import platform
import subprocess
import tempfile
import unittest
from functools import lru_cache
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCH_PLUGIN = REPO_ROOT / "souroldgeezer-architecture"
RELEASE_SCRIPT = (
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "scripts"
    / "dediren-release.sh"
)
FIXTURE = (
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "fixtures"
    / "dediren"
    / "basic"
)
EXPECTED_DEDIREN_VERSION = "0.21.0"
EXPECTED_RELEASE_REPO = "tommimarkus/dediren"
EXPECTED_RELEASE_PLUGIN_IDS = {
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


def current_target() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "linux" and machine in {"x86_64", "amd64"}:
        return "x86_64-unknown-linux-gnu"
    if system == "linux" and machine in {"aarch64", "arm64"}:
        return "aarch64-unknown-linux-gnu"
    if system == "darwin" and machine in {"aarch64", "arm64"}:
        return "aarch64-apple-darwin"
    return f"{machine}-{system}"


def run_resolver(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        ["bash", str(RELEASE_SCRIPT), *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=merged_env,
    )


@lru_cache(maxsize=1)
def release_bundle() -> Path:
    if os.environ.get("DEDIREN_RELEASE_SMOKE") != "1":
        raise unittest.SkipTest("set DEDIREN_RELEASE_SMOKE=1 to download and smoke-test Dediren release bundles")

    result = run_resolver("--ensure-bundle")
    if result.returncode != 0:
        raise AssertionError(
            f"release resolver failed\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return Path(result.stdout.strip())


def run_dediren(*args: str | Path) -> subprocess.CompletedProcess[str]:
    bundle = release_bundle()
    env = os.environ.copy()
    env.setdefault("DEDIREN_SCHEMA_CACHE_DIR", str(REPO_ROOT / ".cache" / "dediren" / "schema-cache"))
    return subprocess.run(
        [bundle / "bin" / "dediren", *args],
        cwd=bundle,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
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


class ArchitectureDedirenReleaseTest(unittest.TestCase):
    def test_dediren_runtime_bundle_is_not_tracked_in_plugin_source(self) -> None:
        self.assertFalse((ARCH_PLUGIN / "tools" / "dediren-linux").exists())
        self.assertFalse((ARCH_PLUGIN / "tools" / "dediren-macos").exists())

    def test_release_resolver_script_is_present_and_pinned(self) -> None:
        script = RELEASE_SCRIPT.read_text(encoding="utf-8")

        self.assertIn(f'DEDIREN_REPO_DEFAULT="{EXPECTED_RELEASE_REPO}"', script)
        self.assertIn(f'DEDIREN_VERSION_DEFAULT="{EXPECTED_DEDIREN_VERSION}"', script)
        self.assertIn("SHA256SUMS", script)
        self.assertIn("https://github.com/%s/releases/download/v%s", script)
        self.assertNotIn("tools/dediren-linux", script)

    def test_release_resolver_has_valid_bash_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(RELEASE_SCRIPT)],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_release_resolver_prints_current_platform_cache_path_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_resolver("--print-path", env={"DEDIREN_CACHE_DIR": temp_dir})

        self.assertEqual(result.returncode, 0, result.stderr)
        expected_suffix = (
            f"dediren-agent-bundle-{EXPECTED_DEDIREN_VERSION}-{current_target()}"
            f"/bin/dediren"
        )
        self.assertTrue(result.stdout.strip().endswith(expected_suffix), result.stdout)

    def test_release_resolver_requires_java_21_before_returning_runnable_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cache_dir = temp_path / "cache"
            bundle_dir = cache_dir / f"dediren-agent-bundle-{EXPECTED_DEDIREN_VERSION}-{current_target()}"
            bin_dir = bundle_dir / "bin"
            fake_bin = temp_path / "fake-bin"
            bin_dir.mkdir(parents=True)
            fake_bin.mkdir()
            (bundle_dir / "bundle.json").write_text("{}", encoding="utf-8")
            fake_dediren = bin_dir / "dediren"
            fake_dediren.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
            fake_dediren.chmod(0o755)
            fake_java = fake_bin / "java"
            fake_java.write_text(
                "#!/usr/bin/env sh\n"
                "printf 'openjdk version \"17.0.12\"\\n' >&2\n",
                encoding="utf-8",
            )
            fake_java.chmod(0o755)

            result = run_resolver(
                "--ensure",
                env={
                    "DEDIREN_CACHE_DIR": str(cache_dir),
                    "JAVA_HOME": "",
                    "JAVACMD": "",
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                },
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Java 21", result.stderr)
        self.assertIn("17", result.stderr)

    def test_release_resolver_lists_supported_release_targets(self) -> None:
        result = run_resolver("--list-targets")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("x86_64-unknown-linux-gnu", result.stdout)
        self.assertIn("aarch64-unknown-linux-gnu", result.stdout)
        self.assertIn("aarch64-apple-darwin", result.stdout)

    def test_release_resolver_preserves_download_failure_without_cleanup_masking(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_bin = temp_path / "bin"
            fake_bin.mkdir()
            fake_curl = fake_bin / "curl"
            fake_curl.write_text(
                "#!/usr/bin/env bash\n"
                "printf 'curl: simulated DNS failure\\n' >&2\n"
                "exit 6\n",
                encoding="utf-8",
            )
            fake_curl.chmod(0o755)

            result = run_resolver(
                "--ensure-bundle",
                env={
                    "DEDIREN_CACHE_DIR": str(temp_path / "cache"),
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                },
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("curl: simulated DNS failure", result.stderr)
        self.assertNotIn("unbound variable", result.stderr)

    def test_skill_fixture_declares_current_release_plugin_version(self) -> None:
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

    def test_current_platform_release_smoke_reports_version(self) -> None:
        bundle = release_bundle()

        self.assertTrue((bundle / "bundle.json").is_file())
        self.assertTrue((bundle / "bin" / "dediren").is_file())

        result = run_dediren("--version")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("dediren", result.stdout.lower())
        self.assertIn(EXPECTED_DEDIREN_VERSION, result.stdout)

        bundle_manifest = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
        self.assertEqual(bundle_manifest["version"], EXPECTED_DEDIREN_VERSION)
        self.assertEqual(bundle_manifest["elk_helper"], "bin/dediren-plugin-elk-layout")

    def test_release_bundle_contains_java_runtime_plugins_schemas_and_guide(self) -> None:
        bundle = release_bundle()
        bundle_manifest = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
        expected_versions = {plugin["id"]: plugin["version"] for plugin in bundle_manifest["plugins"]}

        self.assertEqual(set(expected_versions), EXPECTED_RELEASE_PLUGIN_IDS)
        self.assertEqual(set(expected_versions.values()), {EXPECTED_DEDIREN_VERSION})

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
            "fixtures/source/valid-uml-sequence-basic.json",
            "fixtures/render-metadata/uml-sequence-basic.json",
            "fixtures/layout-result/uml-sequence-basic.json",
            "fixtures/export/uml-sequence-basic.xmi",
            "docs/agent-usage.md",
            "THIRD-PARTY-NOTICES.md",
            f"lib/cli-{EXPECTED_DEDIREN_VERSION}.jar",
            f"lib/core-{EXPECTED_DEDIREN_VERSION}.jar",
            f"lib/uml-{EXPECTED_DEDIREN_VERSION}.jar",
            f"lib/elk-layout-{EXPECTED_DEDIREN_VERSION}.jar",
            "LICENSE",
        ]

        for relative_path in required_paths:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((bundle / relative_path).is_file())

        guide = (bundle / "docs" / "agent-usage.md").read_text(encoding="utf-8")
        for phrase in [
            "Minimal Source JSON",
            "Artifact Map",
            "Command Handoff",
            "Repair Rules",
            "Semantic Profiles",
            "DEDIREN_BUNDLE_ROOT",
            "DEDIREN_SCHEMA_CACHE_DIR",
            "official Eclipse ELK Java libraries",
            "uml-xmi",
            "uml-sequence",
            "Java 21 or newer",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guide)

        elk_manifest = json.loads((bundle / "plugins" / "elk-layout.manifest.json").read_text(encoding="utf-8"))
        self.assertIn("JAVA_HOME", elk_manifest["allowed_env"])
        self.assertIn("PATH", elk_manifest["allowed_env"])

    def test_release_fixture_model_validates_and_renders(self) -> None:
        project = json.loads((FIXTURE / "project.json").read_text(encoding="utf-8"))
        view = project["views"][0]

        schema_result = run_dediren("validate", "--input", FIXTURE / "model.json")
        self.assertEqual(schema_result.returncode, 0, schema_result.stderr)
        self.assertEqual(envelope(schema_result)["status"], "ok")

        semantic_result = run_dediren(
            "validate",
            "--plugin",
            "generic-graph",
            "--profile",
            "archimate",
            "--input",
            FIXTURE / "model.json",
        )
        self.assertEqual(semantic_result.returncode, 0, semantic_result.stderr)
        self.assertEqual(envelope(semantic_result)["status"], "ok")

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
