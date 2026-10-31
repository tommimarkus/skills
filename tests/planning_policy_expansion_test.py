"""Behavior of the deterministic plan expander behind expand_plan.py."""

import contextlib
import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import (
    REPO_ROOT,
    capability_binding_document,
    load_script_module,
    worktree_result,
)

SCRIPTS = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts"
EXPAND = SCRIPTS / "expand_plan.py"
LEDGER = SCRIPTS / "planning_ledger.py"
VALIDATE = SCRIPTS / "validate_plan_contract.py"
FIXTURES = Path(__file__).resolve().parent / "planning_policy_expansion"
TEMPLATE = FIXTURES / "template.json"
INDEX = FIXTURES / "index.jsonl"
STUB_PREDECESSOR = {
    "plan_id": "rule-plan-1",
    "run_id": "11111111-1111-4111-8111-111111111111",
    "plan_sha256": "0" * 64,
    "outcome": "blocked",
    "handoff_sha256": "a" * 64,
}

sys.path.insert(0, str(SCRIPTS))
from planningledger import core, expand, plancontract  # noqa: E402

LEDGER_MODULE = load_script_module("planning_ledger_expansion_shim", LEDGER)


def run(script, *arguments):
    return subprocess.run(
        [sys.executable, "-B", str(script), *map(str, arguments)], capture_output=True
    )


def jsonl(rows):
    return "".join(json.dumps(row) + "\n" for row in rows)


class ExpansionCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.template = json.loads(TEMPLATE.read_text())
        self.rows = [json.loads(line) for line in INDEX.read_text().splitlines()]

    def files(self, template=None, rows=None, index_text=None):
        template_path = self.root / "template.json"
        index_path = self.root / "index.jsonl"
        template_path.write_text(json.dumps(self.template if template is None else template))
        if index_text is None:
            index_text = jsonl(self.rows if rows is None else rows)
        index_path.write_text(index_text)
        return ["--template", template_path, "--index", index_path]

    def expand(self, command, *extra, **variant):
        return run(EXPAND, command, *self.files(**variant), *extra)

    def refused(self, result, code, fragment):
        self.assertEqual(code, result.returncode, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["ok"])
        self.assertIn(fragment, "\n".join(report["errors"]))
        self.assertEqual(b"", result.stderr)

    def plain_template(self, max_leaves=12, **types):
        def simple(**fields):
            return {
                "task": "Make {id}", "boundary": "Only touch out/{id}.txt.",
                "write_set": ["out/{id}.txt"], "read_set_extra": [],
                "acceptance_command": "uv run python -m unittest tests.check_{id}",
                "size": "small", "portable_tier": "mechanical", "max_attempts": 2,
                "settled_decisions": {"mode": "plain"},
                "capability_requirements": {"baseline": "plan-step-base-v1", "additional": []},
                "batch": True, **fields,
            }

        return {
            "schema": "planning-expansion-template-v1", "objective": "Plain objective",
            "scope_summary": "Plain scope", "approved_decisions": ["Plain decision."],
            "series": {"series_id": "plain-series", "max_leaves": max_leaves,
                       "end_verification_commands": ["uv run python -m unittest tests.plain"]},
            "owner_prefix": "p/",
            "types": {name: simple(**fields) for name, fields in (types or {"unit": {}}).items()},
        }

    @staticmethod
    def plain_rows(*specs):
        """Rules from (id, type[, deps]) triples, each with a unique spec path."""
        return [{"id": i, "type": t, "deps": list(rest[0]) if rest else [],
                 "spec": f"specs/{i}.md", "refs": []} for i, t, *rest in specs]

    def plain_slice(self, template, rows, number=1):
        template_path, index_path = self.root / "t.json", self.root / "i.jsonl"
        template_path.write_text(json.dumps(template))
        index_path.write_text(jsonl(rows))
        parsed = expand.load_template(template_path)
        expansion = expand.build(parsed, expand.load_index(index_path, parsed))
        return expand.emit_slice(expansion, number, None if number == 1 else STUB_PREDECESSOR)

    def partition(self):
        result = run(EXPAND, "partition", "--template", TEMPLATE, "--index", INDEX)
        self.assertEqual(0, result.returncode, result.stderr)
        return result

    def validate_files(self, *plans):
        repository = self.root / "repository"
        (repository / "tests").mkdir(parents=True, exist_ok=True)
        (repository / "tests" / "notes.txt").write_text("nothing here pins a written path\n")
        for plan in plans:
            result = run(
                VALIDATE, "validate", plan, "--pin-roots", "tests", "--repo-root", repository
            )
            report = json.loads(result.stdout)
            self.assertEqual((0, True, []), (result.returncode, report["valid"], report["errors"]))
            scan = report["pin_scan"]
            self.assertEqual((["tests"], [], {}), (scan["roots"], scan["roots_missing"], scan["leaves"]))


