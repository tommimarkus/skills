"""Behavior of the deterministic plan expander behind expand_plan.py."""

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT

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
        index_path.write_text(jsonl(self.rows if rows is None else rows) if index_text is None else index_text)
        return ["--template", template_path, "--index", index_path]

    def expand(self, command, *extra, **variant):
        return run(EXPAND, command, *self.files(**variant), *extra)

    def refused(self, result, code, fragment):
        self.assertEqual(code, result.returncode, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["ok"])
        self.assertIn(fragment, "\n".join(report["errors"]))
        self.assertEqual(b"", result.stderr)

    def partition(self):
        result = run(EXPAND, "partition", "--template", TEMPLATE, "--index", INDEX)
        self.assertEqual(0, result.returncode, result.stderr)
        return result

    def validate_files(self, *plans):
        repository = self.root / "repository"
        repository.mkdir(exist_ok=True)
        for plan in plans:
            result = run(VALIDATE, "validate", plan, "--pin-roots", "tests", "--repo-root", repository)
            report = json.loads(result.stdout)
            self.assertEqual((0, True, []), (result.returncode, report["valid"], report["errors"]))


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

    def test_slice_two_matches_its_golden_with_a_real_predecessor_replaced_by_the_stub(self):
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
        self.assertEqual(followers["u6"]["batch"], followers["u7"]["batch"])
        self.assertNotIn("batch", followers["u5"])

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
    def common(self):
        return ["--ledger-root", self.root, "--repo-root", self.root]

    def ledger(self, *arguments):
        result = run(LEDGER, *self.common(), *arguments)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def emit(self, number, name, *extra, template=None):
        path = self.root / f"{name}.json"
        result = run(
            EXPAND, "slice", *self.files(template=template), "--slice", number, "--out", path,
            *self.common(), *extra,
        )
        return result, path

    def init(self, plan_id, path):
        plan = json.loads(path.read_text())
        plan_sha256 = hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        binding = self.root / f"{plan_id}-binding.json"
        binding.write_text(json.dumps({
            "schema": "planning-capability-binding-v1",
            "plan_sha256": plan_sha256,
            "bindings": [
                {"step_id": leaf["id"], "host": "codex", "executor": "gpt-5.6-terra",
                 "requirements": leaf["capability_requirements"], "evidence": ["fixture"]}
                for leaf in plan["leaves"]
            ],
        }))
        assignments = self.root / f"{plan_id}-assignments.json"
        assignments.write_text(json.dumps([
            {"id": leaf["id"], "harness": "codex", "model_or_alias": "gpt-5.6-terra",
             "effort": "medium",
             "worktree": f".worktrees/{leaf['worktree_owner'].replace('/', '-')}"}
            for leaf in plan["leaves"]
        ]))
        return self.ledger(
            "--plan-id", plan_id, "init-v5", "--actor", "parent", "--approved",
            "--plan-file", path, "--assignments-file", assignments,
            "--capability-binding-file", binding, "--pin-roots", "tests",
        )

    def close(self, plan_id, run_id, handoff=None):
        arguments = ["--plan-id", plan_id, "close", "--actor", "parent", "--run-id", run_id,
                     "--outcome", "blocked", "--reason", "fixture"]
        if handoff:
            arguments += ["--series-handoff-file", handoff]
        return self.ledger(*arguments)

    def ledger_bytes(self):
        return {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and "planning-policy" in path.parts
        }

    def test_the_series_runs_end_to_end_without_the_expander_touching_the_ledger(self):
        first_result, first_path = self.emit(1, "slice-1")
        self.assertEqual(0, first_result.returncode, first_result.stdout)
        run_one = self.init("rule-plan-1", first_path)["run_id"]
        content = self.root / "handoff.json"
        content.write_bytes(core.canon({
            "landed": ["slice 1 pages and units"],
            "decisions": ["exemplars landed first"],
            "assumptions_to_revalidate": ["style guide is stable"],
            "remaining_scope": ["slice 2 units"],
        }))
        self.close("rule-plan-1", run_one, content)
        checkpoint = json.loads(
            (self.root / "planning-policy/ledgers/rule-plan-1" / run_one / "checkpoint.json")
            .read_text()
        )
        before = self.ledger_bytes()
        second_result, second_path = self.emit(
            2, "slice-2", "--predecessor-plan-id", "rule-plan-1", "--predecessor-run-id", run_one
        )
        self.assertEqual(0, second_result.returncode, second_result.stdout)
        self.assertEqual(before, self.ledger_bytes())
        plan = json.loads(second_path.read_text())
        self.assertEqual(
            {"plan_id": "rule-plan-1", "run_id": run_one, "plan_sha256": checkpoint["plan_hash"],
             "outcome": "blocked", "handoff_sha256": checkpoint["series_handoff_sha256"]},
            plan["series"]["predecessor"],
        )
        self.assertEqual(checkpoint["plan_hash"], core.digest(json.loads(first_path.read_text())))
        replaced = copy.deepcopy(plan)
        replaced["series"]["predecessor"] = STUB_PREDECESSOR
        self.assertEqual(json.loads((FIXTURES / "expected-slice-2.json").read_text()), replaced)
        self.validate_files(first_path, second_path)
        self.assertEqual("matched", self.init("rule-plan-2", second_path)["series_predecessor"])

    def test_a_predecessor_of_another_series_or_the_wrong_slice_is_refused(self):
        _, first_path = self.emit(1, "slice-1")
        run_one = self.init("rule-plan-1", first_path)["run_id"]
        self.close("rule-plan-1", run_one)
        predecessor = ("--predecessor-plan-id", "rule-plan-1", "--predecessor-run-id", run_one)
        other = copy.deepcopy(self.template)
        other["series"]["series_id"] = "other-series"
        result, _ = self.emit(2, "other", *predecessor, template=other)
        self.refused(result, 1, "series")
        _, second_path = self.emit(2, "slice-2", *predecessor)
        run_two = self.init("rule-plan-2", second_path)["run_id"]
        self.close("rule-plan-2", run_two)
        result, _ = self.emit(
            2, "again", "--predecessor-plan-id", "rule-plan-2", "--predecessor-run-id", run_two
        )
        self.refused(result, 1, "slice")
        missing = "22222222-2222-4222-8222-222222222222"
        result, _ = self.emit(
            2, "gone", "--predecessor-plan-id", "rule-plan-1", "--predecessor-run-id", missing
        )
        self.refused(result, 1, "predecessor")
        _, open_path = self.emit(1, "open")
        open_run = self.init("rule-plan-3", open_path)["run_id"]
        result, _ = self.emit(
            2, "open-successor", "--predecessor-plan-id", "rule-plan-3",
            "--predecessor-run-id", open_run,
        )
        self.refused(result, 1, "closed")


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
            "cycle": (edit(1, deps=["u7"]), "dependency cycle"),
            "unknown dependency": (edit(2, deps=["nope"]), "line 3: unknown dependency nope"),
            "unknown type": (edit(2, type="widget"), "line 3: unknown type widget"),
            "duplicate id": (edit(3, id="u1"), "line 4: duplicate id u1"),
            "self dependency": (edit(3, deps=["u2"]), "depends on itself"),
            "exemplar flag value": (edit(4, exemplar=False), "exemplar must be true"),
            "unknown key": (edit(4, extra=1), "unknown keys"),
            "empty spec": (edit(4, spec=""), "spec"),
        }
        rows_two = edit(2, exemplar=True)
        rows_two[3]["exemplar"] = True
        cases["two exemplars"] = (rows_two, "more than one exemplar")
        for name, (rows, fragment) in cases.items():
            with self.subTest(name):
                self.refused(self.expand("partition", rows=rows), 1, fragment)
        no_declaration = copy.deepcopy(self.template)
        del no_declaration["types"]["unit"]["exemplar"]
        no_declaration["types"]["unit"]["capability_requirements"]["additional"] = []
        rows = copy.deepcopy(self.rows)
        rows[2]["exemplar"] = True
        self.refused(self.expand("partition", template=no_declaration, rows=rows), 1,
                     "declares no exemplar")

    def test_index_file_shape_errors(self):
        text = INDEX.read_text()
        cases = {
            "blank line": (text.replace("\n", "\n\n", 1), "line 2: blank line"),
            "not json": (text + "{oops\n", "line 11"),
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
            "empty rendering": (self.type_edit("doc", task="   "), "renders empty"),
            "unknown top key": ({**template, "extra": 1}, "unknown keys"),
            "bad schema": ({**template, "schema": "other"}, "schema"),
            "too many leaves": ({**template, "series": {**template["series"], "max_leaves": 13}},
                                "max_leaves"),
            "skill follower": (self.type_edit("unit", capability_requirements={
                "baseline": "plan-step-base-v1",
                "additional": [{"kind": "skill", "name": "x", "reason": "y"}]}),
                               "Skill tool"),
            "exemplar type tier": (self.type_edit("doc", portable_tier="standard"),
                                   "followers of an exemplar run at mechanical"),
            "exemplar tier": (self.type_edit("doc", exemplar={"portable_tier": "deep"}),
                              "types.doc.exemplar.portable_tier"),
            "unrequired risk": (self.type_edit("unit", irreducible_unknown_or_risk="why"),
                                "types.unit.irreducible_unknown_or_risk"),
            "reserved decision": (self.type_edit("doc", settled_decisions={
                "exemplar_pattern": "mine"}), "exemplar_pattern"),
            "bad branch": ({**template, "owner_prefix": "rules~"}, "branch name"),
        }
        for name, (variant, fragment) in cases.items():
            with self.subTest(name):
                self.refused(self.expand("partition", template=variant), 1, fragment)

    def test_a_follower_ordered_before_its_exemplar_is_refused(self):
        rows = copy.deepcopy(self.rows)
        for row in rows:
            row.pop("exemplar", None)
        rows[7]["exemplar"] = True
        self.refused(self.expand("partition", rows=rows), 1, "before its exemplar")

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
        self.refused(self.expand("slice", "--slice", 1, template=noop), 1, "known no-op")
        shared = self.type_edit("doc", write_set=["docs/shared.md"])
        shared["types"]["doc"].pop("exemplar")
        rows = [{"id": name, "type": "doc", "deps": [], "spec": f"specs/{name}.md", "refs": []}
                for name in ("p1", "p2")]
        self.refused(self.expand("slice", "--slice", 1, template=shared, rows=rows), 1,
                     "overlapping write")
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
        self.refused(self.expand("partition", template=template, rows=one), 1, "exceeds")


if __name__ == "__main__":
    unittest.main()
