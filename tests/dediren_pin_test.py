"""Tests for scripts/dediren_pin.py, driven in-process with only urlopen stubbed."""
import contextlib
import io
import json
import unittest
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tests.surface_test_lib import REPO_ROOT, load_script_module

pin = load_script_module("dediren_pin_under_test", REPO_ROOT / "scripts" / "dediren_pin.py")

PIN = "2026.10.0"
FLOOR = "2026.07.28"
RUNTIME_TEXT = (
    '"""runtime fixture"""\n'
    'DEDIREN_REPO_DEFAULT = "tommimarkus/dediren"\n'
    f'DEDIREN_VERSION_DEFAULT = "{PIN}"\n'
    f'DEDIREN_VERSION_FLOOR = "{FLOOR}"\n'
    'OTHER = "2026.10.0"\n'
)


def bundle_assets(version: str) -> list[str]:
    return [f"dediren-agent-bundle-{version}.tar.gz", "SHA256SUMS"]


class FakeResponse:
    def __init__(self, tag: str, assets: list[str]) -> None:
        self._body = json.dumps({"tag_name": tag, "assets": [{"name": n} for n in assets]}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._body


def forbidden_urlopen(*args, **kwargs):
    raise AssertionError("the network must not be reached before this refusal")


class DedirenPinTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.module = self.root / pin.RUNTIME_REL
        self.module.parent.mkdir(parents=True)
        self.module.write_text(RUNTIME_TEXT, encoding="utf-8")

    def run_pin(self, *argv: str, urlopen=None) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        stub = urlopen or forbidden_urlopen
        with mock.patch.object(pin.urllib.request, "urlopen", stub), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = pin.main(["--repo-root", str(self.root), *argv])
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    @staticmethod
    def release(tag: str, assets: list[str]):
        return lambda *a, **k: FakeResponse(tag, assets)

    def assert_module_unchanged(self) -> None:
        self.assertEqual(self.module.read_bytes(), RUNTIME_TEXT.encode())

    def test_check_text_behind(self) -> None:
        code, out, _ = self.run_pin("--check", urlopen=self.release("v2026.11.1", []))
        self.assertEqual(code, 0)
        self.assertIn(f"pin:    {PIN}", out)
        self.assertIn(f"floor:  {FLOOR}", out)
        self.assertIn("latest: 2026.11.1", out)
        self.assertIn("status: behind", out)
        self.assertIn("Dediren upstream release adoption", out)

    def test_check_text_current(self) -> None:
        code, out, _ = self.run_pin(urlopen=self.release(f"v{PIN}", []))
        self.assertEqual(code, 0)
        self.assertIn("status: current", out)
        self.assertNotIn("adopt via", out)

    def test_check_json_behind_and_current(self) -> None:
        _, out, _ = self.run_pin("--format", "json", urlopen=self.release("v2026.11.1", []))
        report = json.loads(out)
        self.assertEqual((report["pin"], report["floor"], report["latest"], report["behind"]),
                         (PIN, FLOOR, "2026.11.1", True))
        self.assertEqual(report["module"], pin.RUNTIME_REL)
        _, out, _ = self.run_pin("--check", "--format", "json", urlopen=self.release(f"v{PIN}", []))
        self.assertFalse(json.loads(out)["behind"])

    def test_set_refuses_before_network(self) -> None:
        cases = {"not-a-version": "not a CalVer", "2026.06.0": "below the supported floor"}
        for requested, fragment in cases.items():
            with self.subTest(requested=requested):
                code, _, err = self.run_pin("--set", requested)
                self.assertEqual(code, pin.EXIT_REFUSED)
                self.assertIn(fragment, err)
                self.assert_module_unchanged()

    def test_set_already_pinned_makes_no_network_call(self) -> None:
        code, out, _ = self.run_pin("--set", f"v{PIN}")
        self.assertEqual(code, 0)
        self.assertIn(f"no change: the pin is already {PIN}", out)
        self.assert_module_unchanged()

    def test_set_and_latest_refuse_release_missing_assets(self) -> None:
        version = "2026.11.1"
        incomplete = {
            "no bundle": ["SHA256SUMS"],
            "no sums": [f"dediren-agent-bundle-{version}.tar.gz"],
        }
        for label, assets in incomplete.items():
            for argv in (("--set", version), ("--latest",)):
                with self.subTest(case=label, argv=argv[0]):
                    code, _, err = self.run_pin(*argv, urlopen=self.release(f"v{version}", assets))
                    self.assertEqual(code, pin.EXIT_REFUSED)
                    self.assertIn("does not publish", err)
                    self.assert_module_unchanged()

    def test_dry_run_reports_without_writing(self) -> None:
        stub = self.release("v2026.11.1", bundle_assets("2026.11.1"))
        for argv in (("--set", "2026.11.1"), ("--latest",)):
            with self.subTest(argv=argv[0]):
                code, out, _ = self.run_pin(*argv, "--dry-run", urlopen=stub)
                self.assertEqual(code, 0)
                self.assertIn(f"would move the pin {PIN} -> 2026.11.1", out)
                self.assert_module_unchanged()

    def test_set_rewrites_only_the_pin_line(self) -> None:
        version = "2026.11.1"
        code, out, _ = self.run_pin("--set", f"v{version}",
                                    urlopen=self.release(f"v{version}", bundle_assets(version)))
        self.assertEqual(code, 0)
        self.assertIn(f"moved the pin {PIN} -> {version}", out)
        self.assertEqual(self.module.read_text(encoding="utf-8"),
                         RUNTIME_TEXT.replace(f'DEDIREN_VERSION_DEFAULT = "{PIN}"',
                                              f'DEDIREN_VERSION_DEFAULT = "{version}"'))

    def test_http_error_exits_upstream(self) -> None:
        def fail(*args, **kwargs):
            raise urllib.error.HTTPError("u", 404, "Not Found", {}, None)
        for argv in (("--check",), ("--set", "2026.11.1")):
            with self.subTest(argv=argv[0]):
                code, _, err = self.run_pin(*argv, urlopen=fail)
                self.assertEqual(code, pin.EXIT_UPSTREAM)
                self.assertIn("HTTP 404", err)
        self.assert_module_unchanged()

    def test_non_calver_tag_exits_upstream(self) -> None:
        code, _, err = self.run_pin("--check", urlopen=self.release("nightly", []))
        self.assertEqual(code, pin.EXIT_UPSTREAM)
        self.assertIn("non-CalVer tag", err)

    def test_dry_run_without_set_is_a_usage_error(self) -> None:
        code, _, err = self.run_pin("--dry-run")
        self.assertEqual(code, 2)
        self.assertIn("--dry-run applies to --set / --latest", err)

    def test_missing_runtime_module_exits_refused(self) -> None:
        self.module.unlink()
        code, _, err = self.run_pin("--check")
        self.assertEqual(code, pin.EXIT_REFUSED)
        self.assertIn("is that the repo root?", err)


if __name__ == "__main__":
    unittest.main()
