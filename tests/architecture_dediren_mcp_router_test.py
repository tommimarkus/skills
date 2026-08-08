import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT


SCRIPTS = (
    REPO_ROOT
    / "souroldgeezer-architecture"
    / "skills"
    / "architecture-design"
    / "references"
    / "scripts"
)
LAUNCHER = SCRIPTS / "dediren-mcp.sh"
def run_router(messages: list[dict], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(LAUNCHER)],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        input="".join(json.dumps(message) + "\n" for message in messages),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        env=env,
    )


def responses_by_id(result: subprocess.CompletedProcess[str]) -> dict[object, dict]:
    responses = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    return {response.get("id"): response for response in responses if "id" in response}


class ArchitectureDedirenMcpRouterTest(unittest.TestCase):
    @staticmethod
    def _write_fake_backend(root: Path) -> Path:
        fake_backend = root / "fake-backend.py"
        fake_backend.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import sys

                selected_root = sys.argv[2]
                modern = os.environ.get("FAKE_MODERN") == "1"
                tools = [
                    {
                        "name": "dediren_validate",
                        "description": "Validate a model.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "source": {
                                    "type": "string",
                                    "description": "Path relative to the workspace root.",
                                },
                                "profile": {"type": "string"},
                            },
                            "required": ["source"],
                        },
                    },
                    {
                        "name": "dediren_future_tool",
                        "description": "A tool added by a newer installed Dediren.",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                ]
                for line in sys.stdin:
                    request = json.loads(line)
                    method = request.get("method")
                    if method == "server/discover":
                        if modern:
                            response = {
                                "jsonrpc": "2.0",
                                "id": request["id"],
                                "result": {
                                    "resultType": "complete",
                                    "supportedVersions": ["2026-07-28"],
                                    "capabilities": {"tools": {}},
                                },
                            }
                        else:
                            response = {
                                "jsonrpc": "2.0",
                                "id": request["id"],
                                "error": {"code": -32601, "message": "method not found"},
                            }
                    elif method == "initialize":
                        response = {
                            "jsonrpc": "2.0",
                            "id": request["id"],
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {"tools": {"listChanged": False}},
                                "serverInfo": {"name": "fake", "version": "latest"},
                            },
                        }
                    elif method == "tools/list":
                        if modern:
                            assert request["params"]["_meta"][
                                "io.modelcontextprotocol/protocolVersion"
                            ] == "2026-07-28"
                        cursor = request.get("params", {}).get("cursor")
                        page = tools
                        next_cursor = None
                        if modern:
                            page = tools[1:] if cursor == "next" else tools[:1]
                            next_cursor = None if cursor == "next" else "next"
                        response = {
                            "jsonrpc": "2.0",
                            "id": request["id"],
                            "result": {
                                "resultType": "complete",
                                "tools": page,
                                **({"nextCursor": next_cursor} if next_cursor else {}),
                            },
                        }
                    elif method == "tools/call":
                        if modern:
                            assert request["params"]["_meta"][
                                "io.modelcontextprotocol/protocolVersion"
                            ] == "2026-07-28"
                        response = {
                            "jsonrpc": "2.0",
                            "id": request["id"],
                            "result": {
                                "content": [{
                                    "type": "text",
                                    "text": json.dumps({
                                        "root": selected_root,
                                        "arguments": request["params"]["arguments"],
                                    }),
                                }],
                                "isError": False,
                            },
                        }
                    else:
                        continue
                    print(json.dumps(response), flush=True)
                """
            ),
            encoding="utf-8",
        )
        fake_backend.chmod(0o755)
        return fake_backend

    def test_initialization_supports_legacy_and_stateless_clients_without_starting_dediren(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = run_router(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-11-25",
                            "capabilities": {},
                            "clientInfo": {"name": "legacy-test", "version": "1"},
                        },
                    },
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {
                        "jsonrpc": "2.0",
                        "id": "discover",
                        "method": "server/discover",
                        "params": {
                            "_meta": {
                                "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                                "io.modelcontextprotocol/clientInfo": {
                                    "name": "stateless-test",
                                    "version": "1",
                                },
                                "io.modelcontextprotocol/clientCapabilities": {},
                            }
                        },
                    },
                ],
                env={
                    **os.environ,
                    "DEDIREN_MCP_LAUNCHER": str(root / "must-not-start"),
                },
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        responses = responses_by_id(result)
        self.assertEqual(responses[1]["result"]["protocolVersion"], "2025-11-25")
        discovery = responses["discover"]["result"]
        self.assertIn("2026-07-28", discovery["supportedVersions"])
        self.assertIn("tools", discovery["capabilities"])

    def test_tool_catalog_is_live_from_installed_dediren_and_adds_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_backend = self._write_fake_backend(root)
            result = run_router(
                [{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}],
                env={
                    **os.environ,
                    "DEDIREN_MCP_LAUNCHER": str(fake_backend),
                    "FAKE_MODERN": "1",
                },
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        tools = responses_by_id(result)[2]["result"]["tools"]
        self.assertEqual(
            {tool["name"] for tool in tools},
            {"dediren_validate", "dediren_future_tool"},
        )
        for tool in tools:
            self.assertIn("workspaceRoot", tool["inputSchema"]["properties"])
            self.assertIn("workspaceRoot", tool["inputSchema"]["required"])

    def test_tool_call_routes_to_backend_for_the_explicit_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            fake_backend = self._write_fake_backend(root)

            result = run_router(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "router-test", "version": "1"},
                        },
                    },
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "dediren_validate",
                            "arguments": {
                                "workspaceRoot": str(workspace),
                                "source": "model.json",
                                "profile": "archimate",
                            },
                        },
                    },
                ],
                env={
                    **os.environ,
                    "DEDIREN_MCP_LAUNCHER": str(fake_backend),
                    "FAKE_MODERN": "1",
                },
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(responses_by_id(result)[2]["result"]["content"][0]["text"])
        self.assertEqual(payload["root"], str(workspace.resolve()))
        self.assertEqual(
            payload["arguments"],
            {"source": "model.json", "profile": "archimate"},
        )

    def test_tool_call_rejects_a_path_that_escapes_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            fake_backend = self._write_fake_backend(root)
            result = run_router(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 7,
                        "method": "tools/call",
                        "params": {
                            "name": "dediren_validate",
                            "arguments": {
                                "workspaceRoot": str(workspace),
                                "source": "../outside.json",
                            },
                        },
                    }
                ],
                env={**os.environ, "DEDIREN_MCP_LAUNCHER": str(fake_backend)},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        error = responses_by_id(result)[7]["error"]
        self.assertEqual(error["code"], -32602)
        self.assertIn("workspaceRoot", error["message"])


if __name__ == "__main__":
    unittest.main()
