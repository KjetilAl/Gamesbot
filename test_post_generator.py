import unittest

import post_generator


class TestPersonalSpotlights(unittest.TestCase):
    def test_personal_best_spotlight(self):
        result = post_generator._build_personal_stat_spotlight(
            "gisnep",
            {"is_new_pb": True},
            {},
        )
        self.assertIn("personal best", result.lower())

    def test_wordle_win_rate_spotlight(self):
        result = post_generator._build_personal_stat_spotlight(
            "wordle",
            {"win_percentage": 84.5},
            {},
        )
        self.assertIn("84.5%", result)

    def test_pips_cookie_milestone(self):
        result = post_generator._build_personal_stat_spotlight(
            "pips",
            {"total_cookies": 10},
            {},
        )
        self.assertIn("Cookie milestone", result)


if __name__ == "__main__":
    unittest.main()
