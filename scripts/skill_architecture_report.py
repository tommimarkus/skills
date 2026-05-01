#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPORT_GROUPS = (
    "Trigger Metadata",
    "Workflow Body",
    "On-Demand Knowledge",
    "Deterministic Machinery",
    "Runtime Parity",
    "Repo Guidance Drift",
)

RERUN_COMMAND = "scripts/skill-architecture-report.sh ."
CATEGORY_COVERAGE_FLOOR = 80.0
REPLACEMENT_LEDGER_REL = "tests/skill_architecture_report_ledger.jsonl"
MIN_REPLACEMENT_CASES = 500
MIN_AUTOMATED_RECALL = 90.0
SEVERITY_WEIGHTS = {
    "blocker": 13.0,
    "high": 8.0,
    "medium": 5.0,
    "low": 3.0,
}


@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    severity: str
    standard_anchor: str
    detector_type: str
    fixture_cases: tuple[str, ...]
    remediation: str

    @property
    def weight(self) -> float:
        return SEVERITY_WEIGHTS[self.severity]


@dataclass(frozen=True)
class Coverage:
    deterministic_weight: float
    heuristic_weight: float
    manual_prompt_weight: float
    uncovered_weight: float
    category_percentages: dict[str, float]

    @property
    def total_weight(self) -> float:
        return (
            self.deterministic_weight
            + self.heuristic_weight
            + self.manual_prompt_weight
            + self.uncovered_weight
        )

    @property
    def covered_weight(self) -> float:
        return self.deterministic_weight + self.heuristic_weight + self.manual_prompt_weight

    @property
    def weighted_percentage(self) -> float:
        if self.total_weight == 0:
            return 100.0
        return self.covered_weight / self.total_weight * 100


@dataclass(frozen=True)
class ReplacementCalibration:
    ledger_path: str
    case_count: int
    gold_finding_count: int
    automated_caught_count: int
    manual_only_finding_count: int
    minimum_cases: int = MIN_REPLACEMENT_CASES
    minimum_recall_percentage: float = MIN_AUTOMATED_RECALL

    @property
    def automated_recall_percentage(self) -> float:
        if self.gold_finding_count == 0:
            return 0.0
        return self.automated_caught_count / self.gold_finding_count * 100

    @property
    def passes(self) -> bool:
        return (
            self.case_count >= self.minimum_cases
            and self.automated_recall_percentage >= self.minimum_recall_percentage
        )


@dataclass(frozen=True)
class Finding:
    group: str
    severity: str
    code: str
    path: str
    evidence: str
    rule: str
    claude_impact: str
    codex_impact: str
    action: str
    verify: str = RERUN_COMMAND


@dataclass(frozen=True)
class SkillFile:
    rel: str
    path: Path
    skill_dir: str
    name: str
    description: str
    body: str
    scope: str


