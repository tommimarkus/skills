# lean-audit:dup-intentional — per-case broken-fixture payloads kept literal; the run/flag machinery is already extracted to _assert_broken_fixture_flags/make_clean_fixture
import json
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, write_fixture as write

CHECKER = REPO_ROOT / "scripts" / "check-runtime-metadata-parity.py"
EXAMPLE_PLUGIN = "souroldgeezer-example"
EXAMPLE_LAUNCHER = "skills/example-skill/references/scripts/example-mcp.sh"
POLICY_EXECUTION_TIER_AGENTS = (
    "plan-step-analytical",
    "plan-step-deep",
    "plan-step-mechanical",
    "plan-step-standard",
)


def read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def write_mcp_config(plugin: Path, servers: dict) -> None:
    (plugin / ".mcp.json").write_text(json.dumps(servers, indent=2), encoding="utf-8")


def add_mcp_packaging(repo: Path) -> None:
    """Give the clean fixture a bundled MCP server in the shape each host documents:
    Claude an inline `mcpServers` object, Codex a path to a plugin-root config file.

    Both point at the same launcher on purpose — that shared file existing is
    exactly the evidence that must NOT be read as proof either host registered it.
    """
    plugin = repo / EXAMPLE_PLUGIN

    claude_path = plugin / ".claude-plugin" / "plugin.json"
    claude = read_manifest(claude_path)
    claude["mcpServers"] = {
        "example": {
            "command": f"${{CLAUDE_PLUGIN_ROOT}}/{EXAMPLE_LAUNCHER}",
            "env": {"EXAMPLE_CACHE_DIR": "${CLAUDE_PLUGIN_DATA}/example"},
        }
    }
    write_manifest(claude_path, claude)

    codex_path = plugin / ".codex-plugin" / "plugin.json"
    codex = read_manifest(codex_path)
    codex["mcpServers"] = "./.mcp.json"
    write_manifest(codex_path, codex)

    write_mcp_config(
        plugin,
        {
            "example": {
                "command": "bash",
                "args": [f"./{EXAMPLE_LAUNCHER}"],
                "cwd": ".",
                "startup_timeout_sec": 180,
            }
        },
    )

    launcher = plugin / EXAMPLE_LAUNCHER
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text("#!/usr/bin/env bash\nexec example mcp\n", encoding="utf-8")
    launcher.chmod(0o755)


