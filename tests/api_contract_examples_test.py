import json
import re
import subprocess
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT

API_REFERENCE = (
    REPO_ROOT / "souroldgeezer-design/docs/api-reference/api-design.md"
)
FUNCTIONS_BUILD = (
    REPO_ROOT
    / "souroldgeezer-design/skills/api-design/extensions/azure-functions-dotnet/build.md"
)


def section_markdown(path: Path, heading: str) -> str:
    source = path.read_text(encoding="utf-8")
    start = source.index(heading)
    following = re.search(r"\n###? ", source[start + len(heading) :])
    end = start + len(heading) + following.start() if following else len(source)
    return source[start:end]


def openapi_example() -> dict:
    source = API_REFERENCE.read_text(encoding="utf-8")
    marker = "### OpenAPI 3.1 fragment"
    fragment = source[source.index(marker) :]
    match = re.search(r"```yaml\n(.*?)\n```", fragment, re.DOTALL)
    if not match:
        raise AssertionError("OpenAPI YAML example is missing")
    parsed = subprocess.run(
        ["yq", "-p=yaml", "-o=json"],
        input=match.group(1),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(parsed.stdout)


def resolve_local_ref(document: dict, ref: str) -> dict:
    if not ref.startswith("#/"):
        raise AssertionError(f"expected a local OpenAPI reference, got {ref!r}")
    value = document
    for component in ref[2:].split("/"):
        value = value[component.replace("~1", "/").replace("~0", "~")]
    return value


class ApiContractExamplesTest(unittest.TestCase):
    def test_problem_schema_and_error_responses_parse_to_complete_contracts(self) -> None:
        document = openapi_example()
        problem = document["components"]["schemas"]["Problem"]

        self.assertEqual(problem["type"], "object")
        self.assertTrue({"type", "title", "status", "detail", "instance"}.issubset(problem["required"]))
        self.assertEqual(problem["properties"]["instance"], {"type": "string", "format": "uri-reference"})
        self.assertEqual(problem["properties"]["status"]["type"], "integer")

        operations = [
            operation
            for path in document["paths"].values()
            for method, operation in path.items()
            if method in {"get", "put", "post", "patch", "delete", "head"}
        ]
        for operation in operations:
            for status in ("401", "404"):
                with self.subTest(operation=operation["operationId"], status=status):
                    response = operation["responses"][status]
                    if "$ref" in response:
                        response = resolve_local_ref(document, response["$ref"])
                    schema = response["content"]["application/problem+json"]["schema"]
                    self.assertEqual(
                        resolve_local_ref(document, schema["$ref"]), problem
                    )
                    if status == "401":
                        self.assertIn("WWW-Authenticate", response["headers"])

    def test_webhook_error_paths_emit_problem_response_and_challenge(self) -> None:
        section = section_markdown(
            FUNCTIONS_BUILD, "### `afdotnet.PAT-webhook-receive`"
        )
        code = re.search(r"```csharp\n(.*?)\n```", section, re.DOTALL).group(1)

        self.assertEqual(code.count("return Problem401(req);"), 3)
        self.assertNotIn("Results.Unauthorized()", code)
        self.assertIn("Results.Problem(", code)
        self.assertIn("StatusCodes.Status401Unauthorized", code)
        self.assertIn('req.HttpContext.Response.Headers["WWW-Authenticate"]', code)
        self.assertIn('= "Webhook-HMAC"', code)
        self.assertIn("`application/problem+json`", section)

    def test_durable_fanout_limits_each_scheduled_batch_and_keeps_order(self) -> None:
        section = section_markdown(
            FUNCTIONS_BUILD, "### `afdotnet.PAT-durable-fanout`"
        )
        code = re.search(r"```csharp\n(.*?)\n```", section, re.DOTALL).group(1)

        self.assertIn("foreach (var batch in items.Chunk(50))", code)
        self.assertIn("batch.Select(i =>", code)
        self.assertIn("results.AddRange(await Task.WhenAll(tasks));", code)
        self.assertLess(
            code.index("foreach (var batch"),
            code.index("await Task.WhenAll(tasks)"),
        )


if __name__ == "__main__":
    unittest.main()
