import discord
import asyncio
import datetime
import zoneinfo
from discord.ext import commands, tasks
from typing import Dict, List, Tuple, Optional, Any
from datetime import date
import traceback

# Import custom modules
import database
import score_parser
import game_config
import role_manager
import post_generator
import embed_builder
from config import TOKEN

# Get the CET time zone
CET_TIMEZONE = zoneinfo.ZoneInfo("Europe/Berlin")

# Enable message content intent
intents = discord.Intents.all()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Player Stats Handlers ---
def get_wordle_stats(user_id: int, user_name: str, game_info: dict) -> dict:
    """Gets Wordle player stats."""
    return database.update_player_stats(
        user_id, user_name,
        game_info["game_number"], game_info["attempts"],
        game_info.get("skill"), game_info.get("luck")
    )

def get_connections_stats(user_id: int, user_name: str, game_info: dict) -> dict:
    """Gets Connections player stats."""
    return database.update_connections_stats(
        user_id, user_name,
        game_info.get("mistake_count", 0), game_info.get("perfect_game", False),
        game_info.get("solved_purple_first", False)
    )

def get_gisnep_stats(user_id: int, user_name: str, game_info: dict) -> dict:
    """Gets Gisnep player stats, including server stats."""
    database.update_gisnep_puzzle_stats(game_info["game_number"], game_info["completion_time"])
    player_stats = database.update_gisnep_player_stats(
        str(user_id), user_name, game_info["completion_time"]
    )
    server_stats = database.get_gisnep_puzzle_stats(game_info["game_number"])
    player_stats["server_stats"] = server_stats  # Embed server_stats
    return player_stats

def get_bandle_stats(user_id: int, user_name: str, game_info: dict) -> dict:
    """Gets Bandle player stats."""
    return database.update_bandle_player_stats(
        user_id, user_name,
        game_info["attempts"], game_info["bonus_rounds_completed"]
    )

def get_sexaginta_stats(user_id: int, user_name: str, game_info: dict) -> dict:
    """Gets Sexaginta-quattuordle player stats."""
    return database.update_sexaginta_stats(user_id, user_name, game_info)

def get_framed_stats(user_id: int, user_name: str, game_info: dict) -> dict:
    """Gets Framed player stats."""
    return database.update_framed_player_stats(user_id, user_name, game_info)

def get_word_salad_stats(user_id: int, user_name: str, game_info: dict) -> dict:
    """Gets Word Salad player stats."""
    return database.update_word_salad_player_stats(user_id, user_name, game_info)

def get_minute_cryptic_stats(user_id: int, user_name: str, game_info: dict) -> dict:
    """Gets Minute Cryptic player stats."""
    return database.update_minute_cryptic_player_stats(user_id, user_name, game_info)

def get_pips_stats(user_id: int, user_name: str, game_info: dict) -> dict:
    """Gets Pips player stats."""
    return database.update_pips_player_stats(user_id, user_name, game_info)

PLAYER_STATS_HANDLERS = {
    "wordle": get_wordle_stats,
    "connections": get_connections_stats,
    "gisnep": get_gisnep_stats,
    "bandle": get_bandle_stats,
    "sexaginta": get_sexaginta_stats,
    "framed": get_framed_stats,
    "word_salad": get_word_salad_stats,
    "minute_cryptic": get_minute_cryptic_stats,
    "pips": get_pips_stats,
}


@bot.event
async def on_ready():
    """Handler for when the bot is ready."""
    database.initialize_db()
    print(f'Logged in as {bot.user}')

    # Start the scheduled tasks
    check_weekly_scores.start()
    check_monthly_scores.start()

