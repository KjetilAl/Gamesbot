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

    def test_krillion_post_one_in_a_krillion(self):
        post = post_generator.generate_post(
            "krillion",
            "Alice",
            {
                "game_number": 118,
                "total_score": 375,
                "diving_depth": 3750,
                "one_in_a_krillion_count": 1,
                "deep_cut_count": 1,
                "rare_count": 2,
                "schooler_count": 2,
                "too_clever_count": 0,
                "plankton_count": 1,
                "no_answer_count": 0,
            },
            {"total_plays": 1, "avg_score": 375.0},
        )
        self.assertIn("One in a Krillion", post)
        self.assertIn("375", post)

    def test_krillion_post_multiple_deep_cuts(self):
        post = post_generator.generate_post(
            "krillion",
            "Bob",
            {
                "game_number": 118,
                "total_score": 460,
                "diving_depth": 4600,
                "one_in_a_krillion_count": 0,
                "deep_cut_count": 4,
                "rare_count": 1,
                "schooler_count": 2,
                "too_clever_count": 0,
                "plankton_count": 0,
                "no_answer_count": 0,
            },
            {"total_plays": 1, "avg_score": 460.0},
        )
        self.assertIn("4 Deep Cuts", post)
        self.assertIn("460", post)


if __name__ == "__main__":
    unittest.main()

