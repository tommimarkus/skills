import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "scripts" / "check-runtime-metadata-parity.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


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
    def test_clean_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)

            result = run_checker(repo)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Runtime metadata parity OK", result.stdout)

    def test_skill_description_drift_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            write(
                repo / "souroldgeezer-example/agents/example-skill.md",
                """
                ---
                name: example-skill
                description: Use when this Claude agent has drifted away.
                ---

                Use the matching skill as source of truth.
                """,
            )

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Runtime metadata parity failed", result.stdout)
        self.assertIn("souroldgeezer-example/agents/example-skill.md", result.stdout)
        self.assertIn("description", result.stdout)

    def test_docs_plugin_links_must_be_relative_to_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            write(
                repo / "docs/plugins/example.md",
                """
                # `souroldgeezer-example`

                | Skill | Summary |
                |---|---|
                | [example-skill](souroldgeezer-example/skills/example-skill/SKILL.md) | Broken from docs/plugins |
                """,
            )

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("docs/plugins/example.md", result.stdout)
        self.assertIn("[example-skill](../../souroldgeezer-example/skills/example-skill/SKILL.md)", result.stdout)

    def test_codex_manifest_must_declare_skills_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            write(
                repo / "souroldgeezer-example/.codex-plugin/plugin.json",
                """
                {
                  "name": "souroldgeezer-example",
                  "version": "0.1.0",
                  "description": "Example plugin for runtime metadata parity tests.",
                  "author": {"name": "Sour Old Geezer", "email": "test@example.invalid"},
                  "license": "MIT",
                  "skills": "./wrong-skills/",
                  "interface": {
                    "displayName": "Sour Old Geezer Example",
                    "shortDescription": "Example parity checks.",
                    "defaultPrompt": ["Use example-skill."]
                  }
                }
                """,
            )

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("souroldgeezer-example/.codex-plugin/plugin.json", result.stdout)
        self.assertIn("skills", result.stdout)
        self.assertIn("./skills/", result.stdout)

    def test_missing_openai_metadata_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            (
                repo
                / "souroldgeezer-example"
                / "skills"
                / "example-skill"
                / "agents"
                / "openai.yaml"
            ).unlink()

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "souroldgeezer-example/skills/example-skill/agents/openai.yaml",
            result.stdout,
        )
        self.assertIn("exists", result.stdout)

    def test_openai_short_description_drift_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            write(
                repo / "souroldgeezer-example/skills/example-skill/agents/openai.yaml",
                """
                interface:
                  display_name: "Example Skill"
                  short_description: "Drifted OpenAI metadata."
                  default_prompt: "Use example-skill."
                policy:
                  allow_implicit_invocation: true
                """,
            )

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "souroldgeezer-example/skills/example-skill/agents/openai.yaml",
            result.stdout,
        )
        self.assertIn("interface.short_description", result.stdout)

    def test_orphan_internal_codex_agent_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            write(
                repo / ".codex/agents/orphan.toml",
                '''
                name = "orphan"
                description = "No public or internal skill owns this agent."
                sandbox_mode = "workspace-write"
                ''',
            )

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".codex/agents/orphan.toml", result.stdout)
        self.assertIn("source-of-truth", result.stdout)

    def test_wrong_path_public_codex_agent_alias_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            write(
                repo / ".codex/agents/stale-public-alias.toml",
                '''
                name = "example-skill"
                description = "Use when checking runtime metadata parity for an example skill."
                sandbox_mode = "workspace-write"
                ''',
            )

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".codex/agents/stale-public-alias.toml", result.stdout)
        self.assertIn("source-of-truth", result.stdout)

    def test_wrong_path_internal_codex_agent_alias_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            write(
                repo / ".codex/agents/stale-internal-alias.toml",
                '''
                name = "internal-review"
                description = "Use when checking Codex metadata parity for an internal skill."
                sandbox_mode = "workspace-write"
                ''',
            )

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".codex/agents/stale-internal-alias.toml", result.stdout)
        self.assertIn("source-of-truth", result.stdout)

    def test_internal_skill_without_codex_agent_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            (repo / ".codex" / "agents" / "internal-review.toml").unlink()

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".codex/agents/internal-review.toml", result.stdout)
        self.assertIn("exists", result.stdout)
        self.assertIn("present", result.stdout)
        self.assertIn("missing", result.stdout)

    def test_internal_skill_wrapper_is_keyed_by_directory_when_frontmatter_name_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.make_clean_fixture(repo)
            write(
                repo / ".claude/skills/internal-review/SKILL.md",
                """
                ---
                name: drifted-internal
                description: Use when checking Codex metadata parity for an internal skill.
                ---

                # Internal Review
                """,
            )

            result = run_checker(repo)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".claude/skills/internal-review/SKILL.md", result.stdout)
        self.assertIn("name", result.stdout)
        self.assertNotIn(".codex/agents/drifted-internal.toml", result.stdout)
        self.assertNotIn(".codex/agents/internal-review.toml :: source-of-truth", result.stdout)

    def make_clean_fixture(self, repo: Path) -> None:
        plugin_description = "Example plugin for runtime metadata parity tests."
        skill_description = "Use when checking runtime metadata parity for an example skill."
        internal_description = "Use when checking Codex metadata parity for an internal skill."
        write(
            repo / ".claude-plugin/marketplace.json",
            f"""
            {{
              "name": "souroldgeezer",
              "plugins": [
                {{
                  "name": "souroldgeezer-example",
                  "source": "./souroldgeezer-example",
                  "version": "0.1.0",
                  "description": "{plugin_description}"
                }}
              ]
            }}
            """,
        )
        write(
            repo / "souroldgeezer-example/.claude-plugin/plugin.json",
            f"""
            {{
              "name": "souroldgeezer-example",
              "version": "0.1.0",
              "description": "{plugin_description}",
              "author": {{"name": "Sour Old Geezer", "email": "test@example.invalid"}},
              "license": "MIT"
            }}
            """,
        )
        write(
            repo / "souroldgeezer-example/.codex-plugin/plugin.json",
            f"""
            {{
              "name": "souroldgeezer-example",
              "version": "0.1.0",
              "description": "{plugin_description}",
              "author": {{"name": "Sour Old Geezer", "email": "test@example.invalid"}},
              "license": "MIT",
              "skills": "./skills/",
              "interface": {{
                "displayName": "Sour Old Geezer Example",
                "shortDescription": "Example parity checks.",
                "defaultPrompt": ["Use example-skill."]
              }}
            }}
            """,
        )
        write(
            repo / "souroldgeezer-example/skills/example-skill/SKILL.md",
            f"""
            ---
            name: example-skill
            description: {skill_description}
            ---

            # Example Skill
            """,
        )
        write(
            repo / "souroldgeezer-example/agents/example-skill.md",
            f"""
            ---
            name: example-skill
            description: {skill_description}
            ---

            Use the matching skill as source of truth.
            """,
        )
        write(
            repo / ".codex/agents/example-skill.toml",
            f'''
            name = "example-skill"
            description = "{skill_description}"
            sandbox_mode = "workspace-write"
            ''',
        )
        write(
            repo / "souroldgeezer-example/skills/example-skill/agents/openai.yaml",
            f"""
            interface:
              display_name: "Example Skill"
              short_description: "{skill_description}"
              default_prompt: "Use example-skill."
            policy:
              allow_implicit_invocation: true
            """,
        )
        write(
            repo / "README.md",
            """
            # Example Marketplace

            ## What's in `souroldgeezer-example`

            | Skill | Summary | Extensions |
            |---|---|---|
            | [example-skill](souroldgeezer-example/skills/example-skill/SKILL.md) | Example parity checks | none |
            """,
        )
        write(
            repo / "docs/plugins/example.md",
            """
            # `souroldgeezer-example`

            | Skill | Summary |
            |---|---|
            | [example-skill](../../souroldgeezer-example/skills/example-skill/SKILL.md) | Example parity checks |
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
            """,
        )
        write(
            repo / ".codex/agents/internal-review.toml",
            f'''
            name = "internal-review"
            description = "{internal_description}"
            sandbox_mode = "workspace-write"

            developer_instructions = """
            Read `.claude/skills/internal-review/SKILL.md` and follow it as the source of truth.
            """
            ''',
        )


if __name__ == "__main__":
    unittest.main()
