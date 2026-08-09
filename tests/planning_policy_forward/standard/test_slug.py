import unittest

from slug import slug


class SlugTest(unittest.TestCase):
    def test_normalizes_spaces_and_case(self):
        self.assertEqual(slug("A Small Test"), "a-small-test")


if __name__ == "__main__":
    unittest.main()
