import unittest

from slugify import slugify


class SlugifyTests(unittest.TestCase):
    def test_normalizes_words_and_punctuation(self):
        self.assertEqual(slugify("  Release / Candidate 2! "), "release-candidate-2")

    def test_collapses_separators(self):
        self.assertEqual(slugify("A---B__C"), "a-b-c")


if __name__ == "__main__":
    unittest.main()
