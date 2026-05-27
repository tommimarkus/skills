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


class TypeScriptExtensionSurfaceTest(unittest.TestCase):
    def test_software_design_loads_typescript_extension_and_metadata_mentions_it(self) -> None:
        skill = read("souroldgeezer-design/skills/software-design/SKILL.md")
        extension_authoring = read(
            "souroldgeezer-design/skills/software-design/references/procedures/extension-authoring.md"
        )
        openai = read("souroldgeezer-design/skills/software-design/agents/openai.yaml")
        claude_agent = read("souroldgeezer-design/agents/software-design.md")
        codex_agent = read(".codex/agents/software-design.toml")

        self.assertIn("extensions/typescript.md", skill)
        self.assertIn("typescript.md", extension_authoring)
        for text in (skill, openai, claude_agent, codex_agent):
            self.assertIn("TypeScript", text)

        typescript = read("souroldgeezer-design/skills/software-design/extensions/typescript.md")
        self.assertIn("package.json", typescript)
        self.assertIn("tsconfig.json", typescript)
        self.assertIn("typescript.SD-", typescript)
        self.assertIn("devsecops-audit", typescript)
        self.assertIn("test-quality-audit", typescript)

    def test_typescript_software_design_guidance_is_grounded_in_authoritative_docs(self) -> None:
        typescript = read("souroldgeezer-design/skills/software-design/extensions/typescript.md")
        grounding = read("souroldgeezer-design/skills/software-design/references/source-grounding.md")

        self.assertIn("typescriptlang.org/docs/handbook/project-references.html", typescript)
        self.assertIn("typescriptlang.org/docs/handbook/modules/reference.html", typescript)
        self.assertIn("typescriptlang.org/tsconfig", typescript)
        self.assertIn("nodejs.org/api/packages.html", typescript)
        self.assertIn("docs.npmjs.com/cli/v11/configuring-npm/package-json", typescript)
        self.assertIn("project references", compact(typescript))
        self.assertIn("Node.js package metadata", grounding)

    def test_typescript_support_has_synthetic_eval_coverage(self) -> None:
        software_trigger_ids = {
            record["id"]
            for record in read_jsonl("souroldgeezer-design/skills/software-design/references/evals/trigger-cases.jsonl")
        }
        software_behavior_ids = {
            record["id"]
            for record in read_jsonl("souroldgeezer-design/skills/software-design/references/evals/behavior-cases.jsonl")
        }

        self.assertIn("software-design-trigger-yes-typescript-review", software_trigger_ids)
        self.assertIn("software-design-behavior-typescript-review", software_behavior_ids)


if __name__ == "__main__":
    unittest.main()
