#!/usr/bin/env python3
"""Check Sour Old Geezer runtime metadata parity.

This is intentionally a checker, not a generator: SKILL.md frontmatter remains
the canonical skill trigger metadata, and the shared marketplace remains the
canonical plugin catalog.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Finding:
    path: str
    field: str
    expected: str
    actual: str


def repo_relative(repo: Path, path: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return path.as_posix()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def unquote_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def leading_spaces(value: str) -> int:
    return len(value) - len(value.lstrip(" "))


def parse_block_scalar(lines: list[str], start: int, parent_indent: int) -> tuple[str, int]:
    parts: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if line.strip() and leading_spaces(line) <= parent_indent:
            break
        parts.append(line.strip())
        index += 1
    return normalize_text(" ".join(part for part in parts if part)), index


def parse_yaml_mapping(text: str, source: Path) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if ":" not in stripped:
            raise ValueError(f"Cannot parse YAML-like metadata in {source}: {raw!r}")

        indent = leading_spaces(raw)
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        current = stack[-1][1]

        if raw_value in {">", ">-", "|", "|-"}:
            value, index = parse_block_scalar(lines, index + 1, indent)
            current[key] = value
            continue
        if raw_value == "":
            child: dict[str, Any] = {}
            current[key] = child
            stack.append((indent, child))
            index += 1
            continue

        current[key] = unquote_scalar(raw_value)
        index += 1

    return root


def read_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path} has no YAML frontmatter")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return parse_yaml_mapping("\n".join(lines[1:index]), path)
    raise ValueError(f"{path} has unterminated YAML frontmatter")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def read_yaml(path: Path) -> dict[str, Any]:
    return parse_yaml_mapping(path.read_text(encoding="utf-8"), path)


def compare(
    findings: list[Finding],
    repo: Path,
    path: Path,
    field: str,
    expected: Any,
    actual: Any,
) -> None:
    expected_text = normalize_text(expected)
    actual_text = normalize_text(actual)
    if expected_text != actual_text:
        findings.append(
            Finding(
                path=repo_relative(repo, path),
                field=field,
                expected=expected_text,
                actual=actual_text,
            )
        )


def marketplace_plugins(repo: Path) -> list[dict[str, Any]]:
    marketplace_path = repo / ".claude-plugin" / "marketplace.json"
    marketplace = read_json(marketplace_path)
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        raise ValueError(".claude-plugin/marketplace.json must contain plugins[]")
    return plugins


def check_plugin_metadata(repo: Path, findings: list[Finding]) -> list[Path]:
    plugin_dirs: list[Path] = []
    for plugin in marketplace_plugins(repo):
        source = plugin.get("source", "")
        plugin_dir = repo / source.removeprefix("./")
        plugin_dirs.append(plugin_dir)

        claude_path = plugin_dir / ".claude-plugin" / "plugin.json"
        codex_path = plugin_dir / ".codex-plugin" / "plugin.json"
        claude = read_json(claude_path)
        codex = read_json(codex_path)

        for field in ("name", "version", "description"):
            compare(findings, repo, claude_path, field, plugin.get(field), claude.get(field))
            compare(findings, repo, codex_path, field, plugin.get(field), codex.get(field))
        compare(findings, repo, codex_path, "skills", "./skills/", codex.get("skills"))

    return plugin_dirs


def display_name_for(skill_name: str) -> str:
    acronyms = {
        "api": "API",
        "devsecops": "DevSecOps",
        "pr": "PR",
    }
    return " ".join(acronyms.get(part, part.capitalize()) for part in skill_name.split("-"))


def check_skill_metadata(repo: Path, plugin_dirs: list[Path], findings: list[Finding]) -> set[str]:
    public_skill_names: set[str] = set()
    readme_path = repo / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

    for plugin_dir in plugin_dirs:
        plugin_name = plugin_dir.name
        skills_dir = plugin_dir / "skills"
        for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
            skill_path = skill_dir / "SKILL.md"
            if not skill_path.exists():
                continue

            skill = read_frontmatter(skill_path)
            skill_name = normalize_text(skill.get("name"))
            skill_description = normalize_text(skill.get("description"))
            public_skill_names.add(skill_name)

            compare(findings, repo, skill_path, "name", skill_dir.name, skill_name)

            agent_path = plugin_dir / "agents" / f"{skill_name}.md"
            if agent_path.exists():
                agent = read_frontmatter(agent_path)
                compare(findings, repo, agent_path, "name", skill_name, agent.get("name"))
                compare(findings, repo, agent_path, "description", skill_description, agent.get("description"))
            else:
                findings.append(Finding(repo_relative(repo, agent_path), "exists", "present", "missing"))

            codex_agent_path = repo / ".codex" / "agents" / f"{skill_name}.toml"
            if codex_agent_path.exists():
                codex_agent = read_toml(codex_agent_path)
                compare(findings, repo, codex_agent_path, "name", skill_name, codex_agent.get("name"))
                compare(findings, repo, codex_agent_path, "description", skill_description, codex_agent.get("description"))
            else:
                findings.append(Finding(repo_relative(repo, codex_agent_path), "exists", "present", "missing"))

            openai_path = skill_dir / "agents" / "openai.yaml"
            if openai_path.exists():
                openai = read_yaml(openai_path)
                interface = openai.get("interface", {})
                compare(
                    findings,
                    repo,
                    openai_path,
                    "interface.display_name",
                    display_name_for(skill_name),
                    interface.get("display_name") if isinstance(interface, dict) else "",
                )
                compare(
                    findings,
                    repo,
                    openai_path,
                    "interface.short_description",
                    skill_description,
                    interface.get("short_description") if isinstance(interface, dict) else "",
                )
            else:
                findings.append(Finding(repo_relative(repo, openai_path), "exists", "present", "missing"))

            readme_link = f"[{skill_name}]({plugin_name}/skills/{skill_name}/SKILL.md)"
            if readme and readme_link not in readme:
                findings.append(Finding("README.md", f"skill-link:{skill_name}", readme_link, "missing"))

            docs_plugins = repo / "docs" / "plugins"
            if docs_plugins.exists():
                for doc_path in sorted(docs_plugins.glob("*.md")):
                    doc = doc_path.read_text(encoding="utf-8")
                    if plugin_name in doc and readme_link not in doc:
                        findings.append(
                            Finding(
                                repo_relative(repo, doc_path),
                                f"skill-link:{skill_name}",
                                readme_link,
                                "missing",
                            )
                        )

    return public_skill_names


def check_internal_codex_agents(repo: Path, public_skill_names: set[str], findings: list[Finding]) -> None:
    agents_dir = repo / ".codex" / "agents"
    if not agents_dir.exists():
        return

    for codex_agent_path in sorted(agents_dir.glob("*.toml")):
        codex_agent = read_toml(codex_agent_path)
        agent_name = normalize_text(codex_agent.get("name"))
        if agent_name in public_skill_names:
            continue

        internal_skill_path = repo / ".claude" / "skills" / agent_name / "SKILL.md"
        if internal_skill_path.exists():
            internal_skill = read_frontmatter(internal_skill_path)
            compare(findings, repo, codex_agent_path, "name", internal_skill.get("name"), codex_agent.get("name"))
            compare(
                findings,
                repo,
                codex_agent_path,
                "description",
                internal_skill.get("description"),
                codex_agent.get("description"),
            )
        else:
            findings.append(
                Finding(
                    repo_relative(repo, codex_agent_path),
                    "source-of-truth",
                    "public skill or .claude/skills/<name>/SKILL.md",
                    "missing",
                )
            )


def check_repo(repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    plugin_dirs = check_plugin_metadata(repo, findings)
    public_skill_names = check_skill_metadata(repo, plugin_dirs, findings)
    check_internal_codex_agents(repo, public_skill_names, findings)
    return findings


def print_findings(findings: list[Finding]) -> None:
    if not findings:
        print("Runtime metadata parity OK")
        return

    print("Runtime metadata parity failed")
    for finding in findings:
        print(f"- {finding.path} :: {finding.field}")
        print(f"  expected: {finding.expected}")
        print(f"  actual:   {finding.actual}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check parity and exit nonzero on drift")
    parser.add_argument("repo", nargs="?", default=".", help="repository root to check")
    args = parser.parse_args(argv)
    if not args.check:
        parser.error("only --check mode is supported")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo = Path(args.repo).resolve()
    try:
        findings = check_repo(repo)
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print_findings(findings)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