class FixturePartitionAndGoldenTest(ExpansionCase):
    def test_partition_summary_is_exact_and_deterministic(self):
        first = self.partition()
        self.assertEqual(first.stdout, self.partition().stdout)
        summary = json.loads(first.stdout)
        generator = core.digest(
            {
                "expander": "planning-plan-expander-v1",
                "template": self.template,
                "index": self.rows,
            }
        )
        self.assertEqual(
            {
                "schema": "planning-expansion-partition-v1",
                "generator_sha256": generator,
                "series_id": "rule-series",
                "rule_count": 10,
                "slice_count": 2,
                "exemplars": {"doc": "d2", "unit": "u1"},
                "slices": [
                    {"slice": 1, "final": False, "leaf_count": 6,
                     "ids": ["d2", "u1", "d1", "u2", "u3", "u4"]},
                    {"slice": 2, "final": True, "leaf_count": 4, "ids": ["u5", "d3", "u6", "u7"]},
                ],
            },
            summary,
        )
        self.assertEqual(core.canon(summary), first.stdout.rstrip(b"\n"))
        changed = copy.deepcopy(self.rows)
        changed[-1]["refs"] = ["specs/other.md"]
        other = json.loads(self.expand("partition", rows=changed).stdout)
        self.assertNotEqual(generator, other["generator_sha256"])

    def test_slice_one_matches_its_golden_and_is_byte_stable(self):
        arguments = ("slice", "--template", TEMPLATE, "--index", INDEX, "--slice", 1)
        first = run(EXPAND, *arguments)
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(first.stdout, run(EXPAND, *arguments).stdout)
        golden = json.loads((FIXTURES / "expected-slice-1.json").read_text())
        self.assertEqual(golden, json.loads(first.stdout))
        self.assertEqual(core.canon(golden) + b"\n", first.stdout)
        leaves = {leaf["id"]: leaf for leaf in golden["leaves"]}
        self.assertEqual({"u2", "u3", "u4"}, {i for i, x in leaves.items() if "batch" in x})
        self.assertEqual({"mechanical"}, {leaves[i]["portable_tier"] for i in ("u2", "u3", "u4")})
        self.assertEqual("analytical", leaves["d2"]["portable_tier"])
        self.assertIn("u1", leaves["u3"]["dependencies"])
        self.assertTrue(plancontract.validate(golden, admission=True)["valid"])

    def test_slice_two_emitted_with_the_stub_predecessor_matches_its_golden(self):
        plan = expand_slice_two(self, STUB_PREDECESSOR)
        golden = json.loads((FIXTURES / "expected-slice-2.json").read_text())
        self.assertEqual(STUB_PREDECESSOR, golden["series"]["predecessor"])
        self.assertEqual(golden, plan)
        self.assertEqual(core.canon(golden), core.canon(plan))
        followers = {leaf["id"]: leaf for leaf in golden["leaves"]}
        self.assertEqual([], followers["u5"]["dependencies"])
        self.assertEqual([], followers["d3"]["dependencies"])
        self.assertEqual(["d3"], followers["u7"]["dependencies"])
        self.assertEqual(
            "follow the pattern exemplar u1 landed in src/u1.py; do not re-derive it",
            followers["u7"]["settled_decisions"]["exemplar_pattern"],
        )
        # u7 has an in-slice dependency (d3) its predecessor u6 lacks, so no batch forms.
        self.assertEqual([], [i for i, leaf in followers.items() if "batch" in leaf])

    def test_every_emitted_and_golden_slice_passes_the_validator_with_pin_roots(self):
        emitted = self.root / "slice-1.json"
        result = run(
            EXPAND, "slice", "--template", TEMPLATE, "--index", INDEX, "--slice", 1,
            "--out", emitted,
        )
        report = json.loads(result.stdout)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(core.digest(json.loads(emitted.read_bytes())), report["plan_sha256"])
        self.assertEqual(
            {"ok": True, "slice": 1, "final": False, "plan_sha256": report["plan_sha256"],
             "out": str(emitted)},
            report,
        )
        self.validate_files(emitted, FIXTURES / "expected-slice-1.json",
                            FIXTURES / "expected-slice-2.json")


