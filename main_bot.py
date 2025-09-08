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

@bot.command()
async def leaderboard(ctx, game="wordle", period="weekly"):
    """Display the leaderboard for a game."""
    game = game.lower()
    period = period.lower()

    if period not in ["weekly", "monthly", "overall"]:
        await ctx.send("Invalid period! Use 'weekly', 'monthly', or 'overall'.")
        return

    if game not in game_config.GAME_CONFIGS:
        await ctx.send("Invalid game! Use 'wordle' or 'connections'.")
        return

    config = game_config.GAME_CONFIGS[game]
    game_name = config["name"]

    if game == "wordle":
        leaderboard_data = database.get_wordle_leaderboard(period=period)

        message = f"🏆 **The Wordle {period.capitalize()} Roundup** 🏆\n\n"

        if leaderboard_data["top_players"]:
            medals = ["🥇", "🥈", "🥉"]
            for i, (player, score) in enumerate(leaderboard_data["top_players"]):
                message += f"{medals[i]} **{player}** - ⭐ Total Score: {score}\n"
        else:
            message += "No players ranked this period.\n"

        message += "\n**Superlatives:**\n"
        if leaderboard_data["einstein"]:
            player, avg_skill = leaderboard_data["einstein"]
            message += f"The Einstein Award 🧠: to **{player}** for the highest average skill score this period ({avg_skill:.1f}).\n"
        if leaderboard_data["lucky_charm"]:
            player, avg_luck = leaderboard_data["lucky_charm"]
            message += f"The Lucky Charm Award 🍀: to **{player}** for riding a wave of good fortune with the highest average luck this period ({avg_luck:.1f}).\n"
        if leaderboard_data["ironman"]:
            player, streak = leaderboard_data["ironman"]
            if streak > 1:
                message += f"The Ironman Award 🦾: to **{player}** for maintaining a flawless {streak} game winning streak!\n"

        await ctx.send(message)
        
    elif game == "connections":
        leaderboard_data = database.get_connections_leaderboard(period=period)
        embed = await embed_builder.build_connections_leaderboard_embed(
            title=f"🧩 The Connections {period.capitalize()} Conundrum 🧩",
            leaderboard_data=leaderboard_data,
            period=period,
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)
    elif game == "gisnep":
        leaderboard_data = database.get_gisnep_leaderboard(period=period)
        embed = await embed_builder.build_gisnep_leaderboard_embed(
            title=f"📖 The Gisnep Gazette {period.capitalize()} 📖",
            leaderboard_data=leaderboard_data,
            period=period,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    else:
        # Fallback to old leaderboard for other games
        leaderboard = config["get_leaderboard_function"](period=period)
        leaderboard_message = f"🏆 **{game_name} {period.capitalize()} Leaderboard** 🏆\n"
        # This part is likely incorrect for other games, but it's what was there before.
        try:
            for i, (player, best_score) in enumerate(leaderboard, 1):
                leaderboard_message += f"{i}. {player} - {best_score} points\n"
        except (ValueError, TypeError):
             leaderboard_message += "Could not display leaderboard. Data format is not supported by this command."

        await ctx.send(leaderboard_message)

async def post_scores(period: str):
    """Fetches and posts leaderboard scores for each game to its respective channel."""
    scores_by_game = {}

    # Fetch scores for each game using functions from game_config
    for game_key, config in game_config.GAME_CONFIGS.items():
        if "get_leaderboard_function" in config:
            try:
                scores = config["get_leaderboard_function"](period=period)
                if scores:
                    # Store scores with the game_key to retain access to config
                    scores_by_game[game_key] = scores
            except Exception as e:
                print(f"Error fetching {period} leaderboard for {config['name']}: {e}")
                import traceback
                traceback.print_exc()

    if not scores_by_game:
        print(f"No {period} leaderboard data found for any game.")
        return

    # Iterate over each game with scores, build embed, and post to the respective channel
    for game_key, scores in scores_by_game.items():
        config = game_config.GAME_CONFIGS[game_key]
        game_name = config["name"]
        channel_name = config.get("chat_channel_name")

        if not channel_name:
            print(f"Warning: 'chat_channel_name' not configured for {game_name}. Skipping.")
            continue

        leaderboard_channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
        if not leaderboard_channel:
            print(f"Warning: Could not find the '{channel_name}' channel for {game_name}.")
            continue

        # Define colors
        game_colors = {
            "Wordle": discord.Color.green(), "Connections": discord.Color.purple(), "Framed": discord.Color.red(),
            "Gisnep": discord.Color.blue(), "Bandle": discord.Color.gold(), "Minute Cryptic": discord.Color.dark_teal(),
            "Word Salad": discord.Color.green(),
            "Pips": discord.Color.orange(),
        }
        embed_color = game_colors.get(game_name, discord.Color.from_rgb(128, 128, 128))

        leaderboard_embed = None
        if game_name == "Wordle":
            leaderboard_embed = await embed_builder.build_wordle_leaderboard_embed(
                title=f"🏆 The Wordle {period.capitalize()} Roundup 🏆",
                leaderboard_data=scores,
                period=period,
                color=embed_color
            )

        elif game_name == "Connections":
            leaderboard_embed = await embed_builder.build_connections_leaderboard_embed(
                title=f"🧩 The Connections {period.capitalize()} Conundrum 🧩",
                leaderboard_data=scores,
                period=period,
                color=embed_color
            )

        elif game_name == "Gisnep":
            leaderboard_embed = await embed_builder.build_gisnep_leaderboard_embed(
                title=f"📖 The Gisnep Gazette {period.capitalize()} 📖",
                leaderboard_data=scores,
                period=period,
                color=embed_color
            )
        else:
            # Format data for embed for other games
            formatted_scores_for_embed = []
            game_data_mapping = {
                "Connections": ["display_name", "games_played", "total_score", "avg_score", "solved_count", "purple_first_count", "blue_first_count"],
                "Framed": ["display_name", "games_played", "total_score", "avg_attempts", "solved_count"],
                "Gisnep": ["display_name", "games_played", "avg_time", "best_time"],
                "Bandle": ["display_name", "games_played", "total_score", "avg_attempts", "solved_count",
                           "bonus_microphone_count", "bonus_frame_count", "bonus_person_count", "bonus_globe_count", "bonus_puzzle_count",
                           "bonus_calendar_count", "bonus_cd_count", "bonus_timer_count", "bonus_guitar_count"],
                "Minute Cryptic": ["display_name", "games_played", "solved_count", "avg_score"],
                "Word Salad": ["display_name", "games_played", "avg_time", "best_time", "avg_hints", "total_score", "avg_score"],
                "Pips": ["display_name", "total_score", "games_played", "cookie_count"],
            }
            if game_name in game_data_mapping:
                keys = game_data_mapping[game_name]
                for row in scores:
                    player_data = dict(zip(keys, row))
                    # Generic stats for embed
                    if game_name == "Connections":
                        player_data["avg"] = player_data["avg_score"]
                        player_data["solved"] = player_data["solved_count"]
                    elif game_name == "Framed":
                        player_data["avg"] = player_data["avg_attempts"]
                        player_data["solved"] = player_data["solved_count"]
                    elif game_name == "Gisnep":
                        player_data["avg"] = player_data["avg_time"]
                        player_data["solved"] = player_data["games_played"]
                    elif game_name == "Bandle":
                        player_data["avg"] = player_data["avg_attempts"]
                        player_data["solved"] = player_data["solved_count"]
                    elif game_name == "Minute Cryptic":
                        player_data["avg"] = player_data["avg_score"]
                        player_data["solved"] = player_data["solved_count"]
                    elif game_name == "Word Salad":
                        player_data["avg"] = player_data["avg_score"]
                        player_data["total"] = player_data["total_score"]
                    elif game_name == "Pips":
                        player_data["total_score"] = player_data["total_score"]
                        player_data["cookie_count"] = player_data["cookie_count"]
                    formatted_scores_for_embed.append(player_data)

            if formatted_scores_for_embed:
                leaderboard_embed = await embed_builder.build_leaderboard_embed(
                    game_name=game_name, title=f"{game_name} Leaderboard",
                    rows=formatted_scores_for_embed, period=period.capitalize(), color=embed_color
                )

        # Send embed
        if leaderboard_embed:
            try:
                await leaderboard_channel.send(embed=leaderboard_embed)
                print(f"{period.capitalize()} {game_name} leaderboard posted to #{channel_name}.")
            except discord.errors.HTTPException as e:
                print(f"Error posting {game_name} embed: {e}. Sending as text.")
                fallback_message = f"🏆 **📅 {period.capitalize()} {game_name} Leaderboard** 🏆\n\n(Error displaying embed, showing raw data)\n"
                fallback_message += str(scores)
                await leaderboard_channel.send(fallback_message)
            except Exception as e:
                print(f"An unexpected error occurred when posting {game_name} leaderboard: {e}")

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
