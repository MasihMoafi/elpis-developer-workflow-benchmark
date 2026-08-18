import unittest

from calculator import apply_discount


class ApplyDiscountTests(unittest.TestCase):
    def test_discount(self):
        self.assertEqual(apply_discount(1000, 15), 850)

    def test_truncation(self):
        self.assertEqual(apply_discount(999, 10), 899)

    def test_full_discount(self):
        self.assertEqual(apply_discount(100, 100), 0)

    def test_rejects_invalid_percentage(self):
        with self.assertRaises(ValueError):
            apply_discount(100, -1)
        with self.assertRaises(ValueError):
            apply_discount(100, 101)

