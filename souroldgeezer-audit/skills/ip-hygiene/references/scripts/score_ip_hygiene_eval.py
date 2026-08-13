#!/usr/bin/env python3
"""Deterministically score closed-schema blind IP-hygiene evaluation results."""

import argparse
import json
import re
from pathlib import Path

from validate_ip_hygiene_actual import (
    AUTHORITIES,
    CODES,
    COUNSEL_OUTCOMES,
    FACT_STATUSES,
    LANE_FIELDS,
    OUTCOMES,
    SEVERITIES,
    case_ids,
    validate_file,
)


EXPECTED_REQUIRED_KEYS = {
    "case", "family", "expect", "required_code_groups", "allowed_codes",
    "allowed_classifications", "lane", "outcome", "counsel_outcome",
    "designated_blocker_criterion", "evidence_anchors",
}
EXPECTED_OPTIONAL_KEYS = {"fact_proposition_anchors", "required_proposition_grounding"}
CLASSIFICATION_KEYS = {"severity", "authority_class", "fact_status"}
REQUIRED_PROPOSITION_KEYS = {"codes", "condition_location_anchors"}
FAMILIES = {"IP-SRC", "IP-COPY", "IP-DB", "IP-LIC", "IP-MARK"}
EXPECTATIONS = {"finding", "stopped", "no-finding"}
GENERIC_ANCHOR_TOKENS = {
    "claim", "commands", "component", "copyright", "diagram", "evidence",
    "example", "guide", "inventory", "material", "official", "original",
    "plugin", "policy", "public", "report", "source", "supplied", "table",
    "trademark", "works",
}
LEGAL_MERITS_PATTERNS = tuple(map(re.compile, (
    r"\binfring(?:e(?:s|d)?|ing|ement(?:s)?)\b",
    r"\bnon[- ]?infringing\b",
    r"\b(?:copyrightable|uncopyrightable)\b",
    r"\b(?:protected|unprotected)\s+(?:expression|work|material|content|selection|arrangement|database|mark|logo)\b",
    r"\b(?:protected|unprotected)\s+(?:by|under)\s+(?:copyright|trade[- ]?mark|database rights?)\b",
    r"\b(?:copyright|trade[- ]?mark|database[- ]?right|sui generis)\s+(?:protection|protected status|exception)\b",
    r"\b(?:fair use|fair dealing|quotation exception|copyright exception|trade[- ]?mark exception)\b",
    r"\b(?:exception|limitation|defen[cs]e)\s+(?:appl(?:y|ies)|covers?|permits?|defeats?|succeeds?|fails?)\b",
    r"\b(?:likely|unlikely|likelihood)\b.{0,80}\b(?:confusion|infring|protected|exception)\b",
    r"\b(?:confusingly similar|substantial similarity|substantially similar)\b",
    r"\b(?:violates?|breaches?)\s+(?:copyright|trade[- ]?mark|database rights?)\b",
    r"\b(?:copyright|trade[- ]?mark|database rights?)\s+(?:subsists?|applies?|protects?)\b",
    r"\b(?:owns?|ownership of|title to)\b.{0,80}\b(?:copyright|trade[- ]?mark|database rights?)\b",
    r"\b(?:copyright|trade[- ]?mark|database rights?)\b.{0,80}\b(?:is owned by|belongs? to)\b",
    r"\b(?:lawful|unlawful|illegal)\b.{0,80}\b(?:copy|use|publication|distribution|redistribution)\b",
    r"\b(?:legal merits|merits determination|court would|tribunal would)\b",
)))


def anchor_matches(anchor: str, grounding: str) -> bool:
    folded = anchor.casefold()
    if folded in grounding:
        return True
    distinctive_tokens = {
        token for token in re.findall(r"[a-z0-9]+", folded)
        if len(token) >= 5 and token not in GENERIC_ANCHOR_TOKENS
    }
    return bool(distinctive_tokens.intersection(re.findall(r"[a-z0-9]+", grounding)))


