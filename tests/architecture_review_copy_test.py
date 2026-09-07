import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "souroldgeezer-architecture/skills/architecture-design/references/scripts/review-copy.py"
SPEC = importlib.util.spec_from_file_location("review_copy", SCRIPT)
assert SPEC and SPEC.loader
review_copy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review_copy)


class ArchitectureReviewCopyTest(unittest.TestCase):
    def _workspace(self, root: Path) -> None:
        package = root / "pkg"
        package.mkdir()
        (package / "model.json").write_text('{"fragments": ["../shared.json"]}', encoding="utf-8")
        (root / "shared.json").write_text("{}", encoding="utf-8")
        (root / "outside-policy.json").write_text("{}", encoding="utf-8")
        (package / "package.json").write_text(json.dumps({
            "models": [{"id": "m", "source": "model.json"}],
            "views": [{"id": "v", "model": "m", "render_policy": "../outside-policy.json",
                       "outputs": {"diagram": "generated/v.svg", "layout": "generated/v.json"}}],
            "exports": [],
        }), encoding="utf-8")

    def test_prepare_preserves_relative_inputs_and_missing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            result = review_copy.prepare(source, "pkg/package.json", base / "copy")
            manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], "architecture-review-copy-v1")
            self.assertIsNone(manifest["files"]["pkg/generated/v.svg"])
            self.assertTrue((base / "copy" / "shared.json").is_file())
            verified, code = review_copy.verify_original(Path(result["manifest"]))
            self.assertEqual((verified["status"], code), ("unchanged", 0))

    def test_rejects_symlink_and_detects_inventory_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            self._workspace(source)
            result = review_copy.prepare(source, "pkg/package.json", base / "copy")
            (source / "pkg" / "new-theme.css").write_text("body {}", encoding="utf-8")
            verified, code = review_copy.verify_original(Path(result["manifest"]))
            self.assertEqual(code, 1)
            self.assertIn("pkg/new-theme.css", verified["changed_paths"])
            (source / "pkg" / "model.json").unlink()
            (source / "pkg" / "model.json").symlink_to(source / "shared.json")
            with self.assertRaises(review_copy.CopyError):
                review_copy.prepare(source, "pkg/package.json", base / "copy-two")


if __name__ == "__main__":
    unittest.main()