def run_checker(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--check", str(repo)],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class RuntimeMetadataParityTest(unittest.TestCase):
    def _run_with_broken_fixture(self, rel_path: str, content: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            write(repo / rel_path, content)
            return run_checker(repo)

    def _assert_broken_fixture_flags(self, rel_path: str, content: str, *expect_in_stdout: str
                                      ) -> subprocess.CompletedProcess[str]:
        result = self._run_with_broken_fixture(rel_path, content)
        self.assertNotEqual(result.returncode, 0)
        for substring in expect_in_stdout:
            self.assertIn(substring, result.stdout)
        return result

    def test_clean_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)

            result = run_checker(repo)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Runtime metadata parity OK", result.stdout)

    def test_skill_description_drift_is_detected(self) -> None:
        self._assert_broken_fixture_flags(
            "souroldgeezer-example/agents/example-skill.md",
            """
            ---
            name: example-skill
            description: Use when this Claude agent has drifted away.
            ---

            Use the matching skill as source of truth.
            """,
            "Runtime metadata parity failed",
            "souroldgeezer-example/agents/example-skill.md",
            "description",
        )

    def test_public_skill_agent_must_remain_a_router_only_adapter(self) -> None:
        self._assert_broken_fixture_flags(
            "souroldgeezer-example/agents/example-skill.md",
            """
            ---
            name: example-skill
            description: Use when checking runtime metadata parity for an example skill.
            ---

            Use the `Skill` tool to load and follow
            [`../skills/example-skill/SKILL.md`](../skills/example-skill/SKILL.md)
            as the source of truth.

            1. Reimplement the skill's first workflow step here.
            2. Present a wrapper-specific output contract.
            """,
            "souroldgeezer-example/agents/example-skill.md",
            "router-body",
        )

    def test_unpaired_public_plugin_agent_is_detected(self) -> None:
        self._assert_broken_fixture_flags(
            "souroldgeezer-example/agents/extra-agent.md",
            """
            ---
            name: extra-agent
            description: This agent has no matching published skill.
            ---

            Run an independent workflow.
            """,
            "souroldgeezer-example/agents/extra-agent.md",
            "paired-skill",
            "unpaired agent",
        )

    def test_policy_execution_tier_agents_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo, plugin_name="souroldgeezer-policy")
            for agent_name in POLICY_EXECUTION_TIER_AGENTS:
                write(
                    repo / "souroldgeezer-policy" / "agents" / f"{agent_name}.md",
                    f"""
                    ---
                    name: {agent_name}
                    description: Intentional execution-tier test fixture.
                    ---

                    Execute the approved plan step at this tier.
                    """,
                )

            result = run_checker(repo)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Runtime metadata parity OK", result.stdout)

    def test_plugin_manifest_missing_version_is_detected(self) -> None:
        self._assert_broken_fixture_flags(
            "souroldgeezer-example/.claude-plugin/plugin.json",
            """
            {
              "name": "souroldgeezer-example",
              "description": "Example plugin for runtime metadata parity tests.",
              "author": {"name": "Sour Old Geezer", "email": "test@example.invalid"},
              "license": "MIT"
            }
            """,
            "souroldgeezer-example/.claude-plugin/plugin.json",
            "version",
        )

    def test_codex_manifest_requires_strict_semver(self) -> None:
        self._assert_broken_fixture_flags(
            "souroldgeezer-example/.codex-plugin/plugin.json",
            """
            {
              "name": "souroldgeezer-example",
              "version": "0.01.0",
              "description": "Example plugin for runtime metadata parity tests.",
              "skills": "./skills/"
            }
            """,
            "souroldgeezer-example/.codex-plugin/plugin.json",
            "strict SemVer",
        )

    def test_codex_manifest_description_drift_is_detected(self) -> None:
        self._assert_broken_fixture_flags(
            "souroldgeezer-example/.codex-plugin/plugin.json",
            """
            {
              "name": "souroldgeezer-example",
              "version": "0.1.0",
              "description": "Drifted Codex description.",
              "skills": "./skills/"
            }
            """,
            "souroldgeezer-example/.codex-plugin/plugin.json",
            "description",
        )

    def test_marketplace_entry_with_version_key_is_detected(self) -> None:
        # plugin.json#version is the sole authority (Claude Code always resolves
        # it over a marketplace-entry copy without warning); a marketplace entry
        # carrying a version key is flagged even when the value matches.
        self._assert_broken_fixture_flags(
            ".claude-plugin/marketplace.json",
            """
            {
              "name": "souroldgeezer",
              "plugins": [
                {
                  "name": "souroldgeezer-example",
                  "source": "./souroldgeezer-example",
                  "version": "0.1.0",
                  "description": "Example plugin for runtime metadata parity tests."
                }
              ]
            }
            """,
            ".claude-plugin/marketplace.json",
            "version",
        )

    def test_docs_plugin_links_must_be_relative_to_doc(self) -> None:
        self._assert_broken_fixture_flags(
            "docs/plugins/example.md",
            """
            # `souroldgeezer-example`

            | Skill | Summary |
            |---|---|
            | [example-skill](souroldgeezer-example/skills/example-skill/SKILL.md) | Broken from docs/plugins |
            """,
            "docs/plugins/example.md",
            "[example-skill](../../souroldgeezer-example/skills/example-skill/SKILL.md)",
        )

    def test_shared_internal_skill_without_claude_wrapper_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            (repo / ".claude" / "skills" / "internal-review" / "SKILL.md").unlink()

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".claude/skills/internal-review/SKILL.md", result.stdout)
        self.assertIn("exists", result.stdout)
        self.assertIn("present", result.stdout)
        self.assertIn("missing", result.stdout)

    def test_shared_internal_skill_without_codex_wrapper_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            (repo / ".agents" / "skills" / "internal-review" / "SKILL.md").unlink()

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".agents/skills/internal-review/SKILL.md", result.stdout)
        self.assertIn("exists", result.stdout)
        self.assertIn("present", result.stdout)
        self.assertIn("missing", result.stdout)

    def test_orphan_claude_wrapper_without_shared_skill_is_detected(self) -> None:
        self._assert_broken_fixture_flags(
            ".claude/skills/orphan-review/SKILL.md",
            """
            ---
            name: orphan-review
            description: No shared internal skill owns this Claude wrapper.
            ---

            # Orphan Review
            """,
            ".claude/skills/orphan-review/SKILL.md",
            "source-of-truth",
            "internal-skills/orphan-review/SKILL.md",
        )

    def test_internal_claude_wrapper_must_point_to_shared_skill(self) -> None:
        self._assert_broken_fixture_flags(
            ".claude/skills/internal-review/SKILL.md",
            """
            ---
            name: internal-review
            description: Use when reviewing the internal authoring workflow.
            ---

            # Internal Review

            This wrapper accidentally duplicates workflow text instead of
            delegating to the neutral shared source.
            """,
            ".claude/skills/internal-review/SKILL.md",
            "source-of-truth",
            "internal-skills/internal-review/SKILL.md",
        )

    def test_internal_skill_wrapper_is_keyed_by_directory_when_frontmatter_name_drifts(self) -> None:
        result = self._assert_broken_fixture_flags(
            "internal-skills/internal-review/SKILL.md",
            """
            ---
            name: drifted-internal
            description: Use when reviewing the internal authoring workflow.
            ---

            # Internal Review
            """,
            "internal-skills/internal-review/SKILL.md",
            "name",
        )
        self.assertNotIn(".claude/skills/internal-review/SKILL.md :: source-of-truth", result.stdout)

    # --- Bundled MCP server packaging -------------------------------------
    # A plugin that bundles an MCP server must satisfy BOTH hosts' documented
    # manifest shapes, and every referenced config file and launcher must
    # actually resolve. The shared launcher on disk proves neither registration,
    # so each host is asserted separately.

    def _run_mcp_fixture(self, mutate: Callable[[Path], None] | None = None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            add_mcp_packaging(repo)
            if mutate is not None:
                mutate(repo)
            return run_checker(repo)

    def _assert_mcp_fixture_flags(self, mutate: Callable[[Path], None], *expect_in_stdout: str) -> None:
        result = self._run_mcp_fixture(mutate)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        for substring in expect_in_stdout:
            self.assertIn(substring, result.stdout)

    def test_mcp_equipped_fixture_passes(self) -> None:
        """Positive control for every mutation case below.

        Without it, a mutation test that fails for an unrelated reason — or a
        checker that stopped inspecting MCP packaging entirely — is
        indistinguishable from a working guard.
        """
        result = self._run_mcp_fixture()

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Runtime metadata parity OK", result.stdout)

    def test_mcp_server_registered_on_one_host_only_is_detected(self) -> None:
        """The canonical cross-runtime drift: the plugin installs clean and
        silently exposes no tools on the host that never registered it."""

        def drop_claude_registration(repo: Path) -> None:
            path = repo / EXAMPLE_PLUGIN / ".claude-plugin" / "plugin.json"
            manifest = read_manifest(path)
            del manifest["mcpServers"]
            write_manifest(path, manifest)

        self._assert_mcp_fixture_flags(
            drop_claude_registration,
            f"{EXAMPLE_PLUGIN}/.claude-plugin/plugin.json",
            "mcpServers",
            "missing",
        )

    def test_codex_inline_mcp_object_is_detected(self) -> None:
        """Valid Claude packaging, but Codex resolves servers only through a
        plugin-root config file, so an inline object registers nothing there."""

        def inline_codex_object(repo: Path) -> None:
            path = repo / EXAMPLE_PLUGIN / ".codex-plugin" / "plugin.json"
            manifest = read_manifest(path)
            manifest["mcpServers"] = {"example": {"command": f"${{PLUGIN_ROOT}}/{EXAMPLE_LAUNCHER}"}}
            write_manifest(path, manifest)

        self._assert_mcp_fixture_flags(
            inline_codex_object,
            f"{EXAMPLE_PLUGIN}/.codex-plugin/plugin.json",
            "mcpServers",
        )

    def test_codex_mcp_config_file_that_does_not_resolve_is_detected(self) -> None:
        def point_at_absent_config(repo: Path) -> None:
            path = repo / EXAMPLE_PLUGIN / ".codex-plugin" / "plugin.json"
            manifest = read_manifest(path)
            manifest["mcpServers"] = "./absent-mcp.json"
            write_manifest(path, manifest)

        self._assert_mcp_fixture_flags(
            point_at_absent_config,
            f"{EXAMPLE_PLUGIN}/.codex-plugin/plugin.json",
            f"{EXAMPLE_PLUGIN}/absent-mcp.json",
            "missing",
        )

    def test_mcp_command_that_does_not_resolve_to_a_bundled_file_is_detected(self) -> None:
        """Renaming the launcher breaks both manifests while launcher-behaviour
        tests that hardcode its path stay green."""

        def remove_launcher(repo: Path) -> None:
            (repo / EXAMPLE_PLUGIN / EXAMPLE_LAUNCHER).unlink()

        self._assert_mcp_fixture_flags(
            remove_launcher,
            "mcpServers.example.command",
            f"bundled file at {EXAMPLE_PLUGIN}/{EXAMPLE_LAUNCHER}",
        )

    def test_non_executable_mcp_launcher_is_detected(self) -> None:
        """A stdio server that cannot be exec'd gets no auto-retry from the host."""

        def drop_executable_bit(repo: Path) -> None:
            (repo / EXAMPLE_PLUGIN / EXAMPLE_LAUNCHER).chmod(0o644)

        self._assert_mcp_fixture_flags(
            drop_executable_bit,
            "mcpServers.example.command",
            "not executable",
        )

    def test_mcp_command_using_the_other_hosts_root_token_is_detected(self) -> None:
        """`${CLAUDE_PLUGIN_ROOT}` never substitutes for Codex; it would reach the
        server as a literal path."""

        def use_claude_token_in_codex_config(repo: Path) -> None:
            write_mcp_config(
                repo / EXAMPLE_PLUGIN,
                {"example": {"command": f"${{CLAUDE_PLUGIN_ROOT}}/{EXAMPLE_LAUNCHER}"}},
            )

        self._assert_mcp_fixture_flags(
            use_claude_token_in_codex_config,
            f"{EXAMPLE_PLUGIN}/.mcp.json",
            "mcpServers.example.command",
            "${CLAUDE_PLUGIN_ROOT}",
        )

    def test_codex_hook_root_token_in_mcp_config_is_detected(self) -> None:
        """Codex documents ``PLUGIN_ROOT`` for hooks, not for MCP fields."""

        def use_unexpanded_codex_token(repo: Path) -> None:
            write_mcp_config(
                repo / EXAMPLE_PLUGIN,
                {"example": {"command": f"${{PLUGIN_ROOT}}/{EXAMPLE_LAUNCHER}"}},
            )

        self._assert_mcp_fixture_flags(
            use_unexpanded_codex_token,
            "mcpServers.example.command",
            "${PLUGIN_ROOT}",
            "passes MCP fields literally",
        )

    def test_mcp_env_using_the_other_hosts_data_token_is_detected(self) -> None:
        def use_claude_data_token_in_codex_config(repo: Path) -> None:
            write_mcp_config(
                repo / EXAMPLE_PLUGIN,
                {
                    "example": {
                        "command": "bash",
                        "args": [f"./{EXAMPLE_LAUNCHER}"],
                        "cwd": ".",
                        "env": {"EXAMPLE_CACHE_DIR": "${CLAUDE_PLUGIN_DATA}/example"},
                    }
                },
            )

        self._assert_mcp_fixture_flags(
            use_claude_data_token_in_codex_config,
            "mcpServers.example.env.EXAMPLE_CACHE_DIR",
            "${CLAUDE_PLUGIN_DATA}",
        )

    def test_codex_hook_data_token_in_mcp_env_is_detected(self) -> None:
        def use_unexpanded_codex_data_token(repo: Path) -> None:
            write_mcp_config(
                repo / EXAMPLE_PLUGIN,
                {
                    "example": {
                        "command": "bash",
                        "args": [f"./{EXAMPLE_LAUNCHER}"],
                        "cwd": ".",
                        "env": {"EXAMPLE_CACHE_DIR": "${PLUGIN_DATA}/example"},
                    }
                },
            )

        self._assert_mcp_fixture_flags(
            use_unexpanded_codex_data_token,
            "mcpServers.example.env.EXAMPLE_CACHE_DIR",
            "${PLUGIN_DATA}",
            "passes MCP fields literally",
        )

    def test_mcp_server_names_must_match_across_hosts(self) -> None:
        def rename_codex_server(repo: Path) -> None:
            write_mcp_config(
                repo / EXAMPLE_PLUGIN,
                {"renamed": {"command": "bash", "args": [f"./{EXAMPLE_LAUNCHER}"], "cwd": "."}},
            )

        self._assert_mcp_fixture_flags(
            rename_codex_server,
            "mcpServers:names",
            "example",
            "renamed",
        )

    def make_clean_fixture(self, repo: Path, plugin_name: str = EXAMPLE_PLUGIN) -> None:
        plugin_description = "Example plugin for runtime metadata parity tests."
        skill_description = "Use when checking runtime metadata parity for an example skill."
        internal_description = "Use when reviewing the internal authoring workflow."
        write(
            repo / ".claude-plugin/marketplace.json",
            f"""
            {{
              "name": "souroldgeezer",
              "plugins": [
                {{
                  "name": "{plugin_name}",
                  "source": "./{plugin_name}",
                  "description": "{plugin_description}"
                }}
              ]
            }}
            """,
        )
        write(
            repo / ".agents/plugins/marketplace.json",
            f"""
            {{
              "name": "souroldgeezer",
              "plugins": [
                {{
                  "name": "{plugin_name}",
                  "source": {{"source": "local", "path": "./{plugin_name}"}},
                  "policy": {{"installation": "AVAILABLE", "authentication": "ON_INSTALL"}},
                  "category": "Productivity"
                }}
              ]
            }}
            """,
        )
        write(
            repo / plugin_name / ".claude-plugin/plugin.json",
            f"""
            {{
              "name": "{plugin_name}",
              "version": "0.1.0",
              "description": "{plugin_description}",
              "author": {{"name": "Sour Old Geezer", "email": "test@example.invalid"}},
              "license": "MIT"
            }}
            """,
        )
        write(
            repo / plugin_name / ".codex-plugin/plugin.json",
            f"""
            {{
              "name": "{plugin_name}",
              "version": "0.1.0",
              "description": "{plugin_description}",
              "skills": "./skills/"
            }}
            """,
        )
        write(
            repo / plugin_name / "skills/example-skill/SKILL.md",
            f"""
            ---
            name: example-skill
            description: {skill_description}
            ---

            # Example Skill
            """,
        )
        write(
            repo / plugin_name / "agents/example-skill.md",
            f"""
            ---
            name: example-skill
            description: {skill_description}
            ---

            Use the `Skill` tool to load and follow
            [`../skills/example-skill/SKILL.md`](../skills/example-skill/SKILL.md)
            as the source of truth. Present the result in the shape that skill
            requires.
            """,
        )
        write(
            repo / "README.md",
            f"""
            # Example Marketplace

            ## What's in `{plugin_name}`

            | Skill | Summary | Extensions |
            |---|---|---|
            | [example-skill]({plugin_name}/skills/example-skill/SKILL.md) | Example parity checks | none |
            """,
        )
        write(
            repo / "docs/plugins/example.md",
            f"""
            # `{plugin_name}`

            | Skill | Summary |
            |---|---|
            | [example-skill](../../{plugin_name}/skills/example-skill/SKILL.md) | Example parity checks |
            """,
        )
        write(
            repo / "internal-skills/internal-review/SKILL.md",
            f"""
            ---
            name: internal-review
            description: {internal_description}
            ---

            # Internal Review
            """,
        )
        write(
            repo / ".claude/skills/internal-review/SKILL.md",
            f"""
            ---
            name: internal-review
            description: {internal_description}
            ---

            # Internal Review

            Read `internal-skills/internal-review/SKILL.md` and follow it as the
            source of truth.
            """,
        )
        write(
            repo / ".agents/skills/internal-review/SKILL.md",
            f"""
            ---
            name: internal-review
            description: {internal_description}
            ---

            # Internal Review

            Read `internal-skills/internal-review/SKILL.md` and follow it as the
            source of truth.
            """,
        )


if __name__ == "__main__":
    unittest.main()
