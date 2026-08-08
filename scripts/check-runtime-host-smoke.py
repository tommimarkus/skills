#!/usr/bin/env python3
"""Smoke-test installed Claude Code, Codex, and Copilot plugin surfaces.

The command deliberately uses temporary ``CODEX_HOME`` and
``CLAUDE_CONFIG_DIR``, ``COPILOT_HOME``, and ``COPILOT_CACHE_HOME`` directories.
It never changes ``HOME`` and fingerprints the normal plugin/config control
planes before and after the run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MARKETPLACE = "souroldgeezer"
REQUIRED_DEDIREN_TOOLS = {
    "dediren_build",
    "dediren_diff",
    "dediren_guide",
    "dediren_query",
    "dediren_status",
    "dediren_validate",
    "dediren_verify",
}
DEFAULT_TIMEOUT_SECONDS = 120
MCP_TIMEOUT_SECONDS = 360


class SmokeFailure(RuntimeError):
    """A host-surface assertion or required command failed."""


Runner = Callable[..., subprocess.CompletedProcess[str]]
McpRunner = Callable[..., set[str]]


@dataclass(frozen=True)
class PluginExpectation:
    name: str
    claude_version: str
    codex_version: str
    copilot_version: str | None
    skills: tuple[str, ...]
    agents: tuple[str, ...]


@dataclass(frozen=True)
class SmokeSummary:
    plugins: int
    skills: int
    agents: int
    codex_validator: str
    dediren_tools: int
    copilot_skills: int


# lean-audit:dup-intentional:begin -- the injected runner deliberately mirrors
# checked() so test doubles and the subprocess adapter share one call contract.
def run_command(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    input_text: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=dict(env),
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
# lean-audit:dup-intentional:end


def checked(
    runner: Runner,
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    input_text: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    result = runner(
        argv,
        cwd=cwd,
        env=env,
        input_text=input_text,
        timeout=timeout,
    )
    if result.returncode != 0:
        rendered = " ".join(argv)
        raise SmokeFailure(
            f"command failed ({result.returncode}): {rendered}\n"
            f"stdout={result.stdout[-2000:]}\nstderr={result.stderr[-2000:]}"
        )
    return result


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SmokeFailure(f"cannot read JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SmokeFailure(f"expected a JSON object in {path}")
    return value


def command_json(result: subprocess.CompletedProcess[str], label: str) -> Any:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"{label} did not emit JSON: {result.stdout[-2000:]}") from exc


# lean-audit:dup-intentional:begin -- this typed convenience wrapper mirrors
# checked()'s required runner/cwd/env seam and adds only JSON decoding.
def checked_json(
    runner: Runner,
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    label: str,
) -> Any:
    """Run one required command and decode its machine-readable result."""
    return command_json(checked(runner, argv, cwd=cwd, env=env), label)
# lean-audit:dup-intentional:end


def validate_plugin(
    runner: Runner,
    plugin_dir: Path,
    *,
    host: str,
    cwd: Path,
    env: Mapping[str, str],
) -> None:
    """Run a host's first-party validator without duplicating command checks."""
    argv = [host.lower(), "plugin", "validate"]
    if host == "Claude":
        argv.append("--strict")
    argv.append(str(plugin_dir))
    checked(runner, argv, cwd=cwd, env=env)


