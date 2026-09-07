import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "souroldgeezer-architecture/skills/architecture-design/references/scripts/review-copy.py"
SPEC = importlib.util.spec_from_file_location("review_copy", SCRIPT)
assert SPEC and SPEC.loader
review_copy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review_copy)


class ArchitectureReviewCopyTest(unittest.TestCase):
    def _workspace(self, root: Path, *, existing_outputs: bool = False) -> None:
        package = root / "pkg"
        package.mkdir()
        (package / "model.json").write_text('{"fragments": ["../shared.json"]}', encoding="utf-8")
        (root / "shared.json").write_text("{}", encoding="utf-8")
        (root / "outside-policy.json").write_text("{}", encoding="utf-8")
        (root / "export-policy.json").write_text("{}", encoding="utf-8")
        (package / "theme.css").write_text("body {}", encoding="utf-8")
        (package / "package.json").write_text(json.dumps({
            "package_schema_version": "package.schema.v1",
            "models": [{"id": "m", "source": "model.json"}],
            "views": [{"id": "v", "model": "m", "render_policy": "../outside-policy.json",
                       "outputs": {"diagram": "../evidence/v.svg", "layout": "generated/v.json"}}],
            "exports": [{"id": "e", "view": "v", "lane": "archimate-oef",
                         "policy": "../export-policy.json", "output": "../evidence/v.oef.xml"}],
        }), encoding="utf-8")
        if existing_outputs:
            (root / "evidence").mkdir()
            (root / "evidence" / "v.svg").write_bytes(b"svg evidence")
            (root / "evidence" / "v.oef.xml").write_bytes(b"oef evidence")

    def _run(self, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *(str(arg) for arg in args)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_prepare_preserves_relative_inputs_existing_outputs_and_absences(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source, existing_outputs=True)
            result = review_copy.prepare(source, "pkg/package.json", base / "copy")
            manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))

            self.assertEqual(manifest["schema"], "architecture-review-copy-v1")
            self.assertEqual(manifest["original_workspace_root"], str(source))
            self.assertEqual(manifest["workspace_root"], str(base / "copy"))
            self.assertEqual(manifest["package"], "pkg/package.json")
            self.assertIsNone(manifest["files"]["pkg/generated/v.json"])
            self.assertIsNone(manifest["files"]["pkg/gallery.html"])
            for relative in (
                "shared.json", "outside-policy.json", "export-policy.json",
                "evidence/v.svg", "evidence/v.oef.xml", "pkg/theme.css",
            ):
                copied = base / "copy" / relative
                original = source / relative
                self.assertEqual(copied.read_bytes(), original.read_bytes())
                self.assertNotEqual(copied.stat().st_ino, original.stat().st_ino)
            verified, code = review_copy.verify_original(Path(result["manifest"]))
            self.assertEqual((verified["status"], code), ("unchanged", 0))

    def test_prepare_rejects_absolute_escape_missing_and_colliding_paths(self) -> None:
        cases = {
            "absolute source": ("models", [{"id": "m", "source": "/tmp/model.json"}]),
            "escaping source": ("models", [{"id": "m", "source": "../../model.json"}]),
            "missing source": ("models", [{"id": "m", "source": "missing.json"}]),
            "package output": (
                "views", [{"id": "v", "render_policy": "../outside-policy.json",
                           "outputs": {"diagram": "package.json"}}],
            ),
            "input ancestor output": (
                "views", [{"id": "v", "render_policy": "../outside-policy.json",
                           "outputs": {"diagram": "model.json/diagram.svg"}}],
            ),
            "output ancestor output": (
                "views", [{"id": "v", "render_policy": "../outside-policy.json",
                           "outputs": {"diagram": "generated", "layout": "generated/v.json"}}],
            ),
        }
        for label, (field, value) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                source = base / "source"
                source.mkdir()
                self._workspace(source)
                package_path = source / "pkg/package.json"
                package = json.loads(package_path.read_text(encoding="utf-8"))
                package[field] = value
                package_path.write_text(json.dumps(package), encoding="utf-8")
                with self.assertRaises(review_copy.CopyError):
                    review_copy.prepare(source, "pkg/package.json", base / "copy")

    def test_prepare_rejects_reserved_path_and_its_ancestors_or_descendants(self) -> None:
        for output in (
            ".architecture-review-copy.json",
            ".architecture-review-copy.json/file",
        ):
            with self.subTest(output=output), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                source = base / "source"
                source.mkdir()
                package = {
                    "package_schema_version": "package.schema.v1",
                    "models": [{"id": "m", "source": "model.json"}],
                    "views": [{"id": "v", "render_policy": "policy.json",
                               "outputs": {"diagram": output}}],
                    "exports": [],
                }
                (source / "model.json").write_text("{}", encoding="utf-8")
                (source / "policy.json").write_text("{}", encoding="utf-8")
                (source / "package.json").write_text(json.dumps(package), encoding="utf-8")
                with self.assertRaisesRegex(review_copy.CopyError, "reserved manifest"):
                    review_copy.prepare(source, "package.json", base / "copy")

    def test_prepare_rejects_nested_fragments_even_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            (source / "shared.json").write_text('{"fragments": []}', encoding="utf-8")
            with self.assertRaisesRegex(review_copy.CopyError, "nested fragments"):
                review_copy.prepare(source, "pkg/package.json", base / "copy")

    def test_prepare_rejects_symlink_components_erased_by_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            (source / "external-model.json").write_text("{}", encoding="utf-8")
            (source / "alias").symlink_to(source / "pkg", target_is_directory=True)
            package_path = source / "pkg/package.json"
            package = json.loads(package_path.read_text(encoding="utf-8"))
            package["models"][0]["source"] = "../alias/../external-model.json"
            package_path.write_text(json.dumps(package), encoding="utf-8")
            with self.assertRaisesRegex(review_copy.CopyError, "traverses a symlink"):
                review_copy.prepare(source, "pkg/package.json", base / "copy")

    def test_prepare_rejects_incidental_file_at_declared_output_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            (source / "pkg/generated").write_text("incidental file", encoding="utf-8")
            with self.assertRaisesRegex(review_copy.CopyError, "copied file/output path collision"):
                review_copy.prepare(source, "pkg/package.json", base / "copy")

    def test_prepare_rejects_symlinked_root_dependency_output_and_destination_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            real = base / "real"
            real.mkdir()
            self._workspace(real, existing_outputs=True)
            linked_root = base / "linked-root"
            linked_root.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(review_copy.CopyError, "symlink"):
                review_copy.prepare(linked_root, "pkg/package.json", base / "copy-root")

            (real / "shared.json").unlink()
            (real / "shared.json").symlink_to(real / "export-policy.json")
            with self.assertRaisesRegex(review_copy.CopyError, "symlink"):
                review_copy.prepare(real, "pkg/package.json", base / "copy-dependency")

            (real / "shared.json").unlink()
            (real / "shared.json").write_text("{}", encoding="utf-8")
            (real / "evidence" / "v.svg").unlink()
            (real / "evidence" / "v.svg").symlink_to(real / "evidence" / "v.oef.xml")
            with self.assertRaisesRegex(review_copy.CopyError, "symlink"):
                review_copy.prepare(real, "pkg/package.json", base / "copy-output")

            symlink_parent = base / "destination-parent"
            symlink_parent.symlink_to(base / "elsewhere", target_is_directory=True)
            with self.assertRaisesRegex(review_copy.CopyError, "symlink"):
                review_copy.prepare(real, "pkg/package.json", symlink_parent / "copy")

    def test_prepare_rejects_absent_output_below_symlinked_ancestor_before_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            (source / "evidence").symlink_to(source / "pkg", target_is_directory=True)
            destination = base / "copy"
            with self.assertRaisesRegex(review_copy.CopyError, "symlink"):
                review_copy.prepare(source, "pkg/package.json", destination)
            self.assertFalse(destination.exists())

    def test_prepare_rejects_nonabsolute_existing_and_overlapping_destinations(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            existing = base / "existing"
            existing.mkdir()
            for workspace, destination in (
                (Path("relative"), base / "copy-a"),
                (source, Path("relative-copy")),
                (source, existing),
                (source, source / "inside"),
                (source, base),
            ):
                with self.subTest(workspace=workspace, destination=destination):
                    with self.assertRaises(review_copy.CopyError):
                        review_copy.prepare(workspace, "pkg/package.json", destination)

    def test_prepare_rejects_malformed_package_model_and_nonregular_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for label, mutation in (
                ("package", lambda source: (source / "pkg/package.json").write_text("[]", encoding="utf-8")),
                ("model", lambda source: (source / "pkg/model.json").write_text("[]", encoding="utf-8")),
                ("output", lambda source: (source / "evidence/v.svg").mkdir(parents=True)),
            ):
                with self.subTest(label=label):
                    source = base / f"source-{label}"
                    source.mkdir()
                    self._workspace(source)
                    mutation(source)
                    result = self._run(
                        "prepare", "--workspace-root", source,
                        "--package", "pkg/package.json", "--destination", base / f"copy-{label}",
                    )
                    self.assertEqual(result.returncode, 2, result)
                    self.assertNotIn("Traceback", result.stderr)

    def test_prepare_detects_source_output_and_inventory_races(self) -> None:
        for label in ("source", "output", "output-symlink", "inventory"):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                source = base / "source"
                source.mkdir()
                self._workspace(source)
                real_copy = review_copy.shutil.copyfile
                triggered = False

                def racing_copy(src: Path, dst: Path) -> None:
                    nonlocal triggered
                    real_copy(src, dst)
                    if triggered:
                        return
                    triggered = True
                    if label == "source":
                        (source / "shared.json").write_text('{"changed": true}', encoding="utf-8")
                    elif label == "output":
                        (source / "evidence").mkdir()
                        (source / "evidence/v.svg").write_text("appeared", encoding="utf-8")
                    elif label == "output-symlink":
                        (source / "evidence").symlink_to(
                            source / "pkg", target_is_directory=True
                        )
                    else:
                        (source / "pkg/appeared.css").write_text("body {}", encoding="utf-8")

                with mock.patch.object(review_copy.shutil, "copyfile", side_effect=racing_copy):
                    with self.assertRaisesRegex(review_copy.CopyError, "changed during copy"):
                        review_copy.prepare(source, "pkg/package.json", base / "copy")

    def test_prepare_binds_the_parsed_dependency_graph_before_creating_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            real_read = review_copy.read_json_snapshot

            def racing_read(path: Path, rel: Path, label: str):
                result = real_read(path, rel, label)
                if rel == Path("pkg/model.json"):
                    path.write_text('{"fragments": []}', encoding="utf-8")
                return result

            destination = base / "copy"
            with mock.patch.object(review_copy, "read_json_snapshot", side_effect=racing_read):
                with self.assertRaisesRegex(review_copy.CopyError, "parsed input changed before copy"):
                    review_copy.prepare(source, "pkg/package.json", destination)
            self.assertFalse(destination.exists())

    def test_prepare_binds_package_inventory_before_creating_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            real_read = review_copy.read_json_snapshot

            def racing_read(path: Path, rel: Path, label: str):
                result = real_read(path, rel, label)
                if rel == Path("pkg/model.json"):
                    (source / "pkg/appeared.css").write_text("body {}", encoding="utf-8")
                return result

            destination = base / "copy"
            with mock.patch.object(review_copy, "read_json_snapshot", side_effect=racing_read):
                with self.assertRaisesRegex(review_copy.CopyError, "inventory changed before copy"):
                    review_copy.prepare(source, "pkg/package.json", destination)
            self.assertFalse(destination.exists())

    def test_verify_reports_changed_missing_added_and_absent_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            result = review_copy.prepare(source, "pkg/package.json", base / "copy")
            manifest_path = Path(result["manifest"])

            (source / "shared.json").write_text('{"changed": true}', encoding="utf-8")
            (source / "outside-policy.json").unlink()
            (source / "pkg/new-theme.css").write_text("body {}", encoding="utf-8")
            (source / "pkg/generated/v.json").mkdir(parents=True)
            verified, code = review_copy.verify_original(manifest_path)
            self.assertEqual((verified["status"], code), ("changed", 1))
            self.assertEqual(verified["changed_count"], 4)
            self.assertEqual(set(verified["changed_paths"]), {
                "shared.json", "outside-policy.json", "pkg/new-theme.css", "pkg/generated/v.json",
            })

    def test_verify_detects_symlinked_external_ancestor_and_absent_output_ancestor(self) -> None:
        for target in ("existing", "absent"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                source = base / "source"
                source.mkdir()
                self._workspace(source, existing_outputs=(target == "existing"))
                result = review_copy.prepare(source, "pkg/package.json", base / "copy")
                if target == "existing":
                    original = source / "evidence"
                    moved = source / "same-evidence"
                    original.rename(moved)
                    original.symlink_to(moved, target_is_directory=True)
                    expected_path = "evidence/v.svg"
                else:
                    evidence = source / "evidence"
                    evidence.symlink_to(source / "pkg", target_is_directory=True)
                    expected_path = "evidence/v.svg"
                verified, code = review_copy.verify_original(Path(result["manifest"]))
                self.assertEqual(code, 1)
                self.assertIn(expected_path, verified["changed_paths"])

    def test_verify_treats_missing_or_corrupt_package_as_change(self) -> None:
        for action in ("missing", "corrupt"):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                source = base / "source"
                source.mkdir()
                self._workspace(source)
                result = review_copy.prepare(source, "pkg/package.json", base / "copy")
                package = source / "pkg/package.json"
                package.unlink() if action == "missing" else package.write_text("not json", encoding="utf-8")
                proc = self._run("verify-original", "--manifest", result["manifest"])
                self.assertEqual(proc.returncode, 1, proc)
                self.assertEqual(json.loads(proc.stdout)["status"], "changed")
                self.assertNotIn("Traceback", proc.stderr)

    def test_verify_caps_changed_paths_but_reports_full_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            result = review_copy.prepare(source, "pkg/package.json", base / "copy")
            for index in range(25):
                (source / "pkg" / f"new-{index:02}.txt").write_text("x", encoding="utf-8")
            verified, code = review_copy.verify_original(Path(result["manifest"]))
            self.assertEqual(code, 1)
            self.assertEqual(verified["changed_count"], 25)
            self.assertEqual(len(verified["changed_paths"]), 20)

    def test_verify_rejects_relative_symlinked_and_malformed_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            result = review_copy.prepare(source, "pkg/package.json", base / "copy")
            manifest = Path(result["manifest"])

            self.assertEqual(self._run("verify-original", "--manifest", manifest.name).returncode, 2)
            link = base / "manifest-link"
            link.symlink_to(manifest)
            self.assertEqual(self._run("verify-original", "--manifest", link).returncode, 2)
            manifest.write_text("[]", encoding="utf-8")
            malformed = self._run("verify-original", "--manifest", manifest)
            self.assertEqual(malformed.returncode, 2)
            self.assertNotIn("Traceback", malformed.stderr)


if __name__ == "__main__":
    unittest.main()