@bot.event
async def on_message(message):
    """Handler for new messages."""
    if message.author.bot:
        return
    if not message.guild:
        return
        
    content = message.content
    processed = False

    # --- Performance Optimization: Quick Guard Clause ---
    if "#" not in content and "wordle" not in content.lower():
        await bot.process_commands(message)
        return

    for game_key, config in game_config.GAME_CONFIGS.items():
        # FIX: Replace the underscore in game_key with a space for the name check
        game_name_for_check = game_key.replace('_', ' ')
        game_names_to_check = [game_name_for_check] + config.get("aliases", [])
        
        # This check is now robust and flexible
        is_name_match = any(name in content.lower() for name in game_names_to_check)
        is_game_message = config["is_game_message"](content)

        if is_name_match and is_game_message:
            processed = True
            
            # 1. Parse the message content
            game_info = config["parse_function"](content)
            
            if not game_info:
                await message.channel.send(f"⚠️ Couldn't process your {config['name']} result.")
                break
            
            try:
                # --- Simplified Score and Stat Handling ---
                post_message = None
                player_stats = {}

                # 2. Save score using the configured function
                if game_key == "wordle":
                    config["save_score_function"](message.author.id, message.author.display_name, game_info["game_number"], game_info["attempts"], game_info.get("skill"), game_info.get("luck"), game_info.get("hard_mode", False))
                elif game_key == "connections":
                    config["save_score_function"](message.author.id, message.author.display_name, game_info["game_number"], game_info.get("total_score"), game_info.get("mistake_count"), game_info.get("perfect_game"), game_info.get("solved_purple_first"), game_info.get("skill"), game_info.get("uniqueness"))
                elif game_key == "gisnep":
                    config["save_score_function"](str(message.author.id), message.author.display_name, game_info["game_number"], game_info["completion_time"])
                elif game_key == "bandle":
                    config["save_score_function"](message.author.id, message.author.display_name, game_info["game_number"], game_info["attempts"], game_info["found_total"], game_info["found_percentage"], game_info["current_streak"], game_info["max_streak"], game_info["bonus_rounds_completed"], game_info["bonus_rounds_total"], game_info["bonus_emojis"], game_info["total_score"])
                elif game_key == "framed":
                    config["save_score_function"](message.author.id, message.author.display_name, game_info["game_number"], game_info["attempts"], game_info["total_score"])
                elif game_key == "minute_cryptic":
                    config["save_score_function"](message.author.id, message.author.display_name, game_info["game_date"], game_info["clue"], game_info["word_length"], game_info["score_description"])
                elif game_key == "word_salad":
                    config["save_score_function"](message.author.id, message.author.display_name, game_info["game_number"], game_info["completion_time_seconds"], game_info["hints_used"], game_info["score"])
                elif game_key == "pips":
                    config["save_score_function"](message.author.id, message.author.display_name, game_info["game_number"], game_info["difficulty"], game_info["completion_time"], game_info["score"], game_info["cookie"])
                elif game_key == "sexaginta":
                    config["save_score_function"](message.author.id, message.author.display_name, game_info)

                if stats_handler := PLAYER_STATS_HANDLERS.get(game_key):
                    player_stats = stats_handler(message.author.id, message.author.display_name, game_info)

                game_number_key = config["game_number_key"]
                current_game_identifier = game_info.get(game_number_key)

                if current_game_identifier:
                    latest_game_identifier = config["get_latest_game_number_function"](game_key)
                    should_update_db = False
                    if game_key == "minute_cryptic":
                        if latest_game_identifier is None or date.fromisoformat(str(current_game_identifier)) > date.fromisoformat(str(latest_game_identifier)):
                            should_update_db = True
                    else:
                        if latest_game_identifier is None or int(current_game_identifier) > int(latest_game_identifier):
                            should_update_db = True

                if should_update_db:
                    config["update_latest_game_number_function"](game_key, str(current_game_identifier))

                should_introduce = await role_manager.handle_game_role_assignment(
                    message.guild, message.author, game_key,
                    config, current_game_identifier, latest_game_identifier
                )

                post_message = post_generator.generate_post(
                    game_key,
                    message.author.display_name,
                    game_info,
                    player_stats
                )

                # For Pips, the introduction is only posted when all difficulties are complete.
                # The should_introduce flag from handle_game_role_assignment tells us when this happens.
                if game_key == 'pips' and not should_introduce:
                    post_message = None

                if not post_message and config.get("create_acknowledgement"):
                    acknowledgement = config["create_acknowledgement"](message.author.display_name, game_info)
                    if acknowledgement.strip() != "🤖":
                        post_message = acknowledgement

                if post_message:
                    channel_name = config.get("chat_channel_name")
                    game_channel = discord.utils.get(message.guild.channels, name=channel_name)
                    if game_channel:
                        await game_channel.send(post_message)
                    else:
                        print(f"Warning: Could not find channel '{channel_name}'. Posting in original channel.")
                        await message.channel.send(post_message)

                await message.add_reaction("🤖")

            except Exception as e:
                print(f"Error processing {config['name']} score: {e}")
                traceback.print_exc()
                await message.channel.send(f"⚠️ There was an error processing your {config['name']} score.")
            
            break
    
    if not processed:
        await bot.process_commands(message)