def expand_slice_two(case, predecessor):
    """Slice 2 of the fixture through the public API, with the given predecessor block."""
    template = expand.load_template(TEMPLATE)
    expansion = expand.build(template, expand.load_index(INDEX, template))
    plan = expand.emit_slice(expansion, 2, predecessor)
    case.assertTrue(plancontract.validate(plan, admission=True)["valid"])
    return plan


class LedgerSeriesTest(ExpansionCase):
    """Slices chained through the real ledger: only a completed, matching chain is followed."""

    def setUp(self):
        super().setUp()
        self.template["verification"] = "closeout-only"
        self.template["types"]["unit"]["batch"] = False
        self.template["series"]["max_leaves"] = 4

    def common(self):
        return ["--ledger-root", str(self.root), "--repo-root", str(self.root)]

    def ledger_call(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = LEDGER_MODULE.main([*self.common(), *map(str, arguments)])
        return code, json.loads(stream.getvalue())

    def ledger(self, *arguments):
        code, result = self.ledger_call(*arguments)
        self.assertEqual(0, code, result)
        return result

    def emit(self, number, name, *extra, template=None, rows=None):
        path = self.root / f"{name}.json"
        result = run(
            EXPAND, "slice", *self.files(template=template, rows=rows), "--slice", number,
            "--out", path, *self.common(), *extra,
        )
        return result, path

    def emit_ok(self, number, name, *extra, **variant):
        result, path = self.emit(number, name, *extra, **variant)
        self.assertEqual(0, result.returncode, result.stdout)
        return path

    def api_slice(self, number, name, predecessor):
        """A slice built through the API, for a predecessor the CLI would refuse."""
        _, template_path, _, index_path = self.files()
        template = expand.load_template(template_path)
        expansion = expand.build(template, expand.load_index(index_path, template))
        path = self.root / f"{name}.json"
        path.write_bytes(core.canon(expand.emit_slice(expansion, number, predecessor)))
        return path

    def init(self, plan_id, path):
        plan = json.loads(path.read_text())
        binding = self.root / f"{plan_id}-binding.json"
        binding.write_text(json.dumps(capability_binding_document(plan, "fixture")))
        assignments = self.root / f"{plan_id}-assignments.json"
        assignments.write_text(json.dumps([
            {"id": leaf["id"], "harness": "codex", "model_or_alias": "gpt-5.6-terra",
             "effort": "medium", "worktree": self.worktree(leaf)}
            for leaf in plan["leaves"]
        ]))
        return self.ledger(
            "--plan-id", plan_id, "init-v5", "--actor", "parent", "--approved",
            "--plan-file", path, "--assignments-file", assignments,
            "--capability-binding-file", binding, "--pin-roots", "tests",
        )

    @staticmethod
    def worktree(leaf):
        return f".worktrees/{leaf['worktree_owner'].replace('/', '-')}"

    def checkpoint(self, plan_id, run_id):
        path = self.root / "planning-policy/ledgers" / plan_id / run_id / "checkpoint.json"
        return json.loads(path.read_text())

    def drive(self, plan_id, run_id, plan):
        """Move every leaf, in plan order, to cleaned so a completed close is admissible."""
        for leaf in plan["leaves"]:
            step_id = leaf["id"]
            for target in ("ready", "in_progress"):
                arguments = ["transition", "--actor", "parent", "--run-id", run_id,
                             "--step-id", step_id, "--to", target]
                if target == "ready":
                    arguments += ["--agent-id", f"agent-{step_id}"]
                self.ledger("--plan-id", plan_id, *arguments)
            step = self.checkpoint(plan_id, run_id)["steps"][step_id]
            returned = self.root / f"{plan_id}-{step_id}-return.json"
            returned.write_text(json.dumps({
                "schema": "bounded-step-return-v1", "step_id": step_id,
                "attempt_id": step["attempt_id"], "agent_id": step["agent_id"],
                "status": "completed", "changed_paths": [],
                "acceptance": {"command": leaf["acceptance_command"], "exit_code": 0,
                               "summary": "ok"},
                "blockers": [], "notes": [], "unstarted_remainder": [], "commit_hash": "",
            }))
            self.ledger("--plan-id", plan_id, "record-return", "--actor", "parent",
                        "--run-id", run_id, "--return-file", returned)
            for target, action in (("integrated", "integrate"), ("cleaned", "cleanup")):
                value = worktree_result(
                    action, self.root, leaf["worktree_owner"], self.root / self.worktree(leaf)
                )
                result = self.root / f"{plan_id}-{step_id}-{action}.json"
                result.write_text(json.dumps(value))
                self.ledger("--plan-id", plan_id, "transition", "--actor", "parent",
                            "--run-id", run_id, "--step-id", step_id, "--to", target,
                            "--worktree-result", result)

    def close(self, plan_id, run_id, outcome, final=False):
        arguments = ["--plan-id", plan_id, "close", "--actor", "parent", "--run-id", run_id,
                     "--outcome", outcome, "--reason", "fixture"]
        if not final:
            content = self.root / f"{plan_id}-handoff.json"
            content.write_bytes(core.canon({
                "landed": ["the slice landed"], "decisions": ["exemplars landed first"],
                "assumptions_to_revalidate": ["style guide is stable"],
                "remaining_scope": ["the next slice"],
            }))
            arguments += ["--series-handoff-file", content]
        return self.ledger(*arguments)

    def run_slice(self, plan_id, path, outcome="completed", final=False):
        """Init a slice, drive it to cleaned when completing, and close it."""
        run_id = self.init(plan_id, path)["run_id"]
        if outcome == "completed":
            self.drive(plan_id, run_id, json.loads(path.read_text()))
        self.close(plan_id, run_id, outcome, final)
        return run_id

    def ledger_bytes(self):
        return {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and "planning-policy" in path.parts
        }

    def predecessor_flags(self, plan_id, run_id):
        return ("--predecessor-plan-id", plan_id, "--predecessor-run-id", run_id)

    def refuse_successor(self, number, plan_id, run_id, fragment, **variant):
        result, _ = self.emit(
            number, f"refused-{number}", *self.predecessor_flags(plan_id, run_id), **variant
        )
        self.refused(result, 1, fragment)

    def test_a_three_slice_series_chains_through_completed_predecessors(self):
        first = self.emit_ok(1, "slice-1")
        run_one = self.run_slice("rule-plan-1", first)
        before = self.ledger_bytes()
        second = self.emit_ok(2, "slice-2", *self.predecessor_flags("rule-plan-1", run_one))
        self.assertEqual(before, self.ledger_bytes())
        checkpoint = self.checkpoint("rule-plan-1", run_one)
        self.assertEqual(
            {"plan_id": "rule-plan-1", "run_id": run_one, "plan_sha256": checkpoint["plan_hash"],
             "outcome": "completed", "handoff_sha256": checkpoint["series_handoff_sha256"]},
            json.loads(second.read_text())["series"]["predecessor"],
        )
        self.assertEqual(checkpoint["plan_hash"], core.digest(json.loads(first.read_text())))
        run_two = self.run_slice("rule-plan-2", second)
        third = self.emit_ok(3, "slice-3", *self.predecessor_flags("rule-plan-2", run_two))
        plan = json.loads(third.read_text())
        self.assertEqual(
            (run_two, ["u6", "u7"], True),
            (plan["series"]["predecessor"]["run_id"], [x["id"] for x in plan["leaves"]],
             plan["series"]["final"]),
        )
        self.assertEqual("matched", self.init("rule-plan-3", third)["series_predecessor"])
        self.validate_files(first, second, third)

    def test_a_blocked_predecessor_is_refused_with_the_hand_groom_pointer(self):
        run_one = self.run_slice("rule-plan-1", self.emit_ok(1, "slice-1"), "blocked")
        self.refuse_successor(
            2, "rule-plan-1", run_one,
            "predecessor slice 1 closed blocked, not completed; later slices assume its rules "
            "landed, so hand-groom the successor per plan-series.md "
            "'Successor on a blocked predecessor'",
        )

    def test_an_ancestor_that_is_not_completed_is_refused(self):
        first = self.emit_ok(1, "slice-1")
        run_one = self.run_slice("rule-plan-1", first, "blocked")
        checkpoint = self.checkpoint("rule-plan-1", run_one)
        block = {"plan_id": "rule-plan-1", "run_id": run_one,
                 "plan_sha256": checkpoint["plan_hash"], "outcome": "blocked",
                 "handoff_sha256": checkpoint["series_handoff_sha256"]}
        second = self.api_slice(2, "slice-2", block)
        run_two = self.run_slice("rule-plan-2", second)
        self.refuse_successor(
            3, "rule-plan-2", run_two, "predecessor slice 1 closed blocked, not completed"
        )

    def test_a_predecessor_of_another_series_or_slice_is_refused(self):
        run_one = self.run_slice("rule-plan-1", self.emit_ok(1, "slice-1"))
        flags = self.predecessor_flags("rule-plan-1", run_one)
        other = copy.deepcopy(self.template)
        other["series"]["series_id"] = "other-series"
        self.refuse_successor(
            2, "rule-plan-1", run_one,
            "predecessor slice 1 belongs to series rule-series, not other-series", template=other,
        )
        second = self.emit_ok(2, "slice-2", *flags)
        run_two = self.run_slice("rule-plan-2", second)
        self.refuse_successor(2, "rule-plan-2", run_two, "predecessor slice 1 is recorded as slice 2")

    def test_a_grown_index_or_a_final_predecessor_is_refused(self):
        run_one = self.run_slice("rule-plan-1", self.emit_ok(1, "slice-1"))
        flags = self.predecessor_flags("rule-plan-1", run_one)
        grown = [{"id": "d0", "type": "doc", "deps": [], "spec": "specs/d0.md", "refs": []},
                 *self.rows]
        self.refuse_successor(
            2, "rule-plan-1", run_one,
            "predecessor slice 1 does not match this partition (index changed?)", rows=grown,
        )
        short = [row for row in self.rows if row["id"] in {"d1", "d2", "u1", "u2"}]
        final_run = self.run_slice("rule-plan-9", self.emit_ok(1, "short", rows=short), final=True)
        self.refuse_successor(
            2, "rule-plan-9", final_run, "predecessor slice 1 is final; the series has ended"
        )

    def test_a_missing_or_unclosed_predecessor_is_refused(self):
        run_one = self.run_slice("rule-plan-1", self.emit_ok(1, "slice-1"))
        missing = "22222222-2222-4222-8222-222222222222"
        self.refuse_successor(
            2, "rule-plan-1", missing, "cannot load predecessor run: unresolvable predecessor run"
        )
        open_run = self.init("rule-plan-3", self.emit_ok(1, "open"))["run_id"]
        self.refuse_successor(2, "rule-plan-3", open_run, "predecessor slice 1 is not closed")
        self.assertTrue(run_one)


class BatchingTest(ExpansionCase):
    def batches(self, plan):
        groups = {}
        for leaf in plan["leaves"]:
            if "batch" in leaf:
                groups.setdefault(leaf["batch"], []).append(leaf["id"])
        return groups

    def unit_batches(self, *specs):
        """Batches of a slice of unit rules after a non-batching doc type."""
        template = self.plain_template(doc={"batch": False}, unit={})
        return self.batches(self.plain_slice(template, self.plain_rows(*specs)))

    def test_a_run_of_nine_splits_into_five_and_four(self):
        ids = [f"a{n}" for n in range(1, 10)]
        plan = self.plain_slice(self.plain_template(), self.plain_rows(*[(i, "unit") for i in ids]))
        groups = list(self.batches(plan).values())
        self.assertEqual([ids[:5], ids[5:]], groups)
        self.assertEqual(
            {"p/unit-batch-a1", "p/unit-batch-a6"}, {x["worktree_owner"] for x in plan["leaves"]}
        )

    def test_a_leaf_with_an_extra_external_dependency_starts_a_new_run(self):
        grouped = self.unit_batches(
            ("z", "doc"), ("p1", "unit"), ("p2", "unit"), ("p3", "unit", ["z"]),
            ("p4", "unit", ["z"]),
        )
        self.assertEqual({"unit-batch-p1": ["p1", "p2"], "unit-batch-p3": ["p3", "p4"]}, grouped)
        solo = self.unit_batches(("z", "doc"), ("p1", "unit"), ("p2", "unit", ["z"]))
        self.assertEqual({}, solo)

    def test_a_member_may_depend_on_an_earlier_member_of_its_run(self):
        plan = self.plain_slice(self.plain_template(), self.plain_rows(
            ("p1", "unit"), ("p2", "unit", ["p1"]), ("p3", "unit", ["p2"])))
        self.assertEqual({"unit-batch-p1": ["p1", "p2", "p3"]}, self.batches(plan))

    def test_colliding_batch_names_fall_back_to_numbers_or_are_refused(self):
        template = self.plain_template(**{"x": {}, "x-batch-y": {}})
        rows = self.plain_rows(("y-batch-z", "x"), ("xa", "x"), ("z", "x-batch-y"),
                               ("zb", "x-batch-y"))
        plan = self.plain_slice(template, rows)
        self.assertEqual({"x-batch-y-batch-z": ["y-batch-z", "xa"],
                          "x-batch-y-batch-2": ["z", "zb"]}, self.batches(plan))
        taken = self.unit_batches(("unit-batch-p1", "doc"), ("p1", "unit"), ("p2", "unit"))
        self.assertEqual({"unit-batch-1": ["p1", "p2"]}, taken)
        template = self.plain_template(doc={"batch": False}, unit={})
        both = self.plain_rows(("unit-batch-p1", "doc"), ("unit-batch-1", "doc"),
                               ("p1", "unit"), ("p2", "unit"))
        self.refused(self.expand("partition", template=template, rows=both), 1,
                     "cannot name a batch for type unit")

    def test_literal_braces_render_and_placeholders_fill(self):
        template = self.plain_template(unit={"task": "Keep {{id}} literal for {id} ({type})"})
        plan = self.plain_slice(template, self.plain_rows(("p1", "unit")))
        self.assertEqual("Keep {id} literal for p1 (unit)", plan["leaves"][0]["task"])


class RefusalTest(ExpansionCase):
    def type_edit(self, type_name, **fields):
        template = copy.deepcopy(self.template)
        template["types"][type_name].update(fields)
        return template

    def test_index_errors_are_reported_with_their_line_and_a_nonzero_exit(self):
        def edit(position, **fields):
            rows = copy.deepcopy(self.rows)
            rows[position].update(fields)
            return rows

        cases = {
            "cycle": (edit(1, deps=["u7"]), "dependency cycle: d2 -> "),
            "unknown dependency": (edit(2, deps=["nope"]), "line 3: unknown dependency nope"),
            "unknown type": (edit(2, type="widget"), "line 3: unknown type widget"),
            "duplicate id": (edit(3, id="u1"), "line 4: duplicate id u1"),
            "self dependency": (edit(3, deps=["u2"]), "line 4: u2 depends on itself"),
            "exemplar flag value": (edit(4, exemplar=False), "line 5: exemplar must be true"),
            "unknown key": (edit(4, extra=1), "line 5: rule has unknown keys ['extra']"),
            "empty spec": (edit(4, spec=""), "line 5: spec and refs must be repository-relative"),
        }
        rows_two = edit(2, exemplar=True)
        rows_two[3]["exemplar"] = True
        cases["two exemplars"] = (rows_two, "line 4: more than one exemplar for type unit")
        for name, (rows, fragment) in cases.items():
            with self.subTest(name):
                self.refused(self.expand("partition", rows=rows), 1, fragment)
        no_declaration = copy.deepcopy(self.template)
        del no_declaration["types"]["unit"]["exemplar"]
        no_declaration["types"]["unit"]["capability_requirements"]["additional"] = []
        rows = copy.deepcopy(self.rows)
        rows[2]["exemplar"] = True
        self.refused(self.expand("partition", template=no_declaration, rows=rows), 1,
                     "line 3: type unit declares no exemplar")

    def test_index_file_shape_errors(self):
        text = INDEX.read_text()
        cases = {
            "blank line": (text.replace("\n", "\n\n", 1), "line 2: blank line"),
            "not json": (text + "{oops\n", "line 11: not valid JSON"),
            "not an object": ("[1]\n", "line 1: rule must be an object"),
            "empty": ("", "no rules"),
        }
        for name, (index_text, fragment) in cases.items():
            with self.subTest(name):
                self.refused(self.expand("partition", index_text=index_text), 1, fragment)
        self.assertEqual(0, self.expand("partition", index_text=text.rstrip("\n")).returncode)

    def test_template_errors_name_their_path(self):
        template = copy.deepcopy(self.template)
        cases = {
            "unknown placeholder": (self.type_edit("doc", task="Do {nope}"),
                                    "types.doc.task"),
            "attribute access": (self.type_edit("doc", task="Do {id.upper}"), "types.doc.task"),
            "conversion": (self.type_edit("doc", boundary="Do {id!r}"), "types.doc.boundary"),
            "format spec": (self.type_edit("doc", boundary="Do {id:>4}"), "types.doc.boundary"),
            "positional": (self.type_edit("doc", acceptance_command="run {}"),
                           "types.doc.acceptance_command"),
            "empty rendering": (self.type_edit("doc", task="   "), "types.doc.task renders empty or whitespace-only for rule"),
            "unknown top key": ({**template, "extra": 1}, "template has unknown keys ['extra']"),
            "bad schema": ({**template, "schema": "other"}, "schema must be planning-expansion-template-v1"),
            "too many leaves": ({**template, "series": {**template["series"], "max_leaves": 13}},
                                "series.max_leaves must be an integer from 1 to 12"),
            "skill follower": (self.type_edit("unit", capability_requirements={
                "baseline": "plan-step-base-v1",
                "additional": [{"kind": "skill", "name": "x", "reason": "y"}]}),
                               "mechanical wrappers that lack the Skill tool"),
            "exemplar type tier": (self.type_edit("doc", portable_tier="standard"),
                                   "followers of an exemplar run at mechanical"),
            "exemplar tier": (self.type_edit("doc", exemplar={"portable_tier": "deep"}),
                              "types.doc.exemplar.portable_tier"),
            "unrequired risk": (self.type_edit("unit", irreducible_unknown_or_risk="why"),
                                "types.unit.irreducible_unknown_or_risk"),
            "reserved decision": (self.type_edit("doc", settled_decisions={
                "exemplar_pattern": "mine"}), "must not contain exemplar_pattern"),
            "bad branch": ({**template, "owner_prefix": "rules~"}, "owner_prefix does not form a valid git branch name"),
        }
        for name, (variant, fragment) in cases.items():
            with self.subTest(name):
                self.refused(self.expand("partition", template=variant), 1, fragment)

    def test_a_follower_ordered_before_its_exemplar_is_refused(self):
        rows = copy.deepcopy(self.rows)
        for row in rows:
            row.pop("exemplar", None)
        rows[7]["exemplar"] = True
        self.refused(self.expand("partition", rows=rows), 1, "is a dependency of exemplar d3")

    def test_the_ordering_hint_depends_on_why_the_follower_comes_first(self):
        rows = self.plain_rows(("x1", "doc"), ("x2", "doc"), ("y1", "unit", ["x1"]))
        rows[1]["exemplar"] = True
        template = self.plain_template(doc={"exemplar": {"portable_tier": "standard"}},
                                       unit={"exemplar": {"portable_tier": "standard"}})
        self.refused(self.expand("partition", template=template, rows=rows), 1,
                     "rule x1 (type doc) is ordered before its exemplar x2; add x2 to its deps")
        chained = self.plain_rows(("x1", "doc"), ("x2", "doc", ["x1"]))
        chained[1]["exemplar"] = True
        result = self.expand("partition", template=template, rows=chained)
        self.refused(result, 1, "rule x1 (type doc) is a dependency of exemplar x2; "
                     "choose another exemplar")
        self.assertNotIn("add x2", result.stdout.decode())

    def test_untrusted_values_never_raise(self):
        def with_type(**fields):
            return self.type_edit("doc", **fields)

        cases = {
            "size list": (with_type(size=["small"]), None,
                          "types.doc.size must be small, medium, or large"),
            "tier list": (with_type(portable_tier=["mechanical"]), None,
                          "types.doc.portable_tier is not a known tier"),
            "exemplar tier list": (with_type(exemplar={"portable_tier": ["standard"]}), None,
                                   "types.doc.exemplar.portable_tier must be standard or analytical"),
            "size object": (with_type(size={"a": 1}), None,
                            "types.doc.size must be small, medium, or large"),
            "precision list": ({**self.template, "precision": ["strict"]}, None,
                               "precision must be standard or strict"),
            "verification list": ({**self.template, "verification": ["per-leaf"]}, None,
                                  "verification must be per-leaf or closeout-only"),
            "decision list": ({**self.template, "approved_decisions": [["x"]]}, None,
                              "approved_decisions entries must be non-empty strings"),
            "rule type list": (None, {"type": ["doc"]}, "line 3: type must be a string"),
            "rule deps nested": (None, {"deps": [["d2"]]}, "line 3: deps must be an array of rule ids"),
            "rule id list": (None, {"id": ["u1"]}, "line 3: id must be a stable bounded identifier"),
            "rule refs scalar": (None, {"refs": 5}, "line 3: spec and refs must be repository-relative"),
        }
        for name, (template, edit, fragment) in cases.items():
            with self.subTest(name):
                rows = None
                if edit:
                    rows = copy.deepcopy(self.rows)
                    rows[2].update(edit)
                self.refused(self.expand("partition", template=template, rows=rows), 1, fragment)

    def test_deeply_nested_json_is_refused_cleanly(self):
        nested = "[" * 100000 + "]" * 100000
        template_path = self.root / "deep-template.json"
        template_path.write_text(nested)
        result = run(EXPAND, "partition", "--template", template_path, "--index", INDEX)
        self.refused(result, 1, "template is nested too deeply")
        result = self.expand("partition", index_text=nested + "\n")
        self.refused(result, 1, "line 1: nested too deeply")

    def test_the_input_size_limits_are_enforced(self):
        big = self.root / "big"
        big.write_bytes(b" " * (256 * 1024 + 1))
        result = run(EXPAND, "partition", "--template", big, "--index", INDEX)
        self.refused(result, 1, "template exceeds 262144 bytes")
        index = self.root / "big-index"
        index.write_bytes(b" " * (8 * 1024 * 1024 + 1))
        result = run(EXPAND, "partition", "--template", TEMPLATE, "--index", index)
        self.refused(result, 1, "index exceeds 8388608 bytes")

    def test_a_partition_summary_over_the_cap_is_refused(self):
        template = self.plain_template(max_leaves=1)
        rows = self.plain_rows(*[(f"p{n:04d}", "unit") for n in range(1500)])
        result = self.expand("partition", template=template, rows=rows)
        self.refused(result, 1, "partition summary exceeds 64 KiB")

    def test_usage_errors_exit_two(self):
        base = ("--template", TEMPLATE, "--index", INDEX)
        predecessor = ("--predecessor-plan-id", "rule-plan-1", "--predecessor-run-id",
                       STUB_PREDECESSOR["run_id"])
        run_id = STUB_PREDECESSOR["run_id"]
        for name, arguments, fragment in (
            ("zero", ("--slice", 0), "at least 1"),
            ("past the end", ("--slice", 3, *predecessor), "from 1 to 2"),
            ("no predecessor", ("--slice", 2), "requires --predecessor-plan-id"),
            ("slice one with predecessor", ("--slice", 1, *predecessor), "takes no predecessor"),
            ("plan id only", ("--slice", 2, "--predecessor-plan-id", "rule-plan-1"),
             "requires --predecessor-plan-id"),
            ("run id only", ("--slice", 2, "--predecessor-run-id", run_id),
             "requires --predecessor-plan-id"),
            ("unstable plan id", ("--slice", 2, "--predecessor-plan-id", "Bad Id",
                                  "--predecessor-run-id", run_id), "must be a stable id"),
            ("bad run id", ("--slice", 2, "--predecessor-plan-id", "rule-plan-1",
                            "--predecessor-run-id", "nope"), "UUID4"),
        ):
            with self.subTest(name):
                result = run(EXPAND, "slice", *base, *arguments)
                self.refused(result, 2, fragment)

    def test_a_validator_invalid_template_is_refused_with_the_validator_errors(self):
        noop = self.type_edit("doc", acceptance_command="true")
        self.refused(self.expand("slice", "--slice", 1, template=noop), 1, "leaves[0].acceptance_command cannot be a known no-op command")
        shared = self.type_edit("doc", write_set=["docs/shared.md"])
        shared["types"]["doc"].pop("exemplar")
        rows = [{"id": name, "type": "doc", "deps": [], "spec": f"specs/{name}.md", "refs": []}
                for name in ("p1", "p2")]
        self.refused(self.expand("slice", "--slice", 1, template=shared, rows=rows), 1,
                     "have overlapping write coverage")
        self.refused(self.expand("partition", template=noop), 1, "slice 1: leaves[0]")
        self.refused(self.expand("partition", template=noop), 1, "known no-op")

    def test_an_oversize_slice_shrinks_and_every_slice_fits_the_cap(self):
        template = self.type_edit("doc", task="x" * 6000 + " {id}")
        template["series"]["max_leaves"] = 12
        rows = [{"id": f"p{n:02d}", "type": "doc", "deps": [], "spec": f"specs/p{n:02d}.md",
                 "refs": []} for n in range(12)]
        template["types"]["doc"].pop("exemplar")
        summary = json.loads(self.expand("partition", template=template, rows=rows).stdout)
        counts = [entry["leaf_count"] for entry in summary["slices"]]
        self.assertEqual(12, sum(counts))
        self.assertLess(max(counts), 12)
        self.assertGreater(summary["slice_count"], 1)
        parsed = expand.load_template(self.root / "template.json")
        expansion = expand.build(parsed, expand.load_index(self.root / "index.jsonl", parsed))
        for number in range(1, summary["slice_count"] + 1):
            plan = expand.emit_slice(expansion, number, None if number == 1 else {
                "plan_id": "a" * 64, "run_id": STUB_PREDECESSOR["run_id"],
                "plan_sha256": "f" * 64, "outcome": "abandoned", "handoff_sha256": "f" * 64})
            self.assertLessEqual(len(core.canon(plan)), plancontract.HANDOFF_PLAN_MAX)
        one = [{**rows[0], "id": "huge"}]
        template["types"]["doc"]["task"] = "x" * 70000
        self.refused(self.expand("partition", template=template, rows=one), 1, "alone exceeds the 65536-byte plan cap")


if __name__ == "__main__":
    unittest.main()
