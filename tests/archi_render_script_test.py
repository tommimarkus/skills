import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHI_RENDER = REPO_ROOT / "souroldgeezer-design/skills/architecture-design/references/scripts/archi-render.sh"
DEFAULT_VALIDATE_SCRIPT = (
    REPO_ROOT / "souroldgeezer-design/skills/architecture-design/references/scripts/validate-model.ajs"
)
FIXTURE = (
    REPO_ROOT / "souroldgeezer-design/skills/architecture-design/references/fixtures/application-cooperation.oef.xml"
)


def write_fake_archi(
    path: Path,
    *,
    validation_output: str | None = "ARCHI_VALIDATE_MODEL: OK invalid=0 warnings=0",
) -> None:
    validation_block = ""
    if validation_output is not None:
        validation_block = textwrap.dedent(
            f"""\
            if [[ -n "${{ARCHI_VALIDATE_MODEL_OUTPUT:-}}" ]]; then
              printf '%s\\n' "{validation_output}" > "$ARCHI_VALIDATE_MODEL_OUTPUT"
            else
              printf '%s\\n' "{validation_output}"
            fi
            """
        )

    path.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            printf '%s\\n' "$@" > "$FAKE_ARCHI_ARGS_FILE"

            report_dir=""
            while [[ $# -gt 0 ]]; do
              case "$1" in
                --html.createReport)
                  shift
                  report_dir="$1"
                  ;;
              esac
              shift || true
            done

            {validation_block}

            mkdir -p "$report_dir/images"
            printf 'fake png\\n' > "$report_dir/images/view.png"
            """
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def run_archi_render(fake_archi: Path, args_file: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DISPLAY"] = env.get("DISPLAY", ":99")
    env["FAKE_ARCHI_ARGS_FILE"] = str(args_file)

    return subprocess.run(
        [
            str(ARCHI_RENDER),
            "--quiet",
            "--archi-bin",
            str(fake_archi),
            "--cache-root",
            str(fake_archi.parent / "cache"),
            "--output-root",
            str(fake_archi.parent / "views"),
            str(FIXTURE),
        ],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )


class ArchiRenderScriptTest(unittest.TestCase):
    def test_runs_validate_model_script_after_oef_import_and_before_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_archi = tmp_path / "Archi"
            args_file = tmp_path / "archi.args"
            write_fake_archi(fake_archi)

            result = run_archi_render(fake_archi, args_file)

            self.assertEqual(result.returncode, 0, result.stderr)
            args = args_file.read_text(encoding="utf-8").splitlines()
            self.assertIn("--xmlexchange.import", args)
            self.assertIn("--script.runScript", args)
            self.assertIn("--html.createReport", args)

            import_index = args.index("--xmlexchange.import")
            script_index = args.index("--script.runScript")
            report_index = args.index("--html.createReport")

            self.assertLess(import_index, script_index)
            self.assertLess(script_index, report_index)
            self.assertEqual(str(DEFAULT_VALIDATE_SCRIPT), args[script_index + 1])

    def test_validation_findings_make_render_fail_after_archi_load_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_archi = tmp_path / "Archi"
            args_file = tmp_path / "archi.args"
            write_fake_archi(fake_archi, validation_output="ARCHI_VALIDATE_MODEL: INVALID invalid relationship")

            result = run_archi_render(fake_archi, args_file)

            self.assertEqual(result.returncode, 5, result.stderr)
            self.assertIn("Validate Model reported finding(s)", result.stderr)

    def test_validation_warnings_are_reported_without_failing_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_archi = tmp_path / "Archi"
            args_file = tmp_path / "archi.args"
            write_fake_archi(fake_archi, validation_output="ARCHI_VALIDATE_MODEL: WARN unused element")

            result = run_archi_render(fake_archi, args_file)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Validate Model reported warning(s)", result.stderr)

    def test_missing_validation_output_fails_even_when_archi_renders_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_archi = tmp_path / "Archi"
            args_file = tmp_path / "archi.args"
            write_fake_archi(fake_archi, validation_output=None)

            result = run_archi_render(fake_archi, args_file)

            self.assertEqual(result.returncode, 6, result.stderr)
            self.assertIn("Validate Model produced no machine-readable output", result.stderr)


if __name__ == "__main__":
    unittest.main()
