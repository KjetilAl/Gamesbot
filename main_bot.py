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

                # Save the score
                config["save_score_function"](message.author.id, message.author.display_name, game_info)

                # Send acknowledgement
                ack_message = config["create_acknowledgement"](message.author.display_name, game_info)
                await message.channel.send(ack_message)

                # --- Handle Role Assignment ---
                game_identifier_key = config["game_number_key"]
                current_game_identifier = game_info.get(game_identifier_key) # str (date or number)
                latest_identifier_str = config["get_latest_game_number_function"](game_key) # str

                role_updated = False
                is_newer = False

                if current_game_identifier is not None:
                    # --- UPDATED CALL: Pass game_key ---
                    role_updated = await role_manager.handle_game_role_assignment(
                        message.guild,
                        message.author,
                        game_key,  # <<< Pass the game_key from the loop
                        config,    # Pass the specific game's config dict
                        current_game_identifier,
                        latest_identifier_str
                    )

                    # --- Check if current identifier is newer BEFORE updating DB ---
                    # (Logic remains the same here)
                    try:
                        if game_key == "minute_cryptic":
                            try: # Inner try for date comparison
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
                            # Decide how to handle error - maybe assume not newer? Or log and skip update?
                            is_newer = False # Safer default than True? Depends on desired behavior.
                    else:
                        # Integer comparison for other games
                        try: # Inner try for integer comparison
                            current_num = int(current_game_identifier)
                            latest_num = int(latest_identifier_str) # latest_identifier_str is '0' by default if missing
                            is_newer = current_num > latest_num
                        except (ValueError, TypeError) as e:
                            print(f"Error comparing integer identifiers in main_bot for {game_key}: {e}")
                            is_newer = False # Safer default

                    # Update latest identifier in DB only if newer
                    if is_newer:
                        print(f"Identifier {current_game_identifier} is newer than {latest_identifier_str} for {game_key}. Updating DB.")
                        await config["update_latest_game_number_function"](game_key, str(current_game_identifier))

                # Introduce player if role updated
                if role_updated:
                    await role_manager.introduce_player_in_game_channel(
                        message.guild,
                        message.author.display_name,
                        config,
                        game_info
                    )
            # --- End Role Handling ---

            processed = True
            break # Stop checking other games

    if not processed:
        # If no game score was processed, pass the message to command handlers
        await bot.process_commands(message)
        
async def handle_game_message(message, game_key, game_config):
    """
    Handle a game message (Wordle, Connections, Framed, Gisnep, Bandle).
    
    Args:
        message: The Discord message
        game_key: The key for the game in the GAME_CONFIGS dictionary
        game_config: The game configuration dictionary
    """
    guild = message.guild
    member = message.author
    display_name = message.author.display_name
    user_id = message.author.id
    
    # Parse the message content
    game_info = game_config["parse_function"](message.content)
    
    if not game_info:
        await message.channel.send(f"⚠️ Couldn't process your {game_config['name']} result.")
        return
    
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
    
    # Create the acknowledgement message
    response = game_config["create_acknowledgement"](display_name, game_info)
    
  # Get the latest game number from the database
    game_number_key = game_config["game_number_key"]  # Use game_number_key from config
    latest_game_number = game_config["get_latest_game_number_function"](game_config["name"])
    print(  # DEBUGGING
                        f"{game_config['name']}: Retrieved latest_game_number ="
                        f" {latest_game_number}"
                    )
    current_game_number = game_info[game_number_key]

    # If this is the latest game, update roles and notify
    if current_game_number >= latest_game_number:
        game_config["update_latest_game_number_function"](game_config["name"], current_game_number)
        print(  # DEBUGGING
                        f"{game_config['name']}: Updated latest_game_number to"
                        f" {game_number_key}"
                    )
        
        # Handle role assignment
        success = await role_manager.handle_game_role_assignment(
             guild, 
             member, 
             game_config, 
             current_game_number,
             latest_game_number
)
        
        if success:
            chat_channel_name = game_config["chat_channel_name"]
            response += f"\n\n{member.mention} You now have access to the {chat_channel_name} channel!"
            await role_manager.introduce_player_in_game_channel(guild, display_name, game_config, game_info)
    
    # Send the response message
    await message.channel.send(response)

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
