import unittest
from embed_builder import _safe_float

class TestSafeFloat(unittest.TestCase):
    def test_safe_float_valid_numbers(self):
        self.assertEqual(_safe_float(1), 1.0)
        self.assertEqual(_safe_float(2.5), 2.5)
        self.assertEqual(_safe_float(0), 0.0)
        self.assertEqual(_safe_float(-3.14), -3.14)

    def test_safe_float_valid_strings(self):
        self.assertEqual(_safe_float("1"), 1.0)
        self.assertEqual(_safe_float("2.5"), 2.5)
        self.assertEqual(_safe_float("-3.14"), -3.14)
        self.assertEqual(_safe_float("  4.2  "), 4.2)

    def test_safe_float_invalid_strings(self):
        self.assertEqual(_safe_float("abc"), 0.0)
        self.assertEqual(_safe_float(""), 0.0)
        self.assertEqual(_safe_float("1.2.3"), 0.0)

    def test_safe_float_none(self):
        self.assertEqual(_safe_float(None), 0.0)

    def test_safe_float_custom_default(self):
        self.assertEqual(_safe_float("abc", default=5.0), 5.0)
        self.assertEqual(_safe_float(None, default=-1.0), -1.0)
        self.assertEqual(_safe_float([], default=10.0), 10.0)

    def test_safe_float_type_errors(self):
        self.assertEqual(_safe_float([]), 0.0)
        self.assertEqual(_safe_float({}), 0.0)
        self.assertEqual(_safe_float(object()), 0.0)

if __name__ == "__main__":
    unittest.main()
