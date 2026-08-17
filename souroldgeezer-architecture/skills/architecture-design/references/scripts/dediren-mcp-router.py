#!/usr/bin/env python3
"""Workspace-explicit MCP router for an externally installed Dediren CLI."""

from __future__ import annotations

import atexit
import json
import math
import os
import queue
import shlex
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

SERVER_INFO = {"name": "dediren-workspace-router", "version": "1.0.0"}
MODERN_PROTOCOL = "2026-07-28"
LEGACY_PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
SERVER_META = {"io.modelcontextprotocol/serverInfo": SERVER_INFO}
# Cacheable "complete" results must carry caching hints. Nothing the router
# publishes is caller-specific, so every cached response is shareable.
CACHE_SCOPE = "public"
# Identity, supported versions, and capabilities are fixed for this process.
DISCOVER_TTL_MS = 3_600_000
# The catalog follows the resolved Dediren install, and the router advertises no
# listChanged notification, so this interval is the only re-check clients get.
TOOLS_TTL_MS = 300_000
DEFAULT_STARTUP_TIMEOUT_SECONDS = 120.0
DEFAULT_REQUEST_TIMEOUT_SECONDS = 360.0
STDERR_HEAD_BYTES = 4 * 1024
STDERR_TAIL_BYTES = 12 * 1024
STDERR_MIRROR_LOCK = threading.Lock()
WORKSPACE_ROOT_SCHEMA = {
    "type": "string",
    "description": (
        "Absolute directory that owns this operation. All Dediren path arguments "
        "are resolved beneath it."
    ),
}


