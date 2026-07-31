#!/usr/bin/env python3
"""Check Sour Old Geezer Claude Code and Codex runtime metadata parity.

This is intentionally a checker, not a generator: SKILL.md frontmatter remains
the canonical skill trigger metadata, and the two marketplaces expose one shared
plugin catalog. It keeps plugin identities and semantic versions synchronized,
preserves Claude subagent parity, checks README skill links, and requires thin
Claude and Codex wrappers for repo-internal skills.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CODEX_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
CLAUDE_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


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


def marketplace_plugins(repo: Path, marketplace_path: Path) -> list[dict[str, Any]]:
    marketplace = read_json(marketplace_path)
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        raise ValueError(f"{repo_relative(repo, marketplace_path)} must contain plugins[]")
    return plugins


def marketplace_source_path(plugin: dict[str, Any], *, codex: bool) -> str:
    source = plugin.get("source")
    if codex:
        if not isinstance(source, dict) or source.get("source") != "local":
            return ""
        return normalize_text(source.get("path"))
    return normalize_text(source)


def version_core(value: Any, *, codex: bool) -> tuple[int, int, int] | None:
    text = normalize_text(value)
    pattern = CODEX_VERSION_RE if codex else CLAUDE_VERSION_RE
    if not pattern.fullmatch(text):
        return None
    major, minor, patch = text.split(".")
    return int(major), int(minor), int(patch)


def check_plugin_metadata(repo: Path, findings: list[Finding]) -> list[Path]:
    plugin_dirs: list[Path] = []
    claude_marketplace_path = repo / ".claude-plugin" / "marketplace.json"
    codex_marketplace_path = repo / ".agents" / "plugins" / "marketplace.json"
    claude_plugins = marketplace_plugins(repo, claude_marketplace_path)
    codex_plugins = marketplace_plugins(repo, codex_marketplace_path)
    claude_names = [normalize_text(plugin.get("name")) for plugin in claude_plugins]
    codex_names = [normalize_text(plugin.get("name")) for plugin in codex_plugins]
    compare(findings, repo, codex_marketplace_path, "plugin-order", claude_names, codex_names)
    codex_by_name = {normalize_text(plugin.get("name")): plugin for plugin in codex_plugins}

    for plugin in claude_plugins:
        plugin_name = normalize_text(plugin.get("name"))
        source = marketplace_source_path(plugin, codex=False)
        plugin_dir = repo / source.removeprefix("./")
        plugin_dirs.append(plugin_dir)

        codex_entry = codex_by_name.get(plugin_name)
        if codex_entry is None:
            findings.append(
                Finding(repo_relative(repo, codex_marketplace_path), f"plugin:{plugin_name}", "present", "missing")
            )
            continue
        compare(
            findings,
            repo,
            codex_marketplace_path,
            f"source:{plugin_name}",
            source,
            marketplace_source_path(codex_entry, codex=True),
        )

        claude_path = plugin_dir / ".claude-plugin" / "plugin.json"
        codex_path = plugin_dir / ".codex-plugin" / "plugin.json"
        claude = read_json(claude_path)
        codex = read_json(codex_path)

        for field in ("name", "description"):
            compare(findings, repo, claude_path, field, plugin.get(field), claude.get(field))
            compare(findings, repo, codex_path, field, claude.get(field), codex.get(field))

        claude_version = version_core(claude.get("version"), codex=False)
        codex_version = version_core(codex.get("version"), codex=True)
        if claude_version is None:
            findings.append(Finding(repo_relative(repo, claude_path), "version", "numeric X.Y.Z", normalize_text(claude.get("version"))))
        if codex_version is None:
            findings.append(Finding(repo_relative(repo, codex_path), "version", "strict SemVer X.Y.Z without leading zeroes", normalize_text(codex.get("version"))))
        if claude_version is not None and codex_version is not None and claude_version != codex_version:
            findings.append(Finding(repo_relative(repo, codex_path), "version", ".".join(map(str, claude_version)), normalize_text(codex.get("version"))))

        compare(findings, repo, codex_path, "skills", "./skills/", codex.get("skills"))

        for marketplace_path, marketplace_entry in (
            (claude_marketplace_path, plugin),
            (codex_marketplace_path, codex_entry),
        ):
            if "version" in marketplace_entry:
                findings.append(
                    Finding(
                        repo_relative(repo, marketplace_path),
                        f"version:{plugin_name}",
                        "absent (runtime manifests own version identity)",
                        normalize_text(marketplace_entry.get("version")),
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

            for runtime_dir in (".claude", ".agents"):
                wrapper_path = repo / runtime_dir / "skills" / internal_dir_name / "SKILL.md"
                if wrapper_path.exists():
                    wrapper = read_frontmatter(wrapper_path)
                    wrapper_text = wrapper_path.read_text(encoding="utf-8")
                    compare(findings, repo, wrapper_path, "name", internal_dir_name, wrapper.get("name"))
                    compare(
                        findings,
                        repo,
                        wrapper_path,
                        "description",
                        internal_description,
                        wrapper.get("description"),
                    )
                    require_text_contains(
                        findings,
                        repo,
                        wrapper_path,
                        "source-of-truth",
                        shared_skill_ref,
                        wrapper_text,
                    )
                else:
                    findings.append(Finding(repo_relative(repo, wrapper_path), "exists", "present", "missing"))

                wrapper_dir = wrapper_path.parent
                if wrapper_dir.exists():
                    for wrapper_file in sorted(path for path in wrapper_dir.rglob("*") if path.is_file()):
                        if wrapper_file == wrapper_path:
                            continue
                        expected_shared_path = (
                            repo
                            / "internal-skills"
                            / internal_dir_name
                            / wrapper_file.relative_to(wrapper_dir)
                        )
                        findings.append(
                            Finding(
                                repo_relative(repo, wrapper_file),
                                "shared-location",
                                repo_relative(repo, expected_shared_path),
                                repo_relative(repo, wrapper_file),
                            )
                        )

    for runtime_dir in (".claude", ".agents"):
        skills_dir = repo / runtime_dir / "skills"
        if not skills_dir.exists():
            continue
        for wrapper_path in sorted(skills_dir.glob("*/SKILL.md")):
            wrapper_name = wrapper_path.parent.name
            if wrapper_name in internal_skill_names:
                continue
            findings.append(
                Finding(
                    repo_relative(repo, wrapper_path),
                    "source-of-truth",
                    f"internal-skills/{wrapper_name}/SKILL.md",
                    "missing",
                )
            )


def check_stop_hook_parity(repo: Path, findings: list[Finding]) -> None:
    claude_path = repo / ".claude" / "settings.json"
    codex_path = repo / ".codex" / "hooks.json"
    if not claude_path.exists() and not codex_path.exists():
        return
    if not claude_path.exists():
        findings.append(Finding(repo_relative(repo, claude_path), "exists", "present", "missing"))
        return
    if not codex_path.exists():
        findings.append(Finding(repo_relative(repo, codex_path), "exists", "present", "missing"))
        return

    def commands(path: Path) -> list[str]:
        payload = read_json(path)
        groups = payload.get("hooks", {}).get("Stop", [])
        return [
            normalize_text(hook.get("command"))
            for group in groups
            if isinstance(group, dict)
            for hook in group.get("hooks", [])
            if isinstance(hook, dict) and hook.get("type") == "command"
        ]

    compare(findings, repo, codex_path, "hooks.Stop.commands", commands(claude_path), commands(codex_path))


def check_repo(repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    plugin_dirs = check_plugin_metadata(repo, findings)
    check_skill_metadata(repo, plugin_dirs, findings)
    check_internal_skill_wrappers(repo, findings)
    check_stop_hook_parity(repo, findings)
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