def semantic_version(value: str) -> tuple[int, int, int]:
    parts = value.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise SmokeFailure(f"invalid three-part version: {value!r}")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def load_expectations(repo: Path) -> list[PluginExpectation]:
    claude_marketplace = read_json(repo / ".claude-plugin" / "marketplace.json")
    codex_marketplace = read_json(repo / ".agents" / "plugins" / "marketplace.json")
    claude_plugins = claude_marketplace.get("plugins")
    codex_plugins = codex_marketplace.get("plugins")
    if not isinstance(claude_plugins, list) or not isinstance(codex_plugins, list):
        raise SmokeFailure("both marketplaces must contain plugins[]")

    claude_names = [entry.get("name") for entry in claude_plugins]
    codex_names = [entry.get("name") for entry in codex_plugins]
    if claude_names != codex_names:
        raise SmokeFailure(
            f"marketplace plugin order differs: Claude={claude_names}, Codex={codex_names}"
        )
    if len(claude_names) != 5:
        raise SmokeFailure(f"expected five published plugins, found {len(claude_names)}")

    expectations: list[PluginExpectation] = []
    for claude_entry, codex_entry in zip(claude_plugins, codex_plugins, strict=True):
        name = claude_entry.get("name")
        if not isinstance(name, str) or not name:
            raise SmokeFailure("marketplace plugin name must be a nonempty string")
        claude_source = claude_entry.get("source")
        codex_source = codex_entry.get("source")
        if not isinstance(claude_source, str) or not isinstance(codex_source, dict):
            raise SmokeFailure(f"invalid marketplace source for {name}")
        if codex_source.get("source") != "local" or codex_source.get("path") != claude_source:
            raise SmokeFailure(f"marketplace source differs for {name}")

        plugin_dir = repo / claude_source.removeprefix("./")
        claude_manifest = read_json(plugin_dir / ".claude-plugin" / "plugin.json")
        codex_manifest = read_json(plugin_dir / ".codex-plugin" / "plugin.json")
        claude_version = claude_manifest.get("version")
        codex_version = codex_manifest.get("version")
        if not isinstance(claude_version, str) or not isinstance(codex_version, str):
            raise SmokeFailure(f"both manifests must declare a version for {name}")
        if semantic_version(claude_version) != semantic_version(codex_version):
            raise SmokeFailure(f"manifest versions differ semantically for {name}")

        skills_dir = plugin_dir / "skills"
        agents_dir = plugin_dir / "agents"
        skills = tuple(
            sorted(path.parent.name for path in skills_dir.glob("*/SKILL.md") if path.is_file())
        )
        agents = tuple(sorted(path.stem for path in agents_dir.glob("*.md") if path.is_file()))
        copilot_path = plugin_dir / "plugin.json"
        copilot_version: str | None = None
        if copilot_path.is_file():
            copilot_manifest = read_json(copilot_path)
            value = copilot_manifest.get("version")
            if not isinstance(value, str):
                raise SmokeFailure(f"Copilot manifest must declare a version for {name}")
            if semantic_version(value) != semantic_version(claude_version):
                raise SmokeFailure(f"Copilot manifest version differs semantically for {name}")
            copilot_version = value
        expectations.append(
            PluginExpectation(
                name,
                claude_version,
                codex_version,
                copilot_version,
                skills,
                agents,
            )
        )

    skill_count = sum(len(expectation.skills) for expectation in expectations)
    if skill_count != 15:
        raise SmokeFailure(f"expected 15 shared public skills, found {skill_count}")
    return expectations


def _fingerprint_path(path: Path) -> str:
    digest = hashlib.sha256()
    if not path.exists() and not path.is_symlink():
        digest.update(b"missing")
        return digest.hexdigest()

    candidates = [path]
    if path.is_dir() and not path.is_symlink():
        candidates.extend(sorted(path.rglob("*"), key=lambda item: item.as_posix()))

    for candidate in candidates:
        try:
            info = candidate.lstat()
            relative = "." if candidate == path else candidate.relative_to(path).as_posix()
            digest.update(relative.encode("utf-8", errors="surrogateescape"))
            digest.update(str(stat.S_IFMT(info.st_mode)).encode("ascii"))
            digest.update(str(stat.S_IMODE(info.st_mode)).encode("ascii"))
            if candidate.is_symlink():
                digest.update(os.readlink(candidate).encode("utf-8", errors="surrogateescape"))
            elif candidate.is_file():
                with candidate.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
        except OSError as exc:
            raise SmokeFailure(
                f"cannot fingerprint normal profile path {candidate}: {exc}"
            ) from exc
    return digest.hexdigest()