@bot.command()
async def myscore(ctx):
    """Show the user's last 5 Wordle scores."""
    user_id = ctx.author.id
    scores = database.get_recent_scores(user_id, limit=5)

    if not scores:
        await ctx.send("No Wordle scores recorded for you yet!")
        return

    message = f"📊 **{ctx.author.display_name}'s Last 5 Wordle Scores**\n"
    for game_number, attempts, skill, luck, created_at in scores:
        message += f"📅 {created_at[:10]} | **Game {game_number}** — {attempts}/6 | Skill: {skill}/99 | Luck: {luck}/99\n"

    await ctx.send(message)

async def get_leaderboard_embed(game_key: str, period: str) -> Optional[discord.Embed]:
    """
    Fetches leaderboard data and builds a Discord embed for a given game and period.
    """
    if game_key not in game_config.GAME_CONFIGS:
        return None

    config = game_config.GAME_CONFIGS[game_key]
    game_name = config["name"]

    try:
        leaderboard_data = config["get_leaderboard_function"](period=period)
    except Exception as e:
        print(f"Error fetching {period} leaderboard for {game_name}: {e}")
        leaderboard_data = {} # Ensure leaderboard_data is a dict

    game_colors = {
        "Wordle": discord.Color.green(), "Connections": discord.Color.purple(),
        "Framed": discord.Color.red(), "Gisnep": discord.Color.blue(),
        "Bandle": discord.Color.gold(), "Minute Cryptic": discord.Color.dark_teal(),
        "Word Salad": discord.Color.green(), "Pips": discord.Color.orange(),
        "Sexaginta-Quattuordle": discord.Color.dark_gold(),
    }
    color = game_colors.get(game_name, discord.Color.from_rgb(128, 128, 128))
    title = f"🏆 The {game_name} {period.capitalize()} Leaderboard 🏆"

    return await embed_builder.build_embed_for_game(game_key, title, leaderboard_data, period, color)

@bot.command()
async def leaderboard(ctx, game: str = "wordle", period: str = "weekly"):
    """Display the leaderboard for a specific game and period."""
    game_key = game.lower()
    period = period.lower()

    if period not in ["weekly", "monthly", "overall"]:
        await ctx.send("Invalid period! Use 'weekly', 'monthly', or 'overall'.")
        return

    if game_key not in game_config.GAME_CONFIGS:
        valid_games = ", ".join(game_config.GAME_CONFIGS.keys())
        await ctx.send(f"Invalid game! Please choose from: {valid_games}")
        return

    embed = await get_leaderboard_embed(game_key, period)
    await ctx.send(embed=embed)

async def post_scores(period: str):
    """Fetches and posts leaderboard scores for each game to its respective channel."""
    print(f"--- Starting {period.capitalize()} Score Posting ---")

    for game_key, config in game_config.GAME_CONFIGS.items():
        game_name = config["name"]
        channel_name = config.get("chat_channel_name")

        if not channel_name:
            print(f"Skipping {game_name}: 'chat_channel_name' not configured.")
            continue

        leaderboard_channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
        if not leaderboard_channel:
            print(f"Warning: Could not find the '{channel_name}' channel for {game_name}.")
            continue

        # Generate the embed using the unified function
        leaderboard_embed = await get_leaderboard_embed(game_key, period)

        try:
            await leaderboard_channel.send(embed=leaderboard_embed)
            print(f"✅ {period.capitalize()} {game_name} leaderboard posted to #{channel_name}.")
        except discord.errors.HTTPException as e:
            print(f"❌ Error posting {game_name} embed: {e}. The embed might be too long.")
        except Exception as e:
            print(f"❌ An unexpected error occurred when posting {game_name} leaderboard: {e}")

    print(f"--- Finished {period.capitalize()} Score Posting ---")

@tasks.loop(time=datetime.time(hour=23, minute=59, second=50, tzinfo=CET_TIMEZONE))
async def check_weekly_scores():
    """Post weekly leaderboards on Sunday."""
    if datetime.datetime.now(CET_TIMEZONE).weekday() == 6:  # Sunday
        await post_scores("weekly")

@tasks.loop(time=datetime.time(hour=0, minute=1, second=0, tzinfo=CET_TIMEZONE))
async def check_monthly_scores():
    """Post monthly leaderboards on the first of the month."""
    if datetime.datetime.now(CET_TIMEZONE).day == 1:
        await post_scores("monthly")

if __name__ == "__main__":
    bot.run(TOKEN)
