"""Coverage for the architecture-design plan/map build helper.

The skill drives dediren through the bundled MCP server's `dediren_build` tool; this
helper owns the two deterministic halves the tool does not — planning the tool calls
and mapping their `<out>/<view-id>/` output into the canonical `project.json` paths.
The pure tests (normalize, plan, envelope unwrap, map) always run. The end-to-end map
smoke drives the real pinned runtime to populate a staging dir and is gated behind
DEDIREN_RELEASE_SMOKE=1, like the release suite beside it.
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
RELEASE_SCRIPT = SKILL / "references" / "scripts" / "dediren-release.sh"
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
        # how many dediren_build calls the render lane needs.
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


class PlanTest(unittest.TestCase):
    """`plan` emits exactly the dediren_build MCP calls a package needs."""

    def setUp(self):
        self.module = load_module()

    def _plan(self, name, views_filter=None, no_export=False):
        pkg = FIXTURES / name
        models, views, exports = self.module.normalize(
            json.loads((pkg / "project.json").read_text(encoding="utf-8"))
        )
        views, exports = self.module.select(views, exports, views_filter, no_export)
        return self.module.plan(pkg, models, views, exports)

    def test_v1_plan_is_one_render_call_and_one_export_call(self):
        calls = self._plan("basic")["calls"]

        self.assertEqual([c["tool"] for c in calls], ["dediren_build", "dediren_build"])
        render, export = calls
        # Every call writes into the one staging dir; each view lands under <out>/<view>/.
        self.assertTrue(all(c["arguments"]["out"].endswith(self.module.STAGING_DIR) for c in calls))
        self.assertEqual(render["arguments"]["views"], ["main"])
        self.assertTrue(render["arguments"]["source"].endswith("model.json"))
        self.assertTrue(render["arguments"]["render_policy"].endswith("render-policy.json"))
        self.assertEqual(render["arguments"]["emit"], list(self.module.EMIT_KINDS))
        self.assertNotIn("oef_policy", render["arguments"])
        # Export is a single-view call so the OEF identity fields are its own.
        self.assertEqual(export["arguments"]["views"], ["main"])
        self.assertTrue(export["arguments"]["oef_policy"].endswith("export-policy.json"))
        self.assertNotIn("render_policy", export["arguments"])

    def test_v2_plan_splits_render_by_policy_and_scopes_each_export(self):
        calls = self._plan("mixed")["calls"]
        render = [c["arguments"] for c in calls if "render_policy" in c["arguments"]]
        oef = [c["arguments"] for c in calls if "oef_policy" in c["arguments"]]
        xmi = [c["arguments"] for c in calls if "xmi_policy" in c["arguments"]]

        # Distinct notations => distinct render policies => one render call each.
        self.assertEqual(
            sorted(tuple(a["views"]) for a in render), [("app-cooperation",), ("domain-class",)]
        )
        self.assertEqual([a["views"] for a in oef], [["app-cooperation"]])
        self.assertEqual([a["views"] for a in xmi], [["domain-class"]])

    def test_views_filter_scopes_plan_and_drops_the_other_export(self):
        calls = self._plan("mixed", views_filter="domain-class")["calls"]
        views = {tuple(c["arguments"]["views"]) for c in calls}

        self.assertEqual(views, {("domain-class",)})
        self.assertTrue(any("xmi_policy" in c["arguments"] for c in calls))
        self.assertFalse(any("oef_policy" in c["arguments"] for c in calls))

    def test_no_export_drops_every_export_call(self):
        calls = self._plan("basic", no_export=True)["calls"]

        self.assertEqual(len(calls), 1)
        self.assertIn("render_policy", calls[0]["arguments"])

    def test_unknown_view_filter_is_refused(self):
        with self.assertRaises(self.module.PackageError):
            self._plan("basic", views_filter="ghost")


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


class MapTest(unittest.TestCase):
    """`map` drains a staging dir into the canonical project.json paths."""

    def setUp(self):
        self.module = load_module()

    def _stage(self, name):
        tmp = tempfile.mkdtemp(prefix=f"pkg-{name}-")
        self.addCleanup(shutil.rmtree, tmp, True)
        pkg = Path(tmp) / name
        shutil.copytree(FIXTURES / name, pkg)
        return pkg

    def _write_view_stage(self, pkg, view_id, *, oef=False, xmi=False):
        stage = pkg / self.module.STAGING_DIR / view_id
        stage.mkdir(parents=True)
        (stage / "diagram.svg").write_text("<svg></svg>", encoding="utf-8")
        for kind in ("render-metadata", "layout-result"):
            (stage / f"{kind}.json").write_text(
                json.dumps({"status": "ok", "data": {"nodes": {}, "kind": kind}}), encoding="utf-8"
            )
        if oef:
            (stage / "oef.xml").write_text("<model/>", encoding="utf-8")
        if xmi:
            (stage / "xmi.xml").write_text("<xmi/>", encoding="utf-8")

    def _run_map(self, pkg):
        return self.module.main(["map", str(pkg), "--json"])

    def test_map_moves_artifacts_and_unwraps_emitted_envelopes(self):
        pkg = self._stage("basic")
        self._write_view_stage(pkg, "main", oef=True)

        rc = self._run_map(pkg)

        self.assertEqual(rc, 0)
        self.assertTrue((pkg / "generated/svg/main.svg").is_file())
        self.assertTrue((pkg / "generated/export/basic.oef.xml").is_file())
        metadata = json.loads((pkg / "generated/render-metadata/main.json").read_text())
        # The emitted envelope's .data payload is stored, not the envelope itself.
        self.assertNotIn("data", metadata)
        self.assertNotIn("envelope_schema_version", metadata)
        self.assertEqual(metadata["kind"], "render-metadata")
        # Staging is drained after a successful map.
        self.assertFalse((pkg / self.module.STAGING_DIR).exists())

    def test_map_reports_error_and_exit_1_for_a_missing_declared_artifact(self):
        pkg = self._stage("basic")
        # Stage the render lane but not the export lane the package declares.
        self._write_view_stage(pkg, "main", oef=False)

        rc = self._run_map(pkg)

        self.assertEqual(rc, 1)
        # The render view still materialized; only the export is the error.
        self.assertTrue((pkg / "generated/svg/main.svg").is_file())
        self.assertFalse((pkg / "generated/export/basic.oef.xml").exists())

    def test_map_without_a_staging_dir_is_a_usage_error(self):
        pkg = self._stage("basic")

        rc = self._run_map(pkg)

        self.assertEqual(rc, 2)


class MapSmokeTest(unittest.TestCase):
    """Drains a staging dir populated by the real pinned runtime (gated)."""

    def setUp(self):
        self.module = load_module()

    def _resolve_dediren(self):
        proc = subprocess.run(
            ["bash", str(RELEASE_SCRIPT), "--ensure"],
            check=False, text=True, capture_output=True,
        )
        if proc.returncode != 0:
            raise AssertionError(f"resolver failed: {proc.stderr}")
        return proc.stdout.strip()

    def test_real_build_output_maps_to_canonical_paths(self):
        require_smoke()
        dediren = self._resolve_dediren()
        tmp = tempfile.mkdtemp(prefix="pkg-mapsmoke-")
        self.addCleanup(shutil.rmtree, tmp, True)
        pkg = Path(tmp) / "basic"
        shutil.copytree(FIXTURES / "basic", pkg)

        # The MCP dediren_build tool writes <out>/<view>/diagram.svg identically to the
        # CLI build; stage via the CLI (same engine) so this test exercises map, not the
        # MCP transport (which the release suite's mcp smoke covers).
        staging = pkg / self.module.STAGING_DIR
        env = os.environ.copy()
        env.setdefault("DEDIREN_SCHEMA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "dediren-schemas"))
        subprocess.run(
            [dediren, "build", "--input", str(pkg / "model.json"), "--out", str(staging),
             "--views", "main", "--render-policy", str(pkg / "render-policy.json"),
             "--emit", "render-metadata,layout-result"],
            check=True, text=True, capture_output=True, env=env,
        )
        subprocess.run(
            [dediren, "build", "--input", str(pkg / "model.json"), "--out", str(staging),
             "--views", "main", "--oef-policy", str(pkg / "export-policy.json")],
            check=True, text=True, capture_output=True, env=env,
        )

        rc = self.module.main(["map", str(pkg), "--json"])

        self.assertEqual(rc, 0)
        for declared in (
            "generated/svg/main.svg",
            "generated/render-metadata/main.json",
            "generated/layout/main.json",
            "generated/export/basic.oef.xml",
        ):
            with self.subTest(declared=declared):
                self.assertGreater((pkg / declared).stat().st_size, 0, declared)


if __name__ == "__main__":
    unittest.main()