def profile_fingerprints(paths: Sequence[Path]) -> dict[str, str]:
    return {str(path): _fingerprint_path(path) for path in paths}


def default_profile_control_paths(env: Mapping[str, str]) -> tuple[Path, ...]:
    home = Path.home()
    codex_root = Path(env.get("CODEX_HOME", home / ".codex")).expanduser()
    claude_root = Path(env.get("CLAUDE_CONFIG_DIR", home / ".claude")).expanduser()
    copilot_root = Path(env.get("COPILOT_HOME", home / ".copilot")).expanduser()
    if "COPILOT_CACHE_HOME" in env:
        copilot_marketplaces = Path(env["COPILOT_CACHE_HOME"]).expanduser() / "marketplaces"
    else:
        cache_home = Path(env.get("XDG_CACHE_HOME", home / ".cache")).expanduser()
        copilot_marketplaces = cache_home / "copilot" / "marketplaces"
    claude_config = (
        claude_root / ".claude.json" if "CLAUDE_CONFIG_DIR" in env else home / ".claude.json"
    )
    return (
        codex_root / "config.toml",
        codex_root / "plugins",
        codex_root / ".tmp" / "marketplaces",
        codex_root / ".tmp" / "plugins",
        claude_config,
        claude_root / "settings.json",
        claude_root / "settings.local.json",
        claude_root / "plugins",
        copilot_root / "config.json",
        copilot_root / "settings.json",
        copilot_root / "installed-plugins",
        copilot_root / "plugin-data",
        copilot_marketplaces,
    )


def require_under(path: Path, parent: Path, label: str) -> None:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise SmokeFailure(f"{label} escaped temporary state: {path}") from exc


def assert_installed_skills(
    installed_path: Path,
    expectation: PluginExpectation,
    state_root: Path,
    host: str,
) -> None:
    require_under(installed_path, state_root, f"{host} install path")
    if not installed_path.is_dir():
        raise SmokeFailure(f"{host} install path does not exist: {installed_path}")
    actual = tuple(
        sorted(
            path.parent.name
            for path in (installed_path / "skills").glob("*/SKILL.md")
            if path.is_file()
        )
    )
    if actual != expectation.skills:
        raise SmokeFailure(
            f"{host} installed skills differ for {expectation.name}: "
            f"expected={expectation.skills}, actual={actual}"
        )


def strings_in(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in strings_in(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in strings_in(item)]
    return []


def parse_component_inventory(details: str, component: str) -> tuple[str, ...]:
    match = re.search(
        rf"^\s*{re.escape(component)} \(\d+\)\s*(.*)$",
        details,
        flags=re.MULTILINE,
    )
    if match is None:
        raise SmokeFailure(f"Claude details omitted {component} component inventory")
    return tuple(sorted(part.rstrip(",") for part in match.group(1).split()))


def run_mcp_session(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    runner: Runner = run_command,
    label: str,
) -> set[str]:
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "runtime-host-smoke", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "server/discover",
            "params": {
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                    "io.modelcontextprotocol/clientInfo": {
                        "name": "runtime-host-smoke",
                        "version": "1",
                    },
                    "io.modelcontextprotocol/clientCapabilities": {},
                }
            },
        },
    ]
    input_text = "".join(json.dumps(request) + "\n" for request in requests)
    result = checked(
        runner,
        argv,
        cwd=cwd,
        env=env,
        input_text=input_text,
        timeout=MCP_TIMEOUT_SECONDS,
    )
    responses: dict[int, dict[str, Any]] = {}
    for line in result.stdout.splitlines():
        if not line.lstrip().startswith("{"):
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(message, dict) and isinstance(message.get("id"), int):
            responses[message["id"]] = message
    if set(responses) != {1, 2, 3}:
        raise SmokeFailure(
            f"{label} Dediren adapter omitted JSON-RPC responses; "
            f"ids={sorted(responses)}, stderr={result.stderr[-2000:]}"
        )
    tools = responses[2].get("result", {}).get("tools")
    if not isinstance(tools, list):
        raise SmokeFailure(f"{label} Dediren tools/list response has no tools[]")
    names: set[str] = set()
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = tool.get("name")
        if isinstance(name, str):
            names.add(name)
        schema = tool.get("inputSchema")
        if not isinstance(schema, dict):
            raise SmokeFailure(f"{label} Dediren tool {name} omitted inputSchema")
        properties = schema.get("properties")
        required = schema.get("required")
        if not isinstance(properties, dict) or "workspaceRoot" not in properties:
            raise SmokeFailure(f"{label} Dediren tool {name} omitted workspaceRoot")
        if not isinstance(required, list) or "workspaceRoot" not in required:
            raise SmokeFailure(f"{label} Dediren tool {name} did not require workspaceRoot")
    missing = REQUIRED_DEDIREN_TOOLS - names
    if missing:
        raise SmokeFailure(
            f"{label} Dediren omitted required tools: "
            f"missing={sorted(missing)}, actual={sorted(names)}"
        )
    discovery = responses[3].get("result", {})
    if "2026-07-28" not in discovery.get("supportedVersions", []):
        raise SmokeFailure(f"{label} Dediren adapter omitted stateless protocol discovery")
    return names


