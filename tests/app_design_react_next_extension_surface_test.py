import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_SKILL = "souroldgeezer-design/skills/app-design"
API_SKILL = "souroldgeezer-design/skills/api-design"


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def read_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


class AppDesignReactNextExtensionSurfaceTest(unittest.TestCase):
    def test_app_design_loads_react_and_nextjs_extensions(self) -> None:
        skill = read(f"{APP_SKILL}/SKILL.md")
        readme = read(f"{APP_SKILL}/extensions/README.md")
        openai = read(f"{APP_SKILL}/agents/openai.yaml")
        claude_agent = read("souroldgeezer-design/agents/app-design.md")
        codex_agent = read(".codex/agents/app-design.toml")

        self.assertIn("extensions/react.md", skill)
        self.assertIn("extensions/nextjs.md", skill)
        self.assertIn("load it after the React extension", skill)
        self.assertIn("react.md", readme)
        self.assertIn("nextjs.md", readme)
        for text in (skill, openai, claude_agent, codex_agent):
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
            "react.POS-APP-1",
        ):
            self.assertIn(code, react)

        self.assertIn("React facts", grounding)

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
