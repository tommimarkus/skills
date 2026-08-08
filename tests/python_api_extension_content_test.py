import unittest

from tests.surface_test_lib import compact, read


class PythonApiExtensionContentTest(unittest.TestCase):
    def test_python_api_pack_has_core_and_mode_lanes(self) -> None:
        core = read("souroldgeezer-design/skills/api-design/extensions/python.md")
        build = read("souroldgeezer-design/skills/api-design/extensions/python/build.md")
        review = read("souroldgeezer-design/skills/api-design/extensions/python/review.md")

        for marker in (
            "ASGI",
            "WSGI",
            "Serverless",
            "python/build.md",
            "python/review.md",
            "devsecops-audit",
        ):
            self.assertIn(marker, core)
        self.assertIn("pyapi.PAT-hosted-asgi", build)
        self.assertIn("pyapi.PAT-hosted-wsgi", build)
        self.assertIn("pyapi.PAT-serverless-adapter", build)
        self.assertIn("pyapi.HC-1", review)
        self.assertNotIn("pyapi.HC-", build)
        self.assertNotIn("pyapi.PAT-", review)

    def test_build_patterns_cover_python_runtime_reliability(self) -> None:
        build = compact(read("souroldgeezer-design/skills/api-design/extensions/python/build.md"))

        for marker in (
            "lifespan",
            "bounded executor",
            "durable queue",
            "cancellation",
            "OpenAPI 3.1",
            "deterministic artifact",
        ):
            self.assertIn(marker, build)

    def test_review_codes_cover_requested_failure_modes(self) -> None:
        review = read("souroldgeezer-design/skills/api-design/extensions/python/review.md")

        expected = {
            "pyapi.HC-1": "blocking",
            "pyapi.HC-2": "Required side effect",
            "pyapi.HC-3": "Long-lived outbound client",
            "pyapi.HC-4": "Request-scoped state",
            "pyapi.HC-5": "cancellation",
            "pyapi.HC-6": "listener",
            "pyapi.HC-7": "shutdown",
            "pyapi.HC-8": "OpenAPI",
        }
        for code, marker in expected.items():
            with self.subTest(code=code):
                self.assertIn(code, review)
                self.assertIn(marker, review)

    def test_python_guidance_is_grounded_in_primary_sources(self) -> None:
        core = read("souroldgeezer-design/skills/api-design/extensions/python.md")

        for source in (
            "docs.python.org/3/library/asyncio-dev.html",
            "docs.python.org/3/library/asyncio-task.html",
            "peps.python.org/pep-3333/",
            "asgi.readthedocs.io/en/latest/specs/main.html",
            "asgi.readthedocs.io/en/latest/specs/lifespan.html",
            "docs.aws.amazon.com/lambda/latest/dg/python-handler.html",
            "learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python",
        ):
            self.assertIn(source, core)


if __name__ == "__main__":
    unittest.main()