def expand_claude(value: str, *, plugin_root: Path, plugin_data: Path, project: Path) -> str:
    return (
        value.replace("${CLAUDE_PLUGIN_ROOT}", str(plugin_root))
        .replace("${CLAUDE_PLUGIN_DATA}", str(plugin_data))
        .replace("${CLAUDE_PROJECT_DIR}", str(project))
    )


def expand_copilot(value: str, *, plugin_root: Path, plugin_data: Path) -> str:
    return (
        value.replace("${PLUGIN_ROOT}", str(plugin_root))
        .replace("${COPILOT_PLUGIN_ROOT}", str(plugin_root))
        .replace("${COPILOT_PLUGIN_DATA}", str(plugin_data))
        .replace("${CLAUDE_PLUGIN_DATA}", str(plugin_data))
    )


def _verify_plugin_records(
    records: Sequence[dict[str, Any]],
    expectations: Sequence[PluginExpectation],
    *,
    host: str,
) -> None:
    by_name: dict[str, dict[str, Any]] = {}
    for record in records:
        name = record.get("name")
        if not isinstance(name, str):
            plugin_id = record.get("id")
            if isinstance(plugin_id, str):
                name = plugin_id.split("@", 1)[0]
        if isinstance(name, str):
            by_name[name] = record
    if set(by_name) != {expectation.name for expectation in expectations}:
        raise SmokeFailure(f"{host} installed plugin set differs: {sorted(by_name)}")
    for expectation in expectations:
        record = by_name[expectation.name]
        expected_version = (
            expectation.codex_version if host == "Codex" else expectation.claude_version
        )
        if record.get("version") != expected_version:
            raise SmokeFailure(
                f"{host} version differs for {expectation.name}: {record.get('version')}"
            )
        if record.get("enabled") is not True:
            raise SmokeFailure(f"{host} plugin is not enabled: {expectation.name}")


