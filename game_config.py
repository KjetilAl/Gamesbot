"""
Game Configuration Module - Defines settings and constants for different games.
"""
import score_parser
import database

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
        "get_latest_game_number_function": database.get_latest_game_number_from_db,
        "update_latest_game_number_function": database.update_latest_game_number_in_db,
        "create_acknowledgement": score_parser.create_wordle_acknowledgement,
        "create_introduction": score_parser.create_wordle_introduction
    },
    "connections": {
        "name": "Connections",
        "chat_channel_name": "connections-chat",
        "player_role_name": "connections-player",
        "parse_function": score_parser.parse_connections_result,
        "is_game_message": score_parser.is_connections_message,
        "save_score_function": database.save_connections_score,
        "get_leaderboard_function": database.get_connections_leaderboard,
        "get_latest_game_number_function": database.get_latest_game_number_from_db,
        "update_latest_game_number_function": database.update_latest_game_number_in_db,
        "create_acknowledgement": score_parser.create_connections_acknowledgement,
        "create_introduction": score_parser.create_connections_introduction
    }
"framed": {
    "name": "Framed",
    "chat_channel_name": "framed-chat",
    "player_role_name": "framed-player",
    "parse_function": score_parser.parse_framed_score,
    "is_game_message": score_parser.is_framed_message,
    "save_score_function": database.save_framed_score,
    "get_leaderboard_function": database.get_framed_leaderboard,
    "get_latest_game_number_function": database.get_latest_game_number_from_db,
    "update_latest_game_number_function": database.update_latest_game_number_in_db,
    "create_acknowledgement": score_parser.create_framed_acknowledgement,
    "create_introduction": score_parser.create_framed_introduction
    },
"gisnep": {
    "name": "Gisnep",
    "chat_channel_name": "gisnep-chat",
    "player_role_name": "gisnep-player",
    "parse_function": score_parser.parse_gisnep_score,
    "is_game_message": score_parser.is_gisnep_message,
    "save_score_function": database.save_gisnep_score,
    "get_leaderboard_function": database.get_gisnep_leaderboard,
    "get_latest_game_number_function": database.get_latest_game_number_from_db,
    "update_latest_game_number_function": database.update_latest_game_number_in_db,
    "create_acknowledgement": score_parser.create_gisnep_acknowledgement,
    "create_introduction": score_parser.create_gisnep_introduction
    },
"bandle": {
    "name": "Bandle",
    "chat_channel_name": "bandle-chat",
    "player_role_name": "bandle-player",
    "parse_function": score_parser.parse_bandle_score,
    "is_game_message": score_parser.is_bandle_message,
    "save_score_function": database.save_bandle_score,
    "get_leaderboard_function": database.get_bandle_leaderboard,
    "get_latest_game_number_function": database.get_latest_game_number_from_db,
    "update_latest_game_number_function": database.update_latest_game_number_in_db,
    "create_acknowledgement": score_parser.create_bandle_acknowledgement,
    "create_introduction": score_parser.create_bandle_introduction
    }
}