class RouterError(RuntimeError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


class BackendError(RuntimeError):
    pass


class DiagnosticExcerpt:
    """Retain a bounded byte excerpt while stderr is drained continuously."""

    def __init__(self) -> None:
        self.head = bytearray()
        self.tail = bytearray()
        self.total = 0
        self.lock = threading.Lock()

    def append(self, chunk: bytes) -> None:
        with self.lock:
            self.total += len(chunk)
            head_remaining = STDERR_HEAD_BYTES - len(self.head)
            if head_remaining > 0:
                self.head.extend(chunk[:head_remaining])
                chunk = chunk[head_remaining:]
            if chunk:
                self.tail.extend(chunk)
                if len(self.tail) > STDERR_TAIL_BYTES:
                    del self.tail[:-STDERR_TAIL_BYTES]

    def render(self) -> str:
        with self.lock:
            head = bytes(self.head)
            tail = bytes(self.tail)
            total = self.total
        if total > STDERR_HEAD_BYTES + STDERR_TAIL_BYTES:
            omitted = total - STDERR_HEAD_BYTES - STDERR_TAIL_BYTES
            marker = f"\n...[stderr truncated; {omitted} bytes omitted]...\n".encode()
            excerpt = head + marker + tail
        else:
            excerpt = head + tail
        return excerpt.decode("utf-8", errors="replace").strip()


def mirror_stderr(chunk: bytes) -> None:
    with STDERR_MIRROR_LOCK:
        try:
            binary_stderr = getattr(sys.stderr, "buffer", None)
            if binary_stderr is not None:
                binary_stderr.write(chunk)
                binary_stderr.flush()
                return
            sys.stderr.write(chunk.decode("utf-8", errors="replace"))
            sys.stderr.flush()
        except (OSError, ValueError):
            # A closed host log stream must not stop draining the child pipe.
            return


def diagnostic_context(
    command: tuple[str, ...],
    cwd: Path,
    exit_code: int | None,
    stderr_excerpt: str,
) -> str:
    rendered_exit = str(exit_code) if exit_code is not None else "unknown"
    rendered_stderr = stderr_excerpt or "<none captured>"
    return (
        f"exit {rendered_exit}; command: {shlex.join(command)}; cwd: {cwd}; "
        f"stderr:\n{rendered_stderr}"
    )


class Backend:
    def __init__(
        self,
        root: Path,
        launcher: Path,
        startup_timeout: float,
        request_timeout: float,
    ) -> None:
        self.root = root
        self.startup_timeout = startup_timeout
        self.request_timeout = request_timeout
        self.responses: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self.closed = False
        self.command = (str(launcher), "--upstream", str(root))
        self.diagnostics = DiagnosticExcerpt()
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=os.environ.copy(),
                cwd=root,
                start_new_session=os.name == "posix",
            )
        except OSError as exc:
            context = diagnostic_context(self.command, root, None, "")
            raise BackendError(
                f"could not start the installed Dediren CLI: {exc} ({context})"
            ) from exc
        self.stdout_reader = threading.Thread(
            target=self._read_responses,
            name=f"dediren-mcp-{self.process.pid}",
            daemon=True,
        )
        self.stderr_reader = threading.Thread(
            target=self._read_stderr,
            name=f"dediren-mcp-stderr-{self.process.pid}",
            daemon=True,
        )
        self.stdout_reader.start()
        self.stderr_reader.start()
        self.next_id = 1
        self.modern = False
        try:
            discovery = self.request(
                "server/discover",
                {
                    "_meta": {
                        "io.modelcontextprotocol/protocolVersion": MODERN_PROTOCOL,
                        "io.modelcontextprotocol/clientInfo": SERVER_INFO,
                        "io.modelcontextprotocol/clientCapabilities": {},
                    }
                },
                timeout=self.startup_timeout,
            )
            discovered = discovery.get("result")
            if isinstance(discovered, dict) and MODERN_PROTOCOL in discovered.get(
                "supportedVersions", []
            ):
                self.modern = True
                return

            response = self.request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": SERVER_INFO,
                },
                timeout=self.startup_timeout,
            )
            if "result" not in response:
                raise BackendError(f"Dediren initialization failed: {response.get('error')}")
            self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        except BackendError:
            self.close()
            raise

    def _read_responses(self) -> None:
        if self.process.stdout is None:
            self.responses.put(None)
            return
        try:
            for line in self.process.stdout:
                try:
                    response = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(response, dict):
                    self.responses.put(response)
        finally:
            self.responses.put(None)

    def _read_stderr(self) -> None:
        if self.process.stderr is None:
            return
        descriptor = self.process.stderr.fileno()
        try:
            while True:
                chunk = os.read(descriptor, 4096)
                if not chunk:
                    return
                self.diagnostics.append(chunk)
                mirror_stderr(chunk)
        except OSError:
            return

    def _failure(self, summary: str) -> str:
        exit_code = self.process.poll()
        if exit_code is not None and threading.current_thread() is not self.stderr_reader:
            self.stderr_reader.join(timeout=1)
        context = diagnostic_context(
            self.command,
            self.root,
            exit_code,
            self.diagnostics.render(),
        )
        return f"{summary} ({context})"

    def send(self, message: dict[str, Any]) -> None:
        if self.process.stdin is None:
            raise BackendError("Dediren stdin is unavailable")
        try:
            self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            self.close()
            raise BackendError(self._failure("Dediren closed its input")) from exc

    def request(
        self,
        method: str,
        params: dict[str, Any],
        *,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        request_params = dict(params)
        if self.modern and method != "server/discover":
            meta = request_params.get("_meta")
            request_meta = dict(meta) if isinstance(meta, dict) else {}
            request_meta.update(
                {
                    "io.modelcontextprotocol/protocolVersion": MODERN_PROTOCOL,
                    "io.modelcontextprotocol/clientInfo": SERVER_INFO,
                    "io.modelcontextprotocol/clientCapabilities": {},
                }
            )
            request_params["_meta"] = request_meta
        self.send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": request_params,
            }
        )
        wait_timeout = self.request_timeout if timeout is None else timeout
        deadline = time.monotonic() + wait_timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.close()
                raise BackendError(
                    self._failure(
                        f"Dediren timed out after {wait_timeout:g}s waiting for {method}"
                    )
                )
            try:
                response = self.responses.get(timeout=remaining)
            except queue.Empty as exc:
                self.close()
                raise BackendError(
                    self._failure(
                        f"Dediren timed out after {wait_timeout:g}s waiting for {method}"
                    )
                ) from exc
            if response is None:
                self.close()
                raise BackendError(
                    self._failure(f"Dediren exited before responding to {method}")
                )
            if response.get("id") == request_id:
                return response

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        if self.process.stdin is not None and not self.process.stdin.closed:
            try:
                self.process.stdin.close()
            except OSError:
                pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        readers = (self.stdout_reader, self.stderr_reader)
        for reader in readers:
            if reader.is_alive() and threading.current_thread() is not reader:
                reader.join(timeout=1)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream is not None and not stream.closed:
                try:
                    stream.close()
                except OSError:
                    pass
        for reader in readers:
            if reader.is_alive() and threading.current_thread() is not reader:
                reader.join(timeout=1)


