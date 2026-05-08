import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def read_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


def compact(text: str) -> str:
    return " ".join(text.split())


class JavaExtensionSurfaceTest(unittest.TestCase):
    def test_software_design_loads_java_extension_and_metadata_mentions_it(self) -> None:
        skill = read("souroldgeezer-design/skills/software-design/SKILL.md")
        readme = read("souroldgeezer-design/skills/software-design/extensions/README.md")
        openai = read("souroldgeezer-design/skills/software-design/agents/openai.yaml")
        claude_agent = read("souroldgeezer-design/agents/software-design.md")
        codex_agent = read(".codex/agents/software-design.toml")

        self.assertIn("extensions/java.md", skill)
        self.assertIn("java.md", readme)
        for text in (skill, openai, claude_agent, codex_agent):
            self.assertIn("Java™", text)

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
        index = read("souroldgeezer-audit/skills/test-quality-audit/extensions/index.md")

        self.assertIn("Java", index)
        self.assertIn("java-core.md", index)
        self.assertIn("java-unit.md", index)
        self.assertIn("java-integration.md", index)
        self.assertIn("java-e2e.md", index)

        for name in ("core", "unit", "integration", "e2e"):
            path = REPO_ROOT / f"souroldgeezer-audit/references/test-quality-audit-extensions/java-{name}.md"
            self.assertTrue(path.exists(), path)

        core = read("souroldgeezer-audit/references/test-quality-audit-extensions/java-core.md")
        unit = read("souroldgeezer-audit/references/test-quality-audit-extensions/java-unit.md")
        integration = read("souroldgeezer-audit/references/test-quality-audit-extensions/java-integration.md")
        e2e = read("souroldgeezer-audit/references/test-quality-audit-extensions/java-e2e.md")

        self.assertIn("JUnit", core)
        self.assertIn("Mockito", core)
        self.assertIn("PIT", core)
        self.assertIn("java.HC-", core)
        self.assertIn("java.POS-", core)
        self.assertIn("java.HC-", unit)
        self.assertIn("java.I-HC-", integration)
        self.assertIn("java.E-HC-", e2e)

    def test_test_quality_java_guidance_is_grounded_in_authoritative_docs(self) -> None:
        core = read("souroldgeezer-audit/references/test-quality-audit-extensions/java-core.md")
        e2e = read("souroldgeezer-audit/references/test-quality-audit-extensions/java-e2e.md")

        self.assertIn("docs.junit.org", core)
        self.assertIn("maven.apache.org/surefire/maven-surefire-plugin/examples/junit-platform.html", core)
        self.assertIn("docs.gradle.org/current/userguide/java_testing.html", core)
        self.assertIn("site.mockito.org/javadoc/current/org/mockito/Mockito.html", core)
        self.assertIn("java.testcontainers.org/test_framework_integration/junit_5", core)
        self.assertIn("pitest.org/quickstart/maven", core)
        self.assertIn("testng.org", core)
        self.assertIn("playwright.dev/java/docs/junit", e2e)

    def test_java_support_has_synthetic_eval_coverage(self) -> None:
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

        self.assertIn("test-quality-trigger-yes-java-junit", test_quality_trigger_ids)
        self.assertIn("test-quality-behavior-java-audit", test_quality_behavior_ids)
        self.assertIn("software-design-trigger-yes-java-review", software_trigger_ids)
        self.assertIn("software-design-behavior-java-review", software_behavior_ids)


if __name__ == "__main__":
    unittest.main()
