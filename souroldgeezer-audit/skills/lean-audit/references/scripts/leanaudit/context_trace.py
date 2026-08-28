"""Normalize provider and host token-usage traces without retaining content."""

from __future__ import annotations

# Import/export scaffolding intentionally follows sibling metadata leaves.
# lean-audit:dup-intentional:begin
import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from leanaudit.json_rows import read_json_rows

__all__ = [
    "UsageEvent",
    "normalize_trace_records",
    "read_trace_file",
    "summarize_trace",
    "summarize_trace_records",
]
# lean-audit:dup-intentional:end


_CODEX_USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
_COLLABORATION_CALLS = (
    "spawn_agent",
    "send_message",
    "followup_task",
    "wait_agent",
    "list_agents",
    "interrupt_agent",
)
_TOOL_OUTPUT_CATEGORIES = ("exec", "wait_agent", "list_agents")
_LIMIT_MESSAGES = {
    "TRACE-USAGE-MISSING": "no complete usage record was recognized",
    "TRACE-USAGE-INCOMPLETE": "a usage record omitted required numeric fields",
    "TRACE-USAGE-UNSUPPORTED": "a usage-shaped record used an unsupported field shape",
}


@dataclass(frozen=True)
class UsageEvent:
    """Content-free token metadata normalized from one trace record."""

    event_id: str
    adapter: str
    stage: str
    actor: str
    visibility: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    cache_write_tokens: int
    reasoning_tokens: int
    tool_result_tokens: int
    total_tokens: int

    def as_dict(self) -> dict[str, str | int]:
        return {
            "event_id": self.event_id,
            "adapter": self.adapter,
            "stage": self.stage,
            "actor": self.actor,
            "visibility": self.visibility,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "tool_result_tokens": self.tool_result_tokens,
            "total_tokens": self.total_tokens,
        }