class Router:
    def __init__(self) -> None:
        default_launcher = Path(__file__).with_name("dediren-mcp.sh")
        configured_launcher = Path(
            os.environ.get("DEDIREN_MCP_LAUNCHER", default_launcher)
        ).expanduser()
        self.launcher = configured_launcher.resolve(strict=False)
        self.catalog_root = self.launcher.parent
        self.startup_timeout = positive_timeout(
            "DEDIREN_MCP_STARTUP_TIMEOUT_SEC", DEFAULT_STARTUP_TIMEOUT_SECONDS
        )
        self.request_timeout = positive_timeout(
            "DEDIREN_MCP_REQUEST_TIMEOUT_SEC", DEFAULT_REQUEST_TIMEOUT_SECONDS
        )
        self.backends: dict[Path, Backend] = {}
        self.tools: list[dict[str, Any]] | None = None
        self.tools_by_name: dict[str, dict[str, Any]] = {}
        self.path_fields: dict[str, tuple[str, ...]] = {}
        atexit.register(self.close)

    def close(self) -> None:
        for backend in self.backends.values():
            backend.close()
        self.backends.clear()

    @staticmethod
    def modern(request: dict[str, Any]) -> bool:
        params = request.get("params")
        if not isinstance(params, dict):
            return False
        meta = params.get("_meta")
        return (
            isinstance(meta, dict)
            and meta.get("io.modelcontextprotocol/protocolVersion") == MODERN_PROTOCOL
        )

    @staticmethod
    def workspace(arguments: dict[str, Any]) -> Path:
        raw = arguments.get("workspaceRoot")
        if not isinstance(raw, str) or not raw:
            raise RouterError(-32602, "workspaceRoot must be an absolute directory")
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            raise RouterError(-32602, "workspaceRoot must be an absolute directory")
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise RouterError(-32602, f"workspaceRoot is not accessible: {exc}") from exc
        if not resolved.is_dir():
            raise RouterError(-32602, "workspaceRoot must be an absolute directory")
        return resolved

    def backend(self, root: Path) -> Backend:
        backend = self.backends.get(root)
        if backend is not None and backend.process.poll() is None:
            return backend
        if backend is not None:
            backend.close()
        backend = Backend(
            root,
            self.launcher,
            self.startup_timeout,
            self.request_timeout,
        )
        self.backends[root] = backend
        return backend

    def load_tools(self, backend: Backend | None = None) -> list[dict[str, Any]]:
        if self.tools is not None:
            return self.tools
        catalog_root: Path | None = None
        if backend is None:
            catalog_root = self.catalog_root
            backend = self.backend(catalog_root)
        try:
            raw_tools: list[Any] = []
            cursor: str | None = None
            while True:
                params = {"cursor": cursor} if cursor is not None else {}
                response = backend.request("tools/list", params, timeout=self.startup_timeout)
                result = response.get("result")
                page = result.get("tools") if isinstance(result, dict) else None
                if not isinstance(page, list):
                    raise BackendError("installed Dediren returned no tools[] catalog")
                raw_tools.extend(page)
                next_cursor = result.get("nextCursor")
                if not isinstance(next_cursor, str) or not next_cursor:
                    break
                cursor = next_cursor
        finally:
            if catalog_root is not None:
                catalog_backend = self.backends.pop(catalog_root, None)
                if catalog_backend is not None:
                    catalog_backend.close()

        augmented: list[dict[str, Any]] = []
        for raw_tool in raw_tools:
            if not isinstance(raw_tool, dict) or not isinstance(raw_tool.get("name"), str):
                continue
            tool = dict(raw_tool)
            input_schema = raw_tool.get("inputSchema")
            if not isinstance(input_schema, dict):
                input_schema = {"type": "object"}
            input_schema = dict(input_schema)
            raw_properties = input_schema.get("properties")
            properties = dict(raw_properties) if isinstance(raw_properties, dict) else {}
            properties = {"workspaceRoot": WORKSPACE_ROOT_SCHEMA, **properties}
            raw_required = input_schema.get("required")
            required = list(raw_required) if isinstance(raw_required, list) else []
            if "workspaceRoot" not in required:
                required.insert(0, "workspaceRoot")
            input_schema["type"] = "object"
            input_schema["properties"] = properties
            input_schema["required"] = required
            tool["inputSchema"] = input_schema
            augmented.append(tool)

            path_fields: list[str] = []
            for field, field_schema in properties.items():
                if field == "workspaceRoot" or not isinstance(field_schema, dict):
                    continue
                description = str(field_schema.get("description", "")).lower()
                if field_schema.get("type") == "string" and (
                    "relative to the workspace root" in description
                    or ("path" in description and "workspace" in description)
                ):
                    path_fields.append(field)
            self.path_fields[tool["name"]] = tuple(path_fields)

        if not augmented:
            raise BackendError("installed Dediren exposed no MCP tools")
        self.tools = augmented
        self.tools_by_name = {tool["name"]: tool for tool in augmented}
        return augmented

    def validated_arguments(
        self,
        name: str,
        arguments: dict[str, Any],
        root: Path,
    ) -> dict[str, Any]:
        tool = self.tools_by_name[name]
        schema = tool.get("inputSchema", {})
        properties = schema.get("properties", {})
        allowed = set(properties) - {"workspaceRoot"} if isinstance(properties, dict) else set()
        forwarded = {key: value for key, value in arguments.items() if key != "workspaceRoot"}
        unknown = sorted(set(forwarded) - allowed)
        if unknown:
            raise RouterError(-32602, f"unknown {name} arguments: {', '.join(unknown)}")
        for field in self.path_fields.get(name, ()):
            if field not in forwarded:
                continue
            value = forwarded[field]
            if not isinstance(value, str) or not value:
                raise RouterError(-32602, f"{field} must be a path under workspaceRoot")
            path = Path(value)
            if path.is_absolute():
                raise RouterError(-32602, f"{field} must stay under workspaceRoot")
            try:
                (root / path).resolve(strict=False).relative_to(root)
            except (OSError, ValueError) as exc:
                raise RouterError(-32602, f"{field} must stay under workspaceRoot") from exc
        return forwarded

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request.get("method")
        if not isinstance(method, str):
            return (
                None
                if "id" not in request
                else error_response(request_id, -32600, "invalid JSON-RPC request")
            )
        if method.startswith("notifications/"):
            return None
        try:
            if method == "initialize":
                params = request.get("params") if isinstance(request.get("params"), dict) else {}
                requested = params.get("protocolVersion")
                negotiated = requested if requested in LEGACY_PROTOCOLS else LEGACY_PROTOCOLS[-1]
                return result_response(
                    request_id,
                    {
                        "protocolVersion": negotiated,
                        "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": SERVER_INFO,
                        "instructions": (
                            "Pass an absolute workspaceRoot on every Dediren tool call."
                        ),
                    },
                )
            if method == "server/discover":
                return result_response(
                    request_id,
                    {
                        "resultType": "complete",
                        "supportedVersions": [MODERN_PROTOCOL, *LEGACY_PROTOCOLS],
                        "capabilities": {"tools": {"listChanged": False}},
                        "instructions": (
                            "Pass an absolute workspaceRoot on every Dediren tool call."
                        ),
                        "ttlMs": DISCOVER_TTL_MS,
                        "cacheScope": CACHE_SCOPE,
                        "_meta": SERVER_META,
                    },
                )
            if method == "ping":
                return result_response(request_id, {})
            if method == "tools/list":
                result: dict[str, Any] = {"tools": self.load_tools()}
                if self.modern(request):
                    result.update(
                        {
                            "resultType": "complete",
                            "ttlMs": TOOLS_TTL_MS,
                            "cacheScope": CACHE_SCOPE,
                            "_meta": SERVER_META,
                        }
                    )
                return result_response(request_id, result)
            if method == "tools/call":
                params = request.get("params")
                if not isinstance(params, dict):
                    raise RouterError(-32602, "tools/call params must be an object")
                name = params.get("name")
                arguments = params.get("arguments")
                if not isinstance(arguments, dict):
                    raise RouterError(-32602, "tool arguments must be an object")
                root = self.workspace(arguments)
                backend = self.backend(root)
                self.load_tools(backend)
                if not isinstance(name, str) or name not in self.tools_by_name:
                    raise RouterError(-32602, "unknown Dediren tool name")
                forwarded = self.validated_arguments(name, arguments, root)
                upstream_params: dict[str, Any] = {"name": name, "arguments": forwarded}
                for field in ("inputResponses", "requestState"):
                    if field in params:
                        upstream_params[field] = params[field]
                response = backend.request("tools/call", upstream_params)
                if "error" in response:
                    return {"jsonrpc": "2.0", "id": request_id, "error": response["error"]}
                result = response.get("result")
                if not isinstance(result, dict):
                    raise BackendError("installed Dediren returned no result object")
                if self.modern(request):
                    result = dict(result)
                    result.setdefault("resultType", "complete")
                    result.setdefault("_meta", SERVER_META)
                return result_response(request_id, result)
            return error_response(request_id, -32601, f"method not found: {method}")
        except RouterError as exc:
            return error_response(request_id, exc.code, str(exc))
        except BackendError as exc:
            return error_response(request_id, -32000, str(exc))


def result_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def positive_timeout(name: str, default: float) -> float:
    raw_timeout = os.environ.get(name, str(default))
    try:
        timeout = float(raw_timeout)
    except ValueError:
        return default
    return timeout if math.isfinite(timeout) and timeout > 0 else default


def emit(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    router = Router()

    def shutdown(signum: int, frame: Any) -> None:
        del frame
        router.close()
        raise SystemExit(128 + signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, shutdown)
    try:
        for line in sys.stdin:
            try:
                request = json.loads(line)
            except json.JSONDecodeError as exc:
                emit(error_response(None, -32700, f"parse error: {exc.msg}"))
                continue
            if not isinstance(request, dict):
                emit(error_response(None, -32600, "invalid JSON-RPC request"))
                continue
            response = router.handle(request)
            if response is not None:
                emit(response)
    finally:
        router.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
