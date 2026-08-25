"""Every prose restatement of bounded-step-return-v1 must agree with the validator.

The return contract is stated once in `planning_ledger.py` and restated in seven
worker- and parent-facing documents. Nothing used to check the restatements, so
they drifted: blocker evidence was rendered as required when the validator makes
it optional, and this repo's `extensions/codex.md` adapter named a
`blocked:oversized` status that the schema has never had. Both reached a real
dispatch. This gate derives its expectations from the module
constants, so a restatement that contradicts the code fails here rather than in
a live run.
"""

import importlib.util
import inspect
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]
POLICY = REPO_ROOT / "souroldgeezer-policy"
SKILL = POLICY / "skills/planning-policy"
SCRIPT = SKILL / "references/scripts/planning_ledger.py"

SPEC = importlib.util.spec_from_file_location("ledger", SCRIPT)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(ledger)

# The four execution-tier agents are unpaired, so check-runtime-metadata-parity.py
# never derives or checks their bodies; the two adapters are the only worker-facing
# contract on their host. All seven restate the same schema.
AGENTS = tuple(sorted((POLICY / "agents").glob("plan-step-*.md")))
EXTENSIONS = (SKILL / "extensions/claude-code.md", SKILL / "extensions/codex.md")
REFERENCE = SKILL / "references/ledger-contract.md"
RESTATEMENTS = AGENTS + EXTENSIONS + (REFERENCE,)

WORD_FORMS = {8: ("8", "eight"), 32: ("32", "thirty-two"), 240: ("240",), 480: ("480",)}


