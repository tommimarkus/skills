import json
import os
import signal
import subprocess
import tempfile
import textwrap
import time
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
        capture_output=True,
        timeout=30,
        env=env,
    )


def responses_by_id(result: subprocess.CompletedProcess[str]) -> dict[object, dict]:
    responses = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    return {response.get("id"): response for response in responses if "id" in response}


def close_process(process: subprocess.Popen[str]) -> None:
    if process.stdin is not None and not process.stdin.closed:
        process.stdin.close()
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
    for stream in (process.stdout, process.stderr):
        if stream is not None and not stream.closed:
            stream.close()


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
                import signal
                import sys
                import time
                from pathlib import Path

                selected_root = sys.argv[3] if sys.argv[1] == "mcp" else sys.argv[2]
                actual_cwd = os.getcwd()
                modern = os.environ.get("FAKE_MODERN") == "1"
                lifecycle_log = os.environ.get("FAKE_LIFECYCLE_LOG")

                stderr_bytes = int(os.environ.get("FAKE_STDERR_BYTES", "0"))
                if stderr_bytes:
                    sys.stderr.write("stderr-head\\n" + ("x" * stderr_bytes) + "\\nstderr-tail\\n")
                    sys.stderr.flush()

                def log(event):
                    if lifecycle_log:
                        with open(lifecycle_log, "a", encoding="utf-8") as stream:
                            stream.write(f"{event} {selected_root} {os.getpid()}\\n")

                def stop(signum=None, frame=None):
                    del signum, frame
                    log("stop")
                    raise SystemExit(0)

                signal.signal(signal.SIGTERM, stop)
                signal.signal(signal.SIGINT, stop)
                log("start")
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
                    {
                        "name": "dediren_guide",
                        "description": "Read the installed Dediren guide.",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                ]
                try:
                    for line in sys.stdin:
                        request = json.loads(line)
                        method = request.get("method")
                        if method == os.environ.get("FAKE_HANG_METHOD"):
                            time.sleep(60)
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
                            if os.environ.get("FAKE_EXIT_METHOD") == method:
                                sys.stderr.write(
                                    os.environ.get("FAKE_STDERR_MESSAGE", "backend failed") + "\\n"
                                )
                                sys.stderr.flush()
                                os._exit(int(os.environ.get("FAKE_EXIT_CODE", "23")))
                            crash_marker = os.environ.get("FAKE_CRASH_MARKER")
                            if crash_marker and not Path(crash_marker).exists():
                                Path(crash_marker).touch()
                                os._exit(17)
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
                                            "cwd": actual_cwd,
                                            "arguments": request["params"]["arguments"],
                                        }),
                                    }],
                                    "isError": False,
                                },
                            }
                        else:
                            continue
                        print(json.dumps(response), flush=True)
                finally:
                    log("stop")
                """
            ),
            encoding="utf-8",
        )
        fake_backend.chmod(0o755)
        return fake_backend

    def test_initialization_supports_legacy_and_stateless_clients_without_starting_dediren(
        self,
    ) -> None:
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
            {"dediren_validate", "dediren_future_tool", "dediren_guide"},
        )
        for tool in tools:
            self.assertIn("workspaceRoot", tool["inputSchema"]["properties"])
            self.assertIn("workspaceRoot", tool["inputSchema"]["required"])

    def test_upstream_launcher_logs_only_resolved_command_and_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace with spaces"
            workspace.mkdir()
            fake_backend = self._write_fake_backend(root)
            result = subprocess.run(
                ["bash", str(LAUNCHER), "--upstream", str(workspace)],
                cwd=REPO_ROOT,
                check=False,
                text=True,
                input=json.dumps(
                    {"jsonrpc": "2.0", "id": 26, "method": "server/discover", "params": {}}
                )
                + "\n",
                capture_output=True,
                timeout=10,
                env={**os.environ, "DEDIREN_COMMAND": str(fake_backend)},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["id"], 26)
        self.assertIn("dediren-mcp: exec", result.stderr)
        self.assertIn(str(fake_backend.resolve()), result.stderr)
        self.assertIn("mcp --root", result.stderr)
        self.assertNotIn("DEDIREN_COMMAND=", result.stderr)

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
        self.assertEqual(payload["cwd"], str(workspace.resolve()))

    def test_cached_discovery_survives_deleted_router_cwd_for_workspace_call(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            launch_cwd = root / "plugin-backup"
            launch_cwd.mkdir()
            workspace = root / "workspace"
            workspace.mkdir()
            fake_backend = self._write_fake_backend(root)
            process = subprocess.Popen(
                ["bash", str(LAUNCHER)],
                cwd=launch_cwd,
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={
                    **os.environ,
                    "DEDIREN_MCP_LAUNCHER": str(fake_backend),
                    "FAKE_MODERN": "1",
                },
            )
            assert process.stdin is not None
            assert process.stdout is not None
            try:
                process.stdin.write(
                    json.dumps({"jsonrpc": "2.0", "id": 20, "method": "tools/list", "params": {}})
                    + "\n"
                )
                process.stdin.flush()
                self.assertIn("result", json.loads(process.stdout.readline()))
                launch_cwd.rmdir()
                process.stdin.write(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 21,
                            "method": "tools/call",
                            "params": {
                                "name": "dediren_guide",
                                "arguments": {"workspaceRoot": str(workspace)},
                            },
                        }
                    )
                    + "\n"
                )
                process.stdin.flush()
                response = json.loads(process.stdout.readline())
                payload = json.loads(response["result"]["content"][0]["text"])
            finally:
                close_process(process)

        self.assertEqual(payload["root"], str(workspace.resolve()))
        self.assertEqual(payload["cwd"], str(workspace.resolve()))

    def test_cold_discovery_survives_deleted_router_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            launch_cwd = root / "plugin-backup"
            launch_cwd.mkdir()
            fake_backend = self._write_fake_backend(root)
            process = subprocess.Popen(
                ["bash", str(LAUNCHER)],
                cwd=launch_cwd,
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "DEDIREN_MCP_LAUNCHER": str(fake_backend)},
            )
            assert process.stdin is not None
            assert process.stdout is not None
            try:
                process.stdin.write(
                    json.dumps({"jsonrpc": "2.0", "id": 22, "method": "ping", "params": {}})
                    + "\n"
                )
                process.stdin.flush()
                self.assertIn("result", json.loads(process.stdout.readline()))
                launch_cwd.rmdir()
                process.stdin.write(
                    json.dumps({"jsonrpc": "2.0", "id": 23, "method": "tools/list", "params": {}})
                    + "\n"
                )
                process.stdin.flush()
                response = json.loads(process.stdout.readline())
            finally:
                close_process(process)

        self.assertEqual(
            {tool["name"] for tool in response["result"]["tools"]},
            {"dediren_validate", "dediren_future_tool", "dediren_guide"},
        )

    def test_backend_failure_exposes_command_cwd_exit_and_stderr_without_stdout_noise(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace with spaces"
            workspace.mkdir()
            fake_backend = self._write_fake_backend(root)
            result = run_router(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 24,
                        "method": "tools/call",
                        "params": {
                            "name": "dediren_guide",
                            "arguments": {"workspaceRoot": str(workspace)},
                        },
                    }
                ],
                env={
                    **os.environ,
                    "DEDIREN_MCP_LAUNCHER": str(fake_backend),
                    "FAKE_EXIT_METHOD": "tools/call",
                    "FAKE_EXIT_CODE": "23",
                    "FAKE_STDERR_MESSAGE": "backend diagnostic detail",
                },
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout)
        error = responses_by_id(result)[24]["error"]
        self.assertEqual(error["code"], -32000)
        self.assertIn("exit 23", error["message"])
        self.assertIn(str(fake_backend), error["message"])
        self.assertIn(f"cwd: {workspace.resolve()}", error["message"])
        self.assertIn("backend diagnostic detail", error["message"])
        self.assertIn("backend diagnostic detail", result.stderr)

    def test_oversized_backend_stderr_is_drained_and_bounded_in_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            fake_backend = self._write_fake_backend(root)
            result = run_router(
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 25,
                        "method": "tools/call",
                        "params": {
                            "name": "dediren_guide",
                            "arguments": {"workspaceRoot": str(workspace)},
                        },
                    }
                ],
                env={
                    **os.environ,
                    "DEDIREN_MCP_LAUNCHER": str(fake_backend),
                    "FAKE_STDERR_BYTES": str(256 * 1024),
                    "FAKE_EXIT_METHOD": "tools/call",
                    "FAKE_STDERR_MESSAGE": "final diagnostic tail",
                },
            )

        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        message = responses_by_id(result)[25]["error"]["message"]
        self.assertLess(len(message.encode("utf-8")), 18 * 1024)
        self.assertIn("stderr-head", message)
        self.assertIn("stderr truncated", message)
        self.assertIn("final diagnostic tail", message)

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

    def test_timed_out_backend_is_terminated_and_reported_without_hanging_router(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_backend = self._write_fake_backend(root)
            lifecycle_log = root / "lifecycle.log"
            started = time.monotonic()
            result = run_router(
                [{"jsonrpc": "2.0", "id": 8, "method": "tools/list", "params": {}}],
                env={
                    **os.environ,
                    "DEDIREN_MCP_LAUNCHER": str(fake_backend),
                    "DEDIREN_MCP_STARTUP_TIMEOUT_SEC": "0.2",
                    "FAKE_HANG_METHOD": "tools/list",
                    "FAKE_LIFECYCLE_LOG": str(lifecycle_log),
                },
            )
            elapsed = time.monotonic() - started
            log = lifecycle_log.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(elapsed, 5)
        error = responses_by_id(result)[8]["error"]
        self.assertEqual(error["code"], -32000)
        self.assertIn("timed out", error["message"])
        self.assertIn(str(fake_backend), error["message"])
        self.assertIn(f"cwd: {root.resolve()}", error["message"])
        self.assertIn("exit ", error["message"])
        self.assertIn("stderr:", error["message"])
        self.assertIn("stop ", log)

    def test_dead_workspace_backend_is_restarted_only_for_the_next_tool_call(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            fake_backend = self._write_fake_backend(root)
            crash_marker = root / "crashed-once"
            lifecycle_log = root / "lifecycle.log"
            call = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "dediren_validate",
                    "arguments": {"workspaceRoot": str(workspace), "source": "model.json"},
                },
            }
            result = run_router(
                [{**call, "id": 9}, {**call, "id": 10}],
                env={
                    **os.environ,
                    "DEDIREN_MCP_LAUNCHER": str(fake_backend),
                    "FAKE_CRASH_MARKER": str(crash_marker),
                    "FAKE_LIFECYCLE_LOG": str(lifecycle_log),
                },
            )
            log_lines = lifecycle_log.read_text(encoding="utf-8").splitlines()

        self.assertEqual(result.returncode, 0, result.stderr)
        responses = responses_by_id(result)
        self.assertIn("error", responses[9])
        self.assertIn("result", responses[10])
        workspace_starts = [
            line for line in log_lines if line.startswith(f"start {workspace.resolve()} ")
        ]
        self.assertEqual(len(workspace_starts), 2, log_lines)

    def test_healthy_workspace_backend_is_reused_across_tool_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            fake_backend = self._write_fake_backend(root)
            lifecycle_log = root / "lifecycle.log"
            call = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "dediren_validate",
                    "arguments": {"workspaceRoot": str(workspace), "source": "model.json"},
                },
            }
            result = run_router(
                [{**call, "id": 12}, {**call, "id": 13}],
                env={
                    **os.environ,
                    "DEDIREN_MCP_LAUNCHER": str(fake_backend),
                    "FAKE_LIFECYCLE_LOG": str(lifecycle_log),
                },
            )
            log_lines = lifecycle_log.read_text(encoding="utf-8").splitlines()

        self.assertEqual(result.returncode, 0, result.stderr)
        responses = responses_by_id(result)
        self.assertIn("result", responses[12])
        self.assertIn("result", responses[13])
        workspace_starts = [
            line for line in log_lines if line.startswith(f"start {workspace.resolve()} ")
        ]
        self.assertEqual(len(workspace_starts), 1, log_lines)

    def test_catalog_only_backend_is_reaped_while_router_stays_available(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_backend = self._write_fake_backend(root)
            lifecycle_log = root / "lifecycle.log"
            process = subprocess.Popen(
                ["bash", str(LAUNCHER)],
                cwd=REPO_ROOT,
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={
                    **os.environ,
                    "DEDIREN_MCP_LAUNCHER": str(fake_backend),
                    "FAKE_LIFECYCLE_LOG": str(lifecycle_log),
                },
            )
            assert process.stdin is not None
            assert process.stdout is not None
            try:
                process.stdin.write(
                    json.dumps({"jsonrpc": "2.0", "id": 14, "method": "tools/list", "params": {}})
                    + "\n"
                )
                process.stdin.flush()
                self.assertIn("result", json.loads(process.stdout.readline()))
                deadline = time.monotonic() + 3
                log_lines: list[str] = []
                while time.monotonic() < deadline:
                    if lifecycle_log.exists():
                        log_lines = lifecycle_log.read_text(encoding="utf-8").splitlines()
                        if any(
                            line.startswith(f"stop {root.resolve()} ") for line in log_lines
                        ):
                            break
                    time.sleep(0.05)
                self.assertIsNone(process.poll(), "router exited with its catalog backend")
                process.stdin.write(
                    json.dumps({"jsonrpc": "2.0", "id": 15, "method": "ping", "params": {}}) + "\n"
                )
                process.stdin.flush()
                self.assertEqual(json.loads(process.stdout.readline())["id"], 15)
                process.stdin.close()
                process.wait(timeout=10)
            finally:
                close_process(process)

        self.assertTrue(
            any(line.startswith(f"stop {root.resolve()} ") for line in log_lines),
            log_lines,
        )

    @unittest.skipUnless(hasattr(signal, "SIGTERM"), "requires process signals")
    def test_router_termination_closes_the_live_workspace_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            fake_backend = self._write_fake_backend(root)
            lifecycle_log = root / "lifecycle.log"
            env = {
                **os.environ,
                "DEDIREN_MCP_LAUNCHER": str(fake_backend),
                "FAKE_LIFECYCLE_LOG": str(lifecycle_log),
            }
            process = subprocess.Popen(
                ["bash", str(LAUNCHER)],
                cwd=REPO_ROOT,
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            assert process.stdin is not None
            assert process.stdout is not None
            try:
                request = {
                    "jsonrpc": "2.0",
                    "id": 11,
                    "method": "tools/call",
                    "params": {
                        "name": "dediren_validate",
                        "arguments": {
                            "workspaceRoot": str(workspace),
                            "source": "model.json",
                        },
                    },
                }
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()
                response = json.loads(process.stdout.readline())
                self.assertIn("result", response)
                process.terminate()
                process.wait(timeout=10)
            finally:
                close_process(process)
            time.sleep(0.1)
            log_lines = lifecycle_log.read_text(encoding="utf-8").splitlines()

        workspace_events = [line for line in log_lines if str(workspace.resolve()) in line]
        self.assertTrue(any(line.startswith("start ") for line in workspace_events), log_lines)
        self.assertTrue(any(line.startswith("stop ") for line in workspace_events), log_lines)


if __name__ == "__main__":
    unittest.main()
