import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


FIXTURE = Path(__file__).resolve().parent / "fixture"


CORRECT_SLUG = '''def slug(value: str) -> str:
    pieces = []
    separated = False
    for character in value:
        if "A" <= character <= "Z" or "a" <= character <= "z" or "0" <= character <= "9":
            pieces.append(character.lower())
            separated = False
        elif pieces and not separated:
            pieces.append("-")
            separated = True
    return "".join(pieces).rstrip("-")
'''

CORRECT_LABELS = '''def unique_labels(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        stripped = value.strip()
        if stripped and stripped.casefold() not in seen:
            result.append(stripped)
            seen.add(stripped.casefold())
    return result
'''


class FixtureContractTest(unittest.TestCase):
    def test_immutable_oracle_rejects_incorrect_and_accepts_correct_worker_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "fixture"
            shutil.copytree(FIXTURE, copied)
            (copied / "slug.py").write_text("def slug(value):\n    return value\n", encoding="utf-8")
            (copied / "labels.py").write_text("def unique_labels(values):\n    return values\n", encoding="utf-8")
            rejected = subprocess.run(["python", "oracle_checks.py"], cwd=copied, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            (copied / "slug.py").write_text(CORRECT_SLUG, encoding="utf-8")
            (copied / "labels.py").write_text(CORRECT_LABELS, encoding="utf-8")
            accepted = subprocess.run(["python", "oracle_checks.py"], cwd=copied, capture_output=True, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)


if __name__ == "__main__":
    unittest.main()