def run_host_smoke(
    repo: Path,
    state_root: Path,
    *,
    base_env: Mapping[str, str] | None = None,
    runner: Runner = run_command,
    mcp_runner: McpRunner = run_mcp_session,
    normal_profile_paths: Sequence[Path] | None = None,
) -> SmokeSummary:
    repo = repo.resolve()
    state_root = state_root.resolve()
    if not repo.is_dir():
        raise SmokeFailure(f"repository root does not exist: {repo}")
    if any(state_root.iterdir()):
        raise SmokeFailure(f"fresh state directory is not empty: {state_root}")

    env = dict(os.environ if base_env is None else base_env)
    profiles = tuple(
        default_profile_control_paths(env) if normal_profile_paths is None else normal_profile_paths
    )
    for profile in profiles:
        if profile.resolve() == state_root or state_root.is_relative_to(profile.resolve()):
            raise SmokeFailure(f"temporary state overlaps normal profile path: {profile}")
    profile_before = profile_fingerprints(profiles)

    codex_home = state_root / "codex-home"
    claude_config = state_root / "claude-config"
    copilot_home = state_root / "copilot-home"
    copilot_cache = state_root / "copilot-cache"
    runtime_data = state_root / "runtime-data"
    codex_home.mkdir()
    claude_config.mkdir()
    copilot_home.mkdir()
    copilot_cache.mkdir()
    runtime_data.mkdir()

    codex_env = env.copy()
    codex_env["CODEX_HOME"] = str(codex_home)
    codex_env.pop("CLAUDE_CONFIG_DIR", None)
    codex_env.pop("CLAUDE_PROJECT_DIR", None)
    claude_env = env.copy()
    claude_env["CLAUDE_CONFIG_DIR"] = str(claude_config)
    claude_env.pop("CODEX_HOME", None)
    claude_env.pop("COPILOT_HOME", None)
    claude_env.pop("COPILOT_CACHE_HOME", None)
    copilot_env = env.copy()
    copilot_env["COPILOT_HOME"] = str(copilot_home)
    copilot_env["COPILOT_CACHE_HOME"] = str(copilot_cache)
    copilot_env.pop("CODEX_HOME", None)
    copilot_env.pop("CLAUDE_CONFIG_DIR", None)
    copilot_env.pop("CLAUDE_PROJECT_DIR", None)
    codex_env.pop("COPILOT_HOME", None)
    codex_env.pop("COPILOT_CACHE_HOME", None)

    expectations = load_expectations(repo)
    pending: BaseException | None = None
    summary: SmokeSummary | None = None
    try:
        checked(runner, ["codex", "--version"], cwd=repo, env=codex_env)
        checked(runner, ["claude", "--version"], cwd=repo, env=claude_env)
        checked(runner, ["copilot", "--version"], cwd=repo, env=copilot_env)

        codex_add_marketplace = checked_json(
            runner,
            ["codex", "plugin", "marketplace", "add", str(repo), "--json"],
            cwd=repo,
            env=codex_env,
            label="codex plugin marketplace add",
        )
        if codex_add_marketplace.get("marketplaceName") != MARKETPLACE:
            raise SmokeFailure("Codex registered the repository under the wrong marketplace name")

        codex_installs: dict[str, Path] = {}
        for expectation in expectations:
            payload = checked_json(
                runner,
                [
                    "codex",
                    "plugin",
                    "add",
                    f"{expectation.name}@{MARKETPLACE}",
                    "--json",
                ],
                cwd=repo,
                env=codex_env,
                label=f"codex plugin add {expectation.name}",
            )
            installed_path = Path(payload.get("installedPath", ""))
            assert_installed_skills(installed_path, expectation, state_root, "Codex")
            codex_installs[expectation.name] = installed_path

        # lean-audit:dup-intentional:begin -- adjacent discovery probes use the
        # same checked-JSON seam but validate different host surfaces.
        codex_list = checked_json(
            runner,
            ["codex", "plugin", "list", "--json"],
            cwd=repo,
            env=codex_env,
            label="codex plugin list",
        )
        # lean-audit:dup-intentional:end
        codex_records = codex_list.get("installed")
        if not isinstance(codex_records, list):
            raise SmokeFailure("Codex plugin list JSON omitted installed[]")
        _verify_plugin_records(codex_records, expectations, host="Codex")

        prompt_input = checked_json(
            runner,
            ["codex", "debug", "prompt-input", "Use an installed Sour Old Geezer skill."],
            cwd=repo,
            env=codex_env,
            label="codex debug prompt-input",
        )
        prompt_text = "\n".join(strings_in(prompt_input))
        for expectation in expectations:
            for skill in expectation.skills:
                marker = f"- {expectation.name}:{skill}:"
                if marker not in prompt_text:
                    raise SmokeFailure(f"Codex prompt discovery omitted {marker}")
                skill_path = codex_installs[expectation.name] / "skills" / skill / "SKILL.md"
                if str(skill_path) not in prompt_text:
                    raise SmokeFailure(f"Codex prompt discovery used the wrong path for {marker}")

        plugin_help = checked(
            runner,
            ["codex", "plugin", "--help"],
            cwd=repo,
            env=codex_env,
        ).stdout
        has_codex_validator = re.search(r"^\s+validate\s", plugin_help, re.MULTILINE) is not None
        if has_codex_validator:
            for expectation in expectations:
                # lean-audit:dup-intentional:begin -- both hosts deliberately
                # validate the same plugin set through the shared adapter.
                validate_plugin(
                    runner,
                    repo / expectation.name,
                    host="Codex",
                    cwd=repo,
                    env=codex_env,
                )
                # lean-audit:dup-intentional:end
            codex_validator = "passed"
        else:
            codex_validator = "skipped: current Codex CLI has no plugin validate command"

        checked(
            runner,
            [
                "claude",
                "plugin",
                "marketplace",
                "add",
                str(repo),
                "--scope",
                "user",
            ],
            cwd=repo,
            env=claude_env,
        )
        for expectation in expectations:
            checked(
                runner,
                [
                    "claude",
                    "plugin",
                    "install",
                    f"{expectation.name}@{MARKETPLACE}",
                    "--scope",
                    "user",
                ],
                cwd=repo,
                env=claude_env,
            )

        claude_list = checked_json(
            runner,
            ["claude", "plugin", "list", "--json"],
            cwd=repo,
            env=claude_env,
            label="claude plugin list",
        )
        if not isinstance(claude_list, list):
            raise SmokeFailure("Claude plugin list must emit a JSON array")
        _verify_plugin_records(claude_list, expectations, host="Claude")
        claude_by_name = {
            record["id"].split("@", 1)[0]: record
            for record in claude_list
            if isinstance(record, dict) and isinstance(record.get("id"), str)
        }
        for expectation in expectations:
            install_path = Path(claude_by_name[expectation.name].get("installPath", ""))
            assert_installed_skills(install_path, expectation, state_root, "Claude")
            validate_plugin(
                runner,
                repo / expectation.name,
                host="Claude",
                cwd=repo,
                env=claude_env,
            )
            details = checked(
                runner,
                [
                    "claude",
                    "plugin",
                    "details",
                    f"{expectation.name}@{MARKETPLACE}",
                ],
                cwd=repo,
                env=claude_env,
            ).stdout
            if parse_component_inventory(details, "Skills") != expectation.skills:
                raise SmokeFailure(f"Claude details skill inventory differs for {expectation.name}")
            if parse_component_inventory(details, "Agents") != expectation.agents:
                raise SmokeFailure(f"Claude details agent inventory differs for {expectation.name}")

        architecture = next(
            expectation
            for expectation in expectations
            if expectation.name == "souroldgeezer-architecture"
        )
        if architecture.copilot_version is None:
            raise SmokeFailure("architecture plugin omitted its native Copilot manifest")
        checked(
            runner,
            ["copilot", "plugin", "marketplace", "add", str(repo)],
            cwd=repo,
            env=copilot_env,
        )
        checked(
            runner,
            [
                "copilot",
                "plugin",
                "install",
                f"{architecture.name}@{MARKETPLACE}",
            ],
            cwd=repo,
            env=copilot_env,
        )
        copilot_list = checked(
            runner,
            ["copilot", "plugin", "list"],
            cwd=repo,
            env=copilot_env,
        ).stdout
        copilot_marker = (
            f"{architecture.name}@{MARKETPLACE} (v{architecture.copilot_version})"
        )
        if copilot_marker not in copilot_list:
            raise SmokeFailure(f"Copilot plugin list omitted {copilot_marker}")
        copilot_arch_root = (
            copilot_home / "installed-plugins" / MARKETPLACE / architecture.name
        )
        assert_installed_skills(copilot_arch_root, architecture, state_root, "Copilot")
        copilot_manifest = read_json(copilot_arch_root / "plugin.json")
        if copilot_manifest.get("version") != architecture.copilot_version:
            raise SmokeFailure("Copilot installed architecture plugin at the wrong version")
        copilot_mcp_list = checked_json(
            runner,
            ["copilot", "mcp", "list", "--json"],
            cwd=repo,
            env=copilot_env,
            label="copilot mcp list",
        )
        copilot_servers = copilot_mcp_list.get("mcpServers")
        if not isinstance(copilot_servers, dict):
            raise SmokeFailure("Copilot MCP list omitted mcpServers")
        copilot_server = copilot_servers.get("dediren")
        if not isinstance(copilot_server, dict):
            raise SmokeFailure("installed Copilot plugin omitted the Dediren adapter")
        if copilot_server.get("sourcePlugin") != architecture.name:
            raise SmokeFailure("Copilot loaded Dediren from the wrong plugin")
        if copilot_server.get("sourcePluginVersion") != architecture.copilot_version:
            raise SmokeFailure("Copilot loaded Dediren from the wrong plugin version")
        if "codex plugin" in json.dumps(copilot_server):
            raise SmokeFailure("Copilot incorrectly loaded the Codex MCP bootstrap")

        codex_arch_root = codex_installs[architecture.name]
        codex_manifest = read_json(codex_arch_root / ".codex-plugin" / "plugin.json")
        codex_mcp_path = codex_arch_root / str(codex_manifest.get("mcpServers", "")).removeprefix(
            "./"
        )
        codex_servers = read_json(codex_mcp_path)
        codex_server = codex_servers.get("dediren")
        if not isinstance(codex_server, dict):
            raise SmokeFailure("installed Codex plugin omitted the Dediren adapter")
        codex_mcp_env = codex_env.copy()
        codex_tools = mcp_runner(
            [codex_server["command"], *codex_server.get("args", [])],
            cwd=repo,
            env=codex_mcp_env,
            label="Codex",
        )

        claude_arch_record = claude_by_name[architecture.name]
        claude_arch_root = Path(claude_arch_record["installPath"])
        claude_manifest = read_json(claude_arch_root / ".claude-plugin" / "plugin.json")
        claude_servers = claude_manifest.get("mcpServers")
        if not isinstance(claude_servers, dict) or not isinstance(
            claude_servers.get("dediren"), dict
        ):
            raise SmokeFailure("installed Claude plugin omitted the Dediren adapter")
        claude_server = claude_servers["dediren"]
        claude_plugin_data = runtime_data
        claude_mcp_env = claude_env.copy()
        claude_mcp_env["CLAUDE_PROJECT_DIR"] = str(repo)
        for key, value in claude_server.get("env", {}).items():
            claude_mcp_env[key] = expand_claude(
                value,
                plugin_root=claude_arch_root,
                plugin_data=claude_plugin_data,
                project=repo,
            )
        claude_command = expand_claude(
            claude_server["command"],
            plugin_root=claude_arch_root,
            plugin_data=claude_plugin_data,
            project=repo,
        )
        claude_args = [
            expand_claude(
                value,
                plugin_root=claude_arch_root,
                plugin_data=claude_plugin_data,
                project=repo,
            )
            for value in claude_server.get("args", [])
        ]
        claude_tools = mcp_runner(
            [claude_command, *claude_args],
            cwd=repo,
            env=claude_mcp_env,
            label="Claude",
        )
        copilot_plugin_data = runtime_data / "copilot" / architecture.name
        copilot_mcp_env = copilot_env.copy()
        for key, value in copilot_server.get("env", {}).items():
            copilot_mcp_env[key] = expand_copilot(
                value,
                plugin_root=copilot_arch_root,
                plugin_data=copilot_plugin_data,
            )
        copilot_command = expand_copilot(
            copilot_server["command"],
            plugin_root=copilot_arch_root,
            plugin_data=copilot_plugin_data,
        )
        copilot_args = [
            expand_copilot(
                value,
                plugin_root=copilot_arch_root,
                plugin_data=copilot_plugin_data,
            )
            for value in copilot_server.get("args", [])
        ]
        copilot_cwd = Path(
            expand_copilot(
                copilot_server.get("cwd", str(repo)),
                plugin_root=copilot_arch_root,
                plugin_data=copilot_plugin_data,
            )
        )
        copilot_tools = mcp_runner(
            [copilot_command, *copilot_args],
            cwd=copilot_cwd,
            env=copilot_mcp_env,
            label="Copilot",
        )
        if not codex_tools == claude_tools == copilot_tools:
            raise SmokeFailure("Dediren tool surfaces differ across host adapters")

        summary = SmokeSummary(
            plugins=len(expectations),
            skills=sum(len(expectation.skills) for expectation in expectations),
            agents=sum(len(expectation.agents) for expectation in expectations),
            codex_validator=codex_validator,
            dediren_tools=len(codex_tools),
            copilot_skills=len(architecture.skills),
        )
    except BaseException as exc:
        pending = exc

    profile_after = profile_fingerprints(profiles)
    changed_profiles = [
        path for path in profile_before if profile_before[path] != profile_after[path]
    ]
    if changed_profiles:
        detail = ", ".join(changed_profiles)
        isolation_error = SmokeFailure(f"normal profile control plane changed: {detail}")
        if pending is not None:
            raise isolation_error from pending
        raise isolation_error
    if pending is not None:
        raise pending
    if summary is None:
        raise SmokeFailure("host smoke produced no summary")
    return summary


