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
            print(f"Detected {config['name']} score from {message.author.display_name}")
            processed = True
            
            # Parse the message content
            game_info = config["parse_function"](content)
            
            if not game_info:
                await message.channel.send(f"⚠️ Couldn't process your {config['name']} result.")
                break
            
            # Process the game score based on game type
            try:
                # Save the score (using the code from the handle_game_message function)
                if game_key == "wordle":
                    config["save_score_function"](
                        message.author.id, message.author.display_name, 
                        game_info["game_number"],
                        game_info["attempts"], 
                        game_info.get("skill"),
                        game_info.get("luck"),
                        game_info.get("hard_mode", False)
                    )
                elif game_key == "connections":
                    config["save_score_function"](
                        message.author.id, message.author.display_name, 
                        game_info["puzzle_number"],
                        game_info["total_score"], 
                        game_info["num_guesses"],
                        game_info["solved_purple_first"], 
                        game_info["solved_blue_first"]
                    )
                elif game_key == "framed":
                    config["save_score_function"](
                        message.author.id, message.author.display_name, 
                        game_info["game_number"],
                        game_info["attempts"], 
                        game_info["total_score"]
                    )
                elif game_key == "gisnep":
                    config["save_score_function"](
                        message.author.id, message.author.display_name, 
                        game_info["game_number"],
                        game_info["completion_time"]
                    )
                elif game_key == "bandle":
                    config["save_score_function"](
                        message.author.id, message.author.display_name,
                        game_info["game_number"],
                        game_info["attempts"],
                        game_info["total_score"],
                        game_info["bonus_completed"],
                        game_info["bonus_total"],
                        game_info.get("bonus_categories", {}) # Pass the bonus categories dictionary
                    )
                elif game_key == "minute_cryptic":
                    config["save_score_function"](
                        message.author.id, message.author.display_name,
                        game_info["game_date"],
                        game_info["clue"],
                        game_info["word_length"],
                        game_info["score_description"]
                    )
                elif game_key == "word_salad":
                    config["save_score_function"](
                        message.author.id, message.author.display_name,
                        game_info["game_number"],
                        game_info["completion_time_seconds"],
                        game_info["hints_used"]
                    )
                
                # Create acknowledgement and handle roles
                response = config["create_acknowledgement"](message.author.display_name, game_info)
                
                # Get the latest game number (date) from the database
                game_number_key = config["game_number_key"]
                latest_game_date_str = config["get_latest_game_number_function"](game_key)
                current_game_date_str = game_info[game_number_key]

                if current_game_date_str:
                    # For Minute Cryptic (dates)
                    if game_key == "minute_cryptic":
                        if latest_game_date_str is None or current_game_date_str > latest_game_date_str:
                            config["update_latest_game_number_function"](game_key, current_game_date_str)
                    # For all other games (numbers)
                    else:
                        current_num = int(current_game_date_str)
                        latest_num = int(latest_game_date_str) if latest_game_date_str is not None else 0
                        if latest_game_date_str is None or current_num > latest_num:
                            config["update_latest_game_number_function"](game_key, str(current_num))

                    # Handle role assignment
                    success = await role_manager.handle_game_role_assignment(
                        message.guild,
                        message.author,
                        game_key,
                        config,
                        current_game_date_str,
                        latest_game_date_str
                    )
                    if success:
                        await role_manager.introduce_player_in_game_channel(
                            message.guild,
                            message.author.display_name,
                            config,
                            game_info
                        )
                    
                # Replace message sending with emoji reaction
                await message.add_reaction("🤖")
                
            except Exception as e:
                print(f"Error processing {config['name']} score: {e}")
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
    """Fetches and posts leaderboard scores for all games with detailed stats."""
    scores_by_game = {}
    leaderboard_channel_name = "leaderboards" # Or fetch from a central config

    # Fetch scores for each game using functions from game_config
    for game_key, config in game_config.GAME_CONFIGS.items():
        if "get_leaderboard_function" in config:
            try:
                # Pass the period to the leaderboard function
                scores = config["get_leaderboard_function"](period=period)
                if scores: # Only add if there are scores
                    # Store the raw fetched data
                    scores_by_game[config["name"]] = scores
            except Exception as e:
                print(f"Error fetching {period} leaderboard for {config['name']}: {e}")
                import traceback
                traceback.print_exc() # Print traceback for better debugging

    # Find the 'leaderboards' channel
    leaderboard_channel = discord.utils.get(bot.get_all_channels(), name=leaderboard_channel_name)
    if not leaderboard_channel:
        print(f"Warning: Could not find the '{leaderboard_channel_name}' channel.")
        return

    # Iterate over each game and format/post scores
    if not scores_by_game:
        print(f"No {period} leaderboard data found for any game.")
        # Optional: Post a message indicating no scores found
        # await leaderboard_channel.send(f"No {period.capitalize()} leaderboard data found for any game this period.")
        return

    for game_name, scores in scores_by_game.items():
        message = f"🏆 **📅 {period.capitalize()} {game_name} Leaderboard** 🏆\n\n"

        if not scores:
             message += "No scores recorded for this period.\n\n"
        else:
            # Dynamically format based on game name and fetched columns
            if game_name == "Wordle":
                message += "**Rank | Player | Played | Avg Attempts | Solved | Hard Mode | Best Score**\n"
                message += "------- | -------- | -------- | -------- | -------- | -------- | --------\n"
                for i, row in enumerate(scores, 1):
                    (display_name, games_played, avg_attempts, solved_count, hard_mode_count, best_score) = row
                    message += f"{i}. {display_name} | {games_played} | {avg_attempts:.2f} | {solved_count} | {hard_mode_count} | {best_score}\n"
            elif game_name == "Connections":
                message += "**Rank | Player | Played | Total Score | Avg Score | Solved | Purple First | Blue First**\n"
                message += "------- | -------- | -------- | -------- | -------- | -------- | -------- | --------\n"
                for i, row in enumerate(scores, 1):
                    (display_name, games_played, total_score, avg_score, solved_count, purple_first_count, blue_first_count) = row
                    message += f"{i}. {display_name} | {games_played} | {total_score} | {avg_score:.2f} | {solved_count} | {purple_first_count} | {blue_first_count}\n"
            elif game_name == "Framed":
                 message += "**Rank | Player | Played | Total Score | Avg Attempts | Solved**\n"
                 message += "------- | -------- | -------- | -------- | -------- | --------\n"
                 for i, row in enumerate(scores, 1):
                     (display_name, games_played, total_score, avg_attempts, solved_count) = row
                     message += f"{i}. {display_name} | {games_played} | {total_score} | {avg_attempts:.2f} | {solved_count}\n"
            elif game_name == "Gisnep":
                message += "**Rank | Player | Played | Avg Time | Best Time**\n"
                message += "------- | -------- | -------- | -------- | --------\n"
                for i, row in enumerate(scores, 1):
                    (display_name, games_played, avg_time, best_time) = row
                    # Format time from seconds to M:SS
                    avg_minutes, avg_seconds = divmod(int(avg_time), 60)
                    best_minutes, best_seconds = divmod(int(best_time), 60)
                    message += f"{i}. {display_name} | {games_played} | {avg_minutes:02d}:{avg_seconds:02d} | {best_minutes:02d}:{best_seconds:02d}\n"
            elif game_name == "Bandle":
                 message += "**Rank | Player | Played | Total Score | Avg Attempts | Solved | Bonus (🎤🖼️🧑🌍🧩📅💿⏱️🎸)**\n"
                 message += "------- | -------- | -------- | -------- | -------- | -------- | -------------------------\n"
                 for i, row in enumerate(scores, 1):
                     (display_name, games_played, total_score, avg_attempts, solved_count,
                      bonus_microphone_count, bonus_frame_count, bonus_person_count, bonus_globe_count, bonus_puzzle_count,
                      bonus_calendar_count, bonus_cd_count, bonus_timer_count, bonus_guitar_count) = row
                     bonus_counts = [bonus_microphone_count, bonus_frame_count, bonus_person_count, bonus_globe_count,
                                     bonus_puzzle_count, bonus_calendar_count, bonus_cd_count, bonus_timer_count, bonus_guitar_count]
                     bonus_display = " ".join([str(count) for count in bonus_counts])
                     message += f"{i}. {display_name} | {games_played} | {total_score} | {avg_attempts:.2f} | {solved_count} | {bonus_display}\n"
            elif game_name == "Minute Cryptic":
                message += "**Rank | Player | Played | Solved | Avg Score**\n"
                message += "------- | -------- | -------- | -------- | --------\n"
                for i, row in enumerate(scores, 1):
                    (display_name, games_played, solved_count, avg_score) = row
                    message += f"{i}. {display_name} | {games_played} | {solved_count} | {avg_score:.2f}\n"
            elif game_name == "Word Salad":
                message += "**Rank | Player | Played | Avg Time | Best Time | Avg Hints**\n"
                message += "------- | -------- | -------- | -------- | -------- | --------\n"
                for i, row in enumerate(scores, 1):
                    (display_name, games_played, avg_time, best_time, avg_hints) = row
                    # Format time from seconds to M:SS
                    avg_minutes, avg_seconds = divmod(int(avg_time), 60)
                    best_minutes, best_seconds = divmod(int(best_time), 60)
                    message += f"{i}. {display_name} | {games_played} | {avg_minutes:02d}:{avg_seconds:02d} | {best_minutes:02d}:{best_seconds:02d} | {avg_hints:.2f}\n"

        # Send the formatted leaderboard message
        if scores or "No scores recorded" in message: # Send even if no scores for the period
            try:
                # Use code blocks for better formatting of the table-like structure
                await leaderboard_channel.send(f"```markdown\n{message}\n```")
                print(f"{period.capitalize()} {game_name} leaderboard posted.")
            except discord.errors.HTTPException as e:
                print(f"Error posting {period} {game_name} leaderboard (message too long?): {e}")
                print(f"Attempting to send as multiple messages for {game_name}...")
                # Handle message too long - split and send
                messages = [message[i:i+2000] for i in range(0, len(message), 2000)] # Simple split
                for msg in messages:
                    try:
                        await leaderboard_channel.send(f"```markdown\n{msg}\n```")
                        await asyncio.sleep(1) # Add a small delay
                    except Exception as inner_e:
                         print(f"Error sending part of message for {game_name}: {inner_e}")
            except Exception as e:
                print(f"Error posting {period} {game_name} leaderboard: {e}")
        else:
            print(f"No scores fetched for {period} {game_name}.")

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
