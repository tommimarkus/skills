import unittest

from tests.surface_test_lib import assert_software_design_loads_stack_extension, read, read_jsonl, compact


class TypeScriptExtensionSurfaceTest(unittest.TestCase):
    def test_software_design_loads_typescript_extension_and_metadata_mentions_it(self) -> None:
        assert_software_design_loads_stack_extension(self, "typescript", "TypeScript")

        typescript = read("souroldgeezer-design/skills/software-design/extensions/typescript.md")
        for marker in (
            "package.json",
            "tsconfig.json",
            "typescript.SD-",
            "devsecops-audit",
            "test-quality-audit",
        ):
            self.assertIn(marker, typescript)

    def test_typescript_software_design_guidance_is_grounded_in_authoritative_docs(self) -> None:
        typescript = read("souroldgeezer-design/skills/software-design/extensions/typescript.md")
        grounding = read("souroldgeezer-design/skills/software-design/references/source-grounding.md")

        for source in (
            "typescriptlang.org/docs/handbook/project-references.html",
            "typescriptlang.org/docs/handbook/modules/reference.html",
            "typescriptlang.org/tsconfig",
            "nodejs.org/api/packages.html",
            "docs.npmjs.com/cli/v11/configuring-npm/package-json",
        ):
            self.assertIn(source, typescript)
        self.assertIn("project references", compact(typescript))
        self.assertIn("Node.js package metadata", grounding)

    def test_typescript_lane_covers_project_first_runtime_contracts_and_js_migration(self) -> None:
        typescript = read("souroldgeezer-design/skills/software-design/extensions/typescript.md")
        grounding = read("souroldgeezer-design/skills/software-design/references/source-grounding.md")

        for marker in (
            "project-first",
            "checkJs",
            "allowJs",
            "conditional exports",
            "dependencies",
            "peerDependencies",
            "AbortSignal",
            "error contract",
            "performance evidence",
        ):
            self.assertIn(marker, typescript)
        self.assertIn("Node.js abort-controller", grounding)

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
        self.assertIn("software-design-trigger-yes-js-ts-assimilation", software_trigger_ids)
        self.assertIn("software-design-behavior-js-ts-runtime-contracts", software_behavior_ids)


if __name__ == "__main__":
    unittest.main()
