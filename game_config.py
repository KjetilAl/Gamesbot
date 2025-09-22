"""
Game Configuration Module - Defines settings and constants for different games.
"""
import score_parser
import database
import embed_builder

# --- Data Mappings for Generic Leaderboard ---
# Maps database columns to the keys expected by the generic embed builder
LEADERBOARD_KEY_MAPPINGS = {
    "Framed": ["display_name", "games_played", "total_score", "avg_attempts", "solved_count"],
    "Gisnep": ["display_name", "games_played", "avg_time", "best_time"],
    "Bandle": ["display_name", "games_played", "total_score", "avg_attempts", "solved_count",
               "bonus_microphone_count", "bonus_frame_count", "bonus_person_count", "bonus_globe_count", "bonus_puzzle_count",
               "bonus_calendar_count", "bonus_cd_count", "bonus_timer_count", "bonus_guitar_count"],
    "Minute Cryptic": ["display_name", "games_played", "solved_count", "avg_score"],
    "Word Salad": ["display_name", "games_played", "avg_time", "best_time", "avg_hints", "total_score", "avg_score"],
    "Pips": ["display_name", "total_score", "games_played", "cookie_count"],
    "Sexaginta": ["display_name", "avg_pct", "avg_score", "plays"],
}

# Game configurations dictionary
GAME_CONFIGS = {
    "wordle": {
        "name": "Wordle",
        "chat_channel_name": "wordle-chat",
        "player_role_name": "wordle-player",
        "parse_function": score_parser.parse_wordle_score,
        "is_game_message": score_parser.is_wordle_message,
        "save_score_function": database.save_wordle_score,
        "get_leaderboard_function": database.get_wordle_leaderboard,
        "embed_builder_function": embed_builder.build_wordle_leaderboard_embed,
        "get_latest_game_number_function": database.get_latest_game_number_from_db,
        "update_latest_game_number_function": database.update_latest_game_number_in_db,
        "create_acknowledgement": score_parser.create_wordle_acknowledgement,
        "game_number_key": "game_number"
    },
    "connections": {
        "name": "Connections",
        "chat_channel_name": "connections-chat",
        "player_role_name": "connections-player",
        "parse_function": score_parser.parse_connections_result,
        "is_game_message": score_parser.is_connections_message,
        "save_score_function": database.save_connections_score,
        "get_leaderboard_function": database.get_connections_leaderboard,
        "embed_builder_function": embed_builder.build_connections_leaderboard_embed,
        "get_latest_game_number_function": database.get_latest_game_number_from_db,
        "update_latest_game_number_function": database.update_latest_game_number_in_db,
        "create_acknowledgement": score_parser.create_connections_acknowledgement,
        "game_number_key": "game_number"
    },
    "gisnep": {
        "name": "Gisnep",
        "chat_channel_name": "gisnep-chat",
        "player_role_name": "gisnep-player",
        "parse_function": score_parser.parse_gisnep_score,
        "is_game_message": score_parser.is_gisnep_message,
        "save_score_function": database.save_gisnep_score,
        "get_leaderboard_function": database.get_gisnep_leaderboard,
        "embed_builder_function": embed_builder.build_gisnep_leaderboard_embed,
        "get_latest_game_number_function": database.get_latest_game_number_from_db,
        "update_latest_game_number_function": database.update_latest_game_number_in_db,
        "game_number_key": "game_number"
    },
    "framed": {
        "name": "Framed",
        "chat_channel_name": "framed-chat",
        "player_role_name": "framed-player",
        "parse_function": score_parser.parse_framed_score,
        "is_game_message": score_parser.is_framed_message,
        "save_score_function": database.save_framed_score,
        "get_leaderboard_function": database.get_framed_leaderboard,
        "leaderboard_keys": LEADERBOARD_KEY_MAPPINGS["Framed"],
        "embed_builder_function": embed_builder.build_leaderboard_embed,
        "get_latest_game_number_function": database.get_latest_game_number_from_db,
        "update_latest_game_number_function": database.update_latest_game_number_in_db,
        "game_number_key": "game_number"
    },
    "bandle": {
        "name": "Bandle",
        "chat_channel_name": "bandle-chat",
        "player_role_name": "bandle-player",
        "parse_function": score_parser.parse_bandle_score,
        "is_game_message": score_parser.is_bandle_message,
        "save_score_function": database.save_bandle_score,
        "get_leaderboard_function": database.get_bandle_leaderboard,
        "leaderboard_keys": LEADERBOARD_KEY_MAPPINGS["Bandle"],
        "embed_builder_function": embed_builder.build_bandle_leaderboard_embed,
        "get_latest_game_number_function": database.get_latest_game_number_from_db,
        "update_latest_game_number_function": database.update_latest_game_number_in_db,
        "game_number_key": "game_number"
    },
    "minute_cryptic": {
        "name": "Minute Cryptic",
        "chat_channel_name": "minute-cryptic-chat",
        "player_role_name": "minute-cryptic-player",
        "parse_function": score_parser.parse_minute_cryptic_score,
        "is_game_message": score_parser.is_minute_cryptic_message,
        "save_score_function": database.save_minute_cryptic_score,
        "get_leaderboard_function": database.get_minute_cryptic_leaderboard,
        "leaderboard_keys": LEADERBOARD_KEY_MAPPINGS["Minute Cryptic"],
        "embed_builder_function": embed_builder.build_leaderboard_embed,
        "get_latest_game_number_function": database.get_latest_minute_cryptic_date,
        "update_latest_game_number_function": database.update_latest_minute_cryptic_date,
        "create_acknowledgement": score_parser.create_minute_cryptic_acknowledgement,
        "game_number_key": "game_date"
    },
    "word_salad": {
        "name": "Word Salad",
        "chat_channel_name": "word-salad-chat",
        "player_role_name": "word-salad-player",
        "parse_function": score_parser.parse_word_salad_score,
        "is_game_message": score_parser.is_word_salad_message,
        "save_score_function": database.save_word_salad_score,
        "get_leaderboard_function": database.get_word_salad_leaderboard,
        "leaderboard_keys": LEADERBOARD_KEY_MAPPINGS["Word Salad"],
        "embed_builder_function": embed_builder.build_leaderboard_embed,
        "get_latest_game_number_function": database.get_latest_game_number_from_db,
        "update_latest_game_number_function": database.update_latest_game_number_in_db,
        "game_number_key": "game_number"
    },
    "pips": {
        "name": "Pips",
        "chat_channel_name": "pips-chat",
        "player_role_name": "pips-player",
        "parse_function": score_parser.parse_pips_score,
        "is_game_message": score_parser.is_pips_message,
        "save_score_function": database.save_pips_score,
        "get_leaderboard_function": database.get_pips_leaderboard,
        "leaderboard_keys": LEADERBOARD_KEY_MAPPINGS["Pips"],
        "embed_builder_function": embed_builder.build_leaderboard_embed,
        "get_latest_game_number_function": database.get_latest_game_number_from_db,
        "update_latest_game_number_function": database.update_latest_game_number_in_db,
        "create_acknowledgement": score_parser.create_pips_acknowledgement,
        "game_number_key": "game_number"
    },
    "sexaginta": {
        "name": "Sexaginta-Quattuordle",
        "aliases": ["64ordle", "sexaginta"],
        "is_game_message": score_parser.is_sexaginta_message,
        "parse_function": score_parser.parse_sexaginta_score,
        "save_score_function": database.save_sexaginta_score,
        "get_leaderboard_function": database.get_sexaginta_leaderboard,
        "embed_builder_function": embed_builder.build_sexaginta_leaderboard_embed,
        "leaderboard_keys": LEADERBOARD_KEY_MAPPINGS["Sexaginta"],
        "get_latest_game_number_function": database.get_latest_game_number_from_db,
        "update_latest_game_number_function": database.update_latest_game_number_in_db,
        "chat_channel_name": "64ordle-chat",
        "player_role_name": "64ordle-player",
        "game_number_key": "game_number"
    }
}
