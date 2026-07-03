"""Shims are published contracts: CLI forms run; re-exports match module __all__."""
import ast
import subprocess
import sys
import unittest
from pathlib import Path
from types import ModuleType

from tests.surface_test_lib import REPO_ROOT, load_script_module

SCRIPTS = REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/references/scripts"
# lean_engine.py re-exports three package modules (engine + discovery + registry);
# every other shim maps 1:1 to a single leanaudit module.
PAIRS = (
    ("lean_engine.py", ("leanaudit/engine.py", "leanaudit/discovery.py", "leanaudit/registry.py")),
    ("code_lens.py", ("leanaudit/clones.py",)),
    ("skill_load_cost.py", ("leanaudit/load_cost.py",)),
    ("lean_guard.py", ("leanaudit/guard_lean.py",)),
    ("load_cost_guard.py", ("leanaudit/guard_load_cost.py",)),
)
# The two guard shims (lean_guard.py, load_cost_guard.py) are stdin-driven hooks with
# no --help form; their CLI smoke lives in tests/lean_guard_test.py::MainSubprocess
# and tests/load_cost_guard_test.py.
CLI_SMOKE = (
    ["lean_engine.py", "--help"],
    ["code_lens.py", "--help"],
    ["skill_load_cost.py", "--help"],
)
def _load_shim(shim_name: str) -> ModuleType:
    # Loading a leanaudit/*.py package module directly requires scripts/ on
    # sys.path first (the package does absolute `leanaudit.X` imports); the
    # shim's own sys.path.insert side effect provides that, so always load
    # the shim before any of its paired package modules (see
    # tests/lean_code_lens_test.py's load_clones_mod() for the same pattern).
    return load_script_module(f"shim_{shim_name[:-3]}", SCRIPTS / shim_name)


def _public_top_level_names(tree: ast.Module) -> set[str]:
    """Statically collected top-level def/class/assignment names, minus underscore
    names and anything bound by an import (no runtime introspection, so module-level
    imports like `re` or `Path` can't false-positive)."""
    imported: set[str] = set()
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                imported.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        names.add(sub.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return {n for n in names if not n.startswith("_") and n not in imported}


def _declared_all(tree: ast.Module, path: Path) -> set[str]:
    """The module's __all__, parsed from the same AST (a literal list of strings in
    every leanaudit module)."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if not isinstance(node.value, ast.List):
                        raise AssertionError(f"{path}: __all__ is not a list literal")
                    return {elt.value for elt in node.value.elts}
    raise AssertionError(f"{path} has no literal __all__")


class ShimContractTest(unittest.TestCase):
    def test_reexports_cover_module_all(self) -> None:
        for shim_name, mod_rels in PAIRS:
            with self.subTest(shim=shim_name):
                shim = _load_shim(shim_name)
                for rel in mod_rels:
                    mod = load_script_module(rel.replace("/", "_")[:-3], SCRIPTS / rel)
                    for name in mod.__all__:
                        self.assertTrue(hasattr(shim, name), f"{shim_name} missing {name}")

    def test_cli_help_runs(self) -> None:
        for argv in CLI_SMOKE:
            with self.subTest(cmd=argv[0]):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPTS / argv[0]), *argv[1:]],
                    capture_output=True, text=True,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)


class AllCompletenessTest(unittest.TestCase):
    """Guards the gap test_reexports_cover_module_all cannot see: a public name
    dropped from (or never added to) a module's __all__ shrinks the export and the
    parity check together, silently. ruff F822 only catches over-declaration; this
    static check catches under-declaration."""

    def test_public_top_level_names_are_declared_in_all(self) -> None:
        for path in sorted((SCRIPTS / "leanaudit").glob("*.py")):
            if path.name == "__init__.py":
                continue
            with self.subTest(module=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                public = _public_top_level_names(tree)
                declared = _declared_all(tree, path)
                missing = public - declared
                self.assertFalse(
                    missing,
                    f"{path.name}: public top-level names missing from __all__: "
                    f"{sorted(missing)}",
                )


if __name__ == "__main__":
    unittest.main()
