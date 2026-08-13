#!/usr/bin/env python3
"""Deterministically score closed-schema blind IP-hygiene evaluation results."""

import argparse
import json
from pathlib import Path

from validate_ip_hygiene_actual import CODES, validate_file


EXPECTED_KEYS = {"case", "family", "expect", "required_codes", "allowed_codes", "allowed_classifications", "lane", "outcome", "counsel_outcome", "designated_blocker_criterion"}
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
        required, allowed = item["required_codes"], item["allowed_codes"]
        if not isinstance(required, list) or not isinstance(allowed, list) or not set(required).issubset(allowed):
            errors.append(f"expected line {number}: required_codes must be allowed")
        if not set(required).issubset(CODES) or not set(allowed).issubset(CODES):
            errors.append(f"expected line {number}: invalid expected code")
        if set(required) != set(item["allowed_classifications"]):
            errors.append(f"expected line {number}: classifications must cover exactly required codes")
        for classifications in item["allowed_classifications"].values():
            if not isinstance(classifications, list) or not classifications:
                errors.append(f"expected line {number}: empty allowed classification")
                continue
            for classification in classifications:
                if set(classification) != CLASSIFICATION_KEYS:
                    errors.append(f"expected line {number}: classification keys are closed")
        if item["expect"] == "no-finding" and (required or allowed or item["allowed_classifications"]):
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
        required = set(wanted["required_codes"])
        for code in required - codes:
            errors.append(f"{case}: missing required finding code: {code}")
        for code in codes - set(wanted["allowed_codes"]):
            errors.append(f"{case}: undeclared finding code: {code}")
        if wanted["expect"] == "no-finding" and codes:
            errors.append(f"{case}: forbidden clean-control finding")
        for finding in got.get("findings", []):
            if not isinstance(finding, dict) or finding.get("code") not in required:
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
