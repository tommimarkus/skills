"""Pre-run workflow budget and orchestrator-survivability analyzer."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from leanaudit.context_trace import (
    UsageEvent,
    normalize_trace_records,
    read_trace_file,
    summarize_trace,
)
from leanaudit.discovery import repo_paths
from leanaudit.hook_cost import (
    analyze_hook_registrations,
    is_hook_config_path,
    read_hook_fixture_file,
)
from leanaudit.load_cost import estimate_tokens

__all__ = [
    "Scenario",
    "TokenRange",
    "UsageEvent",
    "analyze_sources",
    "analyze_hook_registrations",
    "forecast_scenario",
    "is_hook_config_path",
    "load_scenario_data",
    "main",
    "normalize_trace_records",
    "read_trace_file",
    "read_hook_fixture_file",
    "read_workflow_sources",
    "summarize_trace",
]


@dataclass(frozen=True)
class TokenRange:
    """Low, expected, and high values for a non-negative token quantity."""

    low: int
    expected: int
    high: int

    def as_dict(self) -> dict[str, int]:
        return {"low": self.low, "expected": self.expected, "high": self.high}

    def lane(self, name: str) -> int:
        return int(getattr(self, name))


@dataclass(frozen=True)
class Scenario:
    """Validated pre-run budget scenario."""

    scenario_id: str
    context_window: int | None
    verification_reserve: int
    base_tokens: TokenRange
    stages: tuple[dict[str, Any], ...]
    calibration_tolerance: float | None


# Detector regex catalogs intentionally repeat declarative name/pattern records.
# lean-audit:dup-intentional:begin
_PHASE_PATTERNS = (
    ("preflight", re.compile(r"\bpre[ -]?flight\b", re.I)),
    ("discovery", re.compile(r"\bdiscover(?:y|ing|ed)?\b", re.I)),
    ("plan", re.compile(r"\bplan(?:ning|ned)?\b", re.I)),
    ("build", re.compile(r"\b(?:build|implement)(?:ing|ed|ation)?\b", re.I)),
    ("verify", re.compile(r"\b(?:verify|verification|test(?:ing|s|ed)?)\b", re.I)),
)
# lean-audit:dup-intentional:end
_DELEGATE_RE = re.compile(
    r"\b(?:delegate|dispatch|subagent|worker|agent tool|parallel agents?)\b", re.I
)
_LOOP_RE = re.compile(r"\b(?:iterat(?:e|ion|ive)|loop|repeat|retry|re-?run)\b", re.I)
_RETRY_RE = re.compile(r"\b(?:retry|retries|attempt again|until (?:tests? )?pass)\b", re.I)
_BOUNDED_RE = re.compile(
    r"\b(?:(?:at most|up to|no more than|limit(?:ed)? to|maximum of|max)\s+\d+|"
    r"\d+\s+(?:iterations?|retries|attempts?|passes|rounds|times))\b",
    re.I,
)
_CHECKPOINT_RE = re.compile(
    r"\b(?:checkpoint|compact|summari[sz]e|fresh context|reset context|discard raw)\b",
    re.I,
)
_TERMINAL_SUCCESS_RE = re.compile(
    r"\b(?:stop successfully (?:when|on)|terminal success|success (?:state|outcome)|"
    r"stop when (?:tests?|verification|checks?) pass|stop on pass)\b",
    re.I,
)
_TERMINAL_FAILURE_RE = re.compile(
    r"\b(?:terminal failure|failure (?:state|outcome|summary)|final failure|"
    r"attempts? (?:are )?exhausted|failed attempts?)\b",
    re.I,
)
_ESCALATION_RE = re.compile(
    r"\b(?:escalat(?:e|es|ed|ion)|human review|report (?:the )?blocker|"
    r"ask (?:the )?user|hand (?:off|back) to)\b",
    re.I,
)
_NO_PROGRESS_RE = re.compile(
    r"\b(?:no (?:(?:new|meaningful) )?(?:progress|evidence|hypothesis|diagnostic|change)|"
    r"unchanged (?:failure|error|evidence|hypothesis|result|signature|(?:failing-check )?set)|"
    r"same (?:failure|failing-check|error|evidence|hypothesis|result|signature|set)|"
    r"failure signature (?:is|remains) unchanged|"
    r"(?:failing-check )?set (?:is|remains) unchanged|"
    r"fail(?:ure|ing-check)s? (?:stop|stops|fail|fails) (?:shrinking|decreasing|changing)|"
    r"state (?:cycle|repeats)|oscillat(?:e|es|ion))\b",
    re.I,
)
_STOP_RE = re.compile(r"\b(?:stop|halt|exit|escalat(?:e|es|ed|ion)|replan)\b", re.I)
_CHECKPOINT_FIELDS = (
    ("objective-or-scope", re.compile(r"\b(?:objective|scope)\b", re.I)),
    ("approved-decisions", re.compile(r"\bapproved (?:plan|decisions?)\b", re.I)),
    ("progress", re.compile(r"\bprogress\b", re.I)),
    (
        "blockers-or-open-choices",
        re.compile(r"\b(?:blockers?|open (?:choices?|questions?))\b", re.I),
    ),
    (
        "obligation-or-evidence-pointers",
        re.compile(
            r"\b(?:obligation|evidence|artifact)s? (?:IDs?|paths?|pointers?|references?)\b",
            re.I,
        ),
    ),
    ("next-decision", re.compile(r"\bnext (?:decision|action)\b", re.I)),
    ("bounded", re.compile(r"\b(?:bounded|size cap|token cap|line cap)\b", re.I)),
    ("summary-contract", re.compile(r"\b(?:summary|schema|return contract)\b", re.I)),
)
_ENUMERATED_SWEEP_RE = re.compile(
    r"\b(?:enumerated|fixed) (?:matrix|sweep|list|set)\b|"
    r"\b(?:matrix|sweep) of \d+ (?:cases?|options?|configurations?|parameters?)\b",
    re.I,
)
_BROAD_BUILD_RE = re.compile(
    r"\b(?:proceed with|begin|start|launch) (?:a )?(?:broad|full|whole|repository-wide) "
    r"(?:implementation|build)\b|"
    r"\bimplement (?:the )?(?:entire|whole|full) (?:repository|project|system|scope)\b",
    re.I,
)
_TBD_SHAPING_RE = re.compile(
    r"\b(?:implementation )?(?:scope|acceptance(?: criteria| checks)?)\b.{0,100}"
    r"\b(?:TBD|to be determined|unknown|unresolved|open)\b",
    re.I | re.S,
)
# Completeness catalogs intentionally share one compiled-field tuple shape.
# lean-audit:dup-intentional:begin
_RESOLVED_PACKET_FIELDS = (
    re.compile(r"\bmust\b", re.I),
    re.compile(r"\bout of scope\b", re.I),
    re.compile(r"\bunknowns?\b", re.I),
    re.compile(r"\bowner\b", re.I),
    re.compile(r"\bdefault\b", re.I),
    re.compile(r"\bacceptance (?:check|criterion|criteria)\b", re.I),
)
# lean-audit:dup-intentional:end
_DISCOVERY_SPIKE_FIELDS = (
    re.compile(r"\b(?:bounded(?: \d+[- ]pass)?|\d+[- ]pass) discovery spike\b", re.I),
    re.compile(r"\bquestion\b", re.I),
    re.compile(r"\bowner\b", re.I),
    re.compile(r"\bexit (?:criterion|condition)\b", re.I),
)
_HANDOFF_RE = re.compile(
    r"\b(?:bounded|compact|summary|schema|return shape|evidence path|artifact path|pointer)\b",
    re.I,
)
_RAW_RESULT_RE = re.compile(
    r"\b(?:full|raw|complete|entire|all)\s+(?:test )?(?:logs?|output|stdout|stderr|"
    r"stack traces?|diffs?|findings|tool results?)\b|\bstdout and stderr\b",
    re.I,
)
_OUT_OF_BAND_RE = re.compile(
    r"\b(?:out[- ]of[- ]band|external (?:file|log|telemetry)|telemetry sink|"
    r"write (?:the )?(?:full|raw|complete) .*? to (?:an? )?(?:file|artifact))\b",
    re.I,
)
_REDISCOVERY_RE = re.compile(
    r"\b(?:re-?run|repeat|redo) discovery\b|\bdiscovery from scratch every\b", re.I
)
_CONTROL_PLANE_RE = re.compile(r"\b(?:orchestrator|coordinator|control plane|lead agent)\b", re.I)
_ENTRY_RE = re.compile(
    r"(?:^|/)(?:SKILL\.md|AGENTS\.md|CLAUDE\.md)$|"
    r"(?:^|/)(?:agents|commands)/.*\.md$"
)
_WORKFLOW_PROCEDURE_RE = re.compile(
    r"(?:^|/)references/procedures/[^/]*"
    r"(?:workflow|orchestrat|coordinat|process|viabil|finishab)[^/]*\.md$",
    re.I,
)
_ORCHESTRATOR_THRESHOLD = 55
_LANES = ("low", "expected", "high")
_WORKFLOW_INTENTIONAL_RE = re.compile(
    r"^[ ]{0,3}<!-- lean-audit:workflow-intentional — [^<>\r\n]*\S -->[ \t]*$"
)
_FENCE_OPEN_RE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})")


def _line(text: str, match: re.Match[str] | None) -> int:
    return 1 if match is None else text.count("\n", 0, match.start()) + 1


def _local_bounds(
    text: str, anchor: re.Match[str] | None, before: int, after: int
) -> tuple[int, int] | None:
    if anchor is None:
        return None
    return max(0, anchor.start() - before), min(len(text), anchor.end() + after)


def _nearby(
    pattern: re.Pattern[str], text: str, anchor: re.Match[str] | None
) -> re.Match[str] | None:
    """Return a match within the anchor's local workflow paragraph/window."""
    bounds = _local_bounds(text, anchor, 300, 500)
    if bounds is None:
        return None
    return pattern.search(text, *bounds)


