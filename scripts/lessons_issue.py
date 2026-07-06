#!/usr/bin/env python3
"""Pure rendering core for the lesson loop's GitHub-issue store.

Replaces the removed local JSONL ledger (scripts/lessons_ledger.py). The
lesson-capture skill turns one captured Layer-2 lesson into a `lesson-candidate`
GitHub issue; this module holds the deterministic, network-free part — the issue
title, body (with a hidden dedup fingerprint and a per-substrate Definition of
Done), and labels — so it is unit-testable in isolation. The skill owns the
judgment, the secret scan, and the GitHub calls. Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys

SUBSTRATES = ("deterministic", "policy", "prose")
CANDIDATE_LABEL = "lesson-candidate"


class LessonIssueError(ValueError):
    """Raised for any invalid lesson-issue field."""


_COMMON_DOD = (
    "- Apply the rule in clean words — never commit secrets or verbatim untrusted "
    "session/file text.\n"
    "- Secret-scan the staged diff before committing: "
    "`git diff --cached | python3 scripts/lessons_secret_scan.py --diff` must print "
    "nothing (the `DSO-POS-9` control).\n"
    "- Graduate on **`main`**. If a published `souroldgeezer-*` surface changed, apply "
    "CalVer stamp + manifest/marketplace/README sync + IP-hygiene per `CLAUDE.md`; "
    "repo-internal edits need no stamp.\n"
    "- Close **as completed** when applied (comment where it landed); close **as not "
    "planned** if rejected (one-line reason)."
)

_SUBSTRATE_DOD = {
    "deterministic": (
        "- Add a `SAC-T#####` fixture via "
        "`tests/generate_skill_architecture_report_ledger.py` and regenerate the JSONL "
        "— **only if the report engine already detects this smell**. Never hand-edit "
        "`tests/skill_architecture_report_ledger.jsonl`; never fake a passing test. If "
        "new detection is needed, record it as engine work and close **as not planned** "
        "rather than fake a fixture.\n"
        "- Suite green: `uv run python -m unittest discover -s tests -p '*_test.py'`."
    ),
    "policy": "- Land as a terse policy line / smell code in the most-specific home.",
    "prose": (
        "- Land as a `CLAUDE.md` / skill-text line in the most-specific home "
        "(last resort — it taxes every future session)."
    ),
}


def validate(*, trigger, proposed_rule, substrate) -> None:
    """Raise LessonIssueError unless the core fields are well-formed."""
    if substrate not in SUBSTRATES:
        raise LessonIssueError(f"invalid substrate: {substrate!r}")
    for name, value in (("trigger", trigger), ("proposed_rule", proposed_rule)):
        if not isinstance(value, str) or not value.strip():
            raise LessonIssueError(f"{name} must be a non-empty string")


def fingerprint(*, substrate: str, proposed_rule: str) -> str:
    """Content dedup key: sha256 over substrate + the proposed rule (16 hex chars)."""
    basis = json.dumps(
        {"substrate": substrate, "proposed_rule": proposed_rule},
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def labels(*, substrate: str) -> list[str]:
    """The label set for a lesson-candidate issue of this substrate."""
    return [CANDIDATE_LABEL, f"lesson:{substrate}"]


def render_body(*, trigger, proposed_rule, substrate) -> str:
    """Render the canonical, human-readable issue body with the dedup marker + DoD."""
    fp = fingerprint(substrate=substrate, proposed_rule=proposed_rule)
    return (
        f"<!-- lesson-fp:{fp} -->\n\n"
        f"**Trigger:** {trigger}\n\n"
        f"**Proposed rule:** {proposed_rule}\n\n"
        f"**Substrate:** {substrate}\n\n"
        f"**Layer:** 2\n\n"
        f"## Definition of Done\n\n"
        f"{_COMMON_DOD}\n\n"
        f"{_SUBSTRATE_DOD[substrate]}\n"
    )


def build(*, trigger, summary, proposed_rule, substrate) -> dict:
    """Return title/labels/fingerprint/body — everything the skill needs to create."""
    validate(trigger=trigger, proposed_rule=proposed_rule, substrate=substrate)
    summary = summary if isinstance(summary, str) else ""
    title = summary.strip() or proposed_rule.strip()
    return {
        "title": title,
        "labels": labels(substrate=substrate),
        "fingerprint": fingerprint(substrate=substrate, proposed_rule=proposed_rule),
        "body": render_body(trigger=trigger, proposed_rule=proposed_rule,
                            substrate=substrate),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="lessons_issue")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="print issue title/labels/fingerprint/body as JSON")
    b.add_argument("--trigger", required=True)
    b.add_argument("--summary", default="")
    b.add_argument("--proposed-rule", required=True, dest="proposed_rule")
    b.add_argument("--substrate", required=True, choices=SUBSTRATES)
    args = parser.parse_args(argv)
    try:
        result = build(trigger=args.trigger, summary=args.summary,
                       proposed_rule=args.proposed_rule, substrate=args.substrate)
    except LessonIssueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
