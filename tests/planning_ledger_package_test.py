"""Gates for the planningledger package behind the planning_ledger.py entry shim."""

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, load_script_module

SCRIPTS = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts"
PACKAGE = SCRIPTS / "planningledger"
SHIM = SCRIPTS / "planning_ledger.py"

# Lowest group first. A module imports only earlier groups, or same-group modules
# without a cycle; nothing imports cli.
IMPORT_ORDER = (
    ("plancontract",),
    ("vocabulary",),
    ("core",),
    ("gitops",),
    ("store", "contract"),
    ("checkpoint",),
    ("schedule", "series"),
    ("returns", "dispatch", "verify", "retention", "closeout", "tracing"),
    ("cli",),
)
GROUP = {name: number for number, group in enumerate(IMPORT_ORDER) for name in group}
# Every module of the package, per the module map in planningledger/__init__.py.
EXTRACTED = set(GROUP)
# plancontract is the validator implementation: the validate_plan_contract.py shim re-exports it,
# so the ledger shim does not (its main and validate would collide with the ledger's).
NOT_LEDGER_REEXPORTED = {"plancontract"}
# Patched by tests on their owner, so called as owner.name() elsewhere and never re-exported.
SEAMS = {
    "now": "core",
    "git": "gitops",
    "run_worktree_helper": "gitops",
    "plan_validator": "contract",
    "changed_path_allowed": "contract",
}

sys.path.insert(0, str(SCRIPTS))
ledger = load_script_module("planning_ledger_package_shim", SHIM)


def parsed(name):
    return ast.parse((PACKAGE / f"{name}.py").read_text(encoding="utf-8"))


def defined(tree):
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(x.id for t in node.targets for x in ast.walk(t) if isinstance(x, ast.Name))
    return names


def declared_all(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("module has no __all__")


def package_imports(tree):
    """Sibling modules this module imports, from `from . import x` and `from .x import y`."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            if node.module:
                found.add(node.module)
            else:
                found.update(alias.name for alias in node.names)
    return found


class PlanningLedgerPackageTest(unittest.TestCase):
    def test_the_package_holds_exactly_the_extracted_modules(self):
        present = {path.stem for path in PACKAGE.glob("*.py")} - {"__init__"}
        self.assertEqual(EXTRACTED, present)
        self.assertLessEqual(present, set(GROUP))

    def test_the_shim_reexports_every_modules_all(self):
        for name in sorted(EXTRACTED - NOT_LEDGER_REEXPORTED):
            module = __import__(f"planningledger.{name}", fromlist=["*"])
            for exported in declared_all(parsed(name)):
                with self.subTest(module=name, name=exported):
                    self.assertIs(getattr(module, exported), getattr(ledger, exported))

    def test_all_lists_exactly_the_modules_public_definitions(self):
        for name in sorted(EXTRACTED - NOT_LEDGER_REEXPORTED):
            owned = {seam for seam, owner in SEAMS.items() if owner == name}
            with self.subTest(module=name):
                self.assertEqual(defined(parsed(name)) - owned - {"__all__"}, set(declared_all(parsed(name))))

    def test_seams_are_absent_from_the_shim_and_called_through_their_owner(self):
        for seam, owner in SEAMS.items():
            with self.subTest(seam=seam):
                self.assertFalse(hasattr(ledger, seam))
                self.assertIn(seam, defined(parsed(owner)))
        for name in sorted(EXTRACTED):
            for node in ast.walk(parsed(name)):
                if isinstance(node, ast.Name) and node.id in SEAMS and SEAMS[node.id] != name:
                    self.fail(f"{name} uses seam {node.id} unqualified; call {SEAMS[node.id]}.{node.id}()")

    def test_the_import_graph_is_acyclic_and_obeys_the_import_order(self):
        edges = {name: package_imports(parsed(name)) for name in EXTRACTED}
        for name, imported in edges.items():
            for target in imported:
                with self.subTest(importer=name, imported=target):
                    self.assertNotEqual("cli", target)
                    self.assertLessEqual(GROUP[target], GROUP[name])
        state = {}

        def visit(name):
            self.assertNotEqual("visiting", state.get(name), f"import cycle through {name}")
            if name not in state:
                state[name] = "visiting"
                for target in edges[name]:
                    visit(target)
                state[name] = "done"

        for name in edges:
            visit(name)

    def test_the_package_docstring_names_every_module_and_imports_nothing(self):
        tree = ast.parse((PACKAGE / "__init__.py").read_text(encoding="utf-8"))
        doc = ast.get_docstring(tree)
        self.assertEqual([], [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))])
        for name in sorted(EXTRACTED):
            self.assertIn(f"- {name}:", doc)
        self.assertIn("vocabulary < core < gitops < {store, contract}", doc)

    def test_help_runs_through_the_shim(self):
        result = subprocess.run(
            [sys.executable, "-B", str(SHIM), "--help"], capture_output=True, text=True
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("usage: planning_ledger.py", result.stdout)


class ReadBoundedJsonTest(unittest.TestCase):
    """read_bounded_json caps the bytes it reads before it parses them."""

    def read(self, content, limit=16):
        from planningledger import core

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_bytes(content)
            return core.read_bounded_json(path, limit, "invalid message", "oversize message")

    def error(self, content, limit=16):
        from planningledger import core

        with self.assertRaises(core.Error) as caught:
            self.read(content, limit)
        return str(caught.exception)

    def test_an_oversized_malformed_file_reports_oversize_not_invalid(self):
        self.assertEqual("oversize message", self.error(b"{" * 64))

    def test_a_within_limit_malformed_file_reports_invalid(self):
        self.assertEqual("invalid message", self.error(b"{not json"))

    def test_a_missing_path_reports_invalid(self):
        from planningledger import core

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(core.Error) as caught:
                core.read_bounded_json(Path(directory) / "absent.json", 16, "invalid message", "oversize message")
        self.assertEqual("invalid message", str(caught.exception))

    def test_a_within_limit_valid_file_parses(self):
        self.assertEqual({"a": 1}, self.read(b'{"a": 1}'))


if __name__ == "__main__":
    unittest.main()