# lean-audit:dup-intentional:begin -- independent CLI entrypoints retain local
# safety flags, dependency checks, diagnostics, and exit-code wording.
def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="require a new empty temporary runtime state (mandatory safety flag)",
    )
    parser.add_argument(
        "--assert-profile-isolation",
        action="store_true",
        help="fingerprint normal plugin/config control planes before and after (mandatory)",
    )
    parser.add_argument("repo", nargs="?", default=".", help="repository root to install")
    args = parser.parse_args(argv)
    if not args.fresh or not args.assert_profile_isolation:
        parser.error("--fresh and --assert-profile-isolation are both required")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    for executable in ("codex", "claude", "copilot"):
        if shutil.which(executable) is None:
            print(f"Error: required CLI is not installed: {executable}", file=sys.stderr)
            return 2

    repo = Path(args.repo).resolve()
    try:
        with tempfile.TemporaryDirectory(prefix="runtime-host-smoke-") as temporary:
            summary = run_host_smoke(repo, Path(temporary))
    except (OSError, SmokeFailure, subprocess.TimeoutExpired) as exc:
        print(f"Runtime host smoke failed: {exc}", file=sys.stderr)
        return 1

    print(f"PASS: isolated installs: {summary.plugins} plugins, {summary.skills} shared skills")
    print(f"PASS: Claude installed component discovery: {summary.agents} agent definitions")
    print(f"PASS: Copilot installed skill discovery: {summary.copilot_skills} shared skill")
    if summary.codex_validator.startswith("skipped:"):
        print(f"SKIP: {summary.codex_validator.removeprefix('skipped: ')}")
    else:
        print("PASS: Codex first-party plugin validation")
    print(f"PASS: Dediren JSON-RPC parity: {summary.dediren_tools} tools per host adapter")
    print("PASS: normal Codex, Claude, and Copilot plugin/config profiles unchanged")
    print("Runtime host smoke OK")
    return 0
# lean-audit:dup-intentional:end


if __name__ == "__main__":
    raise SystemExit(main())
