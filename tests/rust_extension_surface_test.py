import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def read_jsonl(path: str) -> list[dict]:
    records = []
    for line in read(path).splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def compact(text: str) -> str:
    return " ".join(text.split())


class RustExtensionSurfaceTest(unittest.TestCase):
    def test_test_quality_audit_loads_rust_core_and_rubric_addons(self) -> None:
        index = read("souroldgeezer-audit/skills/test-quality-audit/extensions/index.md")

        self.assertIn("Rust", index)
        self.assertIn("rust-core.md", index)
        self.assertIn("rust-unit.md", index)
        self.assertIn("rust-integration.md", index)
        self.assertIn("rust-e2e.md", index)

        for name in ("core", "unit", "integration", "e2e"):
            path = REPO_ROOT / f"souroldgeezer-audit/references/test-quality-audit-extensions/rust-{name}.md"
            self.assertTrue(path.exists(), path)

        core = read("souroldgeezer-audit/references/test-quality-audit-extensions/rust-core.md")
        unit = read("souroldgeezer-audit/references/test-quality-audit-extensions/rust-unit.md")
        integration = read("souroldgeezer-audit/references/test-quality-audit-extensions/rust-integration.md")
        e2e = read("souroldgeezer-audit/references/test-quality-audit-extensions/rust-e2e.md")

        self.assertIn("Cargo.toml", core)
        self.assertIn("cargo-mutants", core)
        self.assertIn("rust.HC-", core)
        self.assertIn("rust.POS-", core)
        self.assertIn("rust.HC-", unit)
        self.assertIn("rust.I-HC-", integration)
        self.assertIn("rust.E-HC-", e2e)

    def test_rust_test_quality_guidance_is_grounded_in_authoritative_docs(self) -> None:
        core = read("souroldgeezer-audit/references/test-quality-audit-extensions/rust-core.md")
        unit = read("souroldgeezer-audit/references/test-quality-audit-extensions/rust-unit.md")

        self.assertIn("doc.rust-lang.org/cargo/commands/cargo-test.html", core)
        self.assertIn("doc.rust-lang.org/rustc/tests/index.html", core)
        self.assertIn("cargo test --doc", core)
        self.assertIn("nexte.st", core)
        self.assertIn("mutants.out/outcomes.json", core)
        self.assertIn("unsafe` functions", core)
        self.assertIn("features should be additive", compact(unit))
        self.assertIn("--no-default-features", unit)

    def test_software_design_loads_rust_extension_and_metadata_mentions_it(self) -> None:
        skill = read("souroldgeezer-design/skills/software-design/SKILL.md")
        readme = read("souroldgeezer-design/skills/software-design/extensions/README.md")
        openai = read("souroldgeezer-design/skills/software-design/agents/openai.yaml")
        claude_agent = read("souroldgeezer-design/agents/software-design.md")
        codex_agent = read(".codex/agents/software-design.toml")

        self.assertIn("extensions/rust.md", skill)
        self.assertIn("rust.md", readme)
        for text in (skill, openai, claude_agent, codex_agent):
            self.assertIn("Rust®", text)

        rust = read("souroldgeezer-design/skills/software-design/extensions/rust.md")
        self.assertIn("Cargo.toml", rust)
        self.assertIn("rust.SD-", rust)
        self.assertIn("cargo clippy", rust)
        self.assertIn("devsecops-audit", rust)

    def test_rust_software_design_guidance_is_grounded_in_authoritative_docs(self) -> None:
        rust = read("souroldgeezer-design/skills/software-design/extensions/rust.md")

        self.assertIn("doc.rust-lang.org/cargo/reference/workspaces.html", rust)
        self.assertIn("doc.rust-lang.org/cargo/reference/features.html", rust)
        self.assertIn("doc.rust-lang.org/reference/visibility-and-privacy.html", rust)
        self.assertIn("rust-lang.github.io/api-guidelines", rust)
        self.assertIn("features are additive", compact(rust))
        self.assertIn("feature unification", rust)

    def test_rust_support_has_synthetic_eval_coverage(self) -> None:
        test_quality_trigger_ids = {
            record["id"]
            for record in read_jsonl("souroldgeezer-audit/skills/test-quality-audit/references/evals/trigger-cases.jsonl")
        }
        test_quality_behavior_ids = {
            record["id"]
            for record in read_jsonl("souroldgeezer-audit/skills/test-quality-audit/references/evals/behavior-cases.jsonl")
        }
        software_trigger_ids = {
            record["id"]
            for record in read_jsonl("souroldgeezer-design/skills/software-design/references/evals/trigger-cases.jsonl")
        }
        software_behavior_ids = {
            record["id"]
            for record in read_jsonl("souroldgeezer-design/skills/software-design/references/evals/behavior-cases.jsonl")
        }

        self.assertIn("test-quality-trigger-yes-rust-nextest", test_quality_trigger_ids)
        self.assertIn("test-quality-behavior-rust-audit", test_quality_behavior_ids)
        self.assertIn("software-design-trigger-yes-rust-review", software_trigger_ids)
        self.assertIn("software-design-behavior-rust-review", software_behavior_ids)


if __name__ == "__main__":
    unittest.main()
