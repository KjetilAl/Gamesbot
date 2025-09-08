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
                    updated_stats = database.update_player_stats(
                        message.author.id,
                        message.author.display_name,
                        game_info["game_number"],
                        game_info["attempts"],
                        game_info.get("skill"),
                        game_info.get("luck")
                    )
                    post_message = post_generator.generate_wordle_post(
                        message.author.display_name,
                        game_info["game_number"],
                        game_info["attempts"],
                        game_info.get("skill"),
                        game_info.get("luck"),
                        updated_stats
                    )

                    # Find the game's chat channel and post the message there
                    channel_name = config.get("chat_channel_name")
                    game_channel = discord.utils.get(message.guild.channels, name=channel_name)
                    if game_channel:
                        await game_channel.send(post_message)
                    else:
                        print(f"Warning: Could not find channel '{channel_name}' for {config['name']}. Posting in original channel.")
                        await message.channel.send(post_message)

                elif game_key == "connections":
                    config["save_score_function"](
                        message.author.id,
                        message.author.display_name,
                        game_info["game_number"],
                        game_info.get("total_score"),
                        game_info.get("mistake_count"),
                        game_info.get("perfect_game"),
                        game_info.get("solved_purple_first"),
                        game_info.get("skill"),
                        game_info.get("uniqueness")
                    )
                    updated_stats = database.update_connections_stats(
                        message.author.id,
                        message.author.display_name,
                        game_info.get("mistake_count", 0),
                        game_info.get("perfect_game", False),
                        game_info.get("solved_purple_first", False)
                    )
                    post_message = post_generator.generate_connections_post(
                        message.author.display_name,
                        game_info["game_number"],
                        game_info,
                        updated_stats
                    )

                    # Find the game's chat channel and post the message there
                    channel_name = config.get("chat_channel_name")
                    game_channel = discord.utils.get(message.guild.channels, name=channel_name)
                    if game_channel:
                        await game_channel.send(post_message)
                    else:
                        print(f"Warning: Could not find channel '{channel_name}' for {config['name']}. Posting in original channel.")
                        await message.channel.send(post_message)

                elif game_key == "framed":
                    config["save_score_function"](
                        message.author.id, message.author.display_name,
                        game_info["game_number"],
                        game_info["attempts"], 
                        game_info["total_score"]
                    )
                elif game_key == "gisnep":
                    # Save score
                    config["save_score_function"](
                        str(message.author.id), message.author.display_name,
                        game_info["game_number"],
                        game_info["completion_time"]
                    )

                    # Update puzzle stats
                    database.update_gisnep_puzzle_stats(
                        game_info["game_number"],
                        game_info["completion_time"]
                    )

                    # Update player stats
                    player_stats = database.update_gisnep_player_stats(
                        str(message.author.id),
                        message.author.display_name,
                        game_info["completion_time"]
                    )

                    # Get server stats for the puzzle
                    server_stats = database.get_gisnep_puzzle_stats(game_info["game_number"])

                    # Generate commentary
                    post_message = post_generator.generate_gisnep_post(
                        message.author.display_name,
                        game_info["game_number"],
                        game_info["completion_time"],
                        player_stats,
                        server_stats
                    )

                    # Post commentary to the dedicated channel
                    channel_name = config.get("chat_channel_name")
                    game_channel = discord.utils.get(message.guild.channels, name=channel_name)
                    if game_channel:
                        await game_channel.send(post_message)
                    else:
                        print(f"Warning: Could not find channel '{channel_name}' for {config['name']}. Posting in original channel.")
                        await message.channel.send(post_message)
                elif game_key == "bandle":
                    config["save_score_function"](
                        message.author.id,
                        message.author.display_name,
                        game_info["game_number"],
                        game_info["attempts"],
                        game_info["found_total"],
                        game_info["found_percentage"],
                        game_info["current_streak"],
                        game_info["max_streak"],
                        game_info["bonus_rounds_completed"],
                        game_info["bonus_rounds_total"],
                        game_info["bonus_emojis"],
                        game_info["total_score"]
                    )
                    player_stats = database.update_bandle_player_stats(
                        message.author.id,
                        message.author.display_name,
                        game_info["attempts"],
                        game_info["bonus_rounds_completed"]
                    )
                    post_message = post_generator.generate_bandle_post(
                        message.author.display_name,
                        game_info,
                        player_stats
                    )
                    channel_name = config.get("chat_channel_name")
                    game_channel = discord.utils.get(message.guild.channels, name=channel_name)
                    if game_channel:
                        await game_channel.send(post_message)
                    else:
                        print(f"Warning: Could not find channel '{channel_name}' for {config['name']}. Posting in original channel.")
                        await message.channel.send(post_message)
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
                        game_info["hints_used"],
                        game_info["score"]
                    )
                elif game_key == "pips":
                    config["save_score_function"](
                        message.author.id, message.author.display_name,
                        game_info["game_number"],
                        game_info["difficulty"],
                        game_info["completion_time"],
                        game_info["score"],
                        game_info["cookie"]
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
                        try:
                            current_num = int(current_game_identifier)
                            latest_num = int(latest_game_identifier) if latest_game_identifier is not None else 0
                            if latest_game_identifier is None or current_num > latest_num:
                                should_update_db = True
                        except (ValueError, TypeError):
                            print(f"Could not compare game identifiers for {game_key}: '{current_game_identifier}' and '{latest_game_identifier}'. Skipping DB update for this game.")
    
                    # Update database if needed
                    if should_update_db:
                        config["update_latest_game_number_function"](game_key, str(current_game_identifier))
                        print(f"Updated latest {game_key} number to {current_game_identifier}")
    
                    # Handle role assignment and determine if an introduction is needed
                    should_introduce = await role_manager.handle_game_role_assignment(
                        message.guild,
                        message.author,
                        game_key,
                        config,
                        current_game_identifier,
                        latest_game_identifier
                    )
    
                    # Post introduction message if required
                    if should_introduce and game_key not in ["wordle", "connections", "gisnep", "bandle"]:
                        await role_manager.introduce_player_in_game_channel(
                            message.guild,
                            message.author,
                            config,
                            game_info
                        )
                
                # Acknowledge the score with an emoji
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

async def get_leaderboard_embed(game_key: str, period: str) -> Optional[discord.Embed]:
    """
    Fetches leaderboard data and builds a Discord embed for a given game and period.

    Args:
        game_key (str): The key for the game (e.g., "wordle").
        period (str): The leaderboard period ("weekly", "monthly", "overall").

    Returns:
        Optional[discord.Embed]: The generated embed, or None if an error occurs.
    """
    if game_key not in game_config.GAME_CONFIGS:
        print(f"Invalid game key '{game_key}' provided.")
        return None

    config = game_config.GAME_CONFIGS[game_key]
    game_name = config["name"]

    # 1. Fetch scores
    try:
        leaderboard_data = config["get_leaderboard_function"](period=period)
        if not leaderboard_data:
            return None  # No data, no embed.
    except Exception as e:
        print(f"Error fetching {period} leaderboard for {game_name}: {e}")
        return None

    # 2. Get the appropriate embed builder function
    builder_func = config.get("embed_builder_function")
    if not builder_func:
        print(f"No embed builder function defined for {game_name}.")
        return None

    # Define colors
    game_colors = {
        "Wordle": discord.Color.green(), "Connections": discord.Color.purple(), "Framed": discord.Color.red(),
        "Gisnep": discord.Color.blue(), "Bandle": discord.Color.gold(), "Minute Cryptic": discord.Color.dark_teal(),
        "Word Salad": discord.Color.green(), "Pips": discord.Color.orange(),
    }
    embed_color = game_colors.get(game_name, discord.Color.from_rgb(128, 128, 128))

    # 3. Build the embed
    title = f"🏆 The {game_name} {period.capitalize()} Leaderboard 🏆"

    # For dedicated builders (Wordle, Connections, Gisnep)
    if game_name in ["Wordle", "Connections", "Gisnep"]:
        return await builder_func(
            title=title,
            leaderboard_data=leaderboard_data,
            period=period,
            color=embed_color
        )
    # For the generic builder
    else:
        keys = config.get("leaderboard_keys")
        if not keys:
            print(f"Missing 'leaderboard_keys' for generic game {game_name}.")
            return None

        # Transform list of tuples into list of dicts
        rows = [dict(zip(keys, row)) for row in leaderboard_data]

        return await builder_func(
            game_name=game_name,
            title=title,
            rows=rows,
            period=period.capitalize(),
            color=embed_color
        )

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

    if embed:
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"Could not generate the {game_key} leaderboard for the {period} period. No data was found.")

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

        # Send embed if it was created successfully
        if leaderboard_embed:
            try:
                await leaderboard_channel.send(embed=leaderboard_embed)
                print(f"✅ {period.capitalize()} {game_name} leaderboard posted to #{channel_name}.")
            except discord.errors.HTTPException as e:
                print(f"❌ Error posting {game_name} embed: {e}. The embed might be too long.")
            except Exception as e:
                print(f"❌ An unexpected error occurred when posting {game_name} leaderboard: {e}")
        else:
            print(f"ℹ️ No leaderboard data for {game_name} for the {period} period. Nothing posted.")

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
