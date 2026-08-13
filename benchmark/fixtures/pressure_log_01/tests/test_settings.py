import unittest

from settings import ROLLOUT_MODE


class SettingsTests(unittest.TestCase):
    def test_authoritative_rollout_mode(self):
        self.assertEqual(ROLLOUT_MODE, "stable")


if __name__ == "__main__":
    unittest.main()
