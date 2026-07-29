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
RENDERED_FIXTURE = (
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "fixtures"
    / "dediren"
    / "rendered"
)
DEPLOYMENT_NOTATION_DOC = (
    ARCH_PLUGIN
    / "skills"
    / "architecture-design"
    / "references"
    / "notations"
    / "uml"
    / "deployment.md"
)
EXPECTED_DEDIREN_VERSION = "2026.07.29"
EXPECTED_RELEASE_REPO = "tommimarkus/dediren"
# Bundle schema v2 (dediren 2026.07.14+) deleted the process-plugin protocol: the five
# first-party engines are in-process libraries behind a typed engine-api, so the bundle
# ships one launcher and no plugin executables, manifests, or capability probes. The
# engine ids below survive only as `--plugin` selector values on the decomposed
# commands; they are no longer discoverable from `bundle.json`, and the pipeline tests
# — not manifest introspection — are what prove they still resolve.
EXPECTED_BUNDLE_SCHEMA_VERSION = "dediren-bundle.schema.v2"
# The decomposed commands' `--plugin` selectors, driven directly by the pipeline tests
# below. The package manifest no longer names them: `package.schema.v1` declares views
# and outputs, and the runtime owns the stage chain.
STAGE_PLUGIN_GENERIC_GRAPH = "generic-graph"
STAGE_PLUGIN_LAYOUT = "elk-layout"
STAGE_PLUGIN_RENDER = "render"
EXPECTED_ARCHITECTURE_EXPORT_LANES = {"archimate-oef", "uml-xmi"}


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


