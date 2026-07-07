#!/usr/bin/env python3
"""Check Sour Old Geezer Claude Code runtime metadata parity.

This is intentionally a checker, not a generator: SKILL.md frontmatter remains
the canonical skill trigger metadata, and the shared marketplace remains the
canonical plugin catalog. It keeps the Claude Code surfaces in sync with each
other — marketplace entry, plugin manifest, the matching subagent, the README
skill links, and the repo-internal skill Claude wrappers.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
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


def markdown_link(label: str, target: str) -> str:
    return f"[{label}]({target})"


def relative_markdown_target(source_path: Path, target_path: Path) -> str:
    return os.path.relpath(target_path, start=source_path.parent).replace(os.sep, "/")


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


def require_text_contains(
    findings: list[Finding],
    repo: Path,
    path: Path,
    field: str,
    expected: str,
    actual_text: str,
) -> None:
    if expected not in actual_text:
        findings.append(Finding(repo_relative(repo, path), field, expected, "missing"))


def marketplace_plugins(repo: Path) -> list[dict[str, Any]]:
    marketplace_path = repo / ".claude-plugin" / "marketplace.json"
    marketplace = read_json(marketplace_path)
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        raise ValueError(".claude-plugin/marketplace.json must contain plugins[]")
    return plugins


def check_plugin_metadata(repo: Path, findings: list[Finding]) -> list[Path]:
    plugin_dirs: list[Path] = []
    marketplace_path = repo / ".claude-plugin" / "marketplace.json"
    for plugin in marketplace_plugins(repo):
        source = plugin.get("source", "")
        plugin_dir = repo / source.removeprefix("./")
        plugin_dirs.append(plugin_dir)

        claude_path = plugin_dir / ".claude-plugin" / "plugin.json"
        claude = read_json(claude_path)

        for field in ("name", "description"):
            compare(findings, repo, claude_path, field, plugin.get(field), claude.get(field))

        # plugin.json#version is the sole version authority: Claude Code always
        # resolves it over a marketplace-entry copy without warning, so a stray
        # marketplace copy is a silent drift risk rather than a helpful mirror.
        if claude.get("version") is None:
            findings.append(Finding(repo_relative(repo, claude_path), "version", "present", "missing"))
        if "version" in plugin:
            findings.append(
                Finding(
                    repo_relative(repo, marketplace_path),
                    "version",
                    "absent (plugin.json#version is the sole authority)",
                    normalize_text(plugin.get("version")),
                )
            )

    return plugin_dirs


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
            skill_dir_name = skill_dir.name
            skill_name = normalize_text(skill.get("name"))
            skill_description = normalize_text(skill.get("description"))
            public_skill_names.add(skill_dir_name)

            compare(findings, repo, skill_path, "name", skill_dir_name, skill_name)

            agent_path = plugin_dir / "agents" / f"{skill_name}.md"
            if agent_path.exists():
                agent = read_frontmatter(agent_path)
                compare(findings, repo, agent_path, "name", skill_name, agent.get("name"))
                compare(findings, repo, agent_path, "description", skill_description, agent.get("description"))
            else:
                findings.append(Finding(repo_relative(repo, agent_path), "exists", "present", "missing"))

            skill_target = plugin_dir / "skills" / skill_name / "SKILL.md"
            readme_link = markdown_link(skill_name, f"{plugin_name}/skills/{skill_name}/SKILL.md")
            if readme and readme_link not in readme:
                findings.append(Finding("README.md", f"skill-link:{skill_name}", readme_link, "missing"))

            docs_plugins = repo / "docs" / "plugins"
            if docs_plugins.exists():
                for doc_path in sorted(docs_plugins.glob("*.md")):
                    doc = doc_path.read_text(encoding="utf-8")
                    doc_link = markdown_link(
                        skill_name,
                        relative_markdown_target(doc_path, skill_target),
                    )
                    if plugin_name in doc and doc_link not in doc:
                        findings.append(
                            Finding(
                                repo_relative(repo, doc_path),
                                f"skill-link:{skill_name}",
                                doc_link,
                                "missing",
                            )
                        )

    return public_skill_names


def check_internal_skill_wrappers(repo: Path, findings: list[Finding]) -> None:
    internal_skill_names: set[str] = set()
    shared_internal_skills_dir = repo / "internal-skills"

    if shared_internal_skills_dir.exists():
        for internal_skill_path in sorted(shared_internal_skills_dir.glob("*/SKILL.md")):
            internal_skill = read_frontmatter(internal_skill_path)
            internal_dir_name = internal_skill_path.parent.name
            internal_name = normalize_text(internal_skill.get("name"))
            internal_description = normalize_text(internal_skill.get("description"))
            internal_skill_names.add(internal_dir_name)
            shared_skill_ref = f"internal-skills/{internal_dir_name}/SKILL.md"

            compare(findings, repo, internal_skill_path, "name", internal_dir_name, internal_name)

            claude_wrapper_path = repo / ".claude" / "skills" / internal_dir_name / "SKILL.md"
            if claude_wrapper_path.exists():
                claude_wrapper = read_frontmatter(claude_wrapper_path)
                claude_wrapper_text = claude_wrapper_path.read_text(encoding="utf-8")
                compare(findings, repo, claude_wrapper_path, "name", internal_dir_name, claude_wrapper.get("name"))
                compare(
                    findings,
                    repo,
                    claude_wrapper_path,
                    "description",
                    internal_description,
                    claude_wrapper.get("description"),
                )
                require_text_contains(
                    findings,
                    repo,
                    claude_wrapper_path,
                    "source-of-truth",
                    shared_skill_ref,
                    claude_wrapper_text,
                )
            else:
                findings.append(Finding(repo_relative(repo, claude_wrapper_path), "exists", "present", "missing"))

            claude_wrapper_dir = claude_wrapper_path.parent
            if claude_wrapper_dir.exists():
                for wrapper_file in sorted(path for path in claude_wrapper_dir.rglob("*") if path.is_file()):
                    if wrapper_file == claude_wrapper_path:
                        continue
                    expected_shared_path = (
                        repo
                        / "internal-skills"
                        / internal_dir_name
                        / wrapper_file.relative_to(claude_wrapper_dir)
                    )
                    findings.append(
                        Finding(
                            repo_relative(repo, wrapper_file),
                            "shared-location",
                            repo_relative(repo, expected_shared_path),
                            repo_relative(repo, wrapper_file),
                        )
                    )

    claude_skills_dir = repo / ".claude" / "skills"
    if claude_skills_dir.exists():
        for claude_wrapper_path in sorted(claude_skills_dir.glob("*/SKILL.md")):
            wrapper_name = claude_wrapper_path.parent.name
            if wrapper_name in internal_skill_names:
                continue
            findings.append(
                Finding(
                    repo_relative(repo, claude_wrapper_path),
                    "source-of-truth",
                    f"internal-skills/{wrapper_name}/SKILL.md",
                    "missing",
                )
            )


def check_repo(repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    plugin_dirs = check_plugin_metadata(repo, findings)
    check_skill_metadata(repo, plugin_dirs, findings)
    check_internal_skill_wrappers(repo, findings)
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
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print_findings(findings)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