def build_rule_catalog() -> tuple[Rule, ...]:
    return (
        Rule(
            "SAC-TRIGGER-DESC-LENGTH",
            "Trigger Metadata",
            "high",
            "docs/skill-architecture.md#1-trigger-metadata",
            "deterministic",
            ("overlong-description", "normal-description"),
            "Shorten the description and front-load the concrete trigger plus boundary context.",
        ),
        Rule(
            "SAC-TRIGGER-MISSING-CONTEXT",
            "Trigger Metadata",
            "high",
            "docs/skill-architecture.md#1-trigger-metadata",
            "heuristic",
            ("vague-trigger", "use-when-boundary"),
            "Add a concise Use when trigger and at least one boundary or out-of-scope cue.",
        ),
        Rule(
            "SAC-TRIGGER-AGGRESSIVE",
            "Trigger Metadata",
            "medium",
            "docs/skill-architecture.md#1-trigger-metadata",
            "heuristic",
            ("always-use-anything", "specific-trigger"),
            "Replace broad imperative trigger wording with concrete task contexts and negative boundaries.",
        ),
        Rule(
            "SAC-TRIGGER-SHORTCUT-DESCRIPTION",
            "Trigger Metadata",
            "medium",
            "docs/skill-architecture.md#1-trigger-metadata",
            "heuristic",
            ("shortcut-description", "capability-description"),
            "Move workflow-step sequences out of trigger metadata and into SKILL.md.",
        ),
        Rule(
            "SAC-WORKFLOW-BODY-SIZE",
            "Workflow Body",
            "medium",
            "docs/skill-architecture.md#2-always-loaded-workflow-skillmd",
            "deterministic",
            ("oversized-skill-body", "compact-skill-body"),
            "Move rarely needed procedure detail into referenced files with explicit load conditions.",
        ),
        Rule(
            "SAC-WORKFLOW-STOP-CONDITIONS",
            "Workflow Body",
            "medium",
            "docs/skill-architecture.md#2-always-loaded-workflow-skillmd",
            "heuristic",
            ("missing-stop-condition", "explicit-stop-condition"),
            "Add explicit stop conditions for blockers, ambiguity, and verification failure.",
        ),
        Rule(
            "SAC-WORKFLOW-OUTPUT",
            "Workflow Body",
            "high",
            "docs/skill-architecture.md#2-always-loaded-workflow-skillmd",
            "heuristic",
            ("missing-output-contract", "explicit-output-contract"),
            "Add a short output contract naming required sections or fields for the final response.",
        ),
        Rule(
            "SAC-WORKFLOW-INPUT-CONTRACT",
            "Workflow Body",
            "high",
            "docs/skill-architecture.md#2-always-loaded-workflow-skillmd",
            "heuristic",
            ("missing-input-contract", "explicit-input-contract"),
            "Add an explicit input or evidence contract so agents know what to inspect before acting.",
        ),
        Rule(
            "SAC-WORKFLOW-EVIDENCE-CONTRACT",
            "Workflow Body",
            "high",
            "docs/skill-architecture.md#2-always-loaded-workflow-skillmd",
            "heuristic",
            ("missing-evidence-contract", "explicit-evidence-contract"),
            "Add an evidence or citation contract so outputs show what was inspected.",
        ),
        Rule(
            "SAC-WORKFLOW-ASK-CONTINUE",
            "Workflow Body",
            "medium",
            "docs/skill-architecture.md#2-always-loaded-workflow-skillmd",
            "heuristic",
            ("missing-ask-continue-rule", "explicit-ask-continue-rule"),
            "Add ask-vs-continue rules for ambiguity, missing inputs, and scope uncertainty.",
        ),
        Rule(
            "SAC-WORKFLOW-RERUN-GUIDANCE",
            "Workflow Body",
            "medium",
            "docs/skill-architecture.md#2-always-loaded-workflow-skillmd",
            "heuristic",
            ("missing-rerun-guidance", "explicit-rerun-guidance"),
            "Add exact validation or rerun guidance near the workflow's completion criteria.",
        ),
        Rule(
            "SAC-WORKFLOW-GENERIC-STEPS",
            "Workflow Body",
            "medium",
            "docs/skill-architecture.md#craft-scorecard",
            "heuristic",
            ("generic-coding-steps", "domain-specific-decision-steps"),
            "Replace generic coding-agent instructions with domain-specific decisions, checks, or stop gates.",
        ),
        Rule(
            "SAC-WORKFLOW-OVERCONSTRAINED",
            "Workflow Body",
            "medium",
            "docs/skill-architecture.md#model-family-calibration",
            "heuristic",
            ("broad-you-must-language", "calibrated-mandatory-language"),
            "Reserve mandatory language for hard gates and leave judgment zones explicit.",
        ),
        Rule(
            "SAC-REF-LIKELY-PROSE-DUMP",
            "On-Demand Knowledge",
            "low",
            "docs/skill-architecture.md#3-on-demand-knowledge",
            "heuristic",
            ("reference-prose-in-skill", "one-hop-reference"),
            "Move reference prose into references/ or extensions/ and leave explicit load instructions in SKILL.md.",
        ),
        Rule(
            "SAC-REF-BROKEN-LINK",
            "On-Demand Knowledge",
            "high",
            "docs/skill-architecture.md#3-on-demand-knowledge",
            "deterministic",
            ("missing-support-link", "resolved-support-link"),
            "Fix the link target or remove the stale reference from the skill body.",
        ),
        Rule(
            "SAC-REF-UNCONDITIONAL-LOAD",
            "On-Demand Knowledge",
            "medium",
            "docs/skill-architecture.md#3-on-demand-knowledge",
            "heuristic",
            ("unconditional-reference-load", "conditional-reference-load"),
            "Add a concrete load condition for referenced support material.",
        ),
        Rule(
            "SAC-REF-UNADVERTISED-PLUGIN-DOC",
            "On-Demand Knowledge",
            "medium",
            "docs/skill-architecture.md#3-on-demand-knowledge",
            "deterministic",
            ("unmentioned-plugin-reference-doc", "plugin-reference-doc-mentioned-by-skill"),
            "Mention the plugin-level reference document from the owning skill workflow or remove the stale document.",
        ),
        Rule(
            "SAC-REF-UNADVERTISED-SUPPORT",
            "On-Demand Knowledge",
            "low",
            "docs/skill-architecture.md#3-on-demand-knowledge",
            "heuristic",
            ("unmentioned-reference-file", "mentioned-reference-bucket"),
            "Mention the support area from SKILL.md with a precise condition, or remove it if obsolete.",
        ),
        Rule(
            "SAC-SCRIPT-UNADVERTISED",
            "Deterministic Machinery",
            "medium",
            "docs/skill-architecture.md#4-deterministic-machinery",
            "deterministic",
            ("unmentioned-helper-script", "documented-helper-script"),
            "Add usage and load conditions for this script in SKILL.md, including a verification command.",
        ),
        Rule(
            "SAC-FIXTURE-UNADVERTISED",
            "Deterministic Machinery",
            "medium",
            "docs/skill-architecture.md#4-deterministic-machinery",
            "deterministic",
            ("unmentioned-fixture", "documented-fixture"),
            "Mention the fixture from SKILL.md with its validation condition or remove the stale fixture.",
        ),
        Rule(
            "SAC-TEMPLATE-UNADVERTISED",
            "Deterministic Machinery",
            "medium",
            "docs/skill-architecture.md#4-deterministic-machinery",
            "deterministic",
            ("unmentioned-template", "documented-template"),
            "Mention the template from SKILL.md with its use condition or remove the unused template.",
        ),
        Rule(
            "SAC-ASSET-UNADVERTISED",
            "Deterministic Machinery",
            "medium",
            "docs/skill-architecture.md#4-deterministic-machinery",
            "deterministic",
            ("unmentioned-asset", "documented-asset"),
            "Mention the asset from SKILL.md with its use condition or remove the unused asset.",
        ),
        Rule(
            "SAC-RUNTIME-MISSING-OPENAI",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("published-skill-without-openai-yaml", "published-skill-with-openai-yaml"),
            "Add agents/openai.yaml that matches the skill purpose and trigger boundaries.",
        ),
        Rule(
            "SAC-RUNTIME-NAME-DRIFT",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("frontmatter-name-drift", "frontmatter-name-matches-directory"),
            "Rename the directory or update frontmatter so both match.",
        ),
        Rule(
            "SAC-RUNTIME-PLUGIN-JSON",
            "Runtime Parity",
            "blocker",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("invalid-plugin-json", "valid-plugin-json"),
            "Fix JSON syntax, then rerun the report.",
        ),
        Rule(
            "SAC-RUNTIME-DEFAULT-PROMPTS",
            "Runtime Parity",
            "medium",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("four-default-prompts", "three-default-prompts"),
            "Reduce defaultPrompt to the highest-value three prompts and keep remaining examples in docs or references.",
        ),
        Rule(
            "SAC-RUNTIME-MANIFEST-SYNC",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("manifest-name-version-description-drift", "manifest-surfaces-synchronized"),
            "Synchronize plugin name, version, and description across Claude, Codex, and marketplace manifests.",
        ),
        Rule(
            "SAC-RUNTIME-CODEX-SKILLS-PATH",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("missing-codex-skills-path", "codex-skills-path-present"),
            "Set .codex-plugin/plugin.json skills to ./skills/ so Codex can load bundled skills.",
        ),
        Rule(
            "SAC-RUNTIME-MISSING-CLAUDE-AGENT",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("published-skill-without-claude-agent", "published-skill-with-claude-agent"),
            "Add the matching plugin-root Claude Code subagent for this published skill.",
        ),
        Rule(
            "SAC-RUNTIME-MISSING-CODEX-AGENT",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("published-skill-without-codex-agent", "published-skill-with-codex-agent"),
            "Add the matching project-scoped Codex custom agent for this published skill.",
        ),
        Rule(
            "SAC-RUNTIME-CLAUDE-AGENT-NAME-DRIFT",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("subagent-name-drift", "subagent-name-matches-skill"),
            "Make the Claude Code subagent frontmatter name match the skill directory.",
        ),
        Rule(
            "SAC-RUNTIME-CLAUDE-AGENT-MISSING-SKILL-TOOL",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("subagent-without-skill-tool", "subagent-with-skill-tool"),
            "Include the Skill tool in the matching Claude Code subagent.",
        ),
        Rule(
            "SAC-RUNTIME-AGENT-DESC-DRIFT",
            "Runtime Parity",
            "medium",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("subagent-description-drift", "subagent-description-matches-skill"),
            "Make the Claude Code subagent description mirror the skill description.",
        ),
        Rule(
            "SAC-RUNTIME-CODEX-AGENT-MISSING-SKILL-SOURCE",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("codex-agent-without-skill-source", "codex-agent-uses-skill-source"),
            "Make the Codex custom agent point to the matching skill as its source of truth.",
        ),
        Rule(
            "SAC-RUNTIME-CODEX-AGENT-MISSING-FOOTER",
            "Runtime Parity",
            "medium",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("codex-agent-without-footer-contract", "codex-agent-preserves-footer-contract"),
            "Make the Codex custom agent preserve the skill's footer disclosure contract.",
        ),
        Rule(
            "SAC-RUNTIME-OPENAI-NAME-DRIFT",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("openai-yaml-name-drift", "openai-yaml-name-matches-skill"),
            "Make agents/openai.yaml name match the skill directory name.",
        ),
        Rule(
            "SAC-RUNTIME-OPENAI-DESC-DRIFT",
            "Runtime Parity",
            "medium",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("openai-yaml-description-drift", "openai-yaml-description-matches-skill"),
            "Make agents/openai.yaml description match the skill description when that field is present.",
        ),
        Rule(
            "SAC-RUNTIME-MISSING-CLAUDE-MANIFEST",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("marketplace-entry-without-claude-manifest", "marketplace-entry-with-claude-manifest"),
            "Add the missing .claude-plugin/plugin.json or remove the stale marketplace entry.",
        ),
        Rule(
            "SAC-RUNTIME-MISSING-CODEX-MANIFEST",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("marketplace-entry-without-codex-manifest", "marketplace-entry-with-codex-manifest"),
            "Add the missing .codex-plugin/plugin.json or document why the plugin is not Codex-visible.",
        ),
        Rule(
            "SAC-RUNTIME-MARKETPLACE-MISSING-ENTRY",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("plugin-manifests-without-marketplace-entry", "plugin-manifests-listed-in-marketplace"),
            "Add the plugin to .claude-plugin/marketplace.json or remove the orphan manifests.",
        ),
        Rule(
            "SAC-DOC-SPLIT-MARKETPLACE",
            "Repo Guidance Drift",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "deterministic",
            ("split-marketplace-catalog", "shared-marketplace-only"),
            "Remove the split catalog or document the explicit split decision in canonical repo guidance.",
        ),
        Rule(
            "SAC-DOC-MISSING-ENTRYPOINT",
            "Repo Guidance Drift",
            "low",
            "docs/skill-architecture.md#advisory-report-contract",
            "deterministic",
            ("missing-agents-or-claude-md", "both-entrypoints-present"),
            "Add the missing entrypoint or document why this fixture/repo is intentionally partial.",
        ),
        Rule(
            "SAC-MANUAL-TASK-VALUE-LIFT",
            "Workflow Body",
            "medium",
            "docs/skill-architecture.md#craft-scorecard",
            "manual-prompt",
            ("review-skill-output-against-generic-agent-baseline",),
            "Ask whether the skill changes decisions or catches failures a generic agent would miss.",
        ),
        Rule(
            "SAC-MANUAL-DEGREE-CALIBRATION",
            "Workflow Body",
            "medium",
            "docs/skill-architecture.md#model-family-calibration",
            "manual-prompt",
            ("review-hard-gates-vs-judgment-zones",),
            "Ask whether mandatory language is reserved for hard gates and judgment remains where needed.",
        ),
        Rule(
            "SAC-MANUAL-RUNTIME-PARITY-SEMANTICS",
            "Runtime Parity",
            "high",
            "docs/skill-architecture.md#runtime-contract",
            "manual-prompt",
            ("compare-claude-codex-user-facing-capability",),
            "Compare runtime metadata semantically after deterministic sync checks pass.",
        ),
        Rule(
            "SAC-MANUAL-IP-HANDOFF",
            "Repo Guidance Drift",
            "high",
            "docs/skill-architecture.md#source-anchors",
            "manual-prompt",
            ("run-ip-hygiene-review-when-source-material-changes",),
            "Prompt for the repo-internal IP hygiene pass when source-derived prose or bundled references changed.",
        ),
        Rule(
            "SAC-UNCOVERED-FRESH-AGENT-EVAL",
            "Workflow Body",
            "low",
            "docs/skill-architecture.md#improvement-loop",
            "uncovered",
            ("fresh-agent-forward-test-remains-human-run",),
            "Run the fixed eval prompts or a fresh-agent forward test outside this static report.",
        ),
    )


RULES_BY_ID = {rule.id: rule for rule in build_rule_catalog()}


def calculate_coverage(rules: Iterable[Rule]) -> Coverage:
    buckets = {
        "deterministic": 0.0,
        "heuristic": 0.0,
        "manual-prompt": 0.0,
        "uncovered": 0.0,
    }
    category_total = {category: 0.0 for category in REPORT_GROUPS}
    category_covered = {category: 0.0 for category in REPORT_GROUPS}
    for rule in rules:
        buckets[rule.detector_type] += rule.weight
        category_total[rule.category] += rule.weight
        if rule.detector_type != "uncovered":
            category_covered[rule.category] += rule.weight

    category_percentages = {}
    for category in REPORT_GROUPS:
        if category_total[category] == 0:
            category_percentages[category] = 100.0
        else:
            category_percentages[category] = category_covered[category] / category_total[category] * 100
    return Coverage(
        deterministic_weight=buckets["deterministic"],
        heuristic_weight=buckets["heuristic"],
        manual_prompt_weight=buckets["manual-prompt"],
        uncovered_weight=buckets["uncovered"],
        category_percentages=category_percentages,
    )


