import unittest

from release import release_window


class ReleaseTests(unittest.TestCase):
    def test_same_day_window(self):
        self.assertEqual(release_window(9, 17), 8)

    def test_overnight_window_wraps_at_midnight(self):
        self.assertEqual(release_window(22, 2), 4)


if __name__ == "__main__":
    unittest.main()
