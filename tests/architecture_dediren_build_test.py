"""Coverage for the architecture-design one-shot build script.

The pure tests (project.json normalization, envelope unwrapping, refusal cases) always
run. The end-to-end tests drive the real pinned dediren runtime and are gated behind
DEDIREN_RELEASE_SMOKE=1, like the release suite beside them.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "souroldgeezer-architecture" / "skills" / "architecture-design"
SCRIPT = SKILL / "references" / "scripts" / "dediren-build.py"
FIXTURES = SKILL / "references" / "fixtures" / "dediren"


def load_module():
    spec = importlib.util.spec_from_file_location("dediren_build", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_smoke():
    if os.environ.get("DEDIREN_RELEASE_SMOKE") != "1":
        raise unittest.SkipTest("set DEDIREN_RELEASE_SMOKE=1 to run the pinned dediren runtime")


class NormalizeTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_v1_project_folds_into_a_single_default_model(self):
        project = json.loads((FIXTURES / "basic" / "project.json").read_text(encoding="utf-8"))

        models, views, exports = self.module.normalize(project)

        self.assertEqual(list(models.values()), ["model.json"])
        self.assertEqual([view["id"] for view in views], ["main"])
        self.assertEqual(views[0]["render_out"], "generated/svg/main.svg")
        self.assertEqual(views[0]["metadata_out"], "generated/render-metadata/main.json")
        self.assertEqual(views[0]["layout_out"], "generated/layout/main.json")
        # v1 names no view on its single export; a one-view package resolves it.
        self.assertEqual([(e["plugin"], e["view_id"]) for e in exports], [("archimate-oef", "main")])

    def test_v2_project_keeps_each_view_bound_to_its_own_model(self):
        project = json.loads((FIXTURES / "mixed" / "project.json").read_text(encoding="utf-8"))

        models, views, exports = self.module.normalize(project)

        self.assertEqual(models, {"arch": "model.json", "uml": "model-uml.json"})
        self.assertEqual(
            {view["id"]: view["model_id"] for view in views},
            {"app-cooperation": "arch", "domain-class": "uml"},
        )
        # Distinct render policies per notation must survive normalization: they decide
        # how many build invocations the render lane needs.
        self.assertEqual(
            {view["id"]: view["render_policy"] for view in views},
            {"app-cooperation": "render-policy.json", "domain-class": "render-policy-uml.json"},
        )
        self.assertEqual(
            [(e["plugin"], e["view_id"], e["model_id"]) for e in exports],
            [("archimate-oef", "app-cooperation", "arch"), ("uml-xmi", "domain-class", "uml")],
        )

    def test_v1_export_naming_no_view_in_a_multi_view_package_is_refused(self):
        """Guessing which view a v1 export belongs to would silently export the wrong one."""
        project = json.loads((FIXTURES / "basic" / "project.json").read_text(encoding="utf-8"))
        second = json.loads(json.dumps(project["views"][0]))
        second["id"] = "secondary"
        project["views"].append(second)

        with self.assertRaises(self.module.PackageError) as caught:
            self.module.normalize(project)

        self.assertIn("names no 'view'", str(caught.exception))

    def test_export_with_unsupported_plugin_is_refused(self):
        project = json.loads((FIXTURES / "basic" / "project.json").read_text(encoding="utf-8"))
        project["export"]["plugin"] = "not-a-lane"

        with self.assertRaises(self.module.PackageError):
            self.module.normalize(project)

    def test_view_naming_unknown_model_is_refused(self):
        project = json.loads((FIXTURES / "mixed" / "project.json").read_text(encoding="utf-8"))
        project["views"][0]["model"] = "ghost"

        with self.assertRaises(self.module.PackageError):
            self.module.normalize(project)


class EnvelopeTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_stage_envelope_is_unwrapped_to_its_data_payload(self):
        """--emit writes generic envelopes; the package stores the .data payload."""
        with tempfile.TemporaryDirectory() as tmp:
            envelope = Path(tmp) / "render-metadata.json"
            envelope.write_text(
                json.dumps(
                    {
                        "envelope_schema_version": "envelope.schema.v1",
                        "status": "ok",
                        "data": {"nodes": {"a": {}}, "edges": {}},
                        "diagnostics": [],
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(self.module.payload_of(envelope), {"nodes": {"a": {}}, "edges": {}})

    def test_a_document_without_data_is_not_treated_as_an_envelope(self):
        """Build's own stdout has no .data; writing it as a payload would corrupt the package."""
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "build-result.json"
            document.write_text(
                json.dumps({"build_result_schema_version": "build-result.schema.v1", "views": []}),
                encoding="utf-8",
            )

            with self.assertRaises(self.module.PackageError):
                self.module.payload_of(document)


