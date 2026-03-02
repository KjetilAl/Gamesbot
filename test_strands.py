import unittest
from score_parser import is_strands_message, parse_strands_score

class TestStrandsParser(unittest.TestCase):
    def test_strands_valid_examples(self):
        msg1 = """Strands #729
“Home office alternative”
🟡🔵🔵🔵
🔵💡🔵🔵"""
        self.assertTrue(is_strands_message(msg1))
        info1 = parse_strands_score(msg1)
        self.assertIsNotNone(info1)
        self.assertEqual(info1["total_score"], 17) # 20 - (1 - 1) - (1 * 3) = 17

        msg2 = """Strands #729
“Home office alternative”
🔵🔵🔵🟡
💡🔵💡🔵
🔵"""
        self.assertTrue(is_strands_message(msg2))
        info2 = parse_strands_score(msg2)
        self.assertIsNotNone(info2)
        self.assertEqual(info2["total_score"], 11) # 20 - (4 - 1) - (2 * 3) = 11

        msg3 = """Strands #729
“Home office alternative”
🔵💡🔵💡
🔵🔵🟡🔵
🔵"""
        self.assertTrue(is_strands_message(msg3))
        info3 = parse_strands_score(msg3)
        self.assertIsNotNone(info3)
        self.assertEqual(info3["total_score"], 8) # 20 - (7 - 1) - (2 * 3) = 8

if __name__ == '__main__':
    unittest.main()