def normalized(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def renderings(value: int) -> tuple[str, ...]:
    """Accepted spellings of a cap, derived from the constant itself."""
    return WORD_FORMS.get(value, (str(value),))


def states_cap(text: str, value: int, *nouns: str) -> bool:
    """True when the document ties the cap's value to one of its nouns nearby."""
    numbers = "|".join(re.escape(form) for form in renderings(value))
    subjects = "|".join(re.escape(noun) for noun in nouns)
    window = r"[^.]{0,80}?"
    return bool(
        re.search(rf"\b(?:{numbers})\b{window}(?:{subjects})", text, re.I)
        or re.search(rf"(?:{subjects}){window}\b(?:{numbers})\b", text, re.I)
    )


class ReturnStatusParityTest(unittest.TestCase):
    def test_every_restatement_names_exactly_the_validator_statuses(self):
        for path in RESTATEMENTS:
            text = normalized(path)
            with self.subTest(document=path.name):
                for status in ledger.RETURN_STATUSES:
                    self.assertIn(status, text, f"{path.name} omits status {status!r}")

    def test_no_restatement_invents_a_blocked_prefixed_status(self):
        """`oversized` is a status; `blocked:` prefixes name blocker codes.

        This repo's `extensions/codex.md` shipped `blocked:oversized`, which no
        valid return can carry, so a worker obeying it never reached the
        terminal path.
        """
        for path in RESTATEMENTS:
            text = normalized(path)
            for status in ledger.RETURN_STATUSES:
                token = f"blocked:{status}"
                with self.subTest(document=path.name, token=token):
                    self.assertNotIn(token, text, f"{path.name} invents status {token!r}")

    def test_note_types_match_the_validator(self):
        for path in RESTATEMENTS:
            text = normalized(path)
            with self.subTest(document=path.name):
                for note_type in ledger.NOTE_TYPES:
                    self.assertIn(note_type, text, f"{path.name} omits note type {note_type!r}")


class EvidencePairParityTest(unittest.TestCase):
    """Blocker and acceptance evidence are optional paired fields.

    `valid_return` accepts a blocker carrying neither `evidence_path` nor
    `sha256`, and `rel()` rejects an empty path — so a stop with no evidence
    artifact (`oversized`, `blocked:missing_input`) must omit both. Prose that
    calls the pair mandatory is unsatisfiable for exactly those stops.
    """

    def test_validator_treats_blocker_evidence_as_optional(self):
        """Pin the behaviour the documents must describe."""
        leaf = {"write_set": ["src"], "acceptance_command": "cmd"}
        step = {"id": "s", "attempt_id": "a", "agent_id": "g"}
        value = {
            "schema": "bounded-step-return-v1",
            "step_id": "s",
            "attempt_id": "a",
            "agent_id": "g",
            "status": "oversized",
            "changed_paths": [],
            "acceptance": {"command": "cmd", "exit_code": None, "summary": ""},
            "blockers": [{"code": "scope", "summary": "too large"}],
            "notes": [],
            "unstarted_remainder": ["next"],
            "commit_hash": "",
        }
        self.assertEqual(value, ledger.valid_return(value, {}, step, leaf))

    def test_no_type_literal_renders_blocker_evidence_as_required(self):
        """A `"evidence_path": string` literal without `?` reads as mandatory."""
        for path in RESTATEMENTS:
            text = normalized(path)
            with self.subTest(document=path.name):
                self.assertNotRegex(
                    text,
                    r'"evidence_path"\s*:\s*string',
                    f"{path.name} renders blocker evidence as a required field",
                )

    def test_every_restatement_marks_the_evidence_pair_optional(self):
        for path in RESTATEMENTS:
            text = normalized(path)
            with self.subTest(document=path.name):
                self.assertRegex(
                    text,
                    r"optional[^.]{0,120}(?:evidence|paired)|(?:evidence|pair)[^.]{0,120}optional",
                    f"{path.name} never calls the evidence pair optional",
                )


class CommitHashParityTest(unittest.TestCase):
    """Changed work is attributable to a commit whatever the status.

    A non-completed stop that edited files used to validate with an empty
    `commit_hash`, which is how a real oversize stop left its partial work
    uncommitted in a worktree the parent had no lane to dispose of.
    """

    def test_validator_rejects_changed_paths_without_a_commit_hash(self):
        leaf = {"write_set": ["src"], "acceptance_command": "cmd"}
        step = {"id": "s", "attempt_id": "a", "agent_id": "g"}
        base = {
            "schema": "bounded-step-return-v1",
            "step_id": "s",
            "attempt_id": "a",
            "agent_id": "g",
            "changed_paths": ["src/x.py"],
            "acceptance": {"command": "cmd", "exit_code": 1, "summary": ""},
            "blockers": [{"code": "scope", "summary": "too large"}],
            "notes": [],
            "commit_hash": "",
        }
        for status, remainder in (("oversized", ["next"]), ("failed", []), ("blocked", [])):
            with self.subTest(status=status):
                value = dict(base, status=status, unstarted_remainder=remainder)
                with self.assertRaises(ledger.Error):
                    ledger.valid_return(value, {}, step, leaf)
                value = dict(value, commit_hash="a" * 40)
                self.assertEqual(value, ledger.valid_return(value, {}, step, leaf))

    def test_every_restatement_extends_the_commit_rule_beyond_completed(self):
        for path in RESTATEMENTS:
            text = normalized(path)
            with self.subTest(document=path.name):
                self.assertRegex(
                    text,
                    r"(?:any other status|every status|whatever its status)",
                    f"{path.name} still ties the commit hash to `completed` alone",
                )


class BoundedCapParityTest(unittest.TestCase):
    CAPS = (
        ("MAX_CHANGED_PATHS", ("changed", "path")),
        ("MAX_BLOCKERS", ("blocker",)),
        ("MAX_NOTES", ("note",)),
        ("MAX_REMAINDER", ("remainder",)),
        ("MAX_BLOCKER_SUMMARY", ("summary", "remainder", "character")),
        ("MAX_ACCEPTANCE_SUMMARY", ("summary", "character")),
    )

    def test_documents_state_the_validator_caps(self):
        for path in RESTATEMENTS:
            text = normalized(path)
            for name, nouns in self.CAPS:
                value = getattr(ledger, name)
                with self.subTest(document=path.name, cap=name):
                    self.assertTrue(
                        states_cap(text, value, *nouns),
                        f"{path.name} does not state {name}={value} near {nouns}",
                    )

    def test_documents_state_the_return_size_bound(self):
        kib = ledger.MAX_RETURN // 1024
        for path in RESTATEMENTS:
            text = normalized(path)
            with self.subTest(document=path.name):
                self.assertRegex(
                    text,
                    rf"\b{kib}\s*KiB",
                    f"{path.name} does not state the {kib} KiB return bound",
                )


class NextBlockScopeParityTest(unittest.TestCase):
    """The doc's claim about which commands emit a live `next` block must match code.

    This repo's own plan for the `next` feature assumed `TRANS` was the general
    v2-v4 state machine and that `transition` could derive a legal-successor
    block from it. It is not: `TRANS`'s keys equal `V1_STATES` exactly, it has
    one call site (`transition1()`, the v1-only path), and using it for v2-v4
    would misreport every stage and raise `KeyError` on the `cleaned`
    transition. The doc was drafted once on that wrong premise before being
    corrected. This gate derives the actual emitter set from
    `planning_ledger.py`'s own source, so a future change that starts (or
    stops) a command emitting `next` — or a doc edit that re-claims a command
    the code does not cover — fails here instead of drifting back to the same
    wrong claim in a live run.
    """

    NEXT_EMIT_CANDIDATES = {
        "init4": "init-v4",
        "record": "record-return",
        "transition2": "transition",
        "close2": "close",
        "reopen2": "reopen",
        "validate": "validate --closeout",
    }

    @staticmethod
    def _emits_next(function_name):
        source = inspect.getsource(getattr(ledger, function_name))
        return "bounded_next(" in source or "next_after_return(" in source

    def test_code_derived_emitters_are_exactly_init_v4_and_record_return(self):
        """Pin the current, intentional scope so a silent expansion is visible."""
        emitters = {
            cli
            for name, cli in self.NEXT_EMIT_CANDIDATES.items()
            if self._emits_next(name)
        }
        self.assertEqual({"init-v4", "record-return"}, emitters)

    def test_ledger_contract_names_every_code_derived_emitter(self):
        text = normalized(REFERENCE)
        for name, cli in self.NEXT_EMIT_CANDIDATES.items():
            if self._emits_next(name):
                with self.subTest(command=cli):
                    self.assertIn(
                        cli,
                        text,
                        f"ledger-contract.md never names {cli!r} as next-emitting, "
                        "but planning_ledger.py's own source shows it is",
                    )

    def test_ledger_contract_does_not_claim_trans_governs_v2_plus(self):
        # A plain char-count window, not `states_cap`'s `[^.]` window: the doc
        # names `planning_ledger.py` near this claim, and that literal period
        # would otherwise cut the window short before reaching `V1_STATES`.
        text = normalized(REFERENCE)
        self.assertRegex(
            text,
            r"TRANS.{0,200}?\bV1_STATES\b",
            "ledger-contract.md must state TRANS's keys equal V1_STATES (v1-only)",
        )
        self.assertNotRegex(
            text,
            r"TRANS.{0,120}?\bsole source of truth\b",
            "ledger-contract.md must not claim TRANS is authoritative for v2-v4 transitions "
            "(it governs only the legacy v1 transition1() path)",
        )


if __name__ == "__main__":
    unittest.main()
