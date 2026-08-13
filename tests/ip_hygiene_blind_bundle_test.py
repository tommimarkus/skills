import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import importlib.util
import shutil
from pathlib import Path

from tests.surface_test_lib import IP_CORPUS_SIZE, REPO_ROOT, load_script_module, read, read_jsonl


BUILDER = (
    REPO_ROOT
    / "souroldgeezer-audit"
    / "skills"
    / "ip-hygiene"
    / "references"
    / "scripts"
    / "build_ip_hygiene_blind_bundle.py"
)


class IpHygieneBlindBundleTest(unittest.TestCase):
    def build_bundle(self, output: Path) -> Path:
        result = subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                "--repo-root",
                str(REPO_ROOT),
                "--output",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return output

    def test_builder_creates_deterministic_allowlisted_blind_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self.build_bundle(root / "first")
            second = self.build_bundle(root / "second")

            first_manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
            second_manifest = json.loads((second / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(first_manifest, second_manifest)
            self.assertEqual(first_manifest["schema_version"], "ip-hygiene-blind-bundle.v1")

            paths = [entry["path"] for entry in first_manifest["files"]]
            self.assertEqual(paths, sorted(paths))
            self.assertIn("EVALUATOR_INSTRUCTIONS.md", paths)
            self.assertIn("cases.jsonl", paths)
            self.assertIn("validate_ip_hygiene_actual.py", paths)
            self.assertFalse(any(path.endswith("/cases.jsonl") for path in paths))
            self.assertFalse(any(path.endswith("/validate_ip_hygiene_actual.py") for path in paths))
            self.assertIn("souroldgeezer-audit/skills/ip-hygiene/SKILL.md", paths)
            self.assertIn("souroldgeezer-audit/docs/audit-reference/audit-craft.md", paths)
            self.assertIn("souroldgeezer-audit/docs/audit-reference/materiality.md", paths)
            self.assertFalse(any("expected.jsonl" in path for path in paths))
            self.assertFalse(any("score_ip_hygiene_eval.py" in path for path in paths))
            self.assertFalse(any("source-grounding.md" in path for path in paths))
            self.assertFalse(any(path.startswith(".git/") for path in paths))
            self.assertFalse(any("/tests/" in path or path.startswith("tests/") for path in paths))

            for entry in first_manifest["files"]:
                content = (first / entry["path"]).read_bytes()
                self.assertEqual(entry["sha256"], hashlib.sha256(content).hexdigest())

            instructions = (first / "EVALUATOR_INSTRUCTIONS.md").read_text(encoding="utf-8")
            self.assertIn("blocked:contaminated", instructions)
            self.assertIn("only assigned bundle", instructions)
            self.assertIn("structure only", instructions)
            self.assertIn("Parent", instructions)
            self.assertIn(
                "validate_ip_hygiene_actual.py --cases cases.jsonl --actual <actual.jsonl>",
                instructions,
            )

            cases = [
                json.loads(line)
                for line in (first / "cases.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual([case["case"] for case in cases], [f"case-{n:03d}" for n in range(1, IP_CORPUS_SIZE + 1)])
            for case in cases:
                self.assertEqual(set(case), {"case", "prompt", "synthetic"})
                self.assertIn("Requested lane:", case["prompt"])
            case_018 = next(case for case in cases if case["case"] == "case-018")
            self.assertNotIn("harmonization source", case_018["prompt"])
            self.assertNotIn("stop the merits decision", case_018["prompt"])

    def test_builder_rejects_allowlisted_symlink_even_when_target_is_a_file(self) -> None:
        spec = importlib.util.spec_from_file_location("ip_blind_builder", BUILDER)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_repo = root / "repo"
            for relative in module.ALLOWLIST:
                source = REPO_ROOT / relative
                destination = fake_repo / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            outside = root / "outside.md"
            outside.write_text("outside contamination", encoding="utf-8")
            linked = fake_repo / module.ALLOWLIST[0]
            linked.unlink()
            linked.symlink_to(outside)
            result = subprocess.run(
                [sys.executable, str(BUILDER), "--repo-root", str(fake_repo),
                 "--output", str(root / "bundle")],
                text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("symlink", result.stderr)



class IpHygieneBundleAllowlistCoverageTest(unittest.TestCase):
    """The bundle allowlist is a hand-maintained list of a fact that lives in the
    skill, so it is checked against the skill rather than trusted.

    It silently missed source-code.md and all six language packs when the
    source-code lane landed: the bundle still built, and the evaluator would
    have judged code-lane cases without the code-lane reference.
    """

    #: Deliberately outside the bundle, with the reason it is not evidence.
    DECLARED_EXCLUSIONS = {
        # Scope/remedy policy for the auditor, not facts about reviewed material.
        "fence-posts.md",
        # Legacy router kept for old inbound links; superseded by the load map.
        "ip-hygiene-reference.md",
        # Eval-authoring guidance; giving it to the evaluator would leak method.
        "source-grounding.md",
    }

    def _allowlist(self) -> set[str]:
        builder = load_script_module(
            "ip_hygiene_bundle_builder",
            REPO_ROOT / "souroldgeezer-audit/skills/ip-hygiene/references/scripts/build_ip_hygiene_blind_bundle.py",
        )
        return set(builder.ALLOWLIST)

    def test_every_extension_pack_reaches_the_evaluator(self) -> None:
        allowlist = self._allowlist()
        packs = sorted(
            (REPO_ROOT / "souroldgeezer-audit/skills/ip-hygiene/extensions").glob("*.md")
        )
        self.assertTrue(packs, "no extension packs found")
        for pack in packs:
            relative = pack.relative_to(REPO_ROOT).as_posix()
            with self.subTest(pack=pack.name):
                self.assertIn(
                    relative,
                    allowlist,
                    f"{pack.name} is not in the blind-bundle allowlist; the "
                    "evaluator would judge its language without it",
                )

    def test_every_reference_is_bundled_or_declared_excluded(self) -> None:
        allowlist = self._allowlist()
        references = sorted(
            (REPO_ROOT / "souroldgeezer-audit/skills/ip-hygiene/references").glob("*.md")
        )
        self.assertTrue(references, "no reference files found")
        for reference in references:
            relative = reference.relative_to(REPO_ROOT).as_posix()
            with self.subTest(reference=reference.name):
                if reference.name in self.DECLARED_EXCLUSIONS:
                    self.assertNotIn(
                        relative,
                        allowlist,
                        f"{reference.name} is declared excluded but is bundled",
                    )
                    continue
                self.assertIn(
                    relative,
                    allowlist,
                    f"{reference.name} is neither bundled nor listed in "
                    "DECLARED_EXCLUSIONS with a reason",
                )

    #: Parent-only scoring material. If any of these ever reaches ALLOWLIST,
    #: every future blind run is silently invalidated: the evaluator would be
    #: reading the answer key (or the method used to author it) instead of
    #: producing an independent judgment.
    PARENT_ONLY_MATERIAL = {
        "souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus/expected.jsonl",
        "souroldgeezer-audit/skills/ip-hygiene/references/scripts/score_ip_hygiene_eval.py",
        "souroldgeezer-audit/skills/ip-hygiene/references/source-grounding.md",
        "souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus/baseline.json",
    }

    def test_parent_only_scoring_material_never_reaches_the_evaluator(self) -> None:
        allowlist = self._allowlist()
        for relative in sorted(self.PARENT_ONLY_MATERIAL):
            with self.subTest(path=relative):
                self.assertNotIn(
                    relative,
                    allowlist,
                    f"{relative} must never be added to ALLOWLIST: it is "
                    "parent-only scoring/eval-authoring material, and bundling "
                    "it would silently invalidate every future blind run by "
                    "letting the evaluator read the answer key or the method "
                    "used to author it",
                )


class IpHygieneGuidanceContaminationGuardTest(unittest.TestCase):
    """Harness-injected repo guidance (CLAUDE.md, README.md, AGENTS.md) reaches
    every subagent regardless of the blind bundle, and arrives before the
    evaluator ever reads EVALUATOR_INSTRUCTIONS.md. This cannot be prevented
    from inside the skill, so the guidance itself is gated instead: it must
    carry no corpus case ID and no expected-outcome vocabulary that would bias
    an evaluator before it starts.
    """

    GUIDANCE_FILES = ("CLAUDE.md", "README.md", "AGENTS.md")

    #: Anchors shorter than this are generic English or technical terms —
    #: "COPYRIGHT", "DO NOT EDIT", "14-row" — that legitimately appear in repo
    #: guidance, so matching on them would block honest documentation without
    #: catching a leak. The longer anchors are invented scenario material
    #: ("EmberMetrics", "12,000 business locations"), which has no reason to
    #: appear in guidance except by having leaked out of a case.
    DISTINCTIVE_ANCHOR_LENGTH = 12

    def test_guidance_files_carry_no_corpus_case_id(self) -> None:
        case_ids = {f"case-{n:03d}" for n in range(1, IP_CORPUS_SIZE + 1)}
        for name in self.GUIDANCE_FILES:
            with self.subTest(file=name):
                text = read(name)
                found = {case_id for case_id in case_ids if case_id in text}
                self.assertFalse(
                    found,
                    f"{name} contains corpus case ID(s) {sorted(found)}; "
                    "harness-injected guidance reaches every blind evaluator "
                    "before it reads EVALUATOR_INSTRUCTIONS.md, so a case ID "
                    "here would silently invalidate every future blind run",
                )

    def test_guidance_files_carry_no_distinctive_case_material(self) -> None:
        """A case ID is the obvious leak; quoted scenario material is the quiet
        one. The corpus already curates a distinctive descriptor per case as its
        evidence anchors, so derive the watch list from those rather than
        hand-maintaining a second copy that drifts as cases are added."""
        anchors = {
            anchor
            for record in read_jsonl(
                "souroldgeezer-audit/skills/ip-hygiene/references/evals/"
                "accuracy-corpus/expected.jsonl"
            )
            for anchor in record.get("evidence_anchors", [])
            if len(anchor) >= self.DISTINCTIVE_ANCHOR_LENGTH
        }
        self.assertTrue(anchors, "no distinctive anchors parsed — the corpus shape changed")
        for name in self.GUIDANCE_FILES:
            with self.subTest(file=name):
                text = read(name).casefold()
                found = sorted(a for a in anchors if a.casefold() in text)
                self.assertFalse(
                    found,
                    f"{name} quotes corpus case material {found}; "
                    "harness-injected guidance reaches every blind evaluator "
                    "before it reads EVALUATOR_INSTRUCTIONS.md, so this would "
                    "silently bias every future blind run",
                )


if __name__ == "__main__":
    unittest.main()
