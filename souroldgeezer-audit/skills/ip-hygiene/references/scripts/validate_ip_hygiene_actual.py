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
    if lane not in LANE_FIELDS:
        errors.append(f"{prefix} invalid lane")
        return errors
    permitted = {"case", "lane", "findings", "counsel_outcome", "legal_clearance", LANE_FIELDS[lane]}
    for key in item:
        if key in {"clearance", "legal_clearance_status"}:
            errors.append(f"{prefix} clearance alias is forbidden: {key}")
        elif key not in permitted:
            errors.append(f"{prefix} undeclared field: {key}")
    if not isinstance(item.get("case"), str) or not item["case"]:
        errors.append(f"{prefix} case must be a nonempty string")
    if item.get("legal_clearance") is not False:
        errors.append(f"{prefix} legal_clearance must be literal false")
    if item.get("counsel_outcome") not in COUNSEL_OUTCOMES:
        errors.append(f"{prefix} invalid counsel_outcome")
    outcome_field = LANE_FIELDS[lane]
    if item.get(outcome_field) not in OUTCOMES[outcome_field]:
        errors.append(f"{prefix} invalid {outcome_field}")
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
        if set(finding) != {"code", "severity", "authority_class", "fact_status"}:
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
        if finding["severity"] not in SEVERITIES:
            errors.append(f"{finding_prefix} invalid severity")
        if finding["authority_class"] not in AUTHORITIES:
            errors.append(f"{finding_prefix} invalid authority_class")
        if finding["fact_status"] not in FACT_STATUSES:
            errors.append(f"{finding_prefix} invalid fact_status")
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
