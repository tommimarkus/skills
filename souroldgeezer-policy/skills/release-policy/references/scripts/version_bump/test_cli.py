import json
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "version-bump"


class VersionBumpCliTest(unittest.TestCase):
    def test_default_semver_patch(self):
        output = subprocess.check_output(
            [sys.executable, str(SCRIPT), "--current", "1.2.3"],
            text=True,
        )
        self.assertEqual(json.loads(output)["next_version"], "1.2.4")


if __name__ == "__main__":
    unittest.main()
