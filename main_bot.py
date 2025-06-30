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
from embed_builder import build_leaderboard_embed
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
                        game_info["puzzle_number"],
                        game_info["completion_time_seconds"],
                        game_info["hints_used"],
                        calculated_score = game_info["score"]
                    )
                
                # Create acknowledgement and handle roles
                response = config["create_acknowledgement"](message.author.display_name, game_info)
                
                # Get the latest game number/date from the database
                game_number_key = config["game_number_key"]
                latest_game_identifier = config["get_latest_game_number_function"](game_key)
                current_game_identifier = game_info[game_number_key]

                if current_game_identifier:
                    # Handle database update for latest game number
                    should_update_db = False
    
                    # For Minute Cryptic (dates)
                    if game_key == "minute_cryptic":
                        if latest_game_identifier is None:
                            should_update_db = True
                        else:
                            try:
                                current_date = date.fromisoformat(str(current_game_identifier))
                                latest_date = date.fromisoformat(str(latest_game_identifier))
                                if current_date > latest_date:
                                    should_update_db = True
                            except ValueError as e:
                                print(f"Date parsing error in main_bot: {e}")
                    # For Word Salad and all other number-based games
                    else:
                        current_num = int(current_game_identifier)
                        latest_num = int(latest_game_identifier) if latest_game_identifier is not None else 0
                        if latest_game_identifier is None or current_num > latest_num:
                            should_update_db = True
    
                    # Update database if needed
                    if should_update_db:
                        config["update_latest_game_number_function"](game_key, str(current_game_identifier))
                        print(f"Updated latest {game_key} number to {current_game_identifier}")
    
                    # Handle role assignment - pass the identifiers as they are
                    success = await role_manager.handle_game_role_assignment(
                        message.guild,
                        message.author,
                        game_key,
                        config,
                        current_game_identifier,
                        latest_game_identifier
                    )
    
                    # If role was assigned successfully, introduce the player in the game channel
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
    """Fetches and posts leaderboard scores for all games using embeds."""
    scores_by_game = {}
    leaderboard_channel_name = "leaderboards"

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

    # Iterate over each game, format data for embed, build embed, and post
    if not scores_by_game:
        print(f"No {period} leaderboard data found for any game.")
        # Optional: Post a message indicating no scores found
        # await leaderboard_channel.send(f"No {period.capitalize()} leaderboard data found for any game this period.")
        return

    for game_name, scores in scores_by_game.items():
        # Format the fetched tuple data into a list of dictionaries for the embed function
        formatted_scores_for_embed = []
        # Define the mapping of database tuple index to dictionary key for each game
        # This makes the formatting cleaner
        game_data_mapping = {
            "Wordle": ["display_name", "games_played", "avg_attempts", "solved_count", "hard_mode_count", "best_score"],
            "Connections": ["display_name", "games_played", "total_score", "avg_score", "solved_count", "purple_first_count", "blue_first_count"],
            "Framed": ["display_name", "games_played", "total_score", "avg_attempts", "solved_count"],
            "Gisnep": ["display_name", "games_played", "avg_time", "best_time"],
            "Bandle": ["display_name", "games_played", "total_score", "avg_attempts", "solved_count",
                       "bonus_microphone_count", "bonus_frame_count", "bonus_person_count", "bonus_globe_count", "bonus_puzzle_count",
                       "bonus_calendar_count", "bonus_cd_count", "bonus_timer_count", "bonus_guitar_count"],
            "Minute Cryptic": ["display_name", "games_played", "solved_count", "avg_score"],
            "Word Salad": ["display_name", "games_played", "avg_time", "best_time", "avg_hints", "total_score", "avg_score"], # Updated keys to include total_score and avg_score
        }

        if game_name in game_data_mapping:
            keys = game_data_mapping[game_name]
            for row in scores:
                 player_data = dict(zip(keys, row))
                 # Add 'avg' and 'solved' keys for generic embed logic if needed, mapping to appropriate stats
                 if game_name == "Wordle":
                     player_data["avg"] = player_data["avg_attempts"]
                     player_data["solved"] = player_data["solved_count"]
                 elif game_name == "Connections":
                     player_data["avg"] = player_data["avg_score"]
                     player_data["solved"] = player_data["solved_count"]
                 elif game_name == "Framed":
                      player_data["avg"] = player_data["avg_attempts"]
                      player_data["solved"] = player_data["solved_count"]
                 elif game_name == "Gisnep":
                      player_data["avg"] = player_data["avg_time"] # Avg time
                      player_data["solved"] = player_data["games_played"] # Using games played as a 'solved' proxy for time games
                 elif game_name == "Bandle":
                      player_data["avg"] = player_data["avg_attempts"]
                      player_data["solved"] = player_data["solved_count"]
                 elif game_name == "Minute Cryptic":
                      player_data["avg"] = player_data["avg_score"]
                      player_data["solved"] = player_data["solved_count"]
                 elif game_name == "Word Salad":
                      player_data["avg"] = player_data["avg_score"] # Now using avg_score as the generic average
                      player_data["total"] = player_data["total_score"] # Add total score

                 formatted_scores_for_embed.append(player_data)
        else:
            print(f"Warning: No data mapping defined for game '{game_name}'. Skipping embed creation.")
            continue # Skip this game if mapping is missing


        # Define example colors (customize as needed)
        game_colors = {
            "Wordle": discord.Color.green(),
            "Connections": discord.Color.purple(),
            "Framed": discord.Color.red(),
            "Gisnep": discord.Color.blue(),
            "Bandle": discord.Color.gold(),
            "Minute Cryptic": discord.Color.dark_teal(),
            "Word Salad": discord.Color.green(),
        }
        embed_color = game_colors.get(game_name, discord.Color.from_rgb(128, 128, 128)) # Corrected gray color

        # Build the embed using the helper function
        leaderboard_embed = await build_leaderboard_embed(
            game_name=game_name, # Pass the game name
            title=f"{game_name} Leaderboard",
            rows=formatted_scores_for_embed,
            period=period.capitalize(),
            color=embed_color
        )

        # Send the embed
        try:
             await leaderboard_channel.send(embed=leaderboard_embed)
             print(f"{period.capitalize()} {game_name} leaderboard embed posted.")
        except discord.errors.HTTPException as e:
             print(f"Error posting {period} {game_name} leaderboard embed: {e}")
             print(f"Attempting to send as plain text for {game_name} due to embed error...")
             # Fallback to plain text if embed fails (e.g., too many fields)
             fallback_message = f"🏆 **📅 {period.capitalize()} {game_name} Leaderboard** 🏆\n\n"
             if formatted_scores_for_embed:
                 fallback_message += "Error displaying embed. Raw data:\n"
                 for i, row in enumerate(formatted_scores_for_embed, 1):
                      fallback_message += f"{i}. {row.get('display_name')}: {row}\n" # Print raw data
             else:
                  fallback_message += "No scores recorded for this period."
             try:
                 await leaderboard_channel.send(fallback_message)
             except Exception as inner_e:
                  print(f"Error sending fallback plain text for {game_name}: {inner_e}")

        except Exception as e:
             print(f"Error posting {period} {game_name} leaderboard embed: {e}")

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
