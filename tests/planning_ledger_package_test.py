"""Gates for the planningledger package behind the planning_ledger.py entry shim."""

import ast
import subprocess
import sys
import unittest

from tests.surface_test_lib import REPO_ROOT, load_script_module

SCRIPTS = REPO_ROOT / "souroldgeezer-policy/skills/planning-policy/references/scripts"
PACKAGE = SCRIPTS / "planningledger"
SHIM = SCRIPTS / "planning_ledger.py"

# Lowest group first. A module imports only earlier groups, or same-group modules
# without a cycle; nothing imports cli.
IMPORT_ORDER = (
    ("vocabulary",),
    ("core",),
    ("store",),
    ("gitops", "contract"),
    ("checkpoint", "legacy"),
    ("schedule", "series"),
    ("returns", "dispatch", "verify", "retention", "closeout", "tracing"),
    ("cli",),
)
GROUP = {name: number for number, group in enumerate(IMPORT_ORDER) for name in group}
# Extracted so far; each splitting step adds its modules here.
EXTRACTED = {
    "vocabulary", "core", "store", "gitops", "contract",
    "checkpoint", "legacy", "schedule", "series", "returns",
}
# Patched by tests on their owner, so called as owner.name() elsewhere and never re-exported.
SEAMS = {
    "now": "core",
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
        for name in sorted(EXTRACTED):
            module = __import__(f"planningledger.{name}", fromlist=["*"])
            for exported in declared_all(parsed(name)):
                with self.subTest(module=name, name=exported):
                    self.assertIs(getattr(module, exported), getattr(ledger, exported))

    def test_all_lists_exactly_the_modules_public_definitions(self):
        for name in sorted(EXTRACTED):
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

    def test_help_runs_through_the_shim(self):
        result = subprocess.run(
            [sys.executable, "-B", str(SHIM), "--help"], capture_output=True, text=True
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("usage: planning_ledger.py", result.stdout)


if __name__ == "__main__":
    unittest.main()
