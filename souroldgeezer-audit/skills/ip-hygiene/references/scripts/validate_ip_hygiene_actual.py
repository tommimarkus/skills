#!/usr/bin/env python3
"""Validate closed-schema blind IP-hygiene evaluation records."""

import argparse
import json
from pathlib import Path


LANE_FIELDS = {
    "triage": "triage_gate",
    "in-depth": "in_depth_verdict",
    "prospective": "prospective_decision",
}
COMMON_EVIDENCE_FIELDS = ("reviewed_surface", "exclusions", "evidence", "limits")
LANE_EVIDENCE_FIELDS = {"triage": (), "in-depth": (), "prospective": ("decision_controls",)}
ASSURANCE_LEVELS = {
    "triage": "limited triage",
    "in-depth": "reasonable-hygiene in-depth",
    "prospective": "prospective bounded decision",
}
OUTCOMES = {
    "triage_gate": {"fail", "not-evaluated", "pass-limited"},
    "in_depth_verdict": {"blocked", "qualified", "no-blocker-identified"},
    "prospective_decision": {"proceed-with-stated-controls", "do-not-proceed", "insufficient-evidence", "counsel-required"},
}
SEVERITIES = {"block", "warn", "info"}
AUTHORITIES = {
    "binding law",
    "binding-law harmonization source",
    "operative licence term",
    "holder policy",
    "project convention",
    "conservative repository policy",
}
FACT_STATUSES = {"fact", "inference"}
COUNSEL_OUTCOMES = {"not-triggered", "recommended", "required"}
INDEPENDENCE = {"independent", "self-review", "unknown"}
CONFIDENCE = {"high", "medium", "low"}
RISK_TIERS = {"high", "medium", "low", "unknown"}
INTENDED_ACTS = {
    "mention", "link", "quote", "copy", "modify", "aggregate", "link/import",
    "execute", "redistribute",
}
CODES = {*(f"IP-SRC-{number}" for number in range(1, 5)),
         *(f"IP-COPY-{number}" for number in range(1, 5)),
         *(f"IP-DB-{number}" for number in range(1, 3)),
         *(f"IP-LIC-{number}" for number in range(1, 5)),
         *(f"IP-MARK-{number}" for number in range(1, 6))}


