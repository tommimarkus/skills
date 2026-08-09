import unittest

from constants import RETRY_LIMIT


class ConstantsTest(unittest.TestCase):
    def test_retry_limit_is_exactly_three(self):
        self.assertEqual(RETRY_LIMIT, 3)


if __name__ == "__main__":
    unittest.main()