def is_legal_merits_proposition(proposition: object) -> bool:
    if not isinstance(proposition, str):
        return True
    folded = proposition.casefold()
    return any(pattern.search(folded) for pattern in LEGAL_MERITS_PATTERNS)


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
        if (
            not isinstance(item, dict)
            or not EXPECTED_REQUIRED_KEYS.issubset(item)
            or not set(item).issubset(EXPECTED_REQUIRED_KEYS | EXPECTED_OPTIONAL_KEYS)
        ):
            errors.append(f"expected line {number}: keys are closed")
            continue
        case = item["case"]
        if not isinstance(case, str) or not case:
            errors.append(f"expected line {number}: case must be a nonempty string")
            continue
        if case in result:
            errors.append(f"expected line {number}: duplicate case: {case}")
        result[case] = item
        if not isinstance(item["family"], str) or item["family"] not in FAMILIES:
            errors.append(f"expected line {number}: invalid family")
        if not isinstance(item["expect"], str) or item["expect"] not in EXPECTATIONS:
            errors.append(f"expected line {number}: invalid expect")
        if not isinstance(item["lane"], str) or item["lane"] not in LANE_FIELDS:
            errors.append(f"expected line {number}: invalid lane")
        else:
            outcome_field = LANE_FIELDS[item["lane"]]
            if not isinstance(item["outcome"], str) or item["outcome"] not in OUTCOMES[outcome_field]:
                errors.append(f"expected line {number}: invalid outcome for lane")
        if not isinstance(item["counsel_outcome"], str) or item["counsel_outcome"] not in COUNSEL_OUTCOMES:
            errors.append(f"expected line {number}: invalid counsel_outcome")
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
        if isinstance(item["family"], str) and item["family"] in FAMILIES and required:
            if not any(code.startswith(item["family"] + "-") for code in required):
                errors.append(f"expected line {number}: required groups must cover the declared family")
        classifications_by_code = item["allowed_classifications"]
        if not isinstance(classifications_by_code, dict):
            errors.append(f"expected line {number}: allowed_classifications must be an object")
            classifications_by_code = {}
        if allowed_set != set(classifications_by_code):
            errors.append(f"expected line {number}: classifications must cover exactly allowed codes")
        mixed_fact_codes: set[str] = set()
        for code, classifications in classifications_by_code.items():
            if not isinstance(classifications, list) or not classifications:
                errors.append(f"expected line {number}: empty allowed classification")
                continue
            fact_statuses: set[str] = set()
            for classification in classifications:
                if not isinstance(classification, dict) or set(classification) != CLASSIFICATION_KEYS:
                    errors.append(f"expected line {number}: classification keys are closed")
                    continue
                if not isinstance(classification["severity"], str) or classification["severity"] not in SEVERITIES:
                    errors.append(f"expected line {number}: invalid classification severity")
                if not isinstance(classification["authority_class"], str) or classification["authority_class"] not in AUTHORITIES:
                    errors.append(f"expected line {number}: invalid classification authority")
                if not isinstance(classification["fact_status"], str) or classification["fact_status"] not in FACT_STATUSES:
                    errors.append(f"expected line {number}: invalid classification fact_status")
                else:
                    fact_statuses.add(classification["fact_status"])
            if {"fact", "inference"}.issubset(fact_statuses):
                mixed_fact_codes.add(code)
        fact_proposition_anchors = item.get("fact_proposition_anchors")
        if mixed_fact_codes:
            if not isinstance(fact_proposition_anchors, dict) or set(fact_proposition_anchors) != mixed_fact_codes:
                errors.append(
                    f"expected line {number}: fact_proposition_anchors must cover every mixed fact/inference code"
                )
            else:
                for code, fact_anchors in fact_proposition_anchors.items():
                    if (
                        not isinstance(fact_anchors, list)
                        or not fact_anchors
                        or any(not isinstance(anchor, str) or not anchor.strip() for anchor in fact_anchors)
                        or len(fact_anchors) != len(set(fact_anchors))
                    ):
                        errors.append(
                            f"expected line {number}: invalid fact proposition anchors for {code}"
                        )
        elif fact_proposition_anchors is not None:
            errors.append(f"expected line {number}: fact_proposition_anchors declared without a mixed code")
        required_proposition_grounding = item.get("required_proposition_grounding")
        if valid_groups and len(groups) > 1 and required_proposition_grounding is None:
            errors.append(
                f"expected line {number}: multiple required propositions need condition/location grounding"
            )
        if required_proposition_grounding is not None:
            valid_propositions = isinstance(required_proposition_grounding, list) and bool(
                required_proposition_grounding
            )
            proposition_groups: list[frozenset[str]] = []
            if valid_propositions:
                for proposition in required_proposition_grounding:
                    if not isinstance(proposition, dict) or set(proposition) != REQUIRED_PROPOSITION_KEYS:
                        valid_propositions = False
                        continue
                    proposition_codes = proposition["codes"]
                    proposition_anchors = proposition["condition_location_anchors"]
                    if (
                        not isinstance(proposition_codes, list)
                        or not proposition_codes
                        or any(not isinstance(code, str) for code in proposition_codes)
                        or len(proposition_codes) != len(set(proposition_codes))
                        or not isinstance(proposition_anchors, list)
                        or not proposition_anchors
                        or any(not isinstance(anchor, str) or not anchor.strip() for anchor in proposition_anchors)
                        or len(proposition_anchors) != len(set(proposition_anchors))
                    ):
                        valid_propositions = False
                        continue
                    proposition_groups.append(frozenset(proposition_codes))
            expected_groups = [frozenset(group) for group in groups] if valid_groups else []
            if (
                not valid_propositions
                or len(proposition_groups) != len(set(proposition_groups))
                or set(proposition_groups) != set(expected_groups)
            ):
                errors.append(
                    f"expected line {number}: required_proposition_grounding must cover each required code group exactly"
                )
        anchors = item["evidence_anchors"]
        valid_anchors = (
            isinstance(anchors, list)
            and bool(anchors)
            and all(isinstance(anchor, str) and anchor.strip() for anchor in anchors)
        )
        if not valid_anchors or len(anchors) != len(set(anchors)):
            errors.append(f"expected line {number}: evidence_anchors must be unique nonempty strings")
        if item["expect"] == "no-finding" and (groups or allowed or item["allowed_classifications"]):
            errors.append(f"expected line {number}: clean control must have no findings")
        if (item["expect"] == "finding" or item["expect"] == "stopped") and not groups:
            errors.append(f"expected line {number}: finding or stopped record must require a code group")
        stopped_outcomes = {
            "triage": {"not-evaluated"},
            "in-depth": {"blocked"},
            "prospective": {"insufficient-evidence", "counsel-required"},
        }
        if item["expect"] == "stopped" and isinstance(item["lane"], str) and item["lane"] in stopped_outcomes:
            if not isinstance(item["outcome"], str) or item["outcome"] not in stopped_outcomes[item["lane"]]:
                errors.append(f"expected line {number}: stopped record has incoherent outcome")
        if item["counsel_outcome"] == "required":
            if not isinstance(item["outcome"], str) or item["outcome"] not in {"blocked", "counsel-required"}:
                errors.append(f"expected line {number}: required counsel must stop the lane")
        if item["outcome"] == "counsel-required" and item["counsel_outcome"] != "required":
            errors.append(f"expected line {number}: counsel-required outcome requires counsel outcome required")
        if item["counsel_outcome"] == "recommended":
            if isinstance(item["outcome"], str) and item["outcome"] in {"blocked", "counsel-required"}:
                errors.append(f"expected line {number}: recommended counsel cannot be a mandatory stop")
        designated = item["designated_blocker_criterion"]
        if designated is not None and (not isinstance(designated, str) or designated not in required):
            errors.append(f"expected line {number}: designated blocker must be required")
        if isinstance(designated, str) and not any(
            classification.get("severity") == "block"
            for classification in classifications_by_code.get(designated, [])
            if isinstance(classification, dict)
        ):
            errors.append(f"expected line {number}: designated blocker must allow block severity")
        if isinstance(designated, str) and item["outcome"] not in {"fail", "blocked", "do-not-proceed"}:
            errors.append(f"expected line {number}: designated blocker contradicts nonblocking lane outcome")
        required_has_block = any(
            classification.get("severity") == "block"
            for code in required
            for classification in classifications_by_code.get(code, [])
            if isinstance(classification, dict)
        )
        if isinstance(item["outcome"], str) and item["outcome"] in {"fail", "do-not-proceed"} and not required_has_block:
            errors.append(f"expected line {number}: blocking outcome requires a required block classification")
        nonblocking_outcomes = {
            "pass-limited", "not-evaluated", "qualified", "no-blocker-identified",
            "proceed-with-stated-controls", "insufficient-evidence", "counsel-required",
        }
        if isinstance(item["outcome"], str) and item["outcome"] in nonblocking_outcomes and required_has_block:
            errors.append(f"expected line {number}: block severity contradicts nonblocking lane outcome")
        if item["outcome"] == "blocked" and item["counsel_outcome"] != "required" and not required_has_block:
            errors.append(f"expected line {number}: blocked outcome requires a block or required counsel")
    return result, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--families", help="comma-separated criterion families")
    args = parser.parse_args()
    expected, errors = expected_records(args.expected)
    assigned_cases, case_errors = case_ids(args.cases)
    errors.extend(case_errors)
    for case in sorted(assigned_cases - set(expected)):
        errors.append(f"missing expected case: {case}")
    for case in sorted(set(expected) - assigned_cases):
        errors.append(f"unexpected expected case: {case}")
    expected_contract_invalid = bool(errors)
    actual, actual_errors = validate_file(args.actual)
    errors.extend(f"actual {error}" for error in actual_errors)
    for case in sorted(set(actual) - set(expected)):
        errors.append(f"unexpected actual case: {case}")
    if expected_contract_invalid:
        print("IP hygiene eval: FAIL")
        for error in errors:
            print(error)
        return 1
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
        findings = got.get("findings", [])
        for group in wanted["required_code_groups"]:
            if not codes.intersection(group):
                errors.append(f"{case}: missing required finding code group: {' | '.join(group)}")
        for proposition in wanted.get("required_proposition_grounding", []):
            proposition_grounded = False
            for finding in findings:
                if not isinstance(finding, dict) or finding.get("code") not in proposition["codes"]:
                    continue
                condition_location = json.dumps(
                    {key: finding.get(key) for key in ("condition", "location")},
                    ensure_ascii=False,
                ).casefold()
                if any(
                    anchor_matches(anchor, condition_location)
                    for anchor in proposition["condition_location_anchors"]
                ):
                    proposition_grounded = True
                    break
            if not proposition_grounded:
                errors.append(
                    f"{case}: ungrounded required proposition: {' | '.join(proposition['codes'])}"
                )
        for code in codes - set(wanted["allowed_codes"]):
            errors.append(f"{case}: undeclared finding code: {code}")
        if wanted["expect"] == "no-finding" and codes:
            errors.append(f"{case}: forbidden clean-control finding")
        for finding in findings:
            if not isinstance(finding, dict) or finding.get("code") not in wanted["allowed_codes"]:
                continue
            allowed = wanted["allowed_classifications"][finding["code"]]
            classification = {key: finding.get(key) for key in CLASSIFICATION_KEYS}
            if classification not in allowed:
                errors.append(f"{case}: wrong classification for {finding['code']}")
            if finding.get("fact_status") == "fact":
                if is_legal_merits_proposition(finding.get("condition")):
                    errors.append(
                        f"{case}: legal-merits proposition must be inference for {finding['code']}"
                    )
                fact_anchors = wanted.get("fact_proposition_anchors", {}).get(
                    finding["code"], wanted["evidence_anchors"]
                )
                condition = finding.get("condition", "").casefold()
                if not any(anchor_matches(anchor, condition) for anchor in fact_anchors):
                    errors.append(
                        f"{case}: fact proposition lacks an accepted factual anchor for {finding['code']}"
                    )
        if got.get("lane") != wanted["lane"]:
            errors.append(f"{case}: wrong lane")
        outcome_field = {"triage": "triage_gate", "in-depth": "in_depth_verdict", "prospective": "prospective_decision"}[wanted["lane"]]
        if got.get(outcome_field) != wanted["outcome"]:
            errors.append(f"{case}: wrong lane outcome")
        if got.get("counsel_outcome") != wanted["counsel_outcome"]:
            errors.append(f"{case}: wrong counsel_outcome")
        if got.get("legal_clearance") is not False:
            errors.append(f"{case}: legal-clearance overclaim")
        anchors = wanted["evidence_anchors"]
        lane_grounding = json.dumps(
            {key: got.get(key) for key in (
                "reviewed_surface", "exclusions", "evidence", "limits", "decision_controls"
            ) if key in got},
            ensure_ascii=False,
        ).casefold()
        if not any(anchor_matches(anchor, lane_grounding) for anchor in anchors):
            errors.append(f"{case}: ungrounded lane evidence")
        for finding in got.get("findings", []):
            if not isinstance(finding, dict):
                continue
            finding_grounding = json.dumps(
                {key: finding.get(key) for key in (
                    "condition", "location", "source_provenance", "evidence"
                )},
                ensure_ascii=False,
            ).casefold()
            if not any(anchor_matches(anchor, finding_grounding) for anchor in anchors):
                errors.append(f"{case}: ungrounded finding: {finding.get('code', '<unknown>')}")
        whole_record = json.dumps(
            {key: value for key, value in got.items() if key != "case"},
            ensure_ascii=False,
        ).casefold()
        if not any(anchor_matches(anchor, whole_record) for anchor in anchors):
            errors.append(f"{case}: missing every evidence anchor: {' | '.join(anchors)}")
    print("IP hygiene eval: " + ("PASS" if not errors else "FAIL"))
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
