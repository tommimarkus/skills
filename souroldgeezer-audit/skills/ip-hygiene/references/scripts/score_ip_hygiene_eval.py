#!/usr/bin/env python3
"""Deterministically score closed-schema blind IP-hygiene evaluation results."""

import argparse
import json
from pathlib import Path

from validate_ip_hygiene_actual import CODES, validate_file


EXPECTED_KEYS = {"case", "family", "expect", "required_code_groups", "allowed_codes", "allowed_classifications", "lane", "outcome", "counsel_outcome", "designated_blocker_criterion"}
CLASSIFICATION_KEYS = {"severity", "authority_class", "fact_status"}


def expected_records(path: Path) -> tuple[dict[str, dict], list[str]]:
    result: dict[str, dict] = {}
    errors: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"expected line {number}: invalid JSON: {error.msg}")
            continue
        if set(item) != EXPECTED_KEYS:
            errors.append(f"expected line {number}: keys are closed")
            continue
        case = item["case"]
        if case in result:
            errors.append(f"expected line {number}: duplicate case: {case}")
        result[case] = item
        groups, allowed = item["required_code_groups"], item["allowed_codes"]
        valid_groups = isinstance(groups, list) and all(
            isinstance(group, list)
            and group
            and all(isinstance(code, str) for code in group)
            and len(group) == len(set(group))
            for group in groups
        )
        required = {
            code
            for group in groups if isinstance(group, list)
            for code in group if isinstance(code, str)
        } if isinstance(groups, list) else set()
        group_entry_count = sum(len(group) for group in groups) if valid_groups else 0
        valid_allowed = (
            isinstance(allowed, list)
            and all(isinstance(code, str) for code in allowed)
            and len(allowed) == len(set(allowed))
        )
        allowed_set = set(allowed) if valid_allowed else set()
        if (
            not valid_groups
            or len(required) != group_entry_count
            or not valid_allowed
            or not required.issubset(allowed_set)
        ):
            errors.append(f"expected line {number}: required_code_groups must be nonempty groups of allowed codes")
        if not required.issubset(CODES) or not allowed_set.issubset(CODES):
            errors.append(f"expected line {number}: invalid expected code")
        if allowed_set != set(item["allowed_classifications"]):
            errors.append(f"expected line {number}: classifications must cover exactly allowed codes")
        for classifications in item["allowed_classifications"].values():
            if not isinstance(classifications, list) or not classifications:
                errors.append(f"expected line {number}: empty allowed classification")
                continue
            for classification in classifications:
                if set(classification) != CLASSIFICATION_KEYS:
                    errors.append(f"expected line {number}: classification keys are closed")
        if item["expect"] == "no-finding" and (groups or allowed or item["allowed_classifications"]):
            errors.append(f"expected line {number}: clean control must have no findings")
        if item["designated_blocker_criterion"] is not None and item["designated_blocker_criterion"] not in required:
            errors.append(f"expected line {number}: designated blocker must be required")
    return result, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--families", help="comma-separated criterion families")
    args = parser.parse_args()
    expected, errors = expected_records(args.expected)
    actual, actual_errors = validate_file(args.actual)
    errors.extend(f"actual {error}" for error in actual_errors)
    for case in sorted(set(actual) - set(expected)):
        errors.append(f"unexpected actual case: {case}")
    declared_families = {item["family"] for item in expected.values()}
    families = {item.strip() for item in args.families.split(",")} if args.families else None
    if families is not None:
        for family in sorted(families - declared_families):
            errors.append(f"unknown family selector: {family or '<empty>'}")
        if not families & declared_families:
            errors.append("family selection covers zero declared cases")
    for case, wanted in expected.items():
        if families is not None and wanted["family"] not in families:
            continue
        got = actual.get(case)
        if got is None:
            errors.append(f"{case}: missing actual result")
            continue
        codes = {finding["code"] for finding in got.get("findings", []) if isinstance(finding, dict) and "code" in finding}
        for group in wanted["required_code_groups"]:
            if not codes.intersection(group):
                errors.append(f"{case}: missing required finding code group: {' | '.join(group)}")
        for code in codes - set(wanted["allowed_codes"]):
            errors.append(f"{case}: undeclared finding code: {code}")
        if wanted["expect"] == "no-finding" and codes:
            errors.append(f"{case}: forbidden clean-control finding")
        for finding in got.get("findings", []):
            if not isinstance(finding, dict) or finding.get("code") not in wanted["allowed_codes"]:
                continue
            allowed = wanted["allowed_classifications"][finding["code"]]
            classification = {key: finding.get(key) for key in CLASSIFICATION_KEYS}
            if classification not in allowed:
                errors.append(f"{case}: wrong classification for {finding['code']}")
        if got.get("lane") != wanted["lane"]:
            errors.append(f"{case}: wrong lane")
        outcome_field = {"triage": "triage_gate", "in-depth": "in_depth_verdict", "prospective": "prospective_decision"}[wanted["lane"]]
        if got.get(outcome_field) != wanted["outcome"]:
            errors.append(f"{case}: wrong lane outcome")
        if got.get("counsel_outcome") != wanted["counsel_outcome"]:
            errors.append(f"{case}: wrong counsel_outcome")
        if got.get("legal_clearance") is not False:
            errors.append(f"{case}: legal-clearance overclaim")
    print("IP hygiene eval: " + ("PASS" if not errors else "FAIL"))
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
