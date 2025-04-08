import discord
import asyncio
import datetime
import zoneinfo
from discord.ext import commands, tasks
from typing import Dict, List, Tuple, Optional, Any
from datetime import date

# Import custom modules
import database
import score_parser
import game_config
import role_manager
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

@bot.event
async def on_ready():
    """Handler for when the bot is ready."""
    database.initialize_db()
    print(f'Logged in as {bot.user}')

    # Start the scheduled tasks
    check_weekly_scores.start()
    check_monthly_scores.start()

    # Check if we should post scores immediately
    now = datetime.datetime.now(CET_TIMEZONE)
    if now.weekday() == 6:  # Sunday
        await post_weekly_scores()
    if now.day == 1:
        await post_monthly_scores()

@bot.event
async def on_message(message):
    """Handler for new messages."""
    if message.author.bot:
        return  # Ignore bot messages
    if not message.guild: # Ignore DMs
        return
    content = message.content
    processed = False
    # Check each game configuration to see if the message matches
    for game_key, config in game_config.GAME_CONFIGS.items():
        if config["is_game_message"](content):
            game_info = config["parse_function"](content)
            if game_info:
                print(f"Detected {config['name']} score from {message.author.display_name}") # Debug log
                user_id = message.author.id
                display_name = message.author.display_name
                # Save the score based on the game type
                if game_key == "wordle":
                    game_config["save_score_function"](
                        user_id, display_name,
                        game_info["game_number"],
                        game_info["attempts"],
                        game_info.get("skill"),  # Use .get() to handle None values
                        game_info.get("luck"),
                        game_info.get("hard_mode", False)
                    )

                elif game_key == "connections":
                    game_config["save_score_function"](user_id, display_name, game_info["puzzle_number"],
                                                       game_info["total_score"], game_info["num_guesses"],
                                                       game_info["solved_purple_first"], game_info["solved_blue_first"])

                elif game_key == "framed":
                    game_config["save_score_function"](user_id, display_name, game_info["game_number"],
                                                       game_info["attempts"], game_info["total_score"])

                elif game_key == "gisnep":
                    game_config["save_score_function"](user_id, display_name, game_info["game_number"],
                                                       game_info["completion_time"])

                elif game_key == "bandle":
                    game_config["save_score_function"](user_id, display_name, game_info["game_number"],
                                                       game_info["attempts"], game_info["total_score"],
                                                       game_info["bonus_completed"], game_info["bonus_total"])

                elif game_key == "minute_cryptic":
                 required_keys = ["game_date", "clue", "word_length", "grid", "score_description"]
                 if all(key in game_info for key in required_keys):
                     saved_successfully = False # Flag to track if save worked
                     try:
                         # Attempt to save the score
                         config["save_score_function"](
                             message.author.id,
                             message.author.display_name,
                             game_info["game_date"],
                             game_info["clue"],
                             game_info["word_length"],
                             game_info["grid"],
                             game_info["score_description"]
                         )
                         saved_successfully = True # Mark as successful if no exception
                         print(f"Successfully saved Minute Cryptic score for {message.author.display_name}") # Optional success log

                     except Exception as e:
                         # Catch potential errors during saving
                         print(f"Error saving Minute Cryptic score for {message.author.display_name}: {e}")
                         # Optionally notify the user
                         await message.channel.send(f"⚠️ Sorry {message.author.display_name}, there was an error saving your Minute Cryptic score.")

                     # --- Only proceed if saving was successful ---
                     if saved_successfully:
                         # Send acknowledgement
                         ack_message = config["create_acknowledgement"](message.author.display_name, game_info)
                         await message.channel.send(ack_message)

                         # --- Handle Role Assignment ---
                         try: # Add a try/except around role handling as well
                            game_identifier_key = config["game_number_key"] # Should be "game_date" for minute_cryptic
                            current_game_identifier = game_info.get(game_identifier_key) # str (date)
                            # Ensure you fetch the latest identifier correctly using the game_key
                            latest_identifier_str = config["get_latest_game_number_function"](game_key) # str
                            role_updated = False
                            is_newer = False

                            if current_game_identifier is not None:
                                # --- Comparison Logic (moved from inside the original try) ---
                                try:
                                     # Date comparison for Minute Cryptic
                                     current_date_str = str(current_game_identifier)
                                     latest_date_str = str(latest_identifier_str)

                                     # Use the correct default date string for comparison if latest is missing
                                     if not latest_date_str or latest_date_str == '0': # Check for '0' or empty
                                         latest_date_str = '2000-01-01' # Use the same default as get_latest...

                                     current_date = date.fromisoformat(current_date_str)
                                     latest_date = date.fromisoformat(latest_date_str)
                                     is_newer = current_date > latest_date

                                except (ValueError, TypeError) as e:
                                     print(f"Error comparing date identifiers in main_bot for {game_key}: {e}")
                                     is_newer = False # Safer default

                                # --- Role Assignment Call (moved from inside the original try) ---
                                role_updated = await role_manager.handle_game_role_assignment(
                                    message.guild,
                                    message.author,
                                    game_key,
                                    config,
                                    current_game_identifier,
                                    latest_identifier_str
                                    # Removed all_game_configs if not needed by role_manager
                                )

                                # --- Update DB and Introduce (moved from inside the original try) ---
                                if is_newer:
                                    print(f"Identifier {current_game_identifier} is newer than {latest_identifier_str} for {game_key}. Updating DB.")
                                    # Ensure the update function is awaited if it's async
                                    await config["update_latest_game_number_function"](game_key, str(current_game_identifier))

                                if role_updated:
                                    # Ensure introduce function is awaited if it's async
                                    await role_manager.introduce_player_in_game_channel(
                                        message.guild,
                                        message.author.display_name,
                                        config,
                                        game_info
                                    )
                         except Exception as e:
                             print(f"Error during role handling/DB update/introduction for {game_key} for {message.author.display_name}: {e}")
                             # Optionally notify user about role assignment issues
                             # await message.channel.send(f"⚠️ There was an issue updating roles for your score.")


                 else: # This else corresponds to 'if all(key in game_info...'
                     print(f"Minute Cryptic game_info dictionary missing keys for {message.author.display_name}: {game_info}")
                     await message.channel.send(f"⚠️ Couldn't process your Minute Cryptic score, {message.author.display_name}. Some information seems missing.")

                 # --- Mark as processed and break loop ---
                 processed = True
                 break # Stop checking other games

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
    for game_number, attempts, skill, luck, timestamp in scores:
        message += f"📅 {timestamp[:10]} | **Game {game_number}** — {attempts}/6 | Skill: {skill}/99 | Luck: {luck}/99\n"

    await ctx.send(message)