class BuildEndToEndTest(unittest.TestCase):
    """Drives the real pinned runtime over the shipped fixture packages."""

    def run_build(self, package, *args):
        env = os.environ.copy()
        # The OEF/XMI lanes fetch their XSDs into a cache dir; keep it inside the
        # sandbox-writable temp tree rather than the user's home cache.
        env.setdefault("DEDIREN_SCHEMA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "dediren-schemas"))
        return subprocess.run(
            ["python3", str(SCRIPT), str(package), *args],
            check=False,
            text=True,
            capture_output=True,
            env=env,
        )

    def stage(self, name):
        tmp = tempfile.mkdtemp(prefix=f"pkg-{name}-")
        self.addCleanup(shutil.rmtree, tmp, True)
        package = Path(tmp) / name
        shutil.copytree(FIXTURES / name, package)
        return package

    def test_v1_package_builds_every_declared_artifact_in_one_pass(self):
        require_smoke()
        package = self.stage("basic")

        result = self.run_build(package, "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["status"], "ok")
        self.assertEqual([view["status"] for view in summary["views"]], ["ok"])
        self.assertEqual([e["status"] for e in summary["exports"]], ["ok"])

        for declared in [
            "generated/svg/main.svg",
            "generated/render-metadata/main.json",
            "generated/layout/main.json",
            "generated/export/basic.oef.xml",
        ]:
            with self.subTest(declared=declared):
                artifact = package / declared
                self.assertTrue(artifact.is_file(), declared)
                self.assertGreater(artifact.stat().st_size, 0, declared)

    def test_emitted_stage_artifacts_land_unwrapped_not_as_envelopes(self):
        require_smoke()
        package = self.stage("basic")

        self.assertEqual(self.run_build(package, "--no-export").returncode, 0)

        metadata = json.loads((package / "generated/render-metadata/main.json").read_text())
        self.assertNotIn("envelope_schema_version", metadata)
        self.assertNotIn("data", metadata)
        self.assertIn("nodes", metadata)
        self.assertEqual(metadata["semantic_profile"], "archimate")

        layout = json.loads((package / "generated/layout/main.json").read_text())
        self.assertNotIn("envelope_schema_version", layout)
        self.assertIn("nodes", layout)

    def test_v2_multimodel_package_routes_each_view_to_its_own_notation(self):
        require_smoke()
        package = self.stage("mixed")

        result = self.run_build(package, "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(
            {view["view"]: view["status"] for view in summary["views"]},
            {"app-cooperation": "ok", "domain-class": "ok"},
        )

        profiles = {
            view: json.loads((package / f"generated/render-metadata/{view}.json").read_text())[
                "semantic_profile"
            ]
            for view in ("app-cooperation", "domain-class")
        }
        self.assertEqual(profiles, {"app-cooperation": "archimate", "domain-class": "uml"})

        for declared in ("generated/export/mixed.oef.xml", "generated/export/mixed.uml.xmi"):
            with self.subTest(declared=declared):
                self.assertGreater((package / declared).stat().st_size, 0)

    def test_views_flag_scopes_the_build_and_its_exports(self):
        require_smoke()
        package = self.stage("mixed")

        result = self.run_build(package, "--views", "domain-class", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual([view["view"] for view in summary["views"]], ["domain-class"])
        # The OEF export belongs to the view we did not build, so it must not run.
        self.assertEqual([e["export"] for e in summary["exports"]], ["uml-xmi"])
        self.assertFalse((package / "generated/svg/app-cooperation.svg").exists())

    def test_unknown_view_is_a_usage_error(self):
        require_smoke()
        package = self.stage("basic")

        result = self.run_build(package, "--views", "ghost")

        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown view", result.stderr)


if __name__ == "__main__":
    unittest.main()