def _workflow_surface(path: str) -> bool:
    return _ENTRY_RE.search(path) is not None or _WORKFLOW_PROCEDURE_RE.search(path) is not None


def _has_workflow_intentional(text: str) -> bool:
    """Recognize the exact HTML marker only outside Markdown fenced code."""
    fence_char: str | None = None
    fence_width = 0
    for line in text.splitlines():
        if fence_char is not None:
            close_re = re.compile(rf"^[ ]{{0,3}}{re.escape(fence_char)}{{{fence_width},}}[ \t]*$")
            if close_re.fullmatch(line):
                fence_char = None
                fence_width = 0
            continue
        fence = _FENCE_OPEN_RE.match(line)
        if fence is not None:
            fence_char = fence.group(1)[0]
            fence_width = len(fence.group(1))
            continue
        if _WORKFLOW_INTENTIONAL_RE.fullmatch(line):
            return True
    return False


def _finding(
    code: str,
    severity: str,
    path: str,
    line: int,
    evidence: str,
    cause: str,
    consequence: str,
    recommendation: str,
    *,
    source: str = "static forecast",
    confidence: str = "medium",
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "path": path,
        "line": line,
        "criteria": code,
        "condition": evidence,
        "cause": cause,
        "consequence": consequence,
        "recommendation": recommendation,
        "source": source,
        "confidence": confidence,
    }