def usage() -> str:
    return (
        "Usage: scripts/skill-architecture-report.sh [--format markdown|json] [--strict] [repo-root]\n\n"
        "Runs deterministic Skill Architecture Craft Standard validation and emits\n"
        "Markdown or machine-readable JSON. Findings exit 0 unless --strict is set;\n"
        "usage and unreadable-path errors exit nonzero.\n"
    )


def relpath(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def normalize_field(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("|", "/")).strip()


def make_finding(
    group: str,
    severity: str,
    code: str,
    path: str,
    evidence: str,
    violated_rule: str,
    impact: str,
    action: str,
    verify: str = RERUN_COMMAND,
) -> Finding:
    claude_impact = impact
    codex_impact = impact
    if code == "SAC-TRIGGER-DESC-LENGTH":
        claude_impact = "Overlong descriptions make Claude trigger matching noisier."
        codex_impact = "Codex may reject or truncate overlong skill metadata."
    else:
        claude_impact = claude_impact.replace("Claude/Codex", "Claude")
        codex_impact = codex_impact.replace("Claude/Codex", "Codex")

    if "$repo_root" in verify:
        verify = RERUN_COMMAND

    return Finding(
        group=group,
        severity=severity,
        code=code,
        path=normalize_field(path),
        evidence=normalize_field(evidence),
        rule=normalize_field(violated_rule),
        claude_impact=normalize_field(claude_impact),
        codex_impact=normalize_field(codex_impact),
        action=normalize_field(action),
        verify=normalize_field(verify),
    )


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "\n".join(lines)

    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
    if end is None:
        return {}, "\n".join(lines)

    frontmatter_lines = lines[1:end]
    body = "\n".join(lines[end + 1 :])
    values: dict[str, str] = {}
    current_key: str | None = None
    block_lines: list[str] = []

    def flush_block() -> None:
        nonlocal current_key, block_lines
        if current_key is not None:
            values[current_key] = " ".join(part.strip() for part in block_lines).strip()
        current_key = None
        block_lines = []

    for line in frontmatter_lines:
        key_match = re.match(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$", line)
        if key_match:
            flush_block()
            key = key_match.group(1)
            value = (key_match.group(2) or "").strip()
            if value in {">", ">-", "|", "|-"}:
                current_key = key
                block_lines = []
            else:
                values[key] = value.strip('"').strip("'")
            continue

        if current_key is not None and (line.startswith(" ") or line.startswith("\t")):
            block_lines.append(line)

    flush_block()
    return values, body


def parse_simple_metadata(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$", line)
        if match:
            values[match.group(1)] = (match.group(2) or "").strip().strip('"').strip("'")
    return values


def load_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, str(error)
    if not isinstance(parsed, dict):
        return None, "top-level JSON value is not an object"
    return parsed, None


def load_toml(path: Path) -> tuple[dict | None, str | None]:
    try:
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        return None, str(error)
    if not isinstance(parsed, dict):
        return None, "top-level TOML value is not a table"
    return parsed, None


def body_line_count(body: str) -> int:
    if body == "":
        return 0
    return len(body.splitlines())


def skill_scope(rel: str) -> str:
    if rel.startswith(".claude/skills/"):
        return "internal"
    if "/skills/" in rel and rel.endswith("/SKILL.md"):
        return "published"
    return "unknown"


def skill_dir_from_rel(rel: str) -> str:
    return rel.removesuffix("/SKILL.md")


def plugin_dir_from_skill_dir(skill_dir: str) -> str:
    return skill_dir.split("/skills/", 1)[0]


def load_skill(repo_root: Path, rel: str) -> SkillFile:
    path = repo_root / rel
    frontmatter, body = parse_frontmatter(path)
    return SkillFile(
        rel=rel,
        path=path,
        skill_dir=skill_dir_from_rel(rel),
        name=frontmatter.get("name", ""),
        description=frontmatter.get("description", ""),
        body=body,
        scope=skill_scope(rel),
    )


IGNORED_PATH_PARTS = {
    ".cache",
    ".git",
    ".gradle",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".worktrees",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
}


def path_is_ignored(path: Path) -> bool:
    return any(part in IGNORED_PATH_PARTS for part in path.parts)


def find_skill_files(repo_root: Path) -> list[str]:
    skill_files: set[str] = set()
    for path in repo_root.rglob("SKILL.md"):
        if path_is_ignored(path.relative_to(repo_root)):
            continue
        rel = relpath(repo_root, path)
        if re.search(r"(^|/)skills/[^/]+/SKILL\.md$", rel):
            skill_files.add(rel)
    return sorted(skill_files)


def find_codex_plugins(repo_root: Path) -> list[str]:
    plugins: list[str] = []
    for path in repo_root.rglob("plugin.json"):
        rel = path.relative_to(repo_root)
        if path_is_ignored(rel):
            continue
        if rel.parts[-2:] == (".codex-plugin", "plugin.json"):
            plugins.append(relpath(repo_root, path))
    return sorted(plugins)


def markdown_links(text: str) -> Iterable[str]:
    for match in re.finditer(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", text):
        yield match.group(1)


def support_is_advertised(text: str, target: str) -> bool:
    direct_needles = (
        f"({target})",
        f"({target}#",
        f"({target}/)",
        f"({target}/#",
    )
    if any(needle in text for needle in direct_needles):
        return True

    path_char = re.compile(r"[A-Za-z0-9_./-]")
    cue = re.compile(
        r"(read|load|use|consult|open|see|follow|run|verify|validate|inspect|"
        r"cite|apply|emit|copy|rerun|re-run|scan)",
        re.I,
    )
    negative = re.compile(r"(do not|never|ignore|obsolete|deprecated|deleted|remove|historical)", re.I)

    for line in text.splitlines():
        if negative.search(line):
            continue
        start = 0
        while True:
            index = line.find(target, start)
            if index < 0:
                break
            before = line[index - 1] if index > 0 else ""
            after_index = index + len(target)
            after = line[after_index] if after_index < len(line) else ""
            after2 = line[after_index + 1] if after_index + 1 < len(line) else ""
            before_ok = not before or not path_char.match(before)
            after_ok = (
                not after
                or after in ".,;:)"
                or not path_char.match(after)
                or (after == "/" and not path_char.match(after2))
            )
            if before_ok and after_ok and (cue.search(line) or line.lstrip().startswith("|")):
                return True
            start = index + len(target)
    return False


def support_files(repo_root: Path, skill_dir: str) -> list[str]:
    root = repo_root / skill_dir
    results: list[str] = []
    for bucket in ("references", "extensions", "examples"):
        support_root = root / bucket
        if not support_root.exists():
            continue
        for path in support_root.rglob("*"):
            if path.is_file():
                results.append(relpath(repo_root, path))
    return sorted(results)


def bucket_files(repo_root: Path, skill_dir: str, bucket: str) -> list[str]:
    root = repo_root / skill_dir / bucket
    if not root.exists():
        return []
    return sorted(relpath(repo_root, path) for path in root.rglob("*") if path.is_file())


def has_input_contract(text: str) -> bool:
    return bool(
        re.search(
            r"(?im)^\s*(?:#+\s*)?(inputs?|evidence|target|pre[- ]flight|before .*confirm|audit target|diagram kind)\b",
            text,
        )
        or re.search(r"\bInputs?:", text)
    )


def has_evidence_contract(text: str) -> bool:
    return bool(
        re.search(
            r"\b(evidence|cite|citation|source-readable|inspected files?|inspected commands?|"
            r"reference sections?|smell codes?|verification layer|confirmation layer|reference path)\b",
            text,
            re.I,
        )
    )


def has_ask_continue_contract(text: str) -> bool:
    return bool(
        re.search(
            r"\b(if .*ambiguous|ambiguous request|ask the user|ask —|ask --|don't invent|do not guess|"
            r"if .*missing|halt and ask|stop and ask|clarify|confirm .* if)\b",
            text,
            re.I,
        )
    )


def unconditional_support_loads(text: str) -> list[str]:
    matches: list[str] = []
    condition = re.compile(r"\b(when|if|for|after|before|based on|conditional on|only when|as needed)\b", re.I)
    load_line = re.compile(r"^(?:[*_` ]*)\b(read|load|consult|open)\b.*\b(references|extensions|examples|fixtures)/[A-Za-z0-9_./-]+", re.I)
    path_pattern = re.compile(r"\b(?:references|extensions|examples|fixtures)/[A-Za-z0-9_./-]+")
    for line in text.splitlines():
        if not load_line.search(line) or condition.search(line):
            continue
        path_match = path_pattern.search(line)
        if path_match:
            matches.append(path_match.group(0).rstrip(".,;:)"))
    return matches


def frontmatter_tools_include_skill(tools: str) -> bool:
    return any(part.strip() == "Skill" for part in re.split(r"[,|\s]+", tools) if part.strip())


def codex_agent_points_to_skill(instructions: str, skill_name: str) -> bool:
    return bool(
        re.search(rf"\buse the {re.escape(skill_name)} skill as the source of truth\b", instructions, re.I)
        or re.search(rf"\b(activate|read|invoke).*{re.escape(skill_name)} skill", instructions, re.I)
    )


def codex_agent_preserves_footer(instructions: str) -> bool:
    return bool(
        re.search(
            r"\b(footer disclosure|disclosure footer|footer|extensions loaded|mcp availability|reference path)\b",
            instructions,
            re.I,
        )
    )


def scan_skill(repo_root: Path, skill: SkillFile) -> list[Finding]:
    findings: list[Finding] = []
    combined_opening = f"{skill.description}\n" + "\n".join(skill.body.splitlines()[:40])
    full_text = skill.path.read_text(encoding="utf-8")

    if len(skill.description) > 1024:
        findings.append(
            make_finding(
                "Trigger Metadata",
                "high",
                "SAC-TRIGGER-DESC-LENGTH",
                skill.rel,
                f"description length={len(skill.description)} characters",
                "Frontmatter description must stay at or below 1024 characters.",
                "Codex may reject or truncate overlong metadata; Claude trigger matching also gets noisier.",
                "Shorten the description and front-load the concrete trigger plus boundary context.",
            )
        )

    if not re.search(r"\b(use when|trigger when|invoke when|do not use when|boundary|scope|out of scope)\b", combined_opening, re.I):
        findings.append(
            make_finding(
                "Trigger Metadata",
                "high",
                "SAC-TRIGGER-MISSING-CONTEXT",
                skill.rel,
                "description/body opening lacks explicit trigger or boundary language",
                "Skill metadata should name positive use context and near-miss boundaries.",
                "Agents may invoke the skill too late, too broadly, or miss it for terse user requests.",
                "Add a concise Use when trigger and at least one boundary or out-of-scope cue.",
            )
        )

    if re.search(r"\b(always use|must use|for anything|for everything|any request|all tasks)\b", skill.description, re.I):
        findings.append(
            make_finding(
                "Trigger Metadata",
                "medium",
                "SAC-TRIGGER-AGGRESSIVE",
                skill.rel,
                f"description contains aggressive trigger wording: {skill.description[:180]}",
                "Triggers should be specific enough to stay quiet for near-miss prompts.",
                "Claude/Codex may over-trigger this skill and consume context before the right workflow is selected.",
                "Replace broad imperative trigger wording with concrete task contexts and negative boundaries.",
            )
        )

    if re.search(
        r"\b(analy[sz]e the code|implement the best solution|run tests|summari[sz]e the changes|"
        r"best practices|general help|any code)\b",
        skill.description,
        re.I,
    ):
        findings.append(
            make_finding(
                "Trigger Metadata",
                "medium",
                "SAC-TRIGGER-SHORTCUT-DESCRIPTION",
                skill.rel,
                f"description contains workflow or vague shortcut wording: {skill.description[:180]}",
                "Trigger metadata should select the skill, not compress the workflow or advertise generic help.",
                "Claude/Codex may skip the loaded workflow or over-trigger on broad nearby tasks.",
                "Move workflow-step sequences out of trigger metadata and into SKILL.md.",
            )
        )

    if body_line_count(skill.body) > 500:
        findings.append(
            make_finding(
                "Workflow Body",
                "medium",
                "SAC-WORKFLOW-BODY-SIZE",
                skill.rel,
                f"body lines={body_line_count(skill.body)}",
                "SKILL.md should stay focused; detailed rubrics and examples belong in one-hop support files.",
                "Large bodies spend agent context every run and make iterative improvement slower.",
                "Move rarely needed procedure detail into referenced files with explicit load conditions.",
            )
        )

    if not re.search(r"\b(stop when|stop if|do not proceed|halt|blocker|exit nonzero|exit 0|ask the user|escalate|unsupported|cannot proceed)\b", full_text, re.I):
        findings.append(
            make_finding(
                "Workflow Body",
                "medium",
                "SAC-WORKFLOW-STOP-CONDITIONS",
                skill.rel,
                "no clear stop or escalation condition matched",
                "Agentic workflows should state when to stop, ask, or fail instead of guessing.",
                "Claude/Codex may continue past uncertainty, over-edit, or silently skip required evidence.",
                "Add explicit stop conditions for blockers, ambiguity, and verification failure.",
            )
        )

    if not re.search(r"\b(output|deliverable|return|report|findings|summary|response must|produce)\b", full_text, re.I):
        findings.append(
            make_finding(
                "Workflow Body",
                "high",
                "SAC-WORKFLOW-OUTPUT",
                skill.rel,
                "no concrete output contract matched",
                "Skills should define the shape of the agent's result, not just activities to perform.",
                "Claude/Codex may produce inconsistent responses that are hard to compare across iterations.",
                "Add a short output contract naming required sections or fields for the final response.",
            )
        )

    if not has_input_contract(full_text):
        findings.append(
            make_finding(
                "Workflow Body",
                "high",
                "SAC-WORKFLOW-INPUT-CONTRACT",
                skill.rel,
                "no explicit input, target, evidence, or pre-flight contract matched",
                "Skills should name the inputs or evidence an agent must inspect before acting.",
                "Claude/Codex may start from assumptions instead of checking the real target surface.",
                "Add an explicit input or evidence contract so agents know what to inspect before acting.",
            )
        )

    if not has_evidence_contract(skill.body):
        findings.append(
            make_finding(
                "Workflow Body",
                "high",
                "SAC-WORKFLOW-EVIDENCE-CONTRACT",
                skill.rel,
                "no evidence, citation, inspected-source, or verification-layer contract matched",
                "Skills should define how outputs prove what evidence was inspected.",
                "Claude/Codex may produce plausible findings without enough traceability for review.",
                "Add an evidence or citation contract so outputs show what was inspected.",
            )
        )

    if not has_ask_continue_contract(full_text):
        findings.append(
            make_finding(
                "Workflow Body",
                "medium",
                "SAC-WORKFLOW-ASK-CONTINUE",
                skill.rel,
                "no ask-vs-continue rule matched",
                "Skills should say when ambiguity, missing inputs, or scope uncertainty require asking.",
                "Claude/Codex may proceed through uncertainty or ask when the workflow already has a safe default.",
                "Add ask-vs-continue rules for ambiguity, missing inputs, and scope uncertainty.",
            )
        )

    if not re.search(r"\b(rerun|re-run|verify|validate|validation|test command|run .* again)\b", full_text, re.I):
        findings.append(
            make_finding(
                "Workflow Body",
                "medium",
                "SAC-WORKFLOW-RERUN-GUIDANCE",
                skill.rel,
                "no rerun or validation loop matched",
                "Skills should tell agents how to verify and repeat after edits.",
                "Claude/Codex may stop after a plausible edit without proving the workflow still works.",
                "Add exact validation or rerun guidance near the workflow's completion criteria.",
            )
        )

    if re.search(r"\banalyze the code, implement the best solution, run tests\b", full_text, re.I):
        findings.append(
            make_finding(
                "Workflow Body",
                "medium",
                "SAC-WORKFLOW-GENERIC-STEPS",
                skill.rel,
                "body uses generic coding-agent sequence instead of skill-specific decision steps",
                "A skill should change decisions or catch failures a generic agent would miss.",
                "Claude/Codex may spend context loading a skill that adds no task-specific lift.",
                "Replace generic coding-agent instructions with domain-specific decisions, checks, or stop gates.",
            )
        )

    broad_must_lines = re.findall(r"(?im)^\s*you must (?:always|never|continue|edit|use|defer|ask)\b", full_text)
    if len(broad_must_lines) >= 3:
        findings.append(
            make_finding(
                "Workflow Body",
                "medium",
                "SAC-WORKFLOW-OVERCONSTRAINED",
                skill.rel,
                f"{len(broad_must_lines)} broad 'you must' lines matched",
                "Mandatory language should be reserved for hard gates rather than broad behavior control.",
                "Claude/Codex may follow rigid instructions when judgment or user clarification is required.",
                "Reserve mandatory language for hard gates and leave judgment zones explicit.",
            )
        )

    if re.search(r"\b(reference-like|comprehensive catalog|full catalog|every possible|complete reference|long reference|all possible options)\b", full_text, re.I):
        findings.append(
            make_finding(
                "On-Demand Knowledge",
                "low",
                "SAC-REF-LIKELY-PROSE-DUMP",
                skill.rel,
                "body contains wording that looks like reference prose",
                "Detailed reusable knowledge should live in one-hop references loaded only when needed.",
                "Agents pay the context cost on every invocation and may miss the core workflow.",
                "Move reference prose into references/ or extensions/ and leave explicit load instructions in SKILL.md.",
            )
        )

    for support_load in unconditional_support_loads(full_text):
        findings.append(
            make_finding(
                "On-Demand Knowledge",
                "medium",
                "SAC-REF-UNCONDITIONAL-LOAD",
                skill.rel,
                f"support path loaded without a condition: {support_load}",
                "Support files should be loaded through explicit task or target conditions.",
                "Claude/Codex may load heavy references unnecessarily or miss the intended decision point.",
                "Add a concrete load condition for referenced support material.",
            )
        )

    for link in markdown_links(full_text):
        if link.startswith(("http:", "https:", "mailto:", "/")) or not link:
            continue
        if not (repo_root / skill.skill_dir / link).exists() and not (repo_root / link).exists():
            findings.append(
                make_finding(
                    "On-Demand Knowledge",
                    "high",
                    "SAC-REF-BROKEN-LINK",
                    skill.rel,
                    f"broken one-hop link target={link}",
                    "Support-file links from SKILL.md must resolve deterministically in local repo use.",
                    "Claude/Codex will fail or hallucinate missing procedure content during iterative improvement.",
                    "Fix the link target or remove the stale reference from the skill body.",
                )
            )

    unadvertised: dict[str, list[str]] = {}
    for support_rel in support_files(repo_root, skill.skill_dir):
        support_from_skill = support_rel.removeprefix(f"{skill.skill_dir}/")
        if support_from_skill.endswith("/README.md"):
            support_bucket = support_from_skill.removesuffix("/README.md")
            if support_is_advertised(full_text, support_from_skill) or support_is_advertised(full_text, support_bucket):
                continue
            unadvertised.setdefault(support_bucket, []).append(support_from_skill)
            continue

        support_bucket = support_from_skill
        if re.match(r"^(references|fixtures|examples)/.+/.+$", support_from_skill):
            support_bucket = support_from_skill.rsplit("/", 1)[0]

        if support_is_advertised(full_text, support_from_skill) or support_is_advertised(
            full_text, support_bucket
        ):
            continue
        unadvertised.setdefault(support_bucket, []).append(support_from_skill)

    for support_bucket in sorted(unadvertised):
        examples = ", ".join(unadvertised[support_bucket][:3])
        findings.append(
            make_finding(
                "On-Demand Knowledge",
                "low",
                "SAC-REF-UNADVERTISED-SUPPORT",
                f"{skill.skill_dir}/{support_bucket}",
                f"{len(unadvertised[support_bucket])} support file(s) not mentioned from {skill.rel}; examples: {examples}",
                "One-hop knowledge should be advertised with load conditions from SKILL.md.",
                "Claude/Codex may never discover useful support material or may load it at the wrong time.",
                "Mention this support area from SKILL.md with a precise condition, or remove it if obsolete.",
            )
        )

    for helper in sorted((repo_root / skill.skill_dir).glob("**/scripts/*")):
        if not helper.is_file():
            continue
        helper_rel = relpath(repo_root, helper)
        helper_from_skill = helper_rel.removeprefix(f"{skill.skill_dir}/")
        if helper_from_skill not in full_text:
            findings.append(
                make_finding(
                    "Deterministic Machinery",
                    "medium",
                    "SAC-SCRIPT-UNADVERTISED",
                    helper_rel,
                    f"script not advertised from {skill.rel}",
                    "Fragile or repeated work should be exposed through documented, discoverable commands.",
                    "Agents may reimplement deterministic checks by hand instead of using the bundled script.",
                    "Add usage and load conditions for this script in SKILL.md, including a verification command.",
                )
            )

    for fixture_rel in bucket_files(repo_root, skill.skill_dir, "fixtures"):
        fixture_from_skill = fixture_rel.removeprefix(f"{skill.skill_dir}/")
        if support_is_advertised(full_text, fixture_from_skill) or support_is_advertised(full_text, "fixtures"):
            continue
        findings.append(
            make_finding(
                "Deterministic Machinery",
                "medium",
                "SAC-FIXTURE-UNADVERTISED",
                fixture_rel,
                f"fixture not advertised from {skill.rel}",
                "Fixtures should be discoverable from the always-loaded workflow with their validation purpose.",
                "Claude/Codex may miss regression cases or invent ad hoc examples instead of using the bundled fixture.",
                "Mention the fixture from SKILL.md with its validation condition or remove the stale fixture.",
            )
        )

    for template_rel in bucket_files(repo_root, skill.skill_dir, "templates"):
        template_from_skill = template_rel.removeprefix(f"{skill.skill_dir}/")
        if support_is_advertised(full_text, template_from_skill) or support_is_advertised(full_text, "templates"):
            continue
        findings.append(
            make_finding(
                "Deterministic Machinery",
                "medium",
                "SAC-TEMPLATE-UNADVERTISED",
                template_rel,
                f"template not advertised from {skill.rel}",
                "Templates should be discoverable from the always-loaded workflow with a use condition.",
                "Claude/Codex may invent output shape instead of using the bundled template.",
                "Mention the template from SKILL.md with its use condition or remove the unused template.",
            )
        )

    for asset_rel in bucket_files(repo_root, skill.skill_dir, "assets"):
        asset_from_skill = asset_rel.removeprefix(f"{skill.skill_dir}/")
        if support_is_advertised(full_text, asset_from_skill) or support_is_advertised(full_text, "assets"):
            continue
        findings.append(
            make_finding(
                "Deterministic Machinery",
                "medium",
                "SAC-ASSET-UNADVERTISED",
                asset_rel,
                f"asset not advertised from {skill.rel}",
                "Skill assets should be discoverable from SKILL.md with their use condition.",
                "Claude/Codex may ignore required bundled material or use it outside the intended context.",
                "Mention the asset from SKILL.md with its use condition or remove the unused asset.",
            )
        )

    if skill.scope == "published" and not (repo_root / skill.skill_dir / "agents/openai.yaml").is_file():
        findings.append(
            make_finding(
                "Runtime Parity",
                "high",
                "SAC-RUNTIME-MISSING-OPENAI",
                skill.rel,
                f"missing {skill.skill_dir}/agents/openai.yaml",
                "Published plugin skills should include basic Codex metadata next to the shared skill.",
                "Claude may have usable subagent guidance while Codex lacks equivalent skill metadata.",
                "Add agents/openai.yaml that matches the skill purpose and trigger boundaries.",
            )
        )

    if skill.scope == "published":
        expected_name = Path(skill.skill_dir).name
        plugin_dir = plugin_dir_from_skill_dir(skill.skill_dir)
        agent_rel = f"{plugin_dir}/agents/{expected_name}.md"
        agent_path = repo_root / agent_rel
        codex_agent_rel = f".codex/agents/{expected_name}.toml"
        codex_agent_path = repo_root / codex_agent_rel
        if not agent_path.is_file():
            findings.append(
                make_finding(
                    "Runtime Parity",
                    "high",
                    "SAC-RUNTIME-MISSING-CLAUDE-AGENT",
                    skill.rel,
                    f"missing {agent_rel}",
                    "Published plugin skills should have matching plugin-root Claude Code subagents.",
                    "Claude delegated workflows may be unavailable while Codex metadata exists.",
                    "Add the matching plugin-root Claude Code subagent for this published skill.",
                )
            )
        else:
            agent_frontmatter, _agent_body = parse_frontmatter(agent_path)
            agent_name = agent_frontmatter.get("name", "")
            if agent_name and agent_name != expected_name:
                findings.append(
                    make_finding(
                        "Runtime Parity",
                        "high",
                        "SAC-RUNTIME-CLAUDE-AGENT-NAME-DRIFT",
                        agent_rel,
                        f"Claude subagent name={agent_name}, skill directory={expected_name}",
                        "Claude subagent frontmatter name should match the shared skill name.",
                        "Claude may expose a different invocation surface from the packaged skill.",
                        "Make the Claude Code subagent frontmatter name match the skill directory.",
                    )
                )
            agent_tools = agent_frontmatter.get("tools", "")
            if agent_tools and not frontmatter_tools_include_skill(agent_tools):
                findings.append(
                    make_finding(
                        "Runtime Parity",
                        "high",
                        "SAC-RUNTIME-CLAUDE-AGENT-MISSING-SKILL-TOOL",
                        agent_rel,
                        f"Claude subagent tools={agent_tools}",
                        "Matching Claude Code subagents should be able to invoke the bundled skill.",
                        "Claude may route to the subagent but fail to load the actual skill workflow.",
                        "Include the Skill tool in the matching Claude Code subagent.",
                    )
                )
            agent_description = agent_frontmatter.get("description", "")
            if skill.description and agent_description and skill.description != agent_description:
                findings.append(
                    make_finding(
                        "Runtime Parity",
                        "medium",
                        "SAC-RUNTIME-AGENT-DESC-DRIFT",
                        agent_rel,
                        "Claude subagent description differs from SKILL.md description",
                        "Claude subagent trigger metadata should mirror the skill description.",
                        "Claude trigger matching can drift from the shared skill contract.",
                        "Make the Claude Code subagent description mirror the skill description.",
                    )
                )

        if not codex_agent_path.is_file():
            findings.append(
                make_finding(
                    "Runtime Parity",
                    "high",
                    "SAC-RUNTIME-MISSING-CODEX-AGENT",
                    skill.rel,
                    f"missing {codex_agent_rel}",
                    "Published plugin skills should have matching project-scoped Codex custom agents in this repo.",
                    "Codex delegated workflows may be unavailable even though Claude subagents exist.",
                    "Add the matching project-scoped Codex custom agent for this published skill.",
                )
            )
        else:
            codex_agent, codex_agent_error = load_toml(codex_agent_path)
            if codex_agent_error is None and codex_agent is not None:
                instructions = str(codex_agent.get("developer_instructions", ""))
                if not codex_agent_points_to_skill(instructions, expected_name):
                    findings.append(
                        make_finding(
                            "Runtime Parity",
                            "high",
                            "SAC-RUNTIME-CODEX-AGENT-MISSING-SKILL-SOURCE",
                            codex_agent_rel,
                            "developer_instructions do not point to the matching skill as source of truth",
                            "Codex custom agents should delegate the contract back to SKILL.md.",
                            "Codex may drift from the shared skill workflow and duplicate stale procedure.",
                            "Make the Codex custom agent point to the matching skill as its source of truth.",
                        )
                    )
                if not codex_agent_preserves_footer(instructions):
                    findings.append(
                        make_finding(
                            "Runtime Parity",
                            "medium",
                            "SAC-RUNTIME-CODEX-AGENT-MISSING-FOOTER",
                            codex_agent_rel,
                            "developer_instructions do not mention footer or disclosure requirements",
                            "Codex custom agents should preserve the skill's output disclosure contract.",
                            "Codex outputs may omit loaded extensions, MCP availability, cost stance, or reference path details.",
                            "Make the Codex custom agent preserve the skill's footer disclosure contract.",
                        )
                    )

        openai_path = repo_root / skill.skill_dir / "agents/openai.yaml"
        openai = parse_simple_metadata(openai_path)
        if openai and "name" in openai and openai.get("name") != expected_name:
            findings.append(
                make_finding(
                    "Runtime Parity",
                    "high",
                    "SAC-RUNTIME-OPENAI-NAME-DRIFT",
                    f"{skill.skill_dir}/agents/openai.yaml",
                    f"openai.yaml name={openai.get('name')}, directory={expected_name}",
                    "Codex per-skill metadata name should match the skill directory.",
                    "Codex may expose confusing skill names or lose parity with the bundled skill.",
                    "Make agents/openai.yaml name match the skill directory name.",
                )
            )
        if openai and "description" in openai and skill.description and openai.get("description") != skill.description:
            findings.append(
                make_finding(
                    "Runtime Parity",
                    "medium",
                    "SAC-RUNTIME-OPENAI-DESC-DRIFT",
                    f"{skill.skill_dir}/agents/openai.yaml",
                    "openai.yaml description differs from SKILL.md description",
                    "Codex per-skill metadata should describe the same trigger contract as the shared skill.",
                    "Codex selection metadata may drift from the bundled workflow.",
                    "Make agents/openai.yaml description match the skill description when that field is present.",
                )
            )

    if skill.name and "/skills/" in skill.rel:
        expected_name = Path(skill.skill_dir).name
        if skill.name != expected_name:
            findings.append(
                make_finding(
                    "Runtime Parity",
                    "high",
                    "SAC-RUNTIME-NAME-DRIFT",
                    skill.rel,
                    f"frontmatter name={skill.name}, directory={expected_name}",
                    "Skill name should match its directory for predictable runtime discovery.",
                    "Claude/Codex may expose confusing names or fail parity checks.",
                    "Rename the directory or update frontmatter so both match.",
                )
            )

    return findings


def scan_codex_plugin(repo_root: Path, rel: str) -> list[Finding]:
    path = repo_root / rel
    plugin, error = load_json(path)
    if error is not None or plugin is None:
        return [
            make_finding(
                "Runtime Parity",
                "blocker",
                "SAC-RUNTIME-PLUGIN-JSON",
                rel,
                f"json could not parse plugin.json: {error}",
                "Plugin metadata must be valid JSON for both packaging and advisory checks.",
                "Codex plugin discovery can fail before skills are visible.",
                "Fix JSON syntax, then rerun the report.",
            )
        ]

    findings: list[Finding] = []
    if plugin.get("skills") != "./skills/":
        findings.append(
            make_finding(
                "Runtime Parity",
                "high",
                "SAC-RUNTIME-CODEX-SKILLS-PATH",
                rel,
                f"skills={plugin.get('skills')!r}",
                "Codex plugin manifests in this repo should point skills to ./skills/.",
                "Codex may install the plugin without exposing bundled skills.",
                "Set .codex-plugin/plugin.json skills to ./skills/ so Codex can load bundled skills.",
            )
        )

    default_prompts = plugin.get("interface", {}).get("defaultPrompt", [])
    prompt_count = len(default_prompts) if isinstance(default_prompts, list) else 0
    if prompt_count > 3:
        findings.append(
            make_finding(
                "Runtime Parity",
                "medium",
                "SAC-RUNTIME-DEFAULT-PROMPTS",
                rel,
                f"interface.defaultPrompt count={prompt_count}",
                "Codex defaultPrompt arrays should contain three or fewer entries.",
                "Extra Codex prompts are ignored or warned about, so advertised entrypoints drift from runtime truth.",
                "Reduce defaultPrompt to the highest-value three prompts and keep remaining examples in docs or references.",
            )
        )
    return findings


def find_plugin_reference_docs(repo_root: Path) -> list[str]:
    docs: list[str] = []
    for path in repo_root.rglob("docs"):
        rel = path.relative_to(repo_root)
        if path_is_ignored(rel):
            continue
        if not path.is_dir() or len(rel.parts) != 2:
            continue
        for reference_root in path.glob("*-reference"):
            if not reference_root.is_dir():
                continue
            for reference in reference_root.rglob("*"):
                if reference.is_file():
                    docs.append(relpath(repo_root, reference))
    return sorted(docs)


def skill_texts_by_plugin(repo_root: Path) -> dict[str, list[tuple[str, str]]]:
    texts: dict[str, list[tuple[str, str]]] = {}
    for skill_rel in find_skill_files(repo_root):
        if "/skills/" not in skill_rel or skill_rel.startswith(".claude/skills/"):
            continue
        skill_dir = skill_dir_from_rel(skill_rel)
        plugin_dir = plugin_dir_from_skill_dir(skill_dir)
        texts.setdefault(plugin_dir, []).append(
            (skill_dir, (repo_root / skill_rel).read_text(encoding="utf-8"))
        )
    return texts


def scan_plugin_reference_docs(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    skill_texts = skill_texts_by_plugin(repo_root)
    for doc_rel in find_plugin_reference_docs(repo_root):
        doc_path = repo_root / doc_rel
        plugin_dir = Path(doc_rel).parts[0]
        advertised = False
        for skill_dir, skill_text in skill_texts.get(plugin_dir, []):
            rel_from_skill = os.path.relpath(doc_path, repo_root / skill_dir).replace(os.sep, "/")
            rel_from_plugin = doc_rel.removeprefix(f"{plugin_dir}/")
            if (
                support_is_advertised(skill_text, rel_from_skill)
                or support_is_advertised(skill_text, rel_from_plugin)
                or support_is_advertised(skill_text, doc_rel)
            ):
                advertised = True
                break
        if advertised:
            continue
        findings.append(
            make_finding(
                "On-Demand Knowledge",
                "medium",
                "SAC-REF-UNADVERTISED-PLUGIN-DOC",
                doc_rel,
                "plugin-level reference document is not mentioned by any owning skill workflow",
                "Plugin-level reference documents should be explicitly selected by SKILL.md.",
                "Claude/Codex may never load the bundled reference or may apply the skill without its canonical rubric.",
                "Mention the plugin-level reference document from the owning skill workflow or remove the stale document.",
            )
        )
    return findings


def scan_manifest_sync(repo_root: Path) -> list[Finding]:
    marketplace_path = repo_root / ".claude-plugin/marketplace.json"
    if not marketplace_path.is_file():
        return []

    marketplace, error = load_json(marketplace_path)
    if error is not None or marketplace is None:
        return [
            make_finding(
                "Runtime Parity",
                "blocker",
                "SAC-RUNTIME-PLUGIN-JSON",
                ".claude-plugin/marketplace.json",
                f"json could not parse marketplace.json: {error}",
                "Marketplace metadata must be valid JSON for advisory checks.",
                "Claude/Codex marketplace discovery can fail before plugins are visible.",
                "Fix JSON syntax, then rerun the report.",
            )
        ]

    findings: list[Finding] = []
    plugins = marketplace.get("plugins", [])
    if not isinstance(plugins, list):
        return findings

    marketplace_sources: set[str] = set()
    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            continue
        source = str(entry.get("source", "")).removeprefix("./")
        if not source:
            continue
        marketplace_sources.add(source)
        surfaces: dict[str, dict] = {"marketplace": entry}
        for label, rel in (
            ("claude", f"{source}/.claude-plugin/plugin.json"),
            ("codex", f"{source}/.codex-plugin/plugin.json"),
        ):
            manifest_path = repo_root / rel
            if not manifest_path.is_file():
                code = (
                    "SAC-RUNTIME-MISSING-CLAUDE-MANIFEST"
                    if label == "claude"
                    else "SAC-RUNTIME-MISSING-CODEX-MANIFEST"
                )
                action = (
                    "Add the missing .claude-plugin/plugin.json or remove the stale marketplace entry."
                    if label == "claude"
                    else "Add the missing .codex-plugin/plugin.json or document why the plugin is not Codex-visible."
                )
                findings.append(
                    make_finding(
                        "Runtime Parity",
                        "high",
                        code,
                        rel,
                        f"marketplace entry source={source} has no {rel}",
                        "Marketplace entries should resolve to both runtime plugin manifests in this repo.",
                        "Claude/Codex marketplace discovery may expose only one runtime or fail during install.",
                        action,
                    )
                )
                continue
            manifest, manifest_error = load_json(manifest_path)
            if manifest_error is not None or manifest is None:
                findings.append(
                    make_finding(
                        "Runtime Parity",
                        "blocker",
                        "SAC-RUNTIME-PLUGIN-JSON",
                        rel,
                        f"json could not parse plugin.json: {manifest_error}",
                        "Plugin metadata must be valid JSON for runtime parity checks.",
                        "Claude/Codex plugin discovery can fail before skills are visible.",
                        "Fix JSON syntax, then rerun the report.",
                    )
                )
                continue
            surfaces[label] = manifest

        drift_fields = []
        for field in ("name", "version", "description"):
            values = {label: surface.get(field) for label, surface in surfaces.items()}
            if len(set(values.values())) > 1:
                drift_fields.append(f"{field}={values}")
        if drift_fields:
            findings.append(
                make_finding(
                    "Runtime Parity",
                    "high",
                    "SAC-RUNTIME-MANIFEST-SYNC",
                    source or f".claude-plugin/marketplace.json#plugins[{index}]",
                    "; ".join(drift_fields),
                    "Plugin name, version, and description should stay synchronized across marketplace, Claude, and Codex manifests.",
                    "Claude/Codex users may see different plugin identity or update surfaces.",
                    "Synchronize plugin name, version, and description across Claude, Codex, and marketplace manifests.",
                )
            )

    manifest_sources: set[str] = set()
    for manifest in repo_root.rglob("plugin.json"):
        rel = manifest.relative_to(repo_root)
        if path_is_ignored(rel):
            continue
        if rel.parts[-2:] not in {(".claude-plugin", "plugin.json"), (".codex-plugin", "plugin.json")}:
            continue
        if len(rel.parts) < 3:
            continue
        manifest_sources.add(rel.parts[0])

    for source in sorted(manifest_sources - marketplace_sources):
        findings.append(
            make_finding(
                "Runtime Parity",
                "high",
                "SAC-RUNTIME-MARKETPLACE-MISSING-ENTRY",
                source,
                "plugin manifest exists but .claude-plugin/marketplace.json has no matching source entry",
                "Published plugin manifests should be reachable from the shared marketplace.",
                "Claude/Codex local marketplace users may never see or update the plugin.",
                "Add the plugin to .claude-plugin/marketplace.json or remove the orphan manifests.",
            )
        )

    return findings


def scan_repo_guidance(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    if (repo_root / ".agents/plugins/marketplace.json").exists():
        findings.append(
            make_finding(
                "Repo Guidance Drift",
                "high",
                "SAC-DOC-SPLIT-MARKETPLACE",
                ".agents/plugins/marketplace.json",
                "secondary Codex marketplace catalog exists",
                "This repo uses .claude-plugin/marketplace.json as the shared marketplace unless a design explicitly splits catalogs.",
                "Claude/Codex package listings may drift and confuse local marketplace refreshes.",
                "Remove the split catalog or document the explicit split decision in canonical repo guidance.",
            )
        )

    if not (repo_root / "AGENTS.md").is_file() or not (repo_root / "CLAUDE.md").is_file():
        findings.append(
            make_finding(
                "Repo Guidance Drift",
                "low",
                "SAC-DOC-MISSING-ENTRYPOINT",
                ".",
                "AGENTS.md or CLAUDE.md is missing",
                "Cross-runtime skill repos need explicit agent entrypoint guidance.",
                "Claude/Codex contributors may apply inconsistent packaging and review rules.",
                "Add the missing entrypoint or document why this fixture/repo is intentionally partial.",
            )
        )
    return findings


def collect_findings(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for skill_rel in find_skill_files(repo_root):
        findings.extend(scan_skill(repo_root, load_skill(repo_root, skill_rel)))
    for plugin_rel in find_codex_plugins(repo_root):
        findings.extend(scan_codex_plugin(repo_root, plugin_rel))
    findings.extend(scan_plugin_reference_docs(repo_root))
    findings.extend(scan_manifest_sync(repo_root))
    findings.extend(scan_repo_guidance(repo_root))
    return findings


def load_replacement_ledger(repo_root: Path) -> list[dict]:
    ledger_path = repo_root / REPLACEMENT_LEDGER_REL
    if not ledger_path.is_file():
        return []
    cases: list[dict] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def write_fixture_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def skill_description_from_fixture(skill_path: Path) -> str:
    frontmatter, _body = parse_frontmatter(skill_path)
    return frontmatter.get("description", "Fixture metadata.")


def make_replacement_fixture(repo: Path, case: dict) -> None:
    if not case.get("omit_repo_guidance", False):
        write_fixture_file(repo / "AGENTS.md", "fixture agents\n")
        write_fixture_file(repo / "CLAUDE.md", "fixture claude\n")

    explicit_paths = {file["path"] for file in case["files"]}
    skill_dirs: list[str] = []
    for file in case["files"]:
        write_fixture_file(repo / file["path"], file["content"])
        if file["path"].endswith("/SKILL.md") and "/skills/" in file["path"]:
            skill_dirs.append(file["path"].removesuffix("/SKILL.md"))

    for skill_dir in skill_dirs:
        skill_name = Path(skill_dir).name
        plugin_dir = skill_dir.split("/skills/", 1)[0]
        skill_path = repo / skill_dir / "SKILL.md"
        description = skill_description_from_fixture(skill_path)

        agent_path = f"{plugin_dir}/agents/{skill_name}.md"
        if not case.get("omit_claude_agent", False) and agent_path not in explicit_paths:
            write_fixture_file(
                repo / agent_path,
                (
                    f"---\nname: {skill_name}\ndescription: {description}\n"
                    "tools: Skill\nmodel: sonnet\n---\n\nInvoke the skill.\n"
                ),
            )

        codex_agent_path = f".codex/agents/{skill_name}.toml"
        if not case.get("omit_codex_agent", False) and codex_agent_path not in explicit_paths:
            write_fixture_file(
                repo / codex_agent_path,
                (
                    f"name = \"{skill_name}\"\n"
                    f"description = \"Fixture Codex wrapper for {skill_name}.\"\n"
                    "sandbox_mode = \"workspace-write\"\n"
                    "developer_instructions = \"\"\"\n"
                    f"You are a fixture practitioner. Use the {skill_name} skill as the source of truth.\n"
                    "Always emit the footer disclosure required by the skill.\n"
                    "\"\"\"\n"
                ),
            )

        openai_path = f"{skill_dir}/agents/openai.yaml"
        if case.get("omit_openai", False) or openai_path in explicit_paths:
            continue
        write_fixture_file(
            repo / openai_path,
            f"name: {skill_name}\ndescription: {description}\n",
        )


def gold_issue_codes(case: dict) -> list[str]:
    issues = []
    if "gold_issue" in case:
        issues.append(case["gold_issue"])
    issues.extend(case.get("gold_issues", []))
    return [issue["code"] for issue in issues if isinstance(issue, dict) and issue.get("code")]


def calculate_replacement_calibration(repo_root: Path) -> ReplacementCalibration:
    cases = load_replacement_ledger(repo_root)
    if not cases:
        return ReplacementCalibration(
            ledger_path=REPLACEMENT_LEDGER_REL,
            case_count=0,
            gold_finding_count=0,
            automated_caught_count=0,
            manual_only_finding_count=0,
        )

    gold_count = 0
    caught_count = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        for index, case in enumerate(cases, start=1):
            fixture = tmp_root / f"case-{index:05d}"
            make_replacement_fixture(fixture, case)
            finding_codes = {finding.code for finding in collect_findings(fixture)}
            for code in gold_issue_codes(case):
                gold_count += 1
                if code in finding_codes:
                    caught_count += 1

    return ReplacementCalibration(
        ledger_path=REPLACEMENT_LEDGER_REL,
        case_count=len(cases),
        gold_finding_count=gold_count,
        automated_caught_count=caught_count,
        manual_only_finding_count=gold_count - caught_count,
    )


def count_severity(findings: list[Finding], severity: str) -> int:
    return sum(1 for finding in findings if finding.severity == severity)


def format_weight(value: float) -> str:
    return f"{value:.1f}"


def format_category_percentages(coverage: Coverage) -> str:
    return ", ".join(
        f"{category}={coverage.category_percentages[category]:.1f}%" for category in REPORT_GROUPS
    )


def format_categories_below_floor(coverage: Coverage) -> str:
    below = [
        category
        for category in REPORT_GROUPS
        if coverage.category_percentages[category] < CATEGORY_COVERAGE_FLOOR
    ]
    if not below:
        return "none"
    return ", ".join(f"{category}={coverage.category_percentages[category]:.1f}%" for category in below)


def categories_below_floor(coverage: Coverage) -> dict[str, float]:
    return {
        category: percentage
        for category, percentage in coverage.category_percentages.items()
        if percentage < CATEGORY_COVERAGE_FLOOR
    }


def finding_to_dict(finding: Finding) -> dict[str, str]:
    return {
        "group": finding.group,
        "severity": finding.severity,
        "code": finding.code,
        "path": finding.path,
        "evidence": finding.evidence,
        "rule": finding.rule,
        "claude_impact": finding.claude_impact,
        "codex_impact": finding.codex_impact,
        "action": finding.action,
        "verify": finding.verify,
    }


def rule_to_dict(rule: Rule) -> dict[str, object]:
    return {
        "id": rule.id,
        "category": rule.category,
        "severity": rule.severity,
        "standard_anchor": rule.standard_anchor,
        "detector_type": rule.detector_type,
        "weight": rule.weight,
        "fixture_cases": list(rule.fixture_cases),
        "remediation": rule.remediation,
    }


def coverage_to_dict(coverage: Coverage) -> dict[str, object]:
    return {
        "weight_policy": "fixed by severity; catalog entries cannot tune weights",
        "severity_weights": SEVERITY_WEIGHTS,
        "category_floor": CATEGORY_COVERAGE_FLOOR,
        "deterministic_weight": coverage.deterministic_weight,
        "heuristic_weight": coverage.heuristic_weight,
        "manual_prompt_weight": coverage.manual_prompt_weight,
        "uncovered_weight": coverage.uncovered_weight,
        "total_weight": coverage.total_weight,
        "covered_weight": coverage.covered_weight,
        "weighted_percentage": coverage.weighted_percentage,
        "category_percentages": coverage.category_percentages,
        "categories_below_floor": categories_below_floor(coverage),
    }


def replacement_calibration_to_dict(calibration: ReplacementCalibration) -> dict[str, object]:
    return {
        "ledger_path": calibration.ledger_path,
        "case_count": calibration.case_count,
        "gold_finding_count": calibration.gold_finding_count,
        "automated_caught_count": calibration.automated_caught_count,
        "manual_only_finding_count": calibration.manual_only_finding_count,
        "automated_recall_percentage": calibration.automated_recall_percentage,
        "minimum_cases": calibration.minimum_cases,
        "minimum_recall_percentage": calibration.minimum_recall_percentage,
        "passes": calibration.passes,
    }


def emit_group(group: str, findings: list[Finding]) -> str:
    lines = [f"## {group}", ""]
    group_findings = [finding for finding in findings if finding.group == group]
    if not group_findings:
        lines.extend(["No advisory findings.", ""])
        return "\n".join(lines)

    for index, finding in enumerate(group_findings, start=1):
        lines.extend(
            [
                f"### {index}. {finding.code} ({finding.severity})",
                "",
                f"- Path: `{finding.path}`",
                f"- Evidence: {finding.evidence}",
                f"- Violated rule: {finding.rule}",
                f"- Claude impact: {finding.claude_impact}",
                f"- Codex impact: {finding.codex_impact}",
                f"- Next action: {finding.action}",
                f"- Verify/rerun: `{finding.verify}`",
                "",
            ]
        )
    return "\n".join(lines)


def owner(path: str) -> str:
    for pattern in (
        r"^\.claude/skills/[^/]+",
        r"^souroldgeezer-[^/]+/skills/[^/]+",
        r"^souroldgeezer-[^/]+/\.codex-plugin/plugin\.json",
        r"^souroldgeezer-[^/]+/\.claude-plugin/plugin\.json",
    ):
        match = re.match(pattern, path)
        if match:
            return match.group(0)
    return path


def emit_grouped_targets(findings: list[Finding]) -> str:
    lines = ["## Grouped Targets", ""]
    if not findings:
        lines.extend(["No target groups.", ""])
        return "\n".join(lines)

    groups: dict[str, dict[str, object]] = {}
    for finding in findings:
        target = owner(finding.path)
        entry = groups.setdefault(target, {"count": 0, "codes": [], "action": finding.action})
        entry["count"] = int(entry["count"]) + 1
        codes = entry["codes"]
        assert isinstance(codes, list)
        if finding.code not in codes:
            codes.append(finding.code)

    for target in sorted(groups):
        entry = groups[target]
        codes = ", ".join(entry["codes"])  # type: ignore[arg-type]
        lines.append(
            f"- `{target}`: {entry['count']} finding(s); codes: {codes}; first action: {entry['action']}"
        )
    lines.append("")
    return "\n".join(lines)


NEXT_PRIORITY = {
    "SAC-RUNTIME-PLUGIN-JSON": 1,
    "SAC-RUNTIME-DEFAULT-PROMPTS": 2,
    "SAC-RUNTIME-MISSING-OPENAI": 3,
    "SAC-TRIGGER-DESC-LENGTH": 4,
    "SAC-TRIGGER-AGGRESSIVE": 5,
    "SAC-TRIGGER-MISSING-CONTEXT": 6,
    "SAC-REF-BROKEN-LINK": 7,
    "SAC-SCRIPT-UNADVERTISED": 8,
    "SAC-WORKFLOW-OUTPUT": 9,
}


def emit_next_iteration(findings: list[Finding]) -> str:
    lines = ["## Next Iteration", ""]
    if not findings:
        lines.extend(
            [
                "No current advisory findings. Re-run the report after skill, metadata, support-file,",
                "or repo-guidance changes.",
                "",
                "- Verify/rerun: `scripts/skill-architecture-report.sh .`",
            ]
        )
        return "\n".join(lines)

    candidates = sorted(
        findings,
        key=lambda finding: (
            NEXT_PRIORITY.get(finding.code, 50),
            owner(finding.path),
            finding.code,
            finding.path,
        ),
    )
    seen: set[str] = set()
    selected: list[Finding] = []
    for finding in candidates:
        target = owner(finding.path)
        if target in seen:
            continue
        seen.add(target)
        selected.append(finding)
        if len(selected) == 5:
            break

    for index, finding in enumerate(selected, start=1):
        lines.append(
            f"{index}. {finding.code} in `{finding.path}`: {finding.action} Verify with `{finding.verify}`."
        )
    lines.extend(["", "Exact rerun command: `scripts/skill-architecture-report.sh .`"])
    return "\n".join(lines)


def render_report(
    repo_root: Path,
    findings: list[Finding],
    rules: tuple[Rule, ...] | None = None,
    calibration: ReplacementCalibration | None = None,
) -> str:
    rules = rules or build_rule_catalog()
    coverage = calculate_coverage(rules)
    calibration = calibration or calculate_replacement_calibration(repo_root)
    lines = [
        "# Skill Architecture Craft Report",
        "",
        "## Summary",
        "",
        f"- Repo: `{repo_root}`",
        (
            "- Findings: "
            f"{len(findings)} total "
            f"({count_severity(findings, 'blocker')} blocker, "
            f"{count_severity(findings, 'high')} high, "
            f"{count_severity(findings, 'medium')} medium, "
            f"{count_severity(findings, 'low')} low)"
        ),
        "- Exit policy: findings exit 0 unless `--strict` is set; rerun after each improvement.",
        "",
        "## Standard Coverage",
        "",
        "- Weight policy: `fixed by severity; catalog entries cannot tune weights`",
        "- Severity weights: `blocker=13, high=8, medium=5, low=3`",
        f"- Category floor: `{CATEGORY_COVERAGE_FLOOR:.1f}% minimum per report group`",
        f"- Deterministic: `{format_weight(coverage.deterministic_weight)}` weighted points",
        f"- Heuristic: `{format_weight(coverage.heuristic_weight)}` weighted points",
        f"- Manual prompt: `{format_weight(coverage.manual_prompt_weight)}` weighted points",
        f"- Uncovered: `{format_weight(coverage.uncovered_weight)}` weighted points",
        f"- Total weighted coverage: `{coverage.weighted_percentage:.1f}%`",
        f"- Category coverage: `{format_category_percentages(coverage)}`",
        f"- Categories below floor: `{format_categories_below_floor(coverage)}`",
        "",
        "## Replacement Calibration",
        "",
        f"- Ledger: `{calibration.ledger_path}`",
        f"- Ledger cases: `{calibration.case_count}` (minimum `{calibration.minimum_cases}`)",
        f"- Skill-only gold findings: `{calibration.gold_finding_count}`",
        f"- Tool-detected gold findings: `{calibration.automated_caught_count}`",
        f"- Manual-only / missed findings: `{calibration.manual_only_finding_count}`",
        f"- Automated replacement recall: `{calibration.automated_recall_percentage:.1f}%` "
        f"(minimum `{calibration.minimum_recall_percentage:.1f}%`)",
        f"- Replacement calibration passes: `{'yes' if calibration.passes else 'no'}`",
        "",
    ]
    for group in REPORT_GROUPS:
        lines.append(emit_group(group, findings))
    lines.append(emit_grouped_targets(findings))
    lines.append(emit_next_iteration(findings))
    return "\n".join(lines).rstrip() + "\n"


def render_json(
    repo_root: Path,
    findings: list[Finding],
    rules: tuple[Rule, ...] | None = None,
    calibration: ReplacementCalibration | None = None,
) -> str:
    rules = rules or build_rule_catalog()
    coverage = calculate_coverage(rules)
    calibration = calibration or calculate_replacement_calibration(repo_root)
    payload = {
        "scope": {
            "repo": str(repo_root),
            "command": "scripts/skill-architecture-report.sh .",
        },
        "summary": {
            "finding_count": len(findings),
            "severity_counts": {
                "blocker": count_severity(findings, "blocker"),
                "high": count_severity(findings, "high"),
                "medium": count_severity(findings, "medium"),
                "low": count_severity(findings, "low"),
            },
        },
        "coverage": coverage_to_dict(coverage),
        "replacement_calibration": replacement_calibration_to_dict(calibration),
        "findings": [finding_to_dict(finding) for finding in findings],
        "rules": [rule_to_dict(rule) for rule in rules],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def run(repo_root: Path) -> str:
    return render_report(repo_root, collect_findings(repo_root))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("repo_root", nargs="?")
    parser.add_argument("extra", nargs="*")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        raise SystemExit(0)
    if args.extra:
        print(usage(), end="", file=sys.stderr)
        print("Error: expected zero or one repo root argument", file=sys.stderr)
        raise SystemExit(2)
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = Path(args.repo_root or ".")
    if not repo_root.is_dir() or not os.access(repo_root, os.R_OK):
        print(f"Error: repo root is not a readable directory: {repo_root}", file=sys.stderr)
        return 2
    resolved_repo_root = repo_root.resolve()
    findings = collect_findings(resolved_repo_root)
    rules = build_rule_catalog()
    coverage = calculate_coverage(rules)
    calibration = calculate_replacement_calibration(resolved_repo_root)
    if args.format == "json":
        print(render_json(resolved_repo_root, findings, rules, calibration), end="")
    else:
        print(render_report(resolved_repo_root, findings, rules, calibration), end="")
    if args.strict and (findings or categories_below_floor(coverage) or not calibration.passes):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
