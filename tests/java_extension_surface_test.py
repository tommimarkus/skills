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


class JavaExtensionSurfaceTest(unittest.TestCase):
    def test_software_design_loads_java_extension_and_metadata_mentions_it(self) -> None:
        assert_software_design_loads_stack_extension(self, "java", "Java™")

        java = read("souroldgeezer-design/skills/software-design/extensions/java.md")
        self.assertIn("pom.xml", java)
        self.assertIn("build.gradle", java)
        self.assertIn("module-info.java", java)
        self.assertIn("java.SD-", java)
        self.assertIn("devsecops-audit", java)

    def test_software_design_java_guidance_is_grounded_in_authoritative_docs(self) -> None:
        java = read("souroldgeezer-design/skills/software-design/extensions/java.md")

        self.assertIn("docs.oracle.com/javase/specs/jls/se21/html/jls-7.html", java)
        self.assertIn("maven.apache.org/pom.html", java)
        self.assertIn("docs.gradle.org/current/userguide/java_plugin.html", java)
        self.assertIn("packages may be grouped into a module", compact(java))
        self.assertIn("source sets", java)

    def test_test_quality_audit_loads_java_core_and_rubric_addons(self) -> None:
        assert_test_quality_stack_pack(self, "java", ("JUnit", "Mockito", "PIT"))
        assert_stack_pack_grounding(self, "java", "Java")

    def test_test_quality_java_guidance_is_grounded_in_authoritative_docs(self) -> None:
        core = read("souroldgeezer-audit/skills/test-quality-audit/references/extensions/java/core.md")
        e2e = read("souroldgeezer-audit/skills/test-quality-audit/references/extensions/java/e2e.md")

        for source in (
            "docs.junit.org",
            "maven.apache.org/surefire/maven-surefire-plugin/examples/junit-platform.html",
            "docs.gradle.org/current/userguide/java_testing.html",
            "site.mockito.org/javadoc/current/org/mockito/Mockito.html",
            "java.testcontainers.org/test_framework_integration/junit_5",
            "pitest.org/quickstart/maven",
            "testng.org",
        ):
            self.assertIn(source, core)
        self.assertIn("playwright.dev/java/docs/junit", e2e)

    def test_java_support_has_synthetic_eval_coverage(self) -> None:
        assert_stack_has_synthetic_eval_coverage(
            self,
            "test-quality-trigger-yes-java-junit",
            "test-quality-behavior-java-audit",
            "software-design-trigger-yes-java-review",
            "software-design-behavior-java-review",
        )


if __name__ == "__main__":
    unittest.main()
