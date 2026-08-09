# lean-audit:dup-intentional — per-extension grounding literals (source URLs, smell codes, eval IDs) are the assertion payload behind the shared read/read_jsonl helpers
import unittest

from tests.surface_test_lib import read, read_jsonl

APP_SKILL = "souroldgeezer-design/skills/app-design"
API_SKILL = "souroldgeezer-design/skills/api-design"


class AppDesignReactNextExtensionSurfaceTest(unittest.TestCase):
    def test_app_design_loads_react_and_nextjs_extensions(self) -> None:
        skill = read(f"{APP_SKILL}/SKILL.md")
        readme = read(f"{APP_SKILL}/extensions/README.md")
        claude_agent = read("souroldgeezer-design/agents/app-design.md")

        self.assertIn("extensions/react.md", skill)
        self.assertIn("extensions/nextjs.md", skill)
        self.assertIn("load it after the React extension", skill)
        self.assertIn("react.md", readme)
        self.assertIn("nextjs.md", readme)
        for text in (skill, claude_agent):
            self.assertIn("React", text)
            self.assertIn("Next.js", text)

    def test_react_app_design_extension_has_grounding_and_codes(self) -> None:
        react = read(f"{APP_SKILL}/extensions/react.md")
        grounding = read(f"{APP_SKILL}/references/source-grounding.md")

        for source in (
            "react.dev/reference/react",
            "react.dev/reference/rules/components-and-hooks-must-be-pure",
            "react.dev/reference/rules/rules-of-hooks",
            "react.dev/reference/react-dom/client/hydrateRoot",
        ):
            self.assertIn(source, react)

        for code in (
            "react.APP-CMP-1",
            "react.APP-STATE-1",
            "react.APP-RENDER-1",
            "react.APP-BROWSER-1",
            "react.APP-EFFECT-1",
            "react.POS-APP-1",
            "react.POS-APP-6",
        ):
            self.assertIn(code, react)

        self.assertIn("React facts", grounding)
        for guidance in (
            "Strict Mode",
            "derived state",
            "AbortSignal",
            "useSyncExternalStore",
            "compiler availability",
        ):
            self.assertIn(guidance, react)

    def test_nextjs_app_design_extension_composes_with_react_and_api_design(self) -> None:
        nextjs = read(f"{APP_SKILL}/extensions/nextjs.md")
        api_nextjs = read(f"{API_SKILL}/extensions/nextjs.md")

        for source in (
            "nextjs.org/docs/app",
            "nextjs.org/docs/app/getting-started/server-and-client-components",
            "nextjs.org/docs/app/guides/caching",
            "nextjs.org/docs/app/api-reference/file-conventions/route-segment-config",
        ):
            self.assertIn(source, nextjs)

        self.assertIn("Load `react.md` first", nextjs)
        self.assertIn("api-design", nextjs)
        self.assertIn("Route Handlers", nextjs)
        self.assertIn("Server Actions", nextjs)
        for code in (
            "nextjs.APP-ROUTE-1",
            "nextjs.APP-RENDER-1",
            "nextjs.APP-CACHE-1",
            "nextjs.APP-FORM-1",
            "nextjs.POS-APP-1",
        ):
            self.assertIn(code, nextjs)

        self.assertIn("app-design", api_nextjs)
        self.assertIn("frontend app", api_nextjs)

    def test_react_nextjs_support_has_synthetic_eval_coverage(self) -> None:
        triggers = {
            record["id"]
            for record in read_jsonl(f"{APP_SKILL}/references/evals/trigger-cases.jsonl")
        }
        behaviors = {
            record["id"]
            for record in read_jsonl(f"{APP_SKILL}/references/evals/behavior-cases.jsonl")
        }

        self.assertIn("app-design-trigger-yes-react-review", triggers)
        self.assertIn("app-design-trigger-yes-nextjs-review", triggers)
        self.assertIn("app-design-trigger-no-nextjs-api-route", triggers)
        self.assertIn("app-design-behavior-react-review", behaviors)
        self.assertIn("app-design-behavior-nextjs-build", behaviors)


if __name__ == "__main__":
    unittest.main()