def _source_finding(
    code: str,
    path: str,
    text: str,
    match: re.Match[str],
    cause: str,
    consequence: str,
    recommendation: str,
    *,
    confidence: str = "medium",
) -> dict[str, Any]:
    return _finding(
        code,
        "warn",
        path,
        _line(text, match),
        match.group(0),
        cause,
        consequence,
        recommendation,
        confidence=confidence,
    )


def _phases(text: str) -> tuple[list[str], dict[str, int], tuple[int, int] | None]:
    """Return the densest local phase cluster, not whole-file vocabulary."""
    # Phase discovery intentionally performs a collect pass before window ranking.
    # lean-audit:dup-intentional:begin
    hits: list[tuple[int, str, re.Match[str]]] = []
    for name, pattern in _PHASE_PATTERNS:
        hits.extend((match.start(), name, match) for match in pattern.finditer(text))
    hits.sort()
    # lean-audit:dup-intentional:end
    if not hits:
        return [], {}, None

    best: list[tuple[int, str, re.Match[str]]] = []
    for anchor, _, _ in hits:
        window = [hit for hit in hits if anchor <= hit[0] <= anchor + 1_200]
        first_by_name: dict[str, tuple[int, str, re.Match[str]]] = {}
        for hit in window:
            first_by_name.setdefault(hit[1], hit)
        candidate = sorted(first_by_name.values())
        if len(candidate) > len(best) or (
            len(candidate) == len(best)
            and candidate[-1][0] - candidate[0][0] < best[-1][0] - best[0][0]
        ):
            best = candidate

    phases = [name for _, name, _ in best]
    lines = {name: _line(text, match) for _, name, match in best}
    region = (max(0, best[0][0] - 300), min(len(text), best[-1][2].end() + 600))
    return phases, lines, region


def _region_search(
    pattern: re.Pattern[str], text: str, region: tuple[int, int] | None
) -> re.Match[str] | None:
    if region is None:
        return None
    return pattern.search(text, region[0], region[1])


def _window(text: str, anchor: re.Match[str] | None) -> str:
    bounds = _local_bounds(text, anchor, 300, 700)
    if bounds is None:
        return ""
    return text[slice(*bounds)]


