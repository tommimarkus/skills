# lean-audit:dup-intentional — source URLs, extension codes, and eval IDs are the surface contract
import unittest

from tests.surface_test_lib import read, read_jsonl


APP_SKILL = "souroldgeezer-design/skills/app-design"


class AppDesignViteExtensionSurfaceTest(unittest.TestCase):
    def test_app_design_loads_vite_before_react_and_keeps_nextjs_order(self) -> None:
        skill = read(f"{APP_SKILL}/SKILL.md")
        readme = read(f"{APP_SKILL}/extensions/README.md")
        claude_agent = read("souroldgeezer-design/agents/app-design.md")

        self.assertIn("extensions/vite.md", skill)
        self.assertIn("load it before the React extension", skill)
        self.assertIn("Vite + React loads Vite then React", skill)
        self.assertIn("React + Next.js stays React then Next.js", skill)
        self.assertLess(skill.index("extensions/vite.md"), skill.index("extensions/react.md"))
        self.assertIn("vite.md", readme)
        self.assertIn("Vite", readme)
        for text in (skill, claude_agent):
            self.assertIn("Vite", text)
        self.assertIn("Vite", skill.split("---", 2)[1])

    def test_vite_extension_has_grounding_scope_and_codes(self) -> None:
        vite = read(f"{APP_SKILL}/extensions/vite.md")
        grounding = read(f"{APP_SKILL}/references/source-grounding.md")

        for source in (
            "vite.dev/guide",
            "vite.dev/guide/env-and-mode",
            "vite.dev/guide/build",
            "vite.dev/guide/ssr",
        ):
            self.assertIn(source, vite)

        for topic in (
            "development server",
            "production build",
            "preview",
            "base",
            "dynamic imports",
            "browser/server/worker",
            "stale deployment",
        ):
            self.assertIn(topic, vite)

        for code in (
            "vite.APP-BUILD-1",
            "vite.APP-ENV-1",
            "vite.APP-ASSET-1",
            "vite.APP-SSR-1",
            "vite.APP-RECOVERY-1",
            "vite.POS-APP-1",
            "vite.POS-APP-2",
            "vite.POS-APP-3",
            "vite.POS-APP-4",
            "vite.POS-APP-5",
        ):
            self.assertIn(code, vite)

        self.assertIn("Vite facts", grounding)

    def test_vite_support_has_synthetic_eval_coverage(self) -> None:
        triggers = {
            record["id"]
            for record in read_jsonl(f"{APP_SKILL}/references/evals/trigger-cases.jsonl")
        }
        behaviors = {
            record["id"]
            for record in read_jsonl(f"{APP_SKILL}/references/evals/behavior-cases.jsonl")
        }

        self.assertIn("app-design-trigger-yes-vite-review", triggers)
        self.assertIn("app-design-trigger-yes-vite-react-build", triggers)
        self.assertIn("app-design-behavior-vite-review", behaviors)
        self.assertIn("app-design-behavior-vite-react-build", behaviors)


if __name__ == "__main__":
    unittest.main()
