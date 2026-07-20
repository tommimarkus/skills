# lean-audit:dup-intentional — parallel per-case test bodies kept literal for readability
import json
import os
import re
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
MIXED_FIXTURE = (
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "fixtures"
    / "dediren"
    / "mixed"
)
EXPECTED_DEDIREN_VERSION = "2026.07.22"
EXPECTED_RELEASE_REPO = "tommimarkus/dediren"
# Bundle schema v2 (dediren 2026.07.14+) deleted the process-plugin protocol: the five
# first-party engines are in-process libraries behind a typed engine-api, so the bundle
# ships one launcher and no plugin executables, manifests, or capability probes. The
# engine ids below survive only as `--plugin` selector values on the decomposed
# commands; they are no longer discoverable from `bundle.json`, and the pipeline tests
# — not manifest introspection — are what prove they still resolve.
EXPECTED_BUNDLE_SCHEMA_VERSION = "dediren-bundle.schema.v2"
EXPECTED_ARCHITECTURE_PROJECT_PLUGIN_IDS = {
    "generic-graph",
    "elk-layout",
    "render",
    "archimate-oef",
}


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


def mcp_session(bundle: Path, root: Path, calls: list[dict]) -> dict[int, dict]:
    """Drive the bundled `dediren mcp` stdio server through one initialize handshake and
    return the JSON-RPC responses keyed by id. ``calls`` carry ids from 2 up (id 1 is the
    handshake). One server run per session, matching how a client drives it."""
    requests = [
        {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "release-test", "version": "0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        *calls,
    ]
    stdin = "".join(json.dumps(request) + "\n" for request in requests)
    proc = subprocess.run(
        [bundle / "bin" / "dediren", "mcp", "--root", str(root)],
        input=stdin, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=os.environ.copy(), timeout=120,
    )
    by_id = {}
    for line in proc.stdout.splitlines():
        if line.strip().startswith("{"):
            message = json.loads(line)
            if "id" in message:
                by_id[message["id"]] = message
    # Responses come back out of order, and a server that stops early simply omits one.
    # Without this check a dropped response surfaces as a bare KeyError at the call site,
    # so assert completeness here where stdout/stderr are still around to say why.
    missing = [r["id"] for r in requests if "id" in r and r["id"] not in by_id]
    if missing:
        raise AssertionError(
            f"dediren mcp returned no response for id(s) {missing}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return by_id


def tool_envelope(response: dict) -> dict:
    """Unwrap the dediren command envelope an MCP tools/call response carries as text."""
    return json.loads(response["result"]["content"][0]["text"])


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


def svg_render_content(result: subprocess.CompletedProcess[str]) -> str:
    # render-result.schema returns data.artifacts[] (since v2, Dediren 2026.06.4); the
    # SVG moved out of the v1 data.content scalar. v3 (Dediren 2026.06.8) added a `png`
    # artifact_kind and an `encoding` field; v4 (Dediren 2026.07.17) removed native raster
    # rendering, dropping `png` from artifact_kind (only `svg`/`html` remain) while keeping
    # the artifacts[] shape and the svg artifact. Mirror the bundle's documented extraction:
    # jq '.data.artifacts[] | select(.artifact_kind=="svg") | .content'.
    data = envelope(result)["data"]
    for artifact in data["artifacts"]:
        if artifact.get("artifact_kind") == "svg":
            return artifact["content"]
    raise AssertionError(f"no svg artifact in render result: {data}")


class ArchitectureDedirenReleaseTest(unittest.TestCase):
    def _assert_validate_ok(self, *args: str | Path) -> None:
        """Run `dediren validate <args>` and assert it succeeds with an ok envelope.
        Shared by the schema-validate / semantic-profile-validate pairs below."""
        result = run_dediren("validate", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(envelope(result)["status"], "ok")

    def _assert_project_ok(self, target: str, plugin: str, view_id: str) -> dict:
        """Run `dediren project --target ... --plugin ... --view ... --input model.json`
        and assert it succeeds with an ok envelope, returning the payload. Shared by
        the projection/metadata projection pair below."""
        result = run_dediren(
            "project", "--target", target, "--plugin", plugin, "--view", view_id,
            "--input", FIXTURE / "model.json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = envelope(result)
        self.assertEqual(payload["status"], "ok")
        return payload

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
            f"dediren-agent-bundle-{EXPECTED_DEDIREN_VERSION}"
            f"/bin/dediren"
        )
        self.assertTrue(result.stdout.strip().endswith(expected_suffix), result.stdout)

    def test_release_resolver_requires_java_21_before_returning_runnable_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cache_dir = temp_path / "cache"
            bundle_dir = cache_dir / f"dediren-agent-bundle-{EXPECTED_DEDIREN_VERSION}"
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
                    # Point sdkman at a nonexistent dir so this stays hermetic:
                    # a sdkman-managed Java >=21 on the host would otherwise be
                    # preferred over the fake Java 17 this test injects on PATH.
                    "SDKMAN_DIR": str(temp_path / "no-sdkman"),
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                },
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Java 21", result.stderr)
        self.assertIn("17", result.stderr)

    def test_release_resolver_prefers_sdkman_java_21_over_older_path_java(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cache_dir = temp_path / "cache"
            bundle_dir = cache_dir / f"dediren-agent-bundle-{EXPECTED_DEDIREN_VERSION}"
            bin_dir = bundle_dir / "bin"
            bin_dir.mkdir(parents=True)
            (bundle_dir / "bundle.json").write_text("{}", encoding="utf-8")
            fake_dediren = bin_dir / "dediren"
            fake_dediren.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
            fake_dediren.chmod(0o755)
            # An older Java on PATH that would be rejected on its own.
            path_bin = temp_path / "path-bin"
            path_bin.mkdir()
            path_java = path_bin / "java"
            path_java.write_text(
                "#!/usr/bin/env sh\nprintf 'openjdk version \"17.0.12\"\\n' >&2\n",
                encoding="utf-8",
            )
            path_java.chmod(0o755)
            # A sdkman-managed Java 21 that must be preferred over the PATH java.
            sdkman_dir = temp_path / "sdkman"
            sdkman_java = sdkman_dir / "candidates" / "java" / "current" / "bin" / "java"
            sdkman_java.parent.mkdir(parents=True)
            sdkman_java.write_text(
                "#!/usr/bin/env sh\nprintf 'openjdk version \"21.0.2\"\\n' >&2\n",
                encoding="utf-8",
            )
            sdkman_java.chmod(0o755)

            result = run_resolver(
                "--ensure",
                env={
                    "DEDIREN_CACHE_DIR": str(cache_dir),
                    "JAVA_HOME": "",
                    "JAVACMD": "",
                    "SDKMAN_DIR": str(sdkman_dir),
                    "PATH": f"{path_bin}:{os.environ['PATH']}",
                },
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("requires Java 21", result.stderr)
        self.assertTrue(result.stdout.strip().endswith("/bin/dediren"), result.stdout)

    def test_release_resolver_serves_a_platform_independent_bundle(self) -> None:
        script = RELEASE_SCRIPT.read_text(encoding="utf-8")

        self.assertNotIn("--list-targets", script)
        self.assertNotIn("apple-darwin", script)
        self.assertNotIn("unknown-linux-gnu", script)
        self.assertIn("platform-independent", script)

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

    def test_mixed_fixture_declares_canonical_multimodel_layout(self) -> None:
        project = json.loads((MIXED_FIXTURE / "project.json").read_text(encoding="utf-8"))
        arch_model = json.loads((MIXED_FIXTURE / "model.json").read_text(encoding="utf-8"))
        uml_model = json.loads((MIXED_FIXTURE / "model-uml.json").read_text(encoding="utf-8"))

        # v2 multi-model project shape binds one single-notation model per notation.
        self.assertEqual(project["schema"], "souroldgeezer.architecture.dediren.project.v2")
        models = {model["id"]: model for model in project["models"]}
        self.assertEqual({model["profile"] for model in models.values()}, {"archimate", "uml"})
        for model in models.values():
            data = json.loads((MIXED_FIXTURE / model["file"]).read_text(encoding="utf-8"))
            self.assertEqual(data["plugins"]["generic-graph"]["semantic_profile"], model["profile"])

        # Every view binds a declared model; every export binds a declared model and view.
        view_ids = {view["id"] for view in project["views"]}
        for view in project["views"]:
            self.assertIn(view["model"], models)
        for export in project["exports"]:
            self.assertIn(export["model"], models)
            self.assertIn(export["view"], view_ids)
        self.assertEqual({view["model"] for view in project["views"]}, set(models))
        self.assertEqual({export["plugin"] for export in project["exports"]}, {"archimate-oef", "uml-xmi"})

        # The cross-notation handoff resolves into the package's ArchiMate model.
        arch_ids = {node["id"] for node in arch_model["nodes"]}
        links = [
            node["properties"]["uml"]["architecture_context"]
            for node in uml_model["nodes"]
            if node.get("properties", {}).get("uml", {}).get("architecture_context")
        ]
        self.assertTrue(links, "mixed fixture should demonstrate a cross-notation handoff link")
        for context in links:
            self.assertEqual(context["profile"], "archimate")
            self.assertIn(context["element_id"], arch_ids)

    def test_every_embedded_dediren_version_pin_matches_expected(self) -> None:
        # A Dediren version bump must update every copy of the pinned version.
        # Discover the pins instead of listing them by hand so a newly added
        # pinned fixture or notation example is guarded automatically, and a
        # bump cannot silently miss a duplicated pin. Pins live in two shapes:
        # required_plugins[].version inside the dediren fixture models, and the
        # required_plugins pin embedded in each UML notation worked example.
        arch_refs = ARCH_PLUGIN / "skills" / "architecture-design" / "references"
        pins: dict[str, str] = {}  # "<relative-path>::<plugin-id>" -> version

        fixture_models = sorted((arch_refs / "fixtures" / "dediren").rglob("*.json"))
        for model_path in fixture_models:
            document = json.loads(model_path.read_text(encoding="utf-8"))
            relative = model_path.relative_to(REPO_ROOT)
            for plugin in document.get("required_plugins", []):
                pins[f"{relative}::{plugin['id']}"] = plugin["version"]
        fixture_pin_count = len(pins)

        required_plugins_array = re.compile(r'"required_plugins"\s*:\s*\[(.*?)\]', re.DOTALL)
        plugin_pin = re.compile(r'"id"\s*:\s*"([^"]+)"\s*,\s*"version"\s*:\s*"([^"]+)"')
        notation_examples = sorted((arch_refs / "notations" / "uml").glob("*.md"))
        for example_path in notation_examples:
            relative = example_path.relative_to(REPO_ROOT)
            for array_body in required_plugins_array.findall(example_path.read_text(encoding="utf-8")):
                for plugin_id, version in plugin_pin.findall(array_body):
                    pins[f"{relative}::{plugin_id}"] = version
        notation_pin_count = len(pins) - fixture_pin_count

        # Guard both discovery sources: an empty glob (moved/renamed directory)
        # would otherwise pass vacuously and stop covering the pins it should.
        self.assertTrue(fixture_pin_count, "expected Dediren fixture version pins")
        self.assertTrue(notation_pin_count, "expected UML notation-example version pins")

        mismatched = {location: version for location, version in pins.items() if version != EXPECTED_DEDIREN_VERSION}
        self.assertEqual(mismatched, {}, f"embedded pins not equal to {EXPECTED_DEDIREN_VERSION}: {mismatched}")

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
        self.assertEqual(bundle_manifest["bundle_schema_version"], EXPECTED_BUNDLE_SCHEMA_VERSION)

    def test_release_bundle_ships_a_single_launcher_with_no_plugin_protocol(self) -> None:
        """Bundle schema v2 deleted the process-plugin protocol.

        Guards the contract the v1 bundle advertised and v2 removed: no `plugins[]` /
        `elk_helper` manifest keys, no `plugins/` manifest directory, and exactly one
        executable in `bin/` (no per-engine child executables to spawn).
        """
        bundle = release_bundle()
        bundle_manifest = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))

        self.assertNotIn("plugins", bundle_manifest)
        self.assertNotIn("elk_helper", bundle_manifest)
        self.assertFalse((bundle / "plugins").exists())
        self.assertEqual(sorted(path.name for path in (bundle / "bin").iterdir()), ["dediren"])

    def test_release_bundle_contains_java_runtime_engines_schemas_and_guide(self) -> None:
        bundle = release_bundle()

        required_paths = [
            # The first-party engines ship as in-process libraries behind the typed
            # engine-api (not plugin executables + manifests). Since dediren 2026.07.19
            # they are consolidated into a single application jar instead of one jar per
            # engine (a bundle size optimization within schema v2), so the file-level
            # check is the one bundle jar; the pipeline tests below prove each engine id
            # still resolves through the launcher.
            f"lib/dediren-bundle-{EXPECTED_DEDIREN_VERSION}.jar",
            # One-shot `dediren build` result contract (new in bundle schema v2).
            "schemas/build-result.schema.json",
            "schemas/model.schema.json",
            "schemas/layout-request.schema.json",
            "schemas/layout-result.schema.json",
            "schemas/render-policy.schema.json",
            "schemas/render-metadata.schema.json",
            "schemas/oef-export-policy.schema.json",
            "schemas/uml-xmi-export-policy.schema.json",
            "fixtures/export-policy/default-uml-xmi.json",
            "fixtures/source/valid-uml-basic.json",
            "fixtures/source/valid-uml-complex.json",
            "fixtures/source/valid-uml-sequence-basic.json",
            "fixtures/source/valid-uml-sequence-fragments.json",
            "fixtures/source/valid-uml-state-machine-basic.json",
            "fixtures/source/valid-uml-use-case-basic.json",
            "fixtures/source/valid-uml-component-basic.json",
            "fixtures/source/valid-uml-deployment-basic.json",
            "fixtures/render-policy/uml-svg.json",
            "fixtures/render-metadata/uml-sequence-basic.json",
            "fixtures/layout-result/uml-sequence-basic.json",
            "fixtures/export/uml-sequence-basic.xmi",
            "docs/agent-usage.md",
            "THIRD-PARTY-NOTICES.md",
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

    def test_release_fixture_model_validates_and_renders(self) -> None:
        project = json.loads((FIXTURE / "project.json").read_text(encoding="utf-8"))
        view = project["views"][0]

        self._assert_validate_ok("--input", FIXTURE / "model.json")
        self._assert_validate_ok(
            "--plugin", "generic-graph", "--profile", "archimate", "--input", FIXTURE / "model.json"
        )

        project_payload = self._assert_project_ok(
            view["projection"]["target"], view["projection"]["plugin"], view["id"]
        )
        metadata_payload = self._assert_project_ok(
            view["metadata"]["target"], view["metadata"]["plugin"], view["id"]
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

            # Envelope-shape assertion only. We consume dediren; its validate-layout
            # *quality verdict* is dediren's own to own (see the sequence-fragments test
            # below and dediren#48). We assert only the envelope fields we parse per the
            # Fast Path contract (.status / .diagnostics[]); render + export are the real
            # consumer contract.
            validation_envelope = envelope(run_dediren("validate-layout", "--input", layout_result_path))
            self.assertIn("status", validation_envelope)
            self.assertIn("diagnostics", validation_envelope)

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
            self.assertEqual(
                envelope(render_result)["data"]["render_result_schema_version"],
                "render-result.schema.v4",
            )
            svg = svg_render_content(render_result)
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

    def test_release_uml_source_fixtures_are_schema_and_profile_valid(self) -> None:
        bundle = release_bundle()
        uml_fixtures = [
            "valid-uml-basic.json",
            "valid-uml-complex.json",
            "valid-uml-sequence-basic.json",
            "valid-uml-sequence-fragments.json",
            "valid-uml-state-machine-basic.json",
            "valid-uml-use-case-basic.json",
            "valid-uml-component-basic.json",
            "valid-uml-deployment-basic.json",
        ]
        for name in uml_fixtures:
            fixture = bundle / "fixtures" / "source" / name
            with self.subTest(fixture=name):
                self.assertTrue(fixture.is_file(), f"missing bundle fixture {name}")
                self._assert_validate_ok("--input", fixture)
                self._assert_validate_ok("--plugin", "generic-graph", "--profile", "uml", "--input", fixture)

    def test_release_uml_sequence_fragments_full_pipeline(self) -> None:
        bundle = release_bundle()
        source = bundle / "fixtures" / "source" / "valid-uml-sequence-fragments.json"
        source_doc = json.loads(source.read_text(encoding="utf-8"))
        view_id = source_doc["plugins"]["generic-graph"]["views"][0]["id"]

        layout_request = run_dediren(
            "project", "--target", "layout-request", "--plugin", "generic-graph",
            "--view", view_id, "--input", source,
        )
        self.assertEqual(layout_request.returncode, 0, layout_request.stderr)
        self.assertEqual(envelope(layout_request)["status"], "ok")

        render_metadata = run_dediren(
            "project", "--target", "render-metadata", "--plugin", "generic-graph",
            "--view", view_id, "--input", source,
        )
        self.assertEqual(render_metadata.returncode, 0, render_metadata.stderr)
        self.assertEqual(envelope(render_metadata)["status"], "ok")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            layout_request_path = temp_path / "layout-request.json"
            layout_request_path.write_text(json.dumps(envelope(layout_request)["data"]), encoding="utf-8")
            render_metadata_path = temp_path / "render-metadata.json"
            render_metadata_path.write_text(json.dumps(envelope(render_metadata)["data"]), encoding="utf-8")

            layout_result = run_dediren("layout", "--plugin", "elk-layout", "--input", layout_request_path)
            self.assertEqual(layout_result.returncode, 0, layout_result.stderr)
            self.assertEqual(envelope(layout_result)["status"], "ok")

            layout_result_path = temp_path / "layout-result.json"
            layout_result_path.write_text(json.dumps(envelope(layout_result)["data"]), encoding="utf-8")

            # We consume dediren; its validate-layout *quality verdict* is dediren's own to
            # own — dediren's suite owns that (its dist-tool smoke deliberately does not run
            # a sequence layout through validate-layout). We assert only the envelope *shape*
            # we parse per the Fast Path contract (.status / .diagnostics[]), never a
            # specific verdict. Sequence Message edges legitimately terminate on the lifeline
            # (node center-x, not the head-node box perimeter), which dediren 2026.07.17+
            # routes correctly and the perimeter check then reports as
            # DEDIREN_LAYOUT_ROUTE_ENDPOINT_OFF_NODE_PERIMETER (status "error", exit 2) — a
            # correct-layout side effect, not an adoption blocker. Render + export below are
            # the real usage contract. See dediren#48; earlier context dediren#13 / #30.
            validation_envelope = envelope(run_dediren("validate-layout", "--input", layout_result_path))
            self.assertIn("status", validation_envelope)
            self.assertIn("diagnostics", validation_envelope)

            render_result = run_dediren(
                "render", "--plugin", "render",
                "--policy", bundle / "fixtures" / "render-policy" / "uml-svg.json",
                "--metadata", render_metadata_path, "--input", layout_result_path,
            )
            self.assertEqual(render_result.returncode, 0, render_result.stderr)
            self.assertIn("<svg", svg_render_content(render_result))

            # uml-xmi export validates against the OMG XMI schema; the runtime fetches it
            # from www.omg.org on first run and caches it under DEDIREN_SCHEMA_CACHE_DIR,
            # so reruns are offline.
            export_result = run_dediren(
                "export", "--plugin", "uml-xmi",
                "--policy", bundle / "fixtures" / "export-policy" / "default-uml-xmi.json",
                "--source", source, "--layout", layout_result_path,
            )
            self.assertEqual(export_result.returncode, 0, export_result.stderr)
            self.assertEqual(envelope(export_result)["data"]["artifact_kind"], "uml-xmi+xml")

    def _stub_bundle(self, cache_dir: Path, version: str, marker: str) -> None:
        """Materialize a resolved-looking bundle (executable `dediren` + `bundle.json`)
        so the launcher's warm path fires without a real download. The stub `dediren`
        echoes `marker` for `mcp` so the test can prove the launcher exec'd it."""
        bundle = cache_dir / f"dediren-agent-bundle-{version}"
        (bundle / "bin").mkdir(parents=True)
        binary = bundle / "bin" / "dediren"
        binary.write_text(
            "#!/usr/bin/env bash\n"
            f"printf '{marker} %s\\n' \"$*\"\n"
            "exit 0\n",
            encoding="utf-8",
        )
        binary.chmod(0o755)
        (bundle / "bundle.json").write_text("{}\n", encoding="utf-8")

    def test_mcp_launcher_starts_from_a_warm_cache_without_network(self) -> None:
        """The overwhelmingly common path: bundle already resolved. The launcher must
        exec the server without touching the network — a sabotaged `curl` that fails if
        called proves the warm path does no session-start download."""
        launcher = RELEASE_SCRIPT.parent / "dediren-mcp.sh"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cache = temp_path / "cache"
            cache.mkdir()
            self._stub_bundle(cache, "0.0.0-test", "STUB-STARTED")

            fake_bin = temp_path / "bin"
            fake_bin.mkdir()
            fake_curl = fake_bin / "curl"
            fake_curl.write_text(
                "#!/usr/bin/env bash\nprintf 'curl must not run on the warm path\\n' >&2\nexit 6\n",
                encoding="utf-8",
            )
            fake_curl.chmod(0o755)

            result = subprocess.run(
                ["bash", str(launcher)],
                cwd=REPO_ROOT, check=False, text=True,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=60,
                env={
                    **os.environ,
                    "DEDIREN_CACHE_DIR": str(cache),
                    "DEDIREN_VERSION": "0.0.0-test",
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                },
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("STUB-STARTED", result.stdout)
        self.assertIn("mcp --root", result.stdout)
        self.assertNotIn("curl must not run", result.stderr)

    def test_mcp_launcher_resolves_on_demand_then_fails_bounded_when_download_fails(self) -> None:
        """A cold cache (fresh install, or a pin bump orphaned the prior bundle) must no
        longer silently give up: the launcher resolves on demand. When the resolve itself
        fails it exits non-zero — no worse than before — but the `subprocess` timeout is
        the regression guard that it stays *bounded* and never hangs session start."""
        launcher = RELEASE_SCRIPT.parent / "dediren-mcp.sh"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cache = temp_path / "cache"
            fake_bin = temp_path / "bin"
            fake_bin.mkdir()
            fake_curl = fake_bin / "curl"
            fake_curl.write_text(
                "#!/usr/bin/env bash\nprintf 'curl: simulated DNS failure\\n' >&2\nexit 6\n",
                encoding="utf-8",
            )
            fake_curl.chmod(0o755)

            result = subprocess.run(
                ["bash", str(launcher)],
                cwd=REPO_ROOT, check=False, text=True,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=90,
                env={
                    **os.environ,
                    "DEDIREN_CACHE_DIR": str(cache),
                    "DEDIREN_VERSION": "0.0.0-test",
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                },
            )

        self.assertNotEqual(result.returncode, 0)
        # It attempted the resolve (curl ran) rather than refusing outright,
        # and the JSON-RPC stdout channel stayed clean on the failure path.
        self.assertIn("simulated DNS failure", result.stderr)
        self.assertIn("resolve", result.stderr.lower())
        self.assertEqual(result.stdout, "")

    def test_launcher_and_resolver_bound_session_start_network(self) -> None:
        """Session start must never hang on a dead socket or a wedged peer. The launcher
        resolves the bundle on demand, so the resolver's network and lock waits carry
        hard bounds; assert they are present so a later edit cannot quietly drop them."""
        launcher_script = (RELEASE_SCRIPT.parent / "dediren-mcp.sh").read_text(encoding="utf-8")
        self.assertIn("--ensure-bundle", launcher_script)

        resolver = RELEASE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("--connect-timeout", resolver)
        self.assertIn("--max-time", resolver)
        self.assertIn("flock -w", resolver)

    def test_mcp_server_exposes_the_three_tools_the_skill_drives(self) -> None:
        """The shipped surface: the bundled `dediren mcp` stdio server the plugin
        declares exposes dediren_validate / dediren_build / dediren_guide, and a
        profile-scoped validate returns an ok envelope."""
        bundle = release_bundle()
        by_id = mcp_session(bundle, FIXTURE, [
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {
                "jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {
                    "name": "dediren_validate",
                    "arguments": {"source": "model.json", "profile": "archimate"},
                },
            },
        ])
        tools = {tool["name"] for tool in by_id[2]["result"]["tools"]}
        self.assertEqual(tools, {"dediren_validate", "dediren_build", "dediren_guide"})
        validation = tool_envelope(by_id[3])
        self.assertEqual(validation["status"], "ok", validation)

    def test_cross_package_identity_property_validates_with_and_without_profile(self) -> None:
        """`source-grounding.md` claims `properties.identity` — the repo-owned
        cross-package identity convention (`architecture.md` §15) — is schema-legal and
        semantically accepted by `dediren_validate` both with and without an explicit
        profile, on the *pinned* bundle. The dediren runtime enforces none of that
        convention, so no other gate re-checks the claim: `scoped_pin_replace` rewrites
        "on the pinned <v> bundle" as a live pin, which without this test would silently
        re-assert the claim against a runtime nobody probed. Pin the claim to the runtime
        so a bump that breaks open `properties` fails here instead of shipping.

        One session per call on purpose: a server that errors on the first tools/call
        answers only one of two batched calls (and non-deterministically which), so
        batching would report the regression this test exists to catch as a missing
        response rather than as the failing envelope."""
        bundle = release_bundle()
        model = json.loads((FIXTURE / "model.json").read_text(encoding="utf-8"))
        for node in model["nodes"]:
            node["properties"]["identity"] = f"canon-{node['id']}"
        # Non-vacuity: the probe must actually carry the property under test, or both
        # calls would pass by validating a plain fixture and prove nothing.
        self.assertTrue(
            model["nodes"] and all(n["properties"].get("identity") for n in model["nodes"]),
            "probe model must carry properties.identity on every node",
        )
        # The claim names both invocations; profile is optional on the MCP tool (the CLI
        # requires --profile), so an omitted profile must still resolve and accept.
        for arguments in ({"source": "model.json", "profile": "archimate"},
                          {"source": "model.json"}):
            with self.subTest(profile=arguments.get("profile", "<omitted>")):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir)
                    (root / "model.json").write_text(json.dumps(model), encoding="utf-8")
                    by_id = mcp_session(bundle, root, [{
                        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "dediren_validate", "arguments": arguments},
                    }])
                envelope = tool_envelope(by_id[2])
                self.assertEqual(envelope["status"], "ok", envelope)


if __name__ == "__main__":
    unittest.main()
