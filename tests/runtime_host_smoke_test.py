import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, load_script_module

SCRIPT = REPO_ROOT / "scripts" / "check-runtime-host-smoke.py"
smoke = load_script_module("runtime_host_smoke", SCRIPT)


class FakeCliRunner:
    """In-process CLI double that materializes realistic isolated install trees."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.calls: list[tuple[tuple[str, ...], dict[str, str]]] = []
        self.codex_installs: dict[str, Path] = {}
        self.claude_installs: dict[str, Path] = {}

    @staticmethod
    def completed(argv, stdout: str = "", stderr: str = "", returncode: int = 0):
        return subprocess.CompletedProcess(list(argv), returncode, stdout, stderr)

    def install(self, host: str, name: str, root: Path) -> tuple[Path, str]:
        manifest_dir = ".codex-plugin" if host == "codex" else ".claude-plugin"
        manifest = json.loads(
            (self.repo / name / manifest_dir / "plugin.json").read_text(encoding="utf-8")
        )
        version = manifest["version"]
        destination = root / "plugins" / "cache" / smoke.MARKETPLACE / name / version
        shutil.copytree(self.repo / name, destination)
        return destination, version

    def __call__(
        self,
        argv,
        *,
        cwd: Path,
        env,
        input_text=None,
        timeout=120,
    ):
        del cwd, input_text, timeout
        args = tuple(str(value) for value in argv)
        child_env = dict(env)
        self.calls.append((args, child_env))

        if args == ("codex", "--version"):
            return self.completed(args, "codex-cli 99.0.0\n")
        if args == ("claude", "--version"):
            return self.completed(args, "99.0.0 (Claude Code)\n")

        if args[:4] == ("codex", "plugin", "marketplace", "add"):
            root = Path(child_env["CODEX_HOME"])
            (root / ".tmp" / "marketplaces").mkdir(parents=True, exist_ok=True)
            return self.completed(
                args,
                json.dumps(
                    {
                        "marketplaceName": smoke.MARKETPLACE,
                        "installedRoot": str(self.repo),
                        "alreadyAdded": False,
                    }
                ),
            )
        if args[:3] == ("codex", "plugin", "add"):
            name = args[3].split("@", 1)[0]
            path, version = self.install("codex", name, Path(child_env["CODEX_HOME"]))
            self.codex_installs[name] = path
            return self.completed(
                args,
                json.dumps(
                    {
                        "pluginId": f"{name}@{smoke.MARKETPLACE}",
                        "name": name,
                        "marketplaceName": smoke.MARKETPLACE,
                        "version": version,
                        "installedPath": str(path),
                    }
                ),
            )
        if args == ("codex", "plugin", "list", "--json"):
            records = []
            for name, path in self.codex_installs.items():
                version = path.name
                records.append(
                    {
                        "pluginId": f"{name}@{smoke.MARKETPLACE}",
                        "name": name,
                        "marketplaceName": smoke.MARKETPLACE,
                        "version": version,
                        "installed": True,
                        "enabled": True,
                        "source": {"source": "local", "path": str(self.repo / name)},
                    }
                )
            return self.completed(args, json.dumps({"installed": records}))
        if args[:3] == ("codex", "debug", "prompt-input"):
            lines = []
            for name, path in self.codex_installs.items():
                for skill_path in sorted((path / "skills").glob("*/SKILL.md")):
                    lines.append(f"- {name}:{skill_path.parent.name}: fake (file: {skill_path})")
            payload = [
                {
                    "type": "message",
                    "content": [{"type": "input_text", "text": "\n".join(lines)}],
                }
            ]
            return self.completed(args, json.dumps(payload))
        if args == ("codex", "plugin", "--help"):
            return self.completed(args, "Commands:\n  add\n  list\n  marketplace\n  remove\n")

        if args[:4] == ("claude", "plugin", "marketplace", "add"):
            root = Path(child_env["CLAUDE_CONFIG_DIR"])
            root.mkdir(parents=True, exist_ok=True)
            (root / ".claude.json").write_text("{}\n", encoding="utf-8")
            return self.completed(args, "Successfully added marketplace\n")
        if args[:3] == ("claude", "plugin", "install"):
            name = args[3].split("@", 1)[0]
            path, _ = self.install("claude", name, Path(child_env["CLAUDE_CONFIG_DIR"]))
            self.claude_installs[name] = path
            return self.completed(args, "Successfully installed plugin\n")
        if args == ("claude", "plugin", "list", "--json"):
            records = []
            for name, path in self.claude_installs.items():
                records.append(
                    {
                        "id": f"{name}@{smoke.MARKETPLACE}",
                        "version": path.name,
                        "scope": "user",
                        "enabled": True,
                        "installPath": str(path),
                    }
                )
            return self.completed(args, json.dumps(records))
        if args[:4] == ("claude", "plugin", "validate", "--strict"):
            return self.completed(args, "Validation passed\n")
        if args[:3] == ("claude", "plugin", "details"):
            name = args[3].split("@", 1)[0]
            path = self.claude_installs[name]
            skills = sorted(item.parent.name for item in (path / "skills").glob("*/SKILL.md"))
            agents = sorted(item.stem for item in (path / "agents").glob("*.md"))
            details = (
                f"{name} {path.name}\n"
                "Component inventory\n"
                f"  Skills ({len(skills)})  {', '.join(skills)}\n"
                f"  Agents ({len(agents)})  {', '.join(agents)}\n"
            )
            return self.completed(args, details)

        return self.completed(args, stderr=f"unexpected fake CLI call: {args}", returncode=64)


class RuntimeHostSmokeTest(unittest.TestCase):
    def test_fresh_host_orchestration_uses_only_isolated_cli_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "fresh-state"
            state.mkdir()
            normal_codex = root / "normal-codex"
            normal_claude = root / "normal-claude"
            normal_codex.mkdir()
            normal_claude.mkdir()
            (normal_codex / "config.toml").write_text("model = 'unchanged'\n", encoding="utf-8")
            (normal_claude / ".claude.json").write_text("{}\n", encoding="utf-8")

            fake = FakeCliRunner(REPO_ROOT)
            mcp_calls = []

            def fake_mcp(argv, *, cwd, env, label):
                mcp_calls.append((tuple(argv), cwd, dict(env), label))
                return set(smoke.EXPECTED_DEDIREN_TOOLS)

            base_env = os.environ.copy()
            original_home = base_env.get("HOME")
            summary = smoke.run_host_smoke(
                REPO_ROOT,
                state,
                base_env=base_env,
                runner=fake,
                mcp_runner=fake_mcp,
                normal_profile_paths=(
                    normal_codex / "config.toml",
                    normal_codex / "plugins",
                    normal_claude / ".claude.json",
                    normal_claude / "plugins",
                ),
            )

            self.assertEqual(summary.plugins, 5)
            self.assertEqual(summary.skills, 15)
            self.assertEqual(summary.dediren_tools, 7)
            self.assertIn("no plugin validate command", summary.codex_validator)
            self.assertEqual((normal_codex / "config.toml").read_text(), "model = 'unchanged'\n")
            self.assertEqual((normal_claude / ".claude.json").read_text(), "{}\n")

            for argv, child_env in fake.calls:
                self.assertEqual(child_env.get("HOME"), original_home, argv)
                if argv[0] == "codex":
                    self.assertEqual(child_env["CODEX_HOME"], str(state / "codex-home"), argv)
                    self.assertNotIn("CLAUDE_CONFIG_DIR", child_env, argv)
                if argv[0] == "claude":
                    self.assertEqual(
                        child_env["CLAUDE_CONFIG_DIR"], str(state / "claude-config"), argv
                    )
                    self.assertNotIn("CODEX_HOME", child_env, argv)

            self.assertEqual([call[3] for call in mcp_calls], ["Codex", "Claude"])
            self.assertEqual(mcp_calls[0][0][0], "bash")
            self.assertTrue(mcp_calls[1][0][0].endswith("/dediren-mcp.sh"))
            for _, cwd, child_env, _ in mcp_calls:
                self.assertEqual(cwd, REPO_ROOT)
                self.assertTrue(
                    Path(child_env["DEDIREN_CACHE_DIR"]).is_relative_to(state), child_env
                )

    def test_profile_control_plane_mutation_fails_even_when_hosts_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "fresh-state"
            state.mkdir()
            normal = root / "normal-config.toml"
            normal.write_text("unchanged\n", encoding="utf-8")
            fake = FakeCliRunner(REPO_ROOT)

            def mutating_mcp(argv, *, cwd, env, label):
                del argv, cwd, env
                if label == "Claude":
                    normal.write_text("changed\n", encoding="utf-8")
                return set(smoke.EXPECTED_DEDIREN_TOOLS)

            with self.assertRaisesRegex(smoke.SmokeFailure, "normal profile control plane changed"):
                smoke.run_host_smoke(
                    REPO_ROOT,
                    state,
                    runner=fake,
                    mcp_runner=mutating_mcp,
                    normal_profile_paths=(normal,),
                )

    def test_json_rpc_session_requires_the_exact_seven_tool_surface(self) -> None:
        requests = []

        def fake_runner(argv, *, cwd, env, input_text=None, timeout=120):
            del cwd, env, timeout
            requests.extend(json.loads(line) for line in input_text.splitlines())
            responses = [
                {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05"}},
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "tools": [{"name": name} for name in sorted(smoke.EXPECTED_DEDIREN_TOOLS)]
                    },
                },
            ]
            return subprocess.CompletedProcess(
                list(argv), 0, "\n".join(json.dumps(item) for item in responses), ""
            )

        actual = smoke.run_mcp_session(
            ["fake-dediren"],
            cwd=REPO_ROOT,
            env=os.environ,
            runner=fake_runner,
            label="fake",
        )

        self.assertEqual(actual, smoke.EXPECTED_DEDIREN_TOOLS)
        self.assertEqual(
            [request.get("method") for request in requests],
            ["initialize", "notifications/initialized", "tools/list"],
        )

    def test_json_rpc_session_rejects_tool_surface_drift(self) -> None:
        def fake_runner(argv, *, cwd, env, input_text=None, timeout=120):
            del cwd, env, input_text, timeout
            responses = [
                {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05"}},
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {
                        "tools": [
                            {"name": name}
                            for name in sorted(smoke.EXPECTED_DEDIREN_TOOLS | {"unexpected_tool"})
                        ]
                    },
                },
            ]
            return subprocess.CompletedProcess(
                list(argv), 0, "\n".join(json.dumps(item) for item in responses), ""
            )

        with self.assertRaisesRegex(smoke.SmokeFailure, "Dediren tools differ"):
            smoke.run_mcp_session(
                ["fake-dediren"],
                cwd=REPO_ROOT,
                env=os.environ,
                runner=fake_runner,
                label="fake",
            )

    def test_command_requires_both_safety_flags(self) -> None:
        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                smoke.parse_args(["--fresh", "."])
        parsed = smoke.parse_args(["--fresh", "--assert-profile-isolation", "."])
        self.assertTrue(parsed.fresh)
        self.assertTrue(parsed.assert_profile_isolation)


if __name__ == "__main__":
    unittest.main()