def _int_value(mapping: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return max(0, int(value))
    return 0


def _text_value(mapping: dict[str, Any], *keys: str, default: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def _find_mapping(record: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    queue: list[dict[str, Any]] = [record]
    seen: set[int] = set()
    while queue:
        current = queue.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))
        for name in names:
            value = current.get(name)
            if isinstance(value, dict):
                return value
        for value in current.values():
            if isinstance(value, dict):
                queue.append(value)
    return {}


def _attributes(record: dict[str, Any]) -> dict[str, Any]:
    attrs = record.get("attributes")
    return attrs if isinstance(attrs, dict) else {}


def _is_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


def _native_codex_usage(record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Classify one native rollout token-count envelope without using its cumulative total."""
    payload = record.get("payload")
    if (
        record.get("type") != "event_msg"
        or not isinstance(payload, dict)
        or payload.get("type") != "token_count"
    ):
        return "not-applicable", {}
    info = payload.get("info")
    if not isinstance(info, dict):
        return "incomplete", {}
    usage = info.get("last_token_usage")
    if not isinstance(usage, dict):
        return "incomplete", {}
    if not all(_is_number(usage.get(field)) for field in _CODEX_USAGE_FIELDS):
        return "incomplete", usage
    return "recognized", usage


def _generic_usage_status(
    record: dict[str, Any], usage: dict[str, Any], attrs: dict[str, Any]
) -> str:
    """Return whether a non-rollout record carries complete, partial, or unknown usage."""
    usage_container = _find_mapping(record, ("usage", "token_usage", "tokenUsage"))
    attr_usage = any(str(key).startswith(("gen_ai.usage.", "llm.token_count.")) for key in attrs)
    if not usage_container and not attr_usage:
        return "not-applicable"

    total_present = any(_is_number(usage.get(key)) for key in ("total_tokens", "totalTokens"))
    input_present = any(
        _is_number(usage.get(key))
        for key in ("input_tokens", "inputTokens", "prompt_tokens", "promptTokens")
    ) or any(
        _is_number(attrs.get(key))
        for key in ("gen_ai.usage.input_tokens", "llm.token_count.prompt")
    )
    output_present = any(
        _is_number(usage.get(key))
        for key in ("output_tokens", "outputTokens", "completion_tokens", "completionTokens")
    ) or any(
        _is_number(attrs.get(key))
        for key in ("gen_ai.usage.output_tokens", "llm.token_count.completion")
    )
    if total_present or (input_present and output_present):
        return "recognized"
    if input_present or output_present:
        return "incomplete"
    return "unsupported"


# Adapter and visibility classifiers deliberately share a typed classifier signature.
# lean-audit:dup-intentional:begin
def _adapter(
    record: dict[str, Any],
    usage: dict[str, Any],
    attrs: dict[str, Any],
    *,
    native_codex: bool = False,
) -> str:
    if native_codex:
        return "codex"
    attr_keys = " ".join(str(key) for key in attrs)
    event_name = " ".join(
        str(record.get(key, "")) for key in ("name", "event", "method", "source")
    ).lower()
    if any(str(key).startswith("gen_ai.") for key in attrs):
        if "claude" in event_name or "claude" in attr_keys.lower():
            return "claude-code"
        if "codex" in event_name or "codex" in attr_keys.lower():
            return "codex"
        return "otel"
    if "input_tokens_details" in usage or "output_tokens_details" in usage:
        return "openai"
    if "cache_read_input_tokens" in usage or "cache_creation_input_tokens" in usage:
        return "anthropic"
    if "tokenusage" in event_name or "codex" in event_name:
        return "codex"
    if "claude" in event_name:
        return "claude-code"
    return "generic"


# lean-audit:dup-intentional:end


def _visibility(record: dict[str, Any], attrs: dict[str, Any]) -> str:
    value: Any = record.get("visibility", attrs.get("lean_audit.visibility", "unknown"))
    if isinstance(value, bool):
        return "model" if value else "out-of-band"
    normalized = str(value).strip().lower()
    if normalized in {"model", "model-visible", "visible", "in-band"}:
        return "model"
    if normalized in {"out-of-band", "external", "telemetry", "file"}:
        return "out-of-band"
    return "unknown"


def _usage_or_attr(
    usage: dict[str, Any],
    attrs: dict[str, Any],
    usage_names: tuple[str, ...],
    attr_names: tuple[str, ...],
) -> int:
    return _int_value(usage, *usage_names) or _int_value(attrs, *attr_names)


def _one_event(record: dict[str, Any], index: int) -> UsageEvent | None:
    attrs = _attributes(record)
    native_status, native_usage = _native_codex_usage(record)
    usage = (
        native_usage
        if native_status == "recognized"
        else _find_mapping(record, ("usage", "token_usage", "tokenUsage"))
    )
    if native_status == "incomplete":
        return None

    input_tokens = _usage_or_attr(
        usage,
        attrs,
        ("input_tokens", "inputTokens", "prompt_tokens", "promptTokens"),
        ("gen_ai.usage.input_tokens", "llm.token_count.prompt"),
    )
    output_tokens = _usage_or_attr(
        usage,
        attrs,
        ("output_tokens", "outputTokens", "completion_tokens", "completionTokens"),
        ("gen_ai.usage.output_tokens", "llm.token_count.completion"),
    )

    input_details = usage.get("input_tokens_details")
    if not isinstance(input_details, dict):
        input_details = {}
    output_details = usage.get("output_tokens_details")
    if not isinstance(output_details, dict):
        output_details = {}

    cached = (
        _int_value(usage, "cached_input_tokens", "cache_read_input_tokens", "cacheReadInputTokens")
        or _int_value(input_details, "cached_tokens", "cachedTokens")
        or _int_value(attrs, "gen_ai.usage.cache_read.input_tokens")
    )
    cache_write = (
        _int_value(
            usage,
            "cache_write_tokens",
            "cache_write_input_tokens",
            "cache_creation_input_tokens",
            "cacheCreationInputTokens",
        )
        or _int_value(input_details, "cache_write_tokens", "cacheWriteTokens")
        or _int_value(attrs, "gen_ai.usage.cache_write.input_tokens")
    )
    reasoning = (
        _int_value(usage, "reasoning_tokens", "reasoningTokens", "reasoning_output_tokens")
        or _int_value(output_details, "reasoning_tokens", "reasoningTokens")
        or _int_value(attrs, "gen_ai.usage.reasoning_tokens")
    )
    tool_result = _int_value(record, "tool_result_tokens", "result_tokens") or _int_value(
        attrs,
        "tool.result_tokens",
        "tool_result_tokens",
        "claude_code.tool.result_tokens",
        "codex.tool.result_tokens",
    )
    total = _int_value(usage, "total_tokens", "totalTokens") or input_tokens + output_tokens
    if not any((input_tokens, output_tokens, cached, cache_write, reasoning, tool_result, total)):
        return None

    stage = _text_value(record, "stage", default="unknown")
    if stage == "unknown":
        stage = _text_value(attrs, "lean_audit.stage", "workflow.stage", default="unknown")
    actor = _text_value(record, "actor", "subagent_id", "agent_id", default="unknown")
    if actor == "unknown":
        actor = _text_value(
            attrs,
            "lean_audit.actor",
            "gen_ai.agent.id",
            "subagent.id",
            default="unknown",
        )
    event_id = _text_value(record, "id", "event_id", "span_id", "ordinal", default=str(index))
    return UsageEvent(
        event_id=event_id,
        adapter=_adapter(
            record,
            usage,
            attrs,
            native_codex=native_status == "recognized",
        ),
        stage=stage,
        actor=actor,
        visibility=_visibility(record, attrs),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached,
        cache_write_tokens=cache_write,
        reasoning_tokens=reasoning,
        tool_result_tokens=tool_result,
        total_tokens=total,
    )


def normalize_trace_records(records: Iterable[dict[str, Any]]) -> list[UsageEvent]:
    """Normalize records to metadata-only events; ignore records without usage."""
    events = []
    for index, record in enumerate(records):
        event = _one_event(record, index)
        if event is not None:
            events.append(event)
    return events


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yield JSONL objects one line at a time so large rollout files stay bounded."""
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: every trace record must be an object")
            yield row


# Evidence-specific readers intentionally remain thin wrappers over json_rows.
# lean-audit:dup-intentional:begin
def read_trace_file(path: Path) -> Iterable[dict[str, Any]]:
    """Read JSON input, streaming `.jsonl` records without retaining their content."""
    if path.suffix.lower() == ".jsonl":
        return _iter_jsonl(path)
    return read_json_rows(
        path,
        nested_list_key="events",
        scalar_error="trace must contain JSON objects",
        row_error="every trace record must be an object",
    )


# lean-audit:dup-intentional:end


def _empty_codex_rollout() -> dict[str, Any]:
    return {
        "compaction_count": 0,
        "collaboration_calls": {name: 0 for name in _COLLABORATION_CALLS},
        "waits": {
            "count": 0,
            "declared_timeout_ms_total": 0,
            "at_or_below_60000_ms": 0,
            "unknown_timeouts": 0,
        },
        "tool_output_utf8_bytes": {
            name: {"count": 0, "total": 0, "maximum": 0} for name in _TOOL_OUTPUT_CATEGORIES
        },
    }


def _json_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _output_bytes(value: Any) -> int:
    if isinstance(value, str):
        rendered = value
    else:
        rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return len(rendered.encode("utf-8"))


def _rollout_lifecycle(
    record: dict[str, Any],
    rollout: dict[str, Any],
    call_categories: dict[str, str],
) -> bool:
    """Update fixed content-free native rollout counters and return envelope recognition."""
    record_type = record.get("type")
    payload = record.get("payload")
    if record_type == "compacted":
        rollout["compaction_count"] += 1
        return True
    if not isinstance(payload, dict) or record_type not in {"response_item", "event_msg"}:
        return record_type in {
            "session_meta",
            "turn_context",
            "world_state",
            "inter_agent_communication_metadata",
        }

    payload_type = payload.get("type")
    if payload_type in {"function_call", "custom_tool_call"}:
        name = payload.get("name")
        call_id = payload.get("call_id")
        if isinstance(name, str) and isinstance(call_id, str) and name in _TOOL_OUTPUT_CATEGORIES:
            call_categories[call_id] = name
        if isinstance(name, str) and name in _COLLABORATION_CALLS:
            rollout["collaboration_calls"][name] += 1
            if name == "wait_agent":
                waits = rollout["waits"]
                waits["count"] += 1
                arguments = _json_object(payload.get("arguments"))
                timeout = None if arguments is None else arguments.get("timeout_ms")
                if (
                    isinstance(timeout, bool)
                    or not isinstance(timeout, (int, float))
                    or timeout < 0
                ):
                    waits["unknown_timeouts"] += 1
                else:
                    timeout_ms = int(timeout)
                    waits["declared_timeout_ms_total"] += timeout_ms
                    if timeout_ms <= 60_000:
                        waits["at_or_below_60000_ms"] += 1
        return True

    if payload_type in {"function_call_output", "custom_tool_call_output"}:
        call_id = payload.get("call_id")
        category = call_categories.pop(call_id, None) if isinstance(call_id, str) else None
        if category is not None:
            byte_count = _output_bytes(payload.get("output"))
            bucket = rollout["tool_output_utf8_bytes"][category]
            bucket["count"] += 1
            bucket["total"] += byte_count
            bucket["maximum"] = max(bucket["maximum"], byte_count)
        return True
    return record_type in {"response_item", "event_msg"}


def _coverage(
    *,
    source_records: int,
    recognized_usage_events: int,
    unsupported_usage_records: int,
    limit_codes: set[str],
) -> dict[str, Any]:
    if recognized_usage_events == 0:
        limit_codes.add("TRACE-USAGE-MISSING")
    eligible = recognized_usage_events > 0 and unsupported_usage_records == 0
    return {
        "source_records": source_records,
        "recognized_usage_events": recognized_usage_events,
        "unsupported_usage_records": unsupported_usage_records,
        "calibration_eligible": eligible,
        "limit_codes": sorted(limit_codes),
    }


def summarize_trace(
    events: list[UsageEvent],
    *,
    coverage: dict[str, Any] | None = None,
    codex_rollout: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate normalized metadata. Raw prompts and tool output never enter it."""
    totals: dict[str, Any] = {
        "event_count": len(events),
        "input_tokens": sum(event.input_tokens for event in events),
        "output_tokens": sum(event.output_tokens for event in events),
        "cached_input_tokens": sum(event.cached_input_tokens for event in events),
        "cache_write_tokens": sum(event.cache_write_tokens for event in events),
        "reasoning_tokens": sum(event.reasoning_tokens for event in events),
        "total_tokens": sum(event.total_tokens for event in events),
    }
    totals.update(
        {
            f"{label}_tool_result_tokens": sum(
                event.tool_result_tokens for event in events if event.visibility == visibility
            )
            for visibility, label in (
                ("model", "model_visible"),
                ("out-of-band", "out_of_band"),
                ("unknown", "unknown_visibility"),
            )
        }
    )
    by_adapter: dict[str, int] = {}
    by_stage: dict[str, int] = {}
    for event in events:
        by_adapter[event.adapter] = by_adapter.get(event.adapter, 0) + event.total_tokens
        by_stage[event.stage] = by_stage.get(event.stage, 0) + event.total_tokens
    totals["by_adapter"] = dict(sorted(by_adapter.items()))
    totals["by_stage"] = dict(sorted(by_stage.items()))
    totals["content_policy"] = "metadata-only"
    trace_coverage = coverage or _coverage(
        source_records=len(events),
        recognized_usage_events=len(events),
        unsupported_usage_records=0,
        limit_codes=set(),
    )
    totals["coverage"] = trace_coverage
    totals["limits"] = [
        {"code": code, "detail": _LIMIT_MESSAGES[code]} for code in trace_coverage["limit_codes"]
    ]
    if codex_rollout is not None:
        totals["codex_rollout"] = codex_rollout
    return totals


def summarize_trace_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Stream trace records into usage coverage and bounded native-rollout counters."""
    events: list[UsageEvent] = []
    source_records = 0
    unsupported_usage_records = 0
    limit_codes: set[str] = set()
    rollout = _empty_codex_rollout()
    call_categories: dict[str, str] = {}
    codex_rollout_seen = False

    for index, record in enumerate(records):
        source_records += 1
        codex_rollout_seen = (
            _rollout_lifecycle(record, rollout, call_categories) or codex_rollout_seen
        )
        native_status, _ = _native_codex_usage(record)
        if native_status == "incomplete":
            unsupported_usage_records += 1
            limit_codes.add("TRACE-USAGE-INCOMPLETE")
            continue

        event = _one_event(record, index)
        if native_status == "recognized":
            if event is not None:
                events.append(event)
            continue

        usage = _find_mapping(record, ("usage", "token_usage", "tokenUsage"))
        generic_status = _generic_usage_status(record, usage, _attributes(record))
        if generic_status == "recognized" and event is not None:
            events.append(event)
        elif generic_status in {"incomplete", "unsupported"}:
            unsupported_usage_records += 1
            limit_codes.add(
                "TRACE-USAGE-INCOMPLETE"
                if generic_status == "incomplete"
                else "TRACE-USAGE-UNSUPPORTED"
            )

    trace_coverage = _coverage(
        source_records=source_records,
        recognized_usage_events=len(events),
        unsupported_usage_records=unsupported_usage_records,
        limit_codes=limit_codes,
    )
    return summarize_trace(
        events,
        coverage=trace_coverage,
        codex_rollout=rollout if codex_rollout_seen else None,
    )