def mcp_session(bundle: Path, root: Path, calls: list[dict], read_only: bool = False) -> dict[int, dict]:
    """Drive the bundled `dediren mcp` stdio server through one initialize handshake and
    return the JSON-RPC responses keyed by id. ``calls`` carry ids from 2 up (id 1 is the
    handshake). One server run per session, matching how a client drives it. ``read_only``
    launches with `--read-only`, which withholds the artifact-writing `dediren_build`."""
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
    command = [bundle / "bin" / "dediren", "mcp", "--root", str(root)]
    if read_only:
        command.append("--read-only")
    proc = subprocess.run(
        command,
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
    # the artifacts[] shape and the svg artifact. v5 (Dediren 2026.07.26) narrowed
    # artifact_kind to `svg` only (dropping `html`) and encoding to `utf-8` only (dropping
    # `base64`) — the skill only ever consumes the svg/utf-8 artifact, so extraction is
    # unchanged. Mirror the bundle's documented extraction:
    # jq '.data.artifacts[] | select(.artifact_kind=="svg") | .content'.
    data = envelope(result)["data"]
    for artifact in data["artifacts"]:
        if artifact.get("artifact_kind") == "svg":
            return artifact["content"]
    raise AssertionError(f"no svg artifact in render result: {data}")


def _sole_json_block(md_path: Path) -> dict:
    """Return the single fenced ```json block from a notation doc, parsed. The per-kind
    notation docs carry exactly one Worked Example JSON block; a surface test exports it so
    the doc's own example is runtime-verified in place instead of being duplicated into a
    separate fixture. Assert exactly one block, so a second example added later fails loudly
    rather than silently exporting the wrong one."""
    blocks = re.findall(r"```json\n(.*?)\n```", md_path.read_text(encoding="utf-8"), re.S)
    if len(blocks) != 1:
        raise AssertionError(
            f"expected exactly one ```json block in {md_path}, found {len(blocks)}"
        )
    return json.loads(blocks[0])


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

    def _build_ok(self, out_dir: Path, *args: str | Path) -> dict:
        """Run `dediren build --out <out_dir> <args>` and assert it succeeds, returning
        the build-result document. Unlike the enveloped commands, `build` prints its
        result document *unwrapped*, so the returned dict is the build-result itself
        (`build_result_schema_version` / `status` / `views` / `model_artifacts`). Shared
        by the provenance, verify, status, and whole-model-interchange probes below, all
        of which need provenance-stamped artifacts a whole `build` produces."""
        result = run_dediren("build", "--out", out_dir, *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        build_result = envelope(result)
        self.assertEqual(build_result["status"], "ok", build_result)
        return build_result

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
        fixture_package = json.loads((FIXTURE / "package.json").read_text(encoding="utf-8"))

        fixture_versions = {plugin["id"]: plugin["version"] for plugin in fixture_model["required_plugins"]}
        self.assertEqual(fixture_versions, {"generic-graph": EXPECTED_DEDIREN_VERSION})
        self.assertEqual(fixture_model["plugins"]["generic-graph"]["semantic_profile"], "archimate")

        # The package declares views and export lanes; the per-stage plugin chain is the
        # runtime's, not the manifest's.
        self.assertEqual(fixture_package["package_schema_version"], "package.schema.v1")
        self.assertEqual({model["source"] for model in fixture_package["models"]}, {"model.json"})
        lanes = {export["lane"] for export in fixture_package["exports"]}
        self.assertTrue(lanes <= EXPECTED_ARCHITECTURE_EXPORT_LANES, lanes)

    def test_mixed_fixture_declares_canonical_multimodel_layout(self) -> None:
        package = json.loads((MIXED_FIXTURE / "package.json").read_text(encoding="utf-8"))
        arch_model = json.loads((MIXED_FIXTURE / "model.json").read_text(encoding="utf-8"))
        uml_model = json.loads((MIXED_FIXTURE / "model-uml.json").read_text(encoding="utf-8"))

        # package.schema.v1 binds one single-notation model per notation. It carries no
        # per-model profile: each model.json's own semantic_profile is the authority.
        self.assertEqual(package["package_schema_version"], "package.schema.v1")
        models = {model["id"]: model for model in package["models"]}
        profiles = set()
        for model in models.values():
            self.assertNotIn("profile", model)
            data = json.loads((MIXED_FIXTURE / model["source"]).read_text(encoding="utf-8"))
            profiles.add(data["plugins"]["generic-graph"]["semantic_profile"])
        self.assertEqual(profiles, {"archimate", "uml"})

        # Every view binds a declared model; every export targets exactly one of a
        # declared view or a declared model (package.schema.v1's oneOf).
        view_ids = {view["id"] for view in package["views"]}
        for view in package["views"]:
            self.assertIn(view["model"], models)
        for export in package["exports"]:
            targets = {key for key in ("view", "model") if key in export}
            self.assertEqual(len(targets), 1, f"{export['id']} must target exactly one")
            if "view" in export:
                self.assertIn(export["view"], view_ids)
            else:
                self.assertIn(export["model"], models)
        self.assertEqual({view["model"] for view in package["views"]}, set(models))
        self.assertEqual({export["lane"] for export in package["exports"]}, {"archimate-oef", "uml-xmi"})

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

    def test_rendered_fixture_declares_canonical_multimodel_layout(self) -> None:
        # The rendered/ gallery fixture is a canonical multi-model package: each
        # models[] entry resolves to a real source file whose semantic_profile matches
        # the declared profile, and each model declares exactly the views package.json
        # binds to it. (It carries no export or cross-notation handoff — that shape is
        # exercised by the mixed fixture above.)
        package = json.loads((RENDERED_FIXTURE / "package.json").read_text(encoding="utf-8"))

        self.assertEqual(package["package_schema_version"], "package.schema.v1")
        models = {model["id"]: model for model in package["models"]}
        profiles = set()
        for model in models.values():
            self.assertNotIn("profile", model)
            data = json.loads((RENDERED_FIXTURE / model["source"]).read_text(encoding="utf-8"))
            profiles.add(data["plugins"]["generic-graph"]["semantic_profile"])
            model_view_ids = {view["id"] for view in data["plugins"]["generic-graph"]["views"]}
            bound_view_ids = {
                view["id"] for view in package["views"] if view["model"] == model["id"]
            }
            self.assertEqual(model_view_ids, bound_view_ids)
        self.assertEqual(profiles, {"archimate", "uml"})

        # package.json is the only authored manifest: the former project.json sidecar
        # is retired (lang/dir went native in 2026.07.29, feature is the dir name).
        self.assertFalse((RENDERED_FIXTURE / "project.json").exists())
        self.assertEqual(package["presentation"], {"lang": "en", "dir": "ltr"})

        # A shared render policy must not carry accessibility text: a policy-level
        # title/description overrides every view's own presentation, which is how two
        # different UML views once both rendered as "Mixed - Domain Class View".
        for policy in sorted(RENDERED_FIXTURE.glob("render-policy*.json")):
            with self.subTest(policy=policy.name):
                self.assertNotIn(
                    "accessibility", json.loads(policy.read_text(encoding="utf-8"))
                )

        # Every view binds a declared model; the models partition the views.
        for view in package["views"]:
            self.assertIn(view["model"], models)
        self.assertEqual({view["model"] for view in package["views"]}, set(models))

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
        package = json.loads((FIXTURE / "package.json").read_text(encoding="utf-8"))
        view = package["views"][0]
        export_spec = package["exports"][0]

        self._assert_validate_ok("--input", FIXTURE / "model.json")
        self._assert_validate_ok(
            "--plugin", "generic-graph", "--profile", "archimate", "--input", FIXTURE / "model.json"
        )

        project_payload = self._assert_project_ok(
            "layout-request", STAGE_PLUGIN_GENERIC_GRAPH, view["id"]
        )
        metadata_payload = self._assert_project_ok(
            "render-metadata", STAGE_PLUGIN_GENERIC_GRAPH, view["id"]
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
                STAGE_PLUGIN_RENDER,
                "--policy",
                FIXTURE / view["render_policy"],
                "--metadata",
                render_metadata_path,
                "--input",
                layout_result_path,
            )
            self.assertEqual(render_result.returncode, 0, render_result.stderr)
            self.assertEqual(
                envelope(render_result)["data"]["render_result_schema_version"],
                "render-result.schema.v5",
            )
            svg = svg_render_content(render_result)
            self.assertIn("<svg", svg)
            self.assertIn('data-dediren-node-id="client"', svg)
            self.assertIn('data-dediren-edge-id="orders-service-serves-client"', svg)

            export_result = run_dediren(
                "export",
                "--plugin",
                export_spec["lane"],
                "--policy",
                FIXTURE / export_spec["policy"],
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
            exported = envelope(export_result)
            self.assertEqual(exported["data"]["artifact_kind"], "uml-xmi+xml")
            # #106: the sequence XMI emits its full abstract syntax — one uml:Interaction
            # packagedElement with nested <lifeline>/<message> children and
            # MessageOccurrenceSpecification fragments (plus CombinedFragment for the
            # fragments in this fixture) — with no omission diagnostic. Pins the corrected
            # `uml/sequence.md` claim (was "XMI-omitted: interactions, lifelines, messages").
            content = exported["data"]["content"]
            for xmi_type in (
                "uml:Interaction", "uml:MessageOccurrenceSpecification", "uml:CombinedFragment",
            ):
                self.assertIn(f'xmi:type="{xmi_type}"', content)
            self.assertIn("<lifeline", content)
            self.assertIn("<message", content)
            sequence_codes = {d["code"] for d in exported.get("diagnostics", [])}
            self.assertNotIn("DEDIREN_XMI_ELEMENTS_OMITTED", sequence_codes)
            self.assertNotIn("DEDIREN_XMI_RELATIONSHIPS_OMITTED", sequence_codes)

    def test_release_uml_deployment_worked_example_xmi_full_pipeline(self) -> None:
        """`uml/deployment.md`'s `Validation, Render, Export` note claims the `uml-xmi`
        export emits the full deployment abstract syntax with no `DEDIREN_XMI_*_OMITTED`
        diagnostic. Verify it end-to-end by running the doc's own Worked Example through
        project -> layout -> uml-xmi export on the pinned bundle and asserting the emitted
        element/relationship types. Closes the #106 non-class XMI coverage gap: before this
        only the `uml-class` view was XMI-exercised, so a false per-kind claim like the
        pre-#106 deployment/sequence "XMI-omitted" text could rot undetected. Exports the
        doc's example in place (single-sourced), so the claim and its evidence cannot
        drift apart."""
        bundle = release_bundle()
        source_doc = _sole_json_block(DEPLOYMENT_NOTATION_DOC)
        view_id = source_doc["plugins"]["generic-graph"]["views"][0]["id"]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "deployment-model.json"
            source.write_text(json.dumps(source_doc), encoding="utf-8")

            layout_request = run_dediren(
                "project", "--target", "layout-request", "--plugin", "generic-graph",
                "--view", view_id, "--input", source,
            )
            self.assertEqual(layout_request.returncode, 0, layout_request.stderr)
            layout_request_path = temp_path / "layout-request.json"
            layout_request_path.write_text(
                json.dumps(envelope(layout_request)["data"]), encoding="utf-8"
            )

            layout_result = run_dediren(
                "layout", "--plugin", "elk-layout", "--input", layout_request_path
            )
            self.assertEqual(layout_result.returncode, 0, layout_result.stderr)
            layout_result_path = temp_path / "layout-result.json"
            layout_result_path.write_text(
                json.dumps(envelope(layout_result)["data"]), encoding="utf-8"
            )

            # uml-xmi export validates against the OMG XMI schema; the runtime fetches it
            # from www.omg.org on first run and caches it under DEDIREN_SCHEMA_CACHE_DIR,
            # so reruns are offline.
            export_result = run_dediren(
                "export", "--plugin", "uml-xmi",
                "--policy", bundle / "fixtures" / "export-policy" / "default-uml-xmi.json",
                "--source", source, "--layout", layout_result_path,
            )
            self.assertEqual(export_result.returncode, 0, export_result.stderr)
            exported = envelope(export_result)
            self.assertEqual(exported["data"]["artifact_kind"], "uml-xmi+xml")
            content = exported["data"]["content"]
            for xmi_type in (
                "uml:Device", "uml:ExecutionEnvironment", "uml:Node", "uml:Artifact",
                "uml:DeploymentSpecification", "uml:Component", "uml:Deployment",
                "uml:Manifestation", "uml:CommunicationPath",
            ):
                self.assertIn(f'xmi:type="{xmi_type}"', content)
            deployment_codes = {d["code"] for d in exported.get("diagnostics", [])}
            self.assertNotIn("DEDIREN_XMI_ELEMENTS_OMITTED", deployment_codes)
            self.assertNotIn("DEDIREN_XMI_RELATIONSHIPS_OMITTED", deployment_codes)

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

    def test_mcp_server_exposes_the_seven_tools_the_skill_drives(self) -> None:
        """The shipped surface: the bundled `dediren mcp` stdio server the plugin
        declares exposes the seven tools the skill drives as of Dediren 2026.07.26 —
        dediren_validate / dediren_build / dediren_guide plus the four model-intelligence
        tools dediren_diff / dediren_query / dediren_verify / dediren_status — and a
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
        self.assertEqual(tools, {
            "dediren_validate", "dediren_build", "dediren_guide",
            "dediren_diff", "dediren_query", "dediren_verify", "dediren_status",
        })
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

    def test_dediren_query_answers_the_three_fixed_kinds_and_rejects_bad_input(self) -> None:
        """`source-grounding.md` claims `dediren_query` answers the three fixed kinds
        (`dependents` / `orphans` / `view-coverage`) on the pinned bundle and rejects an
        unknown `--kind` or a `dependents` call missing `--id`. The query engine is new
        in Dediren 2026.07.26 and the runtime is the only thing that answers it, so
        `scoped_pin_replace` would re-assert the claim against an unprobed runtime; pin it.

        `build`-less CLI probe: the four model-intelligence commands print the standard
        `envelope.schema.v1` with the result document under `.data` (only `build` is
        unwrapped)."""
        dependents = envelope(run_dediren(
            "query", "--kind", "dependents", "--id", "orders-service",
            "--input", FIXTURE / "model.json",
        ))
        self.assertEqual(dependents["status"], "ok", dependents)
        dep_data = dependents["data"]
        self.assertEqual(dep_data["query_result_schema_version"], "query-result.schema.v1")
        self.assertEqual(dep_data["kind"], "dependents")
        self.assertEqual(dep_data["dependents"]["id"], "orders-service")
        self.assertEqual(
            {edge["relationship_id"] for edge in dep_data["dependents"]["inbound"]},
            {"orders-component-realizes-service"},
        )
        self.assertEqual(
            {edge["relationship_id"] for edge in dep_data["dependents"]["outbound"]},
            {"orders-service-serves-client"},
        )

        orphans = envelope(run_dediren(
            "query", "--kind", "orphans", "--input", FIXTURE / "model.json",
        ))
        self.assertEqual(orphans["status"], "ok", orphans)
        self.assertEqual(orphans["data"]["kind"], "orphans")
        self.assertIn("relationship_orphans", orphans["data"]["orphans"])
        self.assertIn("view_orphans", orphans["data"]["orphans"])

        coverage = envelope(run_dediren(
            "query", "--kind", "view-coverage", "--input", FIXTURE / "model.json",
        ))
        self.assertEqual(coverage["status"], "ok", coverage)
        # data key is view_coverage (underscore); the --kind vocabulary is view-coverage.
        cov = coverage["data"]["view_coverage"]
        self.assertEqual({view["id"] for view in cov["views"]}, {"main"})
        # Assert the per-view counts source-grounding names, not just the view id, so the
        # "per-view counts" claim has a probe: main covers all 4 nodes / 3 relationships.
        main_view = next(view for view in cov["views"] if view["id"] == "main")
        self.assertEqual(main_view["node_count"], 4)
        self.assertEqual(main_view["relationship_count"], 3)
        self.assertEqual(cov["model_node_count"], 4)
        self.assertEqual(cov["model_relationship_count"], 3)
        self.assertEqual(cov["uncovered_node_ids"], [])

        # Fixed vocabulary: an unknown kind and a missing --id are both usage errors.
        for args in (["query", "--kind", "nonsense", "--input", str(FIXTURE / "model.json")],
                     ["query", "--kind", "dependents", "--input", str(FIXTURE / "model.json")]):
            with self.subTest(args=args):
                result = run_dediren(*args)
                self.assertEqual(result.returncode, 2, result.stdout)
                bad = envelope(result)
                self.assertEqual(bad["status"], "error", bad)
                self.assertIn(
                    "DEDIREN_COMMAND_INPUT_INVALID",
                    {diag["code"] for diag in bad["diagnostics"]},
                )

    def test_dediren_diff_reports_field_level_model_changes_deterministically(self) -> None:
        """`source-grounding.md` claims `dediren_diff` reports node / relationship / view
        add / remove / change with field-level `{field, from, to}` on the pinned bundle.
        The diff engine is new in Dediren 2026.07.26; pin the claim to the runtime so a
        bump that regresses it fails here instead of shipping."""
        base = json.loads((FIXTURE / "model.json").read_text(encoding="utf-8"))
        revised = json.loads((FIXTURE / "model.json").read_text(encoding="utf-8"))
        # One of each diff class: remove a node + its relationship, add a node +
        # relationship, change a node label and a relationship label, touch the view.
        revised["nodes"] = [n for n in revised["nodes"] if n["id"] != "orders-api"]
        for node in revised["nodes"]:
            if node["id"] == "client":
                node["label"] = "Client (external)"
        revised["nodes"].append({
            "id": "audit-log", "type": "ApplicationComponent", "label": "Audit Log",
            "properties": {"layer": "Application", "evidence": "architect-owned"},
        })
        revised["relationships"] = [
            r for r in revised["relationships"] if r["id"] != "orders-component-provides-api"
        ]
        for rel in revised["relationships"]:
            if rel["id"] == "orders-service-serves-client":
                rel["label"] = "calls"
        revised["relationships"].append({
            "id": "orders-service-writes-audit", "type": "Serving",
            "source": "orders-service", "target": "audit-log", "label": "writes",
            "properties": {"visible": True},
        })
        view = revised["plugins"]["generic-graph"]["views"][0]
        view["nodes"] = ["client", "orders-component", "orders-service", "audit-log"]
        view["relationships"] = [
            "orders-component-realizes-service", "orders-service-serves-client",
            "orders-service-writes-audit",
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            old_path = temp_path / "old.json"
            new_path = temp_path / "new.json"
            old_path.write_text(json.dumps(base), encoding="utf-8")
            new_path.write_text(json.dumps(revised), encoding="utf-8")

            first = run_dediren("diff", "--old", old_path, "--new", new_path)
            self.assertEqual(first.returncode, 0, first.stderr)
            diff = envelope(first)["data"]
            self.assertEqual(diff["diff_result_schema_version"], "diff-result.schema.v1")
            self.assertEqual({n["id"] for n in diff["nodes"]["added"]}, {"audit-log"})
            self.assertEqual({n["id"] for n in diff["nodes"]["removed"]}, {"orders-api"})
            self.assertEqual(
                [(c["id"], c["changes"][0]["field"], c["changes"][0]["from"], c["changes"][0]["to"])
                 for c in diff["nodes"]["changed"]],
                [("client", "label", "Client Application", "Client (external)")],
            )
            self.assertEqual(
                {r["id"] for r in diff["relationships"]["added"]}, {"orders-service-writes-audit"}
            )
            self.assertEqual(
                {r["id"] for r in diff["relationships"]["removed"]}, {"orders-component-provides-api"}
            )
            self.assertEqual(
                [(c["id"], c["changes"][0]["field"]) for c in diff["relationships"]["changed"]],
                [("orders-service-serves-client", "label")],
            )
            changed_view = diff["views"]["changed"][0]
            self.assertEqual(changed_view["id"], "main")
            self.assertEqual(changed_view["nodes_added"], ["audit-log"])
            self.assertEqual(changed_view["nodes_removed"], ["orders-api"])
            self.assertEqual(changed_view["relationships_added"], ["orders-service-writes-audit"])
            self.assertEqual(changed_view["relationships_removed"], ["orders-component-provides-api"])

            # Determinism: the guide promises byte-identical stdout for identical inputs.
            second = run_dediren("diff", "--old", old_path, "--new", new_path)
            self.assertEqual(second.stdout, first.stdout)

    def test_dediren_verify_gates_stale_build_artifacts_against_provenance(self) -> None:
        """`source-grounding.md` claims `dediren_verify` classifies built artifacts
        against the model's recomputed provenance hash on the pinned bundle — `current`
        (ok, exit 0), `stale` (`DEDIREN_ARTIFACT_STALE`, exit 2, the CI drift gate), and
        `unstamped` (`DEDIREN_ARTIFACT_UNSTAMPED`, warning, exit 0). New in Dediren
        2026.07.27; pin every branch to the runtime."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            model_path = temp_path / "model.json"
            model_path.write_text(
                (FIXTURE / "model.json").read_text(encoding="utf-8"), encoding="utf-8"
            )
            artifacts = temp_path / "artifacts"
            self._build_ok(
                artifacts, "--input", model_path,
                "--render-policy", FIXTURE / "render-policy.json",
                "--oef-policy", FIXTURE / "export-policy.json",
            )

            fresh = run_dediren("verify", "--input", model_path, "--artifacts", artifacts)
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            fresh_env = envelope(fresh)
            self.assertEqual(fresh_env["status"], "ok", fresh_env)
            self.assertEqual(
                fresh_env["data"]["verify_result_schema_version"], "verify-result.schema.v1"
            )
            self.assertTrue(
                all(a["status"] == "current" for a in fresh_env["data"]["artifacts"]),
                fresh_env["data"]["artifacts"],
            )

            # Mutate the source: the built artifacts are now stale, and verify is the gate.
            mutated = json.loads(model_path.read_text(encoding="utf-8"))
            for node in mutated["nodes"]:
                if node["id"] == "client":
                    node["label"] = "Renamed Client"
            model_path.write_text(json.dumps(mutated), encoding="utf-8")

            stale = run_dediren("verify", "--input", model_path, "--artifacts", artifacts)
            self.assertEqual(stale.returncode, 2, stale.stdout)
            stale_env = envelope(stale)
            self.assertEqual(stale_env["status"], "error", stale_env)
            self.assertIn(
                "DEDIREN_ARTIFACT_STALE", {d["code"] for d in stale_env["diagnostics"]}
            )
            self.assertTrue(
                any(a["status"] == "stale" for a in stale_env["data"]["artifacts"]),
                stale_env["data"]["artifacts"],
            )

            # A hand-written, unstamped SVG is a warning, not a gate failure.
            unstamped_dir = temp_path / "hand"
            unstamped_dir.mkdir()
            (unstamped_dir / "hand.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>\n', encoding="utf-8"
            )
            unstamped = run_dediren(
                "verify", "--input", model_path, "--artifacts", unstamped_dir
            )
            self.assertEqual(unstamped.returncode, 0, unstamped.stderr)
            unstamped_env = envelope(unstamped)
            self.assertEqual(unstamped_env["status"], "warning", unstamped_env)
            self.assertIn(
                "DEDIREN_ARTIFACT_UNSTAMPED", {d["code"] for d in unstamped_env["diagnostics"]}
            )

    def test_dediren_status_indexes_workspace_models_and_artifacts(self) -> None:
        """`source-grounding.md` claims `dediren_status` indexes a workspace's source
        models (path + sha256) and stamped artifacts (path + status) on the pinned
        bundle. New in Dediren 2026.07.26; an index, not a gate (exit 0). Pin it."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            model_path = temp_path / "model.json"
            model_path.write_text(
                (FIXTURE / "model.json").read_text(encoding="utf-8"), encoding="utf-8"
            )
            self._build_ok(
                temp_path / "generated", "--input", model_path,
                "--render-policy", FIXTURE / "render-policy.json",
            )

            result = run_dediren("status", "--root", temp_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            status = envelope(result)
            self.assertEqual(status["status"], "ok", status)
            data = status["data"]
            self.assertEqual(data["status_result_schema_version"], "status-result.schema.v1")
            self.assertEqual({m["path"] for m in data["models"]}, {"model.json"})
            self.assertTrue(
                all(re.fullmatch(r"[0-9a-f]{64}", m["sha256"]) for m in data["models"]),
                data["models"],
            )
            self.assertTrue(data["artifacts"], "status should index the built artifacts")
            for artifact in data["artifacts"]:
                self.assertIn("path", artifact)
                self.assertIn(artifact["status"], {"current", "stale", "unstamped"})

    def test_dediren_build_stamps_deterministic_provenance_into_svg(self) -> None:
        """`source-grounding.md` claims every `dediren build` SVG carries a deterministic
        `<metadata id="dediren-provenance">` stamp — compact JSON with `model_sha256` /
        `view_id` / `dediren_version`, never a timestamp — on the pinned bundle, the basis
        `verify` checks. New in Dediren 2026.07.26; pin the shape and the determinism."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            first_out = temp_path / "a"
            second_out = temp_path / "b"
            for out in (first_out, second_out):
                self._build_ok(
                    out, "--input", FIXTURE / "model.json",
                    "--render-policy", FIXTURE / "render-policy.json",
                )
            first_svg = (first_out / "main" / "diagram.svg").read_text(encoding="utf-8")
            second_svg = (second_out / "main" / "diagram.svg").read_text(encoding="utf-8")

            match = re.search(
                r'<metadata id="dediren-provenance">(.*?)</metadata>', first_svg, re.DOTALL
            )
            self.assertIsNotNone(match, "SVG carries no dediren-provenance metadata")
            stamp = json.loads(match.group(1))
            self.assertRegex(stamp["model_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(stamp["view_id"], "main")
            self.assertEqual(stamp["dediren_version"], EXPECTED_DEDIREN_VERSION)
            # The lane policy hash is part of the stamp shape source-grounding claims;
            # assert it explicitly, or a field-rename bump would pass the determinism
            # check below (two identical stamps) while silently dropping it.
            self.assertRegex(stamp["render_policy_sha256"], r"^[0-9a-f]{64}$")

            # No timestamp: identical inputs → byte-identical stamped SVG.
            self.assertEqual(first_svg, second_svg)

    def test_dediren_build_writes_whole_model_interchange_for_oef_and_xmi(self) -> None:
        """`source-grounding.md` claims `dediren build --oef-policy` writes a whole-model
        `model.oef.xml` at the out root (listed in build-result `model_artifacts[]`) and,
        on a UML model, `--xmi-policy` writes `model.uml.xml`, both on the pinned bundle.
        New in Dediren 2026.07.26; pin both interchange legs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            oef_out = temp_path / "oef"
            oef_result = self._build_ok(
                oef_out, "--input", FIXTURE / "model.json",
                "--render-policy", FIXTURE / "render-policy.json",
                "--oef-policy", FIXTURE / "export-policy.json",
            )
            self.assertTrue((oef_out / "model.oef.xml").is_file())
            self.assertIn(
                "model.oef.xml", {a["path"] for a in oef_result["model_artifacts"]}
            )

            xmi_out = temp_path / "xmi"
            xmi_result = self._build_ok(
                xmi_out, "--input", MIXED_FIXTURE / "model-uml.json",
                "--render-policy", MIXED_FIXTURE / "render-policy-uml.json",
                "--xmi-policy", MIXED_FIXTURE / "export-policy-uml.json",
            )
            self.assertTrue((xmi_out / "model.uml.xml").is_file())
            self.assertIn(
                "model.uml.xml", {a["path"] for a in xmi_result["model_artifacts"]}
            )

    def test_mcp_read_only_server_withholds_the_build_tool(self) -> None:
        """`source-grounding.md` claims `dediren mcp --read-only` withholds the
        artifact-writing `dediren_build` and keeps exactly the six read-only tools on the
        pinned bundle. New in Dediren 2026.07.26; assert the exact set, so a read-only
        tool going missing fails here too, not only `dediren_build` leaking in."""
        bundle = release_bundle()
        by_id = mcp_session(bundle, FIXTURE, [
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ], read_only=True)
        tools = {tool["name"] for tool in by_id[2]["result"]["tools"]}
        self.assertEqual(tools, {
            "dediren_validate", "dediren_guide", "dediren_diff",
            "dediren_query", "dediren_verify", "dediren_status",
        })
        self.assertNotIn("dediren_build", tools)

    def test_mcp_server_serves_the_four_product_resource_schemes(self) -> None:
        """`source-grounding.md` claims the `dediren mcp` server serves product-owned MCP
        resources under four URI schemes (`dediren://schema/`, `dediren://fixture/`,
        `dediren://guide/`, and `dediren://diagnostics/catalog`) on the pinned bundle, and
        that a `resources/read` returns non-empty content. New in Dediren 2026.07.26;
        assert scheme presence as a superset — a benign fixture add would shift a hard
        resource count but never drop a scheme — and read one resource."""
        bundle = release_bundle()
        by_id = mcp_session(bundle, FIXTURE, [
            {"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "resources/read",
             "params": {"uri": "dediren://diagnostics/catalog"}},
        ])
        uris = {resource["uri"] for resource in by_id[2]["result"]["resources"]}
        self.assertTrue(any(uri.startswith("dediren://schema/") for uri in uris), uris)
        self.assertTrue(any(uri.startswith("dediren://fixture/") for uri in uris), uris)
        self.assertTrue(any(uri.startswith("dediren://guide/") for uri in uris), uris)
        self.assertIn("dediren://diagnostics/catalog", uris)

        contents = by_id[3]["result"]["contents"]
        self.assertTrue(contents, by_id[3])
        self.assertTrue(contents[0]["text"].strip(), "diagnostics catalog resource is empty")


if __name__ == "__main__":
    unittest.main()
