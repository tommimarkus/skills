"""Shared helpers for the repo's surface tests (paths, file reads, per-stack packs)."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def read_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


def compact(text: str) -> str:
    return " ".join(text.split())


def eval_ids(path: str) -> set[str]:
    """The set of case ids in an evals JSONL corpus. Shared by the synthetic
    eval-coverage checks here and in the per-stack surface tests."""
    return {record["id"] for record in read_jsonl(path)}


def load_script_module(name: str, path: Path):
    """Dynamically load a scripts/*.py file as an importable module, registering it
    in sys.modules under `name`. Shared by the tests that exercise repo scripts
    (version_stamp, lessons_issue, lessons_capture_signals, lessons_secret_scan, ...)
    directly rather than via a package import."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_git(cwd, *args: str) -> None:
    """Run a git command in cwd, raising on failure. Shared by the tests that build
    throwaway git fixtures (version_stamp, lessons_issue, lean_engine,
    skill_architecture_report, ...)."""
    subprocess.run(["git", "-C", str(cwd), *args], check=True,
                    capture_output=True, text=True)


def write_fixture(path: Path, content: str) -> None:
    """Write a dedented text fixture, creating parent directories as needed. Shared by
    the tests that build throwaway repo/skill fixtures on disk (runtime-metadata-parity,
    skill-architecture-report, ...)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def classify_tp_fp_fn(expect_positive: bool, fired: bool, tp: int, fp: int, fn: int) -> tuple[int, int, int]:
    """Fold one gold-ledger case's (expected, fired) pair into running true/false
    positive/negative counts. Shared accumulator step for the calibration loops in
    lean_code_lens and lean_engine."""
    if expect_positive and fired:
        return tp + 1, fp, fn
    if expect_positive and not fired:
        return tp, fp, fn + 1
    if not expect_positive and fired:
        return tp, fp + 1, fn
    return tp, fp, fn


def assert_precision_recall_at_least(tc, tp: int, fp: int, fn: int, threshold: float = 0.90) -> None:
    """Compute precision/recall from true/false positive/negative counts and assert
    both meet the threshold. Shared by the gold-ledger calibration tests
    (lean_code_lens, lean_engine, ...)."""
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    tc.assertGreaterEqual(precision, threshold, f"precision {precision:.2f}")
    tc.assertGreaterEqual(recall, threshold, f"recall {recall:.2f}")


def run_ledger_calibration(engine, ledger_path, *, scan, expect_key, min_cases=12):
    """Drive a lean-engine detector over a JSONL calibration ledger.

    Shared by the markdown-engine and verbosity calibration gates, which differ
    only in which detector they call and which expectation key they read.
    `scan(files, registry, expect_source) -> bool` reports whether the detector
    fired on the case's source file. Returns (tp, fp, fn)."""
    text = Path(ledger_path).read_text(encoding="utf-8")
    cases = [json.loads(line) for line in text.splitlines() if line.strip()]
    assert len(cases) >= min_cases, f"ledger too small to calibrate: {len(cases)}"

    tp = fp = fn = 0
    for case in cases:
        files = {f["path"]: f["content"] for f in case["files"]}
        registry = engine.load_registry(None)
        if case.get("registry"):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / ".lean-audit.toml"
                path.write_text(case["registry"], encoding="utf-8")
                registry = engine.load_registry(path)
        fired = scan(files, registry, case["expect_source"])
        tp, fp, fn = classify_tp_fp_fn(case[expect_key], fired, tp, fp, fn)
    return tp, fp, fn


def assert_test_quality_stack_pack(tc, stack: str, core_markers: tuple[str, ...]) -> None:
    """The per-stack test-quality extension pack contract (index row, four files,
    stack-namespaced codes) shared by the java/rust/... surface tests."""
    index = read("souroldgeezer-audit/skills/test-quality-audit/extensions/index.md")
    for name in ("core", "unit", "integration", "e2e"):
        tc.assertIn(f"references/extensions/{stack}/{name}.md", index)
        rel = f"souroldgeezer-audit/skills/test-quality-audit/references/extensions/{stack}/{name}.md"
        tc.assertTrue((REPO_ROOT / rel).exists(), rel)
    core = read(f"souroldgeezer-audit/skills/test-quality-audit/references/extensions/{stack}/core.md")
    for marker in core_markers:
        tc.assertIn(marker, core)
    tc.assertIn(f"{stack}.HC-", core)
    tc.assertIn(f"{stack}.POS-", core)


def assert_stack_pack_grounding(tc, stack: str, display_name: str) -> None:
    """The index mentions the stack's display name and the unit/integration/e2e files
    carry the stack-namespaced HC-/I-HC-/E2E-HC- markers. Companion check to
    assert_test_quality_stack_pack shared by the java/rust/... surface tests."""
    index = read("souroldgeezer-audit/skills/test-quality-audit/extensions/index.md")
    tc.assertIn(display_name, index)

    unit = read(f"souroldgeezer-audit/skills/test-quality-audit/references/extensions/{stack}/unit.md")
    integration = read(f"souroldgeezer-audit/skills/test-quality-audit/references/extensions/{stack}/integration.md")
    e2e = read(f"souroldgeezer-audit/skills/test-quality-audit/references/extensions/{stack}/e2e.md")
    tc.assertIn(f"{stack}.HC-", unit)
    tc.assertIn(f"{stack}.I-HC-", integration)
    tc.assertIn(f"{stack}.E-HC-", e2e)


def assert_software_design_loads_stack_extension(tc, stack: str, display_name: str) -> None:
    """The software-design skill, extension-authoring procedure, and Claude agent all
    mention the stack's extension. Shared setup for the java/rust/typescript/...
    surface tests; stack-specific extension-content assertions stay in the caller."""
    skill = read("souroldgeezer-design/skills/software-design/SKILL.md")
    extension_authoring = read(
        "souroldgeezer-design/skills/software-design/references/procedures/extension-authoring.md"
    )
    claude_agent = read("souroldgeezer-design/agents/software-design.md")

    tc.assertIn(f"extensions/{stack}.md", skill)
    tc.assertIn(f"{stack}.md", extension_authoring)
    for text in (skill, claude_agent):
        tc.assertIn(display_name, text)


def assert_stack_has_synthetic_eval_coverage(
    tc,
    test_quality_trigger_id: str,
    test_quality_behavior_id: str,
    software_trigger_id: str,
    software_behavior_id: str,
) -> None:
    """The four-corpus (test-quality trigger/behavior, software-design trigger/behavior)
    synthetic eval coverage check shared by the java/rust/... surface tests."""
    test_quality_evals = "souroldgeezer-audit/skills/test-quality-audit/references/evals"
    software_evals = "souroldgeezer-design/skills/software-design/references/evals"

    tc.assertIn(test_quality_trigger_id, eval_ids(f"{test_quality_evals}/trigger-cases.jsonl"))
    tc.assertIn(test_quality_behavior_id, eval_ids(f"{test_quality_evals}/behavior-cases.jsonl"))
    tc.assertIn(software_trigger_id, eval_ids(f"{software_evals}/trigger-cases.jsonl"))
    tc.assertIn(software_behavior_id, eval_ids(f"{software_evals}/behavior-cases.jsonl"))
