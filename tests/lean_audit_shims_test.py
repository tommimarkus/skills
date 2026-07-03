"""Shims are published contracts: CLI forms run; re-exports match module __all__."""
import subprocess
import sys
import unittest

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
CLI_SMOKE = (
    ["lean_engine.py", "--help"],
    ["code_lens.py", "--help"],
    ["skill_load_cost.py", "--help"],
)


def _load_shim(shim_name: str):
    # Loading a leanaudit/*.py package module directly requires scripts/ on
    # sys.path first (the package does absolute `leanaudit.X` imports); the
    # shim's own sys.path.insert side effect provides that, so always load
    # the shim before any of its paired package modules (see
    # tests/lean_code_lens_test.py's load_clones_mod() for the same pattern).
    return load_script_module(f"shim_{shim_name[:-3]}", SCRIPTS / shim_name)


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


if __name__ == "__main__":
    unittest.main()