def validate_item(item: object, line: int) -> list[str]:
    prefix = f"line {line}:"
    if not isinstance(item, dict):
        return [f"{prefix} record must be an object"]
    errors: list[str] = []
    lane = item.get("lane")
    if not isinstance(lane, str) or lane not in LANE_FIELDS:
        errors.append(f"{prefix} invalid lane")
        return errors
    permitted = {
        "case", "lane", "findings", "counsel_outcome", "legal_clearance",
        "independence", "assurance_level", LANE_FIELDS[lane],
        *COMMON_EVIDENCE_FIELDS, *LANE_EVIDENCE_FIELDS[lane],
    }
    for key in item:
        if key in {"clearance", "legal_clearance_status"}:
            errors.append(f"{prefix} clearance alias is forbidden: {key}")
        elif key not in permitted:
            errors.append(f"{prefix} undeclared field: {key}")
    if not isinstance(item.get("case"), str) or not item["case"]:
        errors.append(f"{prefix} case must be a nonempty string")
    if item.get("legal_clearance") is not False:
        errors.append(f"{prefix} legal_clearance must be literal false")
    if not isinstance(item.get("counsel_outcome"), str) or item.get("counsel_outcome") not in COUNSEL_OUTCOMES:
        errors.append(f"{prefix} invalid counsel_outcome")
    if not isinstance(item.get("independence"), str) or item.get("independence") not in INDEPENDENCE:
        errors.append(f"{prefix} invalid independence")
    if item.get("assurance_level") != ASSURANCE_LEVELS[lane]:
        errors.append(f"{prefix} invalid assurance_level")
    outcome_field = LANE_FIELDS[lane]
    if not isinstance(item.get(outcome_field), str) or item.get(outcome_field) not in OUTCOMES[outcome_field]:
        errors.append(f"{prefix} invalid {outcome_field}")
    for field in (*COMMON_EVIDENCE_FIELDS, *LANE_EVIDENCE_FIELDS[lane]):
        value = item.get(field)
        if (
            not isinstance(value, list)
            or not value
            or any(not isinstance(entry, str) or not entry.strip() for entry in value)
        ):
            errors.append(f"{prefix} {field} must be a nonempty array of nonempty strings")
    findings = item.get("findings")
    if not isinstance(findings, list):
        errors.append(f"{prefix} findings must be an array")
        return errors
    seen_codes: set[str] = set()
    for index, finding in enumerate(findings):
        finding_prefix = f"{prefix} findings[{index}]:"
        if not isinstance(finding, dict):
            errors.append(f"{finding_prefix} finding must be an object")
            continue
        if set(finding) != {
            "code", "severity", "authority_class", "fact_status", "condition",
            "location", "source_provenance", "intended_act", "distribution_audience",
            "jurisdiction_applicability", "confidence", "evidence", "cause",
            "consequence", "recommendation", "risk_tier", "counsel_outcome",
        }:
            errors.append(f"{finding_prefix} finding keys are closed")
            continue
        code = finding["code"]
        if not isinstance(code, str) or not code:
            errors.append(f"{finding_prefix} code must be a nonempty string")
        elif code not in CODES:
            errors.append(f"{finding_prefix} invalid code")
        elif code in seen_codes:
            errors.append(f"{finding_prefix} duplicate finding code: {code}")
        else:
            seen_codes.add(code)
        if not isinstance(finding["severity"], str) or finding["severity"] not in SEVERITIES:
            errors.append(f"{finding_prefix} invalid severity")
        if not isinstance(finding["authority_class"], str) or finding["authority_class"] not in AUTHORITIES:
            errors.append(f"{finding_prefix} invalid authority_class")
        if not isinstance(finding["fact_status"], str) or finding["fact_status"] not in FACT_STATUSES:
            errors.append(f"{finding_prefix} invalid fact_status")
        if not isinstance(finding["intended_act"], str) or finding["intended_act"] not in INTENDED_ACTS:
            errors.append(f"{finding_prefix} invalid intended_act")
        if not isinstance(finding["confidence"], str) or finding["confidence"] not in CONFIDENCE:
            errors.append(f"{finding_prefix} invalid confidence")
        if not isinstance(finding["risk_tier"], str) or finding["risk_tier"] not in RISK_TIERS:
            errors.append(f"{finding_prefix} invalid risk_tier")
        if not isinstance(finding["counsel_outcome"], str) or finding["counsel_outcome"] not in COUNSEL_OUTCOMES:
            errors.append(f"{finding_prefix} invalid counsel_outcome")
        elif finding["counsel_outcome"] != item.get("counsel_outcome"):
            errors.append(f"{finding_prefix} counsel_outcome must match the case outcome")
        for field in (
            "condition", "location", "source_provenance", "distribution_audience",
            "jurisdiction_applicability", "cause", "consequence", "recommendation",
        ):
            if not isinstance(finding[field], str) or not finding[field].strip():
                errors.append(f"{finding_prefix} {field} must be a nonempty string")
        evidence = finding["evidence"]
        if (
            not isinstance(evidence, list)
            or not evidence
            or any(not isinstance(entry, str) or not entry.strip() for entry in evidence)
        ):
            errors.append(f"{finding_prefix} evidence must be a nonempty array of nonempty strings")
    return errors


def validate_file(path: Path) -> tuple[dict[str, dict], list[str]]:
    result: dict[str, dict] = {}
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"line {line_number}: invalid JSON: {error.msg}")
            continue
        errors.extend(validate_item(item, line_number))
        if isinstance(item, dict) and isinstance(item.get("case"), str):
            if item["case"] in result:
                errors.append(f"line {line_number}: duplicate case: {item['case']}")
            result[item["case"]] = item
    return result, errors


def case_ids(path: Path) -> tuple[set[str], list[str]]:
    result: set[str] = set()
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"cases line {line_number}: invalid JSON: {error.msg}")
            continue
        case = item.get("case") if isinstance(item, dict) else None
        if not isinstance(case, str) or not case:
            errors.append(f"cases line {line_number}: case must be a nonempty string")
        elif case in result:
            errors.append(f"cases line {line_number}: duplicate case: {case}")
        else:
            result.add(case)
    return result, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    args = parser.parse_args(argv)
    actual, errors = validate_file(args.actual)
    expected_cases, case_errors = case_ids(args.cases)
    errors.extend(case_errors)
    for case in sorted(expected_cases - set(actual)):
        errors.append(f"missing actual case: {case}")
    for case in sorted(set(actual) - expected_cases):
        errors.append(f"unexpected actual case: {case}")
    print("IP hygiene actual schema: " + ("PASS" if not errors else "FAIL"))
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
