import unittest

from labels import unique_labels
from oracle import expected_slug, expected_unique_labels
from slug import slug


class FixtureOracleTest(unittest.TestCase):
    def test_slug_representative_edges(self):
        cases = {
            "A Small Test": "a-small-test",
            "  A---B__C  ": "a-b-c",
            "Café & Tea": "caf-tea",
            "AKB": "a-b",
            "***": "",
            "": "",
            "v2.0": "v2-0",
        }
        for value, expected in cases.items():
            self.assertEqual(expected_slug(value), expected)
            self.assertEqual(slug(value), expected)

    def test_labels_representative_edges(self):
        values = [" A ", "a", "", "B", " b ", "  ", "CAFÉ", "café"]
        expected = ["A", "B", "CAFÉ"]
        self.assertEqual(expected_unique_labels(values), expected)
        self.assertEqual(unique_labels(values), expected)


if __name__ == "__main__":
    unittest.main()
