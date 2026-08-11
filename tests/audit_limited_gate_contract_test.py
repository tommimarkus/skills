import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT


AUDIT_CRAFT = REPO_ROOT / "souroldgeezer-audit/docs/audit-reference/audit-craft.md"
PUBLIC_DOCS = (REPO_ROOT / "AGENTS.md", REPO_ROOT / "CLAUDE.md", REPO_ROOT / "README.md")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class AuditLimitedGateContractTest(unittest.TestCase):
    def test_shared_contract_defines_labels_and_status_precedence(self) -> None:
        craft = " ".join(read(AUDIT_CRAFT).split())
        for label in (
            "`Quick gate: <status>`",
            "`triage gate: <status>`",
            "`limited-scope gate: <status>`",
        ):
            with self.subTest(label=label):
                self.assertIn(label, craft)
        for rule in (
            "`fail` if any substantiated in-scope `block` exists",
            "`not-evaluated` when required evidence or machinery cannot rule out blockers",
            "otherwise `pass-limited`.",
            "Warn and info findings never make this gate fail.",
            "A remediated block needs a clean rerun before the gate can pass.",
            "mechanical status check, not a rollup or reasonable-assurance verdict",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, craft)

    def test_shared_contract_maps_each_bounded_domain_lane(self) -> None:
        craft = " ".join(read(AUDIT_CRAFT).split())
        for adoption in (
            "`test-quality-audit` and `devsecops-audit` use `Quick gate: <status>`",
            "`ip-hygiene` uses `triage gate: <status>`",
            "`lean-audit` uses `limited-scope gate: <status>`",
        ):
            with self.subTest(adoption=adoption):
                self.assertIn(adoption, craft)

    def test_public_docs_repeat_the_bounded_lane_contract(self) -> None:
        for path in PUBLIC_DOCS:
            text = read(path)
            with self.subTest(path=path.name):
                self.assertIn("bounded-lane gate", text)
                self.assertIn("Quick gate: <status>", text)
                self.assertIn("triage gate: <status>", text)
                self.assertIn("limited-scope gate: <status>", text)
                self.assertIn("pass-limited", text)
                self.assertIn("not-evaluated", text)
                self.assertIn("fail", text)


if __name__ == "__main__":
    unittest.main()
