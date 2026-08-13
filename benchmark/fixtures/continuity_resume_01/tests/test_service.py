import unittest

from service import remaining_retries


class ServiceTests(unittest.TestCase):
    def test_remaining_retries(self):
        self.assertEqual(remaining_retries(2, 5), 3)

    def test_never_negative(self):
        self.assertEqual(remaining_retries(7, 5), 0)


if __name__ == "__main__":
    unittest.main()
