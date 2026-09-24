import json
import re
import subprocess
import unittest

from tests.surface_test_lib import REPO_ROOT

API_REFERENCE = (
    REPO_ROOT / "souroldgeezer-design/docs/api-reference/api-design.md"
)
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
            (method, operation)
            for path in document["paths"].values()
            for method, operation in path.items()
            if method in {"get", "put", "post", "patch", "delete", "head"}
        ]
        for method, operation in operations:
            for status in ("401", "404"):
                with self.subTest(operation=operation["operationId"], status=status):
                    response = operation["responses"][status]
                    if "$ref" in response:
                        response = resolve_local_ref(document, response["$ref"])
                    if method == "head":
                        self.assertNotIn("content", response)
                    else:
                        schema = response["content"]["application/problem+json"]["schema"]
                        self.assertEqual(
                            resolve_local_ref(document, schema["$ref"]), problem
                        )
                    if status == "401":
                        self.assertIn("WWW-Authenticate", response["headers"])


if __name__ == "__main__":
    unittest.main()
