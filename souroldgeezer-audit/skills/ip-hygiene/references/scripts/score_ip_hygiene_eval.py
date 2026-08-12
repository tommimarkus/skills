#!/usr/bin/env python3
"""Deterministically compare blind IP-hygiene eval results to expectations."""

import argparse
import json
from pathlib import Path


def records(path: Path) -> dict[str, dict]:
    result = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not item.get("case"):
            raise ValueError(f"{path}:{number}: missing case")
        result[item["case"]] = item
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--families", help="comma-separated criterion families")
    args = parser.parse_args()
    families = set(args.families.split(",")) if args.families else None
    expected = records(args.expected)
    actual = records(args.actual)
    errors: list[str] = []
    for case, wanted in expected.items():
        if families and wanted["family"] not in families:
            continue
        got = actual.get(case)
        if got is None:
            errors.append(f"{case}: missing actual result")
            continue
        codes = set(got.get("codes", got.get("required_codes", [])))
        required = set(wanted["required_codes"])
        if wanted["triage_gate"] == "fail" and not required.issubset(codes):
            errors.append(f"{case}: missed designated blocker")
        if wanted["expect"] == "no-finding" and codes:
            errors.append(f"{case}: forbidden clean-control finding")
        if set(wanted["forbidden_codes"]) & codes:
            errors.append(f"{case}: forbidden finding code")
        for field in ("severity", "triage_gate", "in_depth_verdict", "authority_class", "fact_status", "counsel_outcome"):
            if got.get(field) != wanted[field]:
                errors.append(f"{case}: wrong {field}")
        if got.get("legal_clearance") is True or got.get("clearance") is True:
            errors.append(f"{case}: legal-clearance overclaim")
    print("IP hygiene eval: " + ("PASS" if not errors else "FAIL"))
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