@bot.command()
async def leaderboard(ctx, game="wordle"):
    """Display the leaderboard for Wordle or Connections."""
    game = game.lower()

    if game not in game_config.GAME_CONFIGS:
        await ctx.send("Invalid game choice! Use 'wordle' or 'connections'.")
        return

    config = game_config.GAME_CONFIGS[game]
    leaderboard = config["get_leaderboard_function"]()
    game_name = config["name"]

    # Format the leaderboard display
    leaderboard_message = f"🏆 **{game_name} Leaderboard** 🏆\n"
    for i, (player, best_score) in enumerate(leaderboard, 1):
        leaderboard_message += f"{i}. {player} - {best_score} points\n"

    # Send leaderboard to channel
    await ctx.send(leaderboard_message)

async def post_scores(period: str):
    """Fetches and posts leaderboard scores for all games."""
    scores_by_game = {}
    leaderboard_channel_name = "leaderboards" # Or fetch from a central config

    # Fetch scores for each game using functions from game_config
    for game_key, config in game_config.GAME_CONFIGS.items():
        if "get_leaderboard_function" in config:
            try:
                scores = config["get_leaderboard_function"](period=period)
                if scores: # Only add if there are scores
                    scores_by_game[config["name"]] = scores
            except Exception as e:
                print(f"Error fetching {period} leaderboard for {config['name']}: {e}")

    # Find the 'leaderboards' channel
    leaderboard_channel = discord.utils.get(bot.get_all_channels(), name=leaderboard_channel_name)
    if not leaderboard_channel:
        print(f"Warning: Could not find the '{leaderboard_channel_name}' channel.")
        return

    # Iterate over each game and post scores
    if not scores_by_game:
        print(f"No {period} leaderboard data found for any game.")
        return

    for game_name, scores in scores_by_game.items():
        message = f"**📅 {period.capitalize()} {game_name} Leaderboard**\n"
        rank = 1
        for player_data in scores:
            # Adapt formatting based on data structure returned by leaderboard function
            if game_name == "Minute Cryptic": # Specific formatting for Minute Cryptic (solved count)
                player, score = player_data # Expecting (display_name, solved_count)
                message += f"{rank}. {player}: {score} solved\n"
            # Add elif for other games with non-standard score formats if needed
            else: # Default formatting (assuming score is points or similar)
                try:
                    player, score = player_data # Expecting (display_name, score)
                    message += f"{rank}. {player}: {score} points\n" # Or adjust unit
                except ValueError:
                    print(f"Warning: Could not unpack score data for {game_name}: {player_data}")
                    message += f"{rank}. {player_data[0]}: Score format error\n" # Fallback

            rank += 1

        if rank > 1: # Only send if there was data
            try:
                await leaderboard_channel.send(message)
                print(f"{period.capitalize()} {game_name} leaderboard posted.")
            except discord.errors.HTTPException as e:
                print(f"Error posting {period} {game_name} leaderboard (message too long?): {e}")
            except Exception as e:
                print(f"Error posting {period} {game_name} leaderboard: {e}")
        else:
            print(f"No valid scores formatted for {period} {game_name} leaderboard.")

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
