# lean-audit:dup-intentional — per-stack grounding literals (source URLs, smell codes, eval IDs) are the assertion payload; the shared pack/eval contract checks are already extracted to surface_test_lib
import unittest

from tests.surface_test_lib import (
    assert_software_design_loads_stack_extension,
    assert_stack_has_synthetic_eval_coverage,
    assert_stack_pack_grounding,
    assert_test_quality_stack_pack,
    compact,
    read,
)


class RustExtensionSurfaceTest(unittest.TestCase):
    def test_test_quality_audit_loads_rust_core_and_rubric_addons(self) -> None:
        assert_test_quality_stack_pack(self, "rust", ("Cargo.toml", "cargo-mutants"))
        assert_stack_pack_grounding(self, "rust", "Rust")

    def test_rust_test_quality_guidance_is_grounded_in_authoritative_docs(self) -> None:
        core = read("souroldgeezer-audit/skills/test-quality-audit/references/extensions/rust/core.md")
        unit = read("souroldgeezer-audit/skills/test-quality-audit/references/extensions/rust/unit.md")

        for source in (
            "doc.rust-lang.org/cargo/commands/cargo-test.html",
            "doc.rust-lang.org/rustc/tests/index.html",
            "cargo test --doc",
            "nexte.st",
            "mutants.out/outcomes.json",
            "unsafe` functions",
        ):
            self.assertIn(source, core)
        self.assertIn("features should be additive", compact(unit))
        self.assertIn("--no-default-features", unit)

    def test_software_design_loads_rust_extension_and_metadata_mentions_it(self) -> None:
        assert_software_design_loads_stack_extension(self, "rust", "Rust®")

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
        assert_stack_has_synthetic_eval_coverage(
            self,
            "test-quality-trigger-yes-rust-nextest",
            "test-quality-behavior-rust-audit",
            "software-design-trigger-yes-rust-review",
            "software-design-behavior-rust-review",
        )


if __name__ == "__main__":
    unittest.main()
