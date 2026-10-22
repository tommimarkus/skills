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
import re
import unittest
from pathlib import Path

from tests.planning_ledger_dispatch_test import leaf
from tests.planning_ledger_verify_test import VerifyHarness

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

    def test_wrappers_gate_binding_and_work_unit_context_on_v5_only(self):
        for path in AGENTS:
            text = normalized(path)
            with self.subTest(document=path.name):
                self.assertIn("Assignments use v5", text)
                self.assertNotIn("v1–v", text)
                self.assertNotIn("v4–v5", text)
                self.assertNotIn("report its raw output", text)

    def test_codex_handoff_gates_binding_and_decomposition_on_v5_only(self):
        text = normalized(SKILL / "extensions/codex.md")
        self.assertIn("v5", text)
        self.assertNotIn("v1–v", text)
        self.assertNotIn("v4–v5", text)

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


class NextBlockScopeParityTest(VerifyHarness):
    """The doc's claim about which commands emit a live `next` block must match behavior.

    The doc was once drafted on a wrong premise about which commands emit `next`.
    This gate runs each candidate command against fixture runs and records which
    results actually carry a `next` block, so a command that starts (or stops)
    emitting one, or a doc edit that re-claims a command the ledger does not
    cover, fails here instead of drifting back into a live run. A source-text
    heuristic once pinned only three emitters and missed the ones that build
    their block through helper functions.
    """

    NEXT_EMIT_CANDIDATES = {
        "init-v5": "init-v5",
        "transition": "transition",
        "record-return": "record-return",
        "record-verify": "record-verify",
        "close": "close",
        "reopen": "reopen",
        "validate": "validate --closeout",
    }
    EXPECTED_EMITTERS = {
        "init-v5", "transition", "record-return", "record-verify", "reopen", "validate --closeout",
    }

    def observed_emitters(self):
        """Run the candidates over three fresh runs; return the commands whose result has `next`."""
        seen = {}

        def run(name, *arguments):
            code, result = self.call(*arguments)
            self.assertEqual(0, code, (name, result))
            seen[self.NEXT_EMIT_CANDIDATES[name]] = "next" in result
            return result

        def actor(*arguments):
            return (*arguments[:1], "--actor", "parent", "--run-id", self.run_id, *arguments[1:])

        # Fresh run: init-v5, then a pending step becomes ready.
        seen["init-v5"] = "next" in self.init([leaf("alpha", "leaf-alpha")])
        run("transition", *actor("transition", "--step-id", "alpha", "--to", "ready", "--agent-id", "w"))

        # Verified run: record-return, record-verify, validate --closeout, close completed.
        self.setUp()
        packet, returned = self.completed()
        seen["record-return"] = "next" in returned
        _, issued = self.verify_handoff()
        (verify,) = issued["handoffs"]
        run("record-verify", *actor("record-verify", "--return-file", str(self.verify_return(verify))))
        landed_code, landed = self.land()
        self.assertEqual(0, landed_code, landed)
        run("validate", "validate", "--run-id", self.run_id, "--closeout")
        run("close", *actor("close", "--outcome", "completed"))

        # Retryable failure: close blocked, then reopen.
        self.setUp()
        packet = self.started()
        self.commit_file("src/alpha/a.txt", "x\n")
        blocker = {"code": "failed:acceptance", "summary": "acceptance failed"}
        self.returned(packet, "failed", blockers=[blocker])
        run("close", *actor("close", "--outcome", "blocked", "--reason", "stuck"))
        run("reopen", *actor("reopen", "--reason", "retry"))
        return {cli for cli, emitted in seen.items() if emitted}

    def test_behavioral_emitters_are_exactly_the_pinned_set(self):
        """Pin the current scope so a silent expansion or loss is visible; `close` is terminal."""
        self.assertEqual(self.EXPECTED_EMITTERS, self.observed_emitters())

    def test_ledger_contract_names_every_behavioral_emitter(self):
        text = normalized(REFERENCE)
        for cli in sorted(self.observed_emitters()):
            with self.subTest(command=cli):
                self.assertIn(
                    cli,
                    text,
                    f"ledger-contract.md never names {cli!r} as next-emitting, "
                    "but a live run shows it is",
                )


class ReferencedReturnCodeParityTest(unittest.TestCase):
    """Guidance may only name a return code the ledger registers or a script emits."""

    CODE = re.compile(r"\b(?:blocked|failed|oversized):[a-z][a-z0-9_]*")
    EMITTER_SCRIPTS = (
        SCRIPT,
        *sorted((SCRIPT.parent / "planningledger").glob("*.py")),
        SKILL / "references/scripts/validate_plan_contract.py",
        SKILL / "references/scripts/persist_plan.py",
        REPO_ROOT / "scripts/planning_policy_forward_eval.py",
    )

    @classmethod
    def allowed(cls) -> set[str]:
        codes = {code for family in ledger.RETURN_CODES.values() for code in family}
        for script in cls.EMITTER_SCRIPTS:
            codes.update(cls.CODE.findall(script.read_text(encoding="utf-8")))
        return codes

    @staticmethod
    def scanned() -> list[Path]:
        paths = set(POLICY.glob("**/*.md"))
        paths.update((SKILL / "references/evals").glob("*.jsonl"))
        paths.update(
            path
            for path in (REPO_ROOT / "tests/planning_policy_forward").rglob("*")
            if path.is_file()
        )
        paths.update((REPO_ROOT / "CLAUDE.md", REPO_ROOT / "AGENTS.md"))
        return sorted(paths)

    def test_allowed_set_derives_from_the_registry(self):
        allowed = self.allowed()
        self.assertTrue({"blocked:environment", "failed:execution", "oversized:scope"} <= allowed)
        self.assertNotIn("blocked:oversized", allowed)

    def test_every_named_return_code_is_registered_or_emitted(self):
        allowed = self.allowed()
        unknown = {}
        for path in self.scanned():
            text = path.read_text(encoding="utf-8")
            for code in sorted(set(self.CODE.findall(text)) - allowed):
                unknown.setdefault(code, []).append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(
            {},
            unknown,
            "return code named in guidance but neither registered in RETURN_CODES "
            "nor emitted by a planning script",
        )


if __name__ == "__main__":
    unittest.main()