def _has_all(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return all(pattern.search(text) is not None for pattern in patterns)


def _checkpoint_missing_fields(text: str, checkpoint: re.Match[str] | None) -> list[str]:
    region = _window(text, checkpoint)
    return [name for name, pattern in _CHECKPOINT_FIELDS if pattern.search(region) is None]


def _has_no_progress_exit(text: str, anchor: re.Match[str] | None) -> bool:
    region = _window(text, anchor)
    no_progress = _NO_PROGRESS_RE.search(region)
    return no_progress is not None and _nearby(_STOP_RE, region, no_progress) is not None


def _schema_inventory(files: dict[str, str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            schema = value.get("inputSchema", value.get("input_schema"))
            if isinstance(schema, dict):
                surface = {
                    "name": value.get("name", "unknown"),
                    "description": value.get("description", ""),
                    "schema": schema,
                }
                rows.append(
                    {
                        "path": path,
                        "name": str(surface["name"]),
                        "proxy_tokens": estimate_tokens(
                            json.dumps(surface, sort_keys=True, separators=(",", ":"))
                        ),
                    }
                )
            for nested in value.values():
                walk(nested, path)
        elif isinstance(value, list):
            for nested in value:
                walk(nested, path)

    for path, text in files.items():
        if not path.endswith(".json"):
            continue
        try:
            walk(json.loads(text), path)
        except json.JSONDecodeError:
            continue
    return {
        "tools": sorted(rows, key=lambda row: (row["path"], row["name"])),
        "proxy_tokens": sum(int(row["proxy_tokens"]) for row in rows),
        "evidence": "local JSON inputSchema/input_schema definitions only",
    }


def analyze_sources(
    files: dict[str, str],
    *,
    hook_fixture_metadata: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Find likely persistent orchestrators and source-readable token risks."""
    artifacts: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    intentional_workflow_paths: list[str] = []
    for path, text in sorted(files.items()):
        if not path.endswith(".md") or not _workflow_surface(path):
            continue
        if _has_workflow_intentional(text):
            intentional_workflow_paths.append(path)
            continue
        phases, phase_lines, workflow_region = _phases(text)
        delegate = _region_search(_DELEGATE_RE, text, workflow_region)
        loop = _region_search(_LOOP_RE, text, workflow_region)
        retry = _region_search(_RETRY_RE, text, workflow_region)
        control_plane = _region_search(_CONTROL_PLANE_RE, text, workflow_region)
        bounded = _nearby(_BOUNDED_RE, text, loop or retry)
        checkpoint = _nearby(_CHECKPOINT_RE, text, loop or retry)
        checkpoint_missing = _checkpoint_missing_fields(text, checkpoint)
        terminal_success = _nearby(_TERMINAL_SUCCESS_RE, text, retry or loop)
        terminal_failure = _nearby(_TERMINAL_FAILURE_RE, text, retry or loop)
        escalation = _nearby(_ESCALATION_RE, text, retry or loop)
        terminal_contract = all(
            match is not None for match in (bounded, terminal_success, terminal_failure, escalation)
        )
        no_progress_exit = _has_no_progress_exit(text, retry or loop)
        workflow_text = "" if workflow_region is None else text[slice(*workflow_region)]
        enumerated_sweep = _ENUMERATED_SWEEP_RE.search(workflow_text)
        effective_loop = None if enumerated_sweep is not None else loop
        effective_retry = None if enumerated_sweep is not None else retry
        broad_build = _BROAD_BUILD_RE.search(workflow_text)
        deferred_shaping = _TBD_SHAPING_RE.search(workflow_text)
        resolved_packet = _has_all(workflow_text, _RESOLVED_PACKET_FIELDS)
        discovery_spike = _has_all(workflow_text, _DISCOVERY_SPIKE_FIELDS)
        handoff = _nearby(_HANDOFF_RE, text, delegate)
        raw_result = _nearby(_RAW_RESULT_RE, text, delegate)
        out_of_band = _nearby(_OUT_OF_BAND_RE, text, raw_result)
        rediscovery = _region_search(_REDISCOVERY_RE, text, workflow_region)
        entry_bonus = 5 if _ENTRY_RE.search(path) else 0
        score = min(
            100,
            len(phases) * 8
            + (15 if delegate else 0)
            + (10 if effective_loop else 0)
            + (5 if effective_retry else 0)
            + (15 if control_plane else 0)
            + (15 if broad_build is not None and deferred_shaping is not None else 0)
            + entry_bonus,
        )
        artifact = {
            "path": path,
            "proxy_tokens": estimate_tokens(text),
            "phases": phases,
            "phase_lines": phase_lines,
            "score": score,
            "signals": {
                "delegation": delegate is not None,
                "loop": loop is not None,
                "retry": retry is not None,
                "effective_loop": effective_loop is not None,
                "effective_retry": effective_retry is not None,
                "named_control_plane": control_plane is not None,
                "bounded": bounded is not None,
                "checkpoint": checkpoint is not None,
                "checkpoint_declared": checkpoint is not None,
                "checkpoint_complete": checkpoint is not None and not checkpoint_missing,
                "checkpoint_missing_fields": checkpoint_missing,
                "terminal_success": terminal_success is not None,
                "terminal_failure": terminal_failure is not None,
                "escalation": escalation is not None,
                "no_progress_exit": no_progress_exit,
                "deferred_implementation_scope": deferred_shaping is not None,
                "bounded_handoff": handoff is not None,
                "raw_model_result": raw_result is not None and out_of_band is None,
                "out_of_band_logging": out_of_band is not None,
                "rediscovery": rediscovery is not None,
            },
        }
        if len(phases) < 2 and not (control_plane is not None and effective_loop is not None):
            continue
        artifacts.append(artifact)
        if score < _ORCHESTRATOR_THRESHOLD:
            continue
        if raw_result is not None and out_of_band is None:
            findings.append(
                _source_finding(
                    "LA-ORCH-1",
                    path,
                    text,
                    raw_result,
                    "bulk worker/tool output is returned to a persistent coordinator",
                    "the control plane retains detail and loses capacity for later decisions",
                    "keep raw output out of band and return a bounded summary plus evidence path",
                    confidence="high",
                )
            )
        if rediscovery is not None:
            findings.append(
                _source_finding(
                    "LA-ORCH-2",
                    path,
                    text,
                    rediscovery,
                    "discovery is repeated instead of reused across iterations",
                    "unchanged inventory repeatedly consumes coordinator context and run tokens",
                    "persist a discovery index and refresh only invalidated evidence",
                )
            )
        unbounded_handoff = handoff is None or (raw_result is not None and out_of_band is None)
        if delegate is not None and unbounded_handoff:
            findings.append(
                _source_finding(
                    "LA-ORCH-3",
                    path,
                    text,
                    delegate,
                    "delegated work lacks an effective bounded return contract",
                    "worker fan-out can flood the orchestrator with overlapping detail",
                    "require result, evidence paths, blocker, and next decision under a size cap",
                )
            )
        # Static finding emitters intentionally preserve code-specific local branches.
        # lean-audit:dup-intentional:begin
        if effective_loop is not None and bounded is None:
            findings.append(
                _source_finding(
                    "LA-RUN-1",
                    path,
                    text,
                    effective_loop,
                    "the iterative path has no finite attempt bound",
                    "pre-run total and peak context cannot be bounded",
                    "declare best/expected/upper iterations and a terminal outcome",
                    confidence="high",
                )
            )
        if effective_retry is not None and not terminal_contract:
            findings.append(
                _source_finding(
                    "LA-RUN-4",
                    path,
                    text,
                    effective_retry,
                    "retry ownership lacks a complete count, success, failure, "
                    "and escalation contract",
                    "repeated failures consume context without producing verification evidence",
                    "set a retry count plus terminal success, failure-summary, "
                    "and escalation outcomes",
                    confidence="high",
                )
            )
        # lean-audit:dup-intentional:end
        if (
            effective_loop is not None
            and bounded is not None
            and terminal_contract
            and not no_progress_exit
            and enumerated_sweep is None
        ):
            findings.append(
                _source_finding(
                    "LA-RUN-6",
                    path,
                    text,
                    effective_loop,
                    "the bounded repair/verification loop has no unchanged-delta exit",
                    "an attempt fence can still spend every retry without objective progress",
                    "stop or escalate when failures, evidence, and hypothesis stop changing",
                    confidence="high",
                )
            )
        if (
            broad_build is not None
            and deferred_shaping is not None
            and not (resolved_packet or discovery_spike)
        ):
            findings.append(
                _source_finding(
                    "LA-RUN-7",
                    path,
                    text,
                    broad_build,
                    "broad implementation starts while scope or acceptance remains "
                    "explicitly unresolved",
                    "the implementer must repeatedly reinterpret obligations during "
                    "expensive build work",
                    "resolve a must/out/unknown packet or run a bounded question-owned "
                    "discovery spike",
                    confidence="high",
                )
            )
        if effective_loop is not None and checkpoint_missing:
            evidence_match = checkpoint or effective_loop
            missing = ", ".join(checkpoint_missing)
            findings.append(
                _source_finding(
                    "LA-ORCH-5",
                    path,
                    text,
                    evidence_match,
                    f"the loop checkpoint is absent or incomplete; missing: {missing}",
                    "the orchestrator accumulates history until coherence and speed degrade",
                    "checkpoint a bounded state contract with decisions, progress, "
                    "obligations, and next action",
                )
            )
    orchestrators = sorted(
        (artifact for artifact in artifacts if artifact["score"] >= _ORCHESTRATOR_THRESHOLD),
        key=lambda artifact: (-int(artifact["score"]), str(artifact["path"])),
    )
    return {
        "artifacts": artifacts,
        "orchestrators": orchestrators,
        "tool_schema_inventory": _schema_inventory(files),
        "hook_cost": analyze_hook_registrations(files, hook_fixture_metadata),
        "findings": findings,
        "intentional_workflow_paths": intentional_workflow_paths,
        "limits": [
            "static workflow prose proves declared structure, not actual host retention",
            "exact finishability requires a scenario with context capacity and stage ranges",
        ],
    }


def read_workflow_sources(root: Path) -> dict[str, str]:
    """Read tracked/unignored workflow surfaces and local JSON tool schemas."""
    root = root.resolve()
    in_repo = repo_paths(root)
    paths: list[Path]
    if in_repo is None:
        paths = [path for path in root.rglob("*") if path.is_file()]
    else:
        paths = [root / rel for rel in sorted(in_repo)]
    files: dict[str, str] = {}
    for path in paths:
        if path.suffix not in {".md", ".json"} or not path.is_file():
            continue
        try:
            if path.stat().st_size > 1_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        if (
            (path.suffix == ".md" and _workflow_surface(rel))
            or is_hook_config_path(rel)
            or "inputSchema" in text
            or "input_schema" in text
        ):
            files[rel] = text
    return files


def _range(value: Any, field: str, *, minimum: int = 0) -> TokenRange:
    if isinstance(value, bool):
        raise ValueError(f"{field}: expected a non-negative integer or range")
    if isinstance(value, int):
        result = TokenRange(value, value, value)
    elif isinstance(value, dict):
        try:
            result = TokenRange(int(value["low"]), int(value["expected"]), int(value["high"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{field}: range needs integer low/expected/high") from exc
    else:
        raise ValueError(f"{field}: expected a non-negative integer or range")
    if result.low < minimum or not result.low <= result.expected <= result.high:
        raise ValueError(f"{field}: require {minimum} <= low <= expected <= high")
    return result


def _optional_range(mapping: dict[str, Any], field: str, default: int = 0) -> TokenRange:
    return _range(mapping.get(field, default), field)


def load_scenario_data(data: dict[str, Any]) -> Scenario:
    """Validate and normalize a JSON scenario. Never invent a context capacity."""
    scenario_id = str(data.get("id", "scenario"))
    context_value = data.get("context_window")
    context_window: int | None
    if context_value is None:
        context_window = None
    elif (
        isinstance(context_value, int) and not isinstance(context_value, bool) and context_value > 0
    ):
        context_window = context_value
    else:
        raise ValueError("context_window: expected a positive integer")
    reserve = data.get("verification_reserve", 0)
    if not isinstance(reserve, int) or isinstance(reserve, bool) or reserve < 0:
        raise ValueError("verification_reserve: expected a non-negative integer")
    orchestrator = data.get("orchestrator", {})
    if not isinstance(orchestrator, dict):
        raise ValueError("orchestrator: expected an object")
    stages = data.get("stages")
    if (
        not isinstance(stages, list)
        or not stages
        or not all(isinstance(row, dict) for row in stages)
    ):
        raise ValueError("stages: expected a non-empty list of objects")
    ids = [str(stage.get("id", "")) for stage in stages]
    if any(not stage_id for stage_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("stages: every stage needs a unique non-empty id")
    for index, stage in enumerate(stages):
        prefix = f"stages[{index}]"
        _range(stage.get("iterations", 1), f"{prefix}.iterations", minimum=1)
        for field in (
            "prompt_tokens",
            "tool_schema_tokens",
            "hook_tokens",
            "tool_result_tokens",
            "out_of_band_result_tokens",
            "output_tokens",
            "fixed_output_tokens",
            "per_item_output_tokens",
            "item_count",
            "retained_tokens",
            "compaction_target",
        ):
            if field in stage:
                _range(stage[field], f"{prefix}.{field}")
        workers = stage.get("workers")
        if workers is not None:
            if not isinstance(workers, dict):
                raise ValueError(f"{prefix}.workers: expected an object")
            for field in (
                "count",
                "shared_prefix_tokens",
                "local_tokens",
                "tool_result_tokens",
                "out_of_band_result_tokens",
                "output_tokens",
                "handoff_tokens",
            ):
                if field in workers:
                    _range(
                        workers[field],
                        f"{prefix}.workers.{field}",
                        minimum=1 if field == "count" else 0,
                    )
    tolerance = data.get("calibration_tolerance")
    if tolerance is not None:
        if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or tolerance < 0:
            raise ValueError("calibration_tolerance: expected a non-negative number")
        tolerance = float(tolerance)
    return Scenario(
        scenario_id=scenario_id,
        context_window=context_window,
        verification_reserve=reserve,
        base_tokens=_range(orchestrator.get("base_tokens", 0), "orchestrator.base_tokens"),
        stages=tuple(stages),
        calibration_tolerance=tolerance,
    )


def _stage_lane(stage: dict[str, Any], lane: str) -> dict[str, int]:
    fields = (
        "prompt_tokens",
        "tool_schema_tokens",
        "hook_tokens",
        "tool_result_tokens",
        "out_of_band_result_tokens",
        "output_tokens",
    )
    values = {field: _optional_range(stage, field).lane(lane) for field in fields}
    if "item_count" in stage:
        item_count = _range(stage["item_count"], "item_count").lane(lane)
        fixed_output = _optional_range(stage, "fixed_output_tokens").lane(lane)
        per_item_output = _optional_range(stage, "per_item_output_tokens").lane(lane)
        values["output_tokens"] += fixed_output + per_item_output * item_count
    values["iterations"] = _range(stage.get("iterations", 1), "iterations", minimum=1).lane(lane)
    workers = stage.get("workers")
    if isinstance(workers, dict):
        count = _optional_range(workers, "count", 1).lane(lane)
        shared = _optional_range(workers, "shared_prefix_tokens").lane(lane)
        local = _optional_range(workers, "local_tokens").lane(lane)
        tool = _optional_range(workers, "tool_result_tokens").lane(lane)
        out_of_band = _optional_range(workers, "out_of_band_result_tokens").lane(lane)
        output = _optional_range(workers, "output_tokens").lane(lane)
        handoff = _optional_range(workers, "handoff_tokens").lane(lane)
    else:
        count = shared = local = tool = out_of_band = output = handoff = 0
    values["worker_count"] = count
    values["worker_per_call"] = shared + local + tool + output
    values["worker_out_of_band"] = out_of_band
    values["worker_shared_prefix"] = shared
    values["worker_handoff"] = handoff
    return values


def _simulate_lane(scenario: Scenario, lane: str) -> dict[str, Any]:
    current = scenario.base_tokens.lane(lane)
    total = 0
    repeated_context = 0
    prompt_tax = 0
    schema_tax = 0
    hook_tax = 0
    tool_result_tax = 0
    handoff_tax = 0
    output_tax = 0
    out_of_band_observations = 0
    worker_total = 0
    rows: list[dict[str, Any]] = []
    earliest_overflow: str | None = None
    verification_peak: int | None = None
    for stage in scenario.stages:
        values = _stage_lane(stage, lane)
        peak = current
        stage_total = 0
        stage_worker_total = 0
        handoff_total = values["worker_count"] * values["worker_handoff"]
        worker_call_total = values["worker_count"] * values["worker_per_call"]
        worker_out_of_band = values["worker_count"] * values["worker_out_of_band"]
        for _ in range(values["iterations"]):
            added_input = (
                values["prompt_tokens"]
                + values["tool_schema_tokens"]
                + values["hook_tokens"]
                + values["tool_result_tokens"]
                + handoff_total
            )
            input_tokens = current + added_input
            call_peak = input_tokens + values["output_tokens"]
            peak = max(peak, call_peak)
            call_total = input_tokens + values["output_tokens"] + worker_call_total
            stage_total += call_total
            total += call_total
            repeated_context += current
            prompt_tax += values["prompt_tokens"]
            schema_tax += values["tool_schema_tokens"]
            hook_tax += values["hook_tokens"]
            tool_result_tax += values["tool_result_tokens"]
            handoff_tax += handoff_total
            output_tax += values["output_tokens"]
            out_of_band_observations += values["out_of_band_result_tokens"] + worker_out_of_band
            worker_total += worker_call_total
            stage_worker_total += worker_call_total
            if "retained_tokens" in stage:
                retained = _range(stage["retained_tokens"], "retained_tokens").lane(lane)
            else:
                retained = (
                    values["prompt_tokens"]
                    + values["hook_tokens"]
                    + values["tool_result_tokens"]
                    + handoff_total
                    + values["output_tokens"]
                )
            current += retained
        if "compaction_target" in stage:
            current = _range(stage["compaction_target"], "compaction_target").lane(lane)
        role = str(stage.get("role", "other"))
        capacity = scenario.context_window
        allowed = None
        if capacity is not None:
            allowed = (
                capacity if role == "verify" else max(0, capacity - scenario.verification_reserve)
            )
            if peak > allowed and earliest_overflow is None:
                earliest_overflow = str(stage["id"])
        if role == "verify":
            verification_peak = max(verification_peak or 0, peak)
        rows.append(
            {
                "id": str(stage["id"]),
                "role": role,
                "iterations": values["iterations"],
                "peak_context": peak,
                "context_after": current,
                "total_tokens": stage_total,
                "worker_total_tokens": stage_worker_total,
                "handoff_tokens": handoff_total * values["iterations"],
                "out_of_band_result_tokens": (
                    values["out_of_band_result_tokens"] + worker_out_of_band
                )
                * values["iterations"],
                "allowed_context": allowed,
            }
        )
    reserve_remaining = None
    if scenario.context_window is not None and verification_peak is not None:
        reserve_remaining = scenario.context_window - verification_peak
    return {
        "peak_context": max((row["peak_context"] for row in rows), default=current),
        "context_after": current,
        "total_tokens": total,
        "repeated_context_tokens": repeated_context,
        "prompt_tokens": prompt_tax,
        "tool_schema_tokens": schema_tax,
        "hook_tokens": hook_tax,
        "model_visible_tool_result_tokens": tool_result_tax,
        "handoff_tokens": handoff_tax,
        "output_tokens": output_tax,
        "out_of_band_result_tokens": out_of_band_observations,
        "worker_total_tokens": worker_total,
        "earliest_overflow": earliest_overflow,
        "verification_peak": verification_peak,
        "verification_reserve_remaining": reserve_remaining,
        "stages": rows,
    }


def _range_from_lanes(lanes: dict[str, dict[str, Any]], key: str) -> dict[str, int | None]:
    return {lane: lanes[lane][key] for lane in _LANES}


def forecast_scenario(scenario: Scenario) -> dict[str, Any]:
    """Forecast peak coordinator context and total run usage for three lanes."""
    lanes = {lane: _simulate_lane(scenario, lane) for lane in _LANES}
    limits: list[str] = []
    if scenario.context_window is None:
        verdict = "indeterminate"
        limits.append("context_window is unknown; no capacity or verification-reserve verdict")
    elif lanes["expected"]["earliest_overflow"] is not None:
        verdict = "infeasible"
    elif lanes["high"]["earliest_overflow"] is not None:
        verdict = "at-risk"
    else:
        verdict = "feasible"
    for stage in scenario.stages:
        output_components_declared = any(
            field in stage for field in ("fixed_output_tokens", "per_item_output_tokens")
        )
        if output_components_declared and "item_count" not in stage:
            limits.append(
                f"{stage['id']}: item_count is unknown; fixed/per-item output is excluded "
                "and legacy output_tokens is retained"
            )

    findings: list[dict[str, Any]] = []
    expected_overflow = lanes["expected"]["earliest_overflow"]
    upper_overflow = lanes["high"]["earliest_overflow"]
    if expected_overflow is not None or upper_overflow is not None:
        stage_id = str(expected_overflow or upper_overflow)
        findings.append(
            _finding(
                "LA-RUN-2",
                "block" if expected_overflow is not None else "warn",
                scenario.scenario_id,
                1,
                f"earliest overflow: expected={expected_overflow}, upper={upper_overflow}",
                "retained orchestration context plus stage payload exceeds its usable capacity",
                "the workflow may stop before it can return a complete result",
                f"reduce retained payload before {stage_id} or introduce a "
                "checkpoint/worker boundary",
                source="scenario forecast",
                confidence="high" if expected_overflow is not None else "medium",
            )
        )
    verify_remaining = lanes["expected"]["verification_reserve_remaining"]
    # Forecast finding emitters deliberately retain explicit code-specific evidence.
    # lean-audit:dup-intentional:begin
    if verify_remaining is not None and verify_remaining < 0:
        findings.append(
            _finding(
                "LA-RUN-3",
                "block",
                scenario.scenario_id,
                1,
                f"expected verification headroom {verify_remaining} tokens",
                "earlier stages consume the capacity needed to complete verification",
                "test attempts can stop without producing usable verification evidence",
                "reserve verification capacity and bound model-visible test output before building",
                source="scenario forecast",
                confidence="high",
            )
        )
    # lean-audit:dup-intentional:end
    duplicated_prefix = sum(
        _stage_lane(stage, "expected")["worker_shared_prefix"]
        * max(0, _stage_lane(stage, "expected")["worker_count"] - 1)
        * _stage_lane(stage, "expected")["iterations"]
        for stage in scenario.stages
    )
    if scenario.context_window and duplicated_prefix >= scenario.context_window // 10:
        findings.append(
            _finding(
                "LA-ORCH-6",
                "warn",
                scenario.scenario_id,
                1,
                f"expected duplicated worker prefix: {duplicated_prefix} tokens",
                "parallel workers each receive a large shared prefix",
                "fan-out multiplies input cost before task-local work begins",
                "move stable evidence behind pointers or a shared discovery artifact",
                source="scenario forecast",
            )
        )

    stage_rows = []
    for index, stage in enumerate(scenario.stages):
        row: dict[str, Any] = {"id": str(stage["id"]), "role": str(stage.get("role", "other"))}
        for key in (
            "iterations",
            "peak_context",
            "context_after",
            "total_tokens",
            "worker_total_tokens",
            "handoff_tokens",
            "out_of_band_result_tokens",
            "allowed_context",
        ):
            row[key] = {lane: lanes[lane]["stages"][index][key] for lane in _LANES}
        stage_rows.append(row)
    waterfall_keys = (
        "repeated_context_tokens",
        "prompt_tokens",
        "tool_schema_tokens",
        "hook_tokens",
        "model_visible_tool_result_tokens",
        "handoff_tokens",
        "output_tokens",
        "worker_total_tokens",
        "out_of_band_result_tokens",
    )
    return {
        "scenario": scenario.scenario_id,
        "verdict": verdict,
        "context_window": scenario.context_window,
        "verification_reserve": scenario.verification_reserve,
        "peak_context": _range_from_lanes(lanes, "peak_context"),
        "total_run_tokens": _range_from_lanes(lanes, "total_tokens"),
        "cost_waterfall": {key: _range_from_lanes(lanes, key) for key in waterfall_keys},
        "earliest_expected_overflow": expected_overflow,
        "earliest_upper_overflow": upper_overflow,
        "verification_reserve_remaining": _range_from_lanes(
            lanes, "verification_reserve_remaining"
        ),
        "stages": stage_rows,
        "findings": findings,
        "limits": limits,
    }


def _calibration_finding(
    scenario: Scenario, forecast: dict[str, Any], trace: dict[str, Any]
) -> dict[str, Any] | None:
    if scenario.calibration_tolerance is None:
        return None
    expected = int(forecast["total_run_tokens"]["expected"])
    observed = int(trace["total_tokens"])
    if expected == 0 or observed <= expected * (1 + scenario.calibration_tolerance):
        return None
    return _finding(
        "LA-RUN-5",
        "warn",
        scenario.scenario_id,
        1,
        f"observed {observed} vs expected forecast {expected} tokens",
        "observed host/provider usage exceeds the declared forecast tolerance",
        "future pre-run decisions understate completion risk",
        "attribute the delta, update stage ranges, and retain the prior forecast as evidence",
        source="observed trace calibration",
        confidence="high",
    )


def _text_report(report: dict[str, Any]) -> str:
    lines = ["Lean workflow-cost audit"]
    static = report["static"]
    lines.append(f"orchestrators: {len(static['orchestrators'])}")
    lines.append(f"hook registrations: {len(static['hook_cost']['registrations'])}")
    forecast = report.get("forecast")
    if isinstance(forecast, dict):
        lines.append(f"run verdict: {forecast['verdict']}")
        lines.append(f"earliest expected overflow: {forecast['earliest_expected_overflow']}")
    trace = report.get("trace")
    if isinstance(trace, dict):
        lines.append(f"observed trace tokens: {trace['total_tokens']}")
    findings = report["findings"]
    if findings:
        lines.append("findings:")
        for finding in findings:
            lines.append(
                f"- {finding['code']} [{finding['severity']}] "
                f"{finding['path']}:{finding['line']} — {finding['condition']}"
            )
    else:
        lines.append("findings: none")
    return "\n".join(lines)


# Stable analyzer CLIs intentionally keep their domain-specific parser descriptions local.
# lean-audit:dup-intentional:begin
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pre-run workflow budget and orchestrator-survivability audit"
    )
    # lean-audit:dup-intentional:end
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--scenario", help="JSON stage-budget scenario")
    parser.add_argument("--trace", action="append", default=[], help="JSON/JSONL usage trace")
    parser.add_argument(
        "--hook-fixture",
        action="append",
        default=[],
        help="JSON/JSONL content-free hook fixture metadata",
    )
    parser.add_argument("--context-window", type=int, help="override declared context capacity")
    parser.add_argument(
        "--verification-reserve", type=int, help="override tokens reserved for verification"
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve()
        if not root.is_dir():
            raise ValueError(f"{root}: root must be a directory")
        hook_fixture_metadata: list[dict[str, Any]] = []
        for fixture_path in args.hook_fixture:
            hook_fixture_metadata.extend(read_hook_fixture_file(Path(fixture_path)))
        static = analyze_sources(
            read_workflow_sources(root),
            hook_fixture_metadata=hook_fixture_metadata,
        )
        forecast: dict[str, Any] | None = None
        scenario: Scenario | None = None
        if args.scenario:
            data = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("scenario root must be an object")
            scenario = load_scenario_data(data)
            if args.context_window is not None:
                if args.context_window <= 0:
                    raise ValueError("--context-window must be positive")
                scenario = replace(scenario, context_window=args.context_window)
            if args.verification_reserve is not None:
                if args.verification_reserve < 0:
                    raise ValueError("--verification-reserve must be non-negative")
                scenario = replace(scenario, verification_reserve=args.verification_reserve)
            forecast = forecast_scenario(scenario)
        trace_events: list[UsageEvent] = []
        for trace_path in args.trace:
            trace_events.extend(normalize_trace_records(read_trace_file(Path(trace_path))))
        trace = summarize_trace(trace_events) if args.trace else None
        findings = list(static["findings"])
        if forecast is not None:
            findings.extend(forecast["findings"])
        if scenario is not None and forecast is not None and trace is not None:
            calibration = _calibration_finding(scenario, forecast, trace)
            if calibration is not None:
                findings.append(calibration)
        report = {
            "schema_version": 1,
            "root": str(root),
            "static": static,
            "forecast": forecast,
            "trace": trace,
            "findings": findings,
            "content_policy": "metadata-only",
        }
        print(json.dumps(report, indent=2) if args.format == "json" else _text_report(report))
        return 1 if any(finding["severity"] == "block" for finding in findings) else 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"workflow-cost: {exc}", file=sys.stderr)
        return 2
