#!/usr/bin/env python3
"""Workspace-explicit MCP router for an externally installed Dediren CLI."""

from __future__ import annotations

import atexit
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


SERVER_INFO = {"name": "dediren-workspace-router", "version": "1.0.0"}
MODERN_PROTOCOL = "2026-07-28"
LEGACY_PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
SERVER_META = {"io.modelcontextprotocol/serverInfo": SERVER_INFO}
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


class Backend:
    def __init__(self, root: Path, launcher: Path) -> None:
        self.root = root
        try:
            self.process = subprocess.Popen(
                [str(launcher), "--upstream", str(root)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=None,
                text=True,
                bufsize=1,
                env=os.environ.copy(),
            )
        except OSError as exc:
            raise BackendError(f"could not start the installed Dediren CLI: {exc}") from exc
        self.next_id = 1
        self.modern = False
        discovery = self.request(
            "server/discover",
            {
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": MODERN_PROTOCOL,
                    "io.modelcontextprotocol/clientInfo": SERVER_INFO,
                    "io.modelcontextprotocol/clientCapabilities": {},
                }
            },
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
        )
        if "result" not in response:
            self.close()
            raise BackendError(f"Dediren initialization failed: {response.get('error')}")
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def send(self, message: dict[str, Any]) -> None:
        if self.process.stdin is None:
            raise BackendError("Dediren stdin is unavailable")
        try:
            self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise BackendError("Dediren closed its input") from exc

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
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
        if self.process.stdout is None:
            raise BackendError("Dediren stdout is unavailable")
        for line in self.process.stdout:
            try:
                response = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(response, dict) and response.get("id") == request_id:
                return response
        raise BackendError(
            f"Dediren exited before responding (exit {self.process.poll()})"
        )

    def close(self) -> None:
        if self.process.poll() is not None:
            return
        if self.process.stdin is not None:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)


class Router:
    def __init__(self) -> None:
        default_launcher = Path(__file__).with_name("dediren-mcp.sh")
        self.launcher = Path(os.environ.get("DEDIREN_MCP_LAUNCHER", default_launcher))
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
        return isinstance(meta, dict) and meta.get(
            "io.modelcontextprotocol/protocolVersion"
        ) == MODERN_PROTOCOL

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
        backend = Backend(root, self.launcher)
        self.backends[root] = backend
        return backend

    def load_tools(self, backend: Backend | None = None) -> list[dict[str, Any]]:
        if self.tools is not None:
            return self.tools
        if backend is None:
            backend = self.backend(Path.cwd().resolve())
        raw_tools: list[Any] = []
        cursor: str | None = None
        while True:
            params = {"cursor": cursor} if cursor is not None else {}
            response = backend.request("tools/list", params)
            result = response.get("result")
            page = result.get("tools") if isinstance(result, dict) else None
            if not isinstance(page, list):
                raise BackendError("installed Dediren returned no tools[] catalog")
            raw_tools.extend(page)
            next_cursor = result.get("nextCursor")
            if not isinstance(next_cursor, str) or not next_cursor:
                break
            cursor = next_cursor

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
            return None if "id" not in request else error_response(
                request_id, -32600, "invalid JSON-RPC request"
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
                        "instructions": "Pass an absolute workspaceRoot on every Dediren tool call.",
                    },
                )
            if method == "server/discover":
                return result_response(
                    request_id,
                    {
                        "resultType": "complete",
                        "supportedVersions": [MODERN_PROTOCOL, *LEGACY_PROTOCOLS],
                        "capabilities": {"tools": {"listChanged": False}},
                        "instructions": "Pass an absolute workspaceRoot on every Dediren tool call.",
                        "_meta": SERVER_META,
                    },
                )
            if method == "ping":
                return result_response(request_id, {})
            if method == "tools/list":
                result: dict[str, Any] = {"tools": self.load_tools()}
                if self.modern(request):
                    result.update({"resultType": "complete", "_meta": SERVER_META})
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


def emit(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    router = Router()
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
    router.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
