import unittest

from calculator import apply_discount


class CalculatorTests(unittest.TestCase):
    def test_discount(self):
        self.assertEqual(apply_discount(1000, 15), 850)

    def test_fractional_cents_are_truncated(self):
        self.assertEqual(apply_discount(99, 10), 89)


if __name__ == "__main__":
    unittest.main()
