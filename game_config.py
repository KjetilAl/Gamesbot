"""
Game Configuration Module - Defines settings and constants for different games.
"""
import score_parser
import database

# Game configurations dictionary
GAME_CONFIGS = {
    "wordle": {
        "name": "Wordle",
        "score_channel_name": "wordle-score",
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
        "score_channel_name": "connections-score",
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
}
