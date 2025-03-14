import discord
import asyncio
import datetime
import zoneinfo
from discord.ext import commands, tasks
from typing import Dict, List, Tuple, Optional, Any

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

    content = message.content
    processed = False

    # Check if the message is in the 'scores' channel
    if message.channel.name == "scores":
        # Check each game configuration
        for game_key, config in game_config.GAME_CONFIGS.items():
            if config["is_game_message"](content):
                print(f"Detected {config['name']} message from {message.author.display_name}")
                await handle_game_message(message, game_key, config)
                processed = True
                break

    if not processed:
        await bot.process_commands(message)  # Process commands if not a game message

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
                        f" {game_number}"
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

@tasks.loop(time=datetime.time(hour=23, minute=59, second=50, tzinfo=CET_TIMEZONE))
async def check_weekly_scores():
    """Check if we need to post weekly scores."""
    now = datetime.datetime.now(CET_TIMEZONE)
    if now.weekday() == 6:  # Sunday
        await post_weekly_scores()
        print("Weekly scores posted.")
    else:
        print("Not Sunday, skipping weekly scores.")

@tasks.loop(time=datetime.time(hour=0, minute=1, second=0, tzinfo=CET_TIMEZONE))
async def check_monthly_scores():
    """Check if we need to post monthly scores."""
    now = datetime.datetime.now(CET_TIMEZONE)
    if now.day == 1:  # First day of the month
        await post_monthly_scores()
        print("Monthly scores posted.")
    else:
        print("Not the first of the month, skipping monthly scores.")

async def post_weekly_scores():
    """Post the weekly scores to all game score channels."""
    wordle_scores, connections_scores = database.get_weekly_scores()
    
    # Create a mapping of game keys to their scores
    scores_by_game = {
        "wordle": wordle_scores,
        "connections": connections_scores
        # Any new games would be added here automatically when database.get_weekly_scores() is updated
    }
    
    # Iterate through all game configurations
    for game_key, config in game_config.GAME_CONFIGS.items():
        # Skip any games that don't have scores available
        if game_key not in scores_by_game or not scores_by_game[game_key]:
            continue
            
        # Get the score channel for this game
        channel = discord.utils.get(bot.get_all_channels(), name=config["score_channel_name"])
        if not channel:
            print(f"Warning: Could not find channel {config['score_channel_name']} for {config['name']} weekly scores")
            continue
            
        # Format and send the message
        scores = scores_by_game[game_key]
        
        if not scores:
            print(f"No weekly scores for {config['name']}")
            continue
            
        message = f"**📅 Weekly {config['name']} Scores**\n"
        for i, (player, score) in enumerate(scores, 1):
            message += f"{i}. {player}: {score} points\n"
            
        try:
            await channel.send(message)
            print(f"Weekly scores for {config['name']} posted to {channel.name}")
        except Exception as e:
            print(f"Error posting weekly scores for {config['name']}: {e}")

async def post_monthly_scores():
    """Post the monthly scores to all game score channels."""
    wordle_scores, connections_scores = database.get_monthly_scores()
    
    # Create a mapping of game keys to their scores
    scores_by_game = {
        "wordle": wordle_scores,
        "connections": connections_scores
        # Any new games would be added here automatically when database.get_monthly_scores() is updated
    }
    
    # Iterate through all game configurations
    for game_key, config in game_config.GAME_CONFIGS.items():
        # Skip any games that don't have scores available
        if game_key not in scores_by_game or not scores_by_game[game_key]:
            continue
            
        # Get the score channel for this game
        channel = discord.utils.get(bot.get_all_channels(), name=config["score_channel_name"])
        if not channel:
            print(f"Warning: Could not find channel {config['score_channel_name']} for {config['name']} monthly scores")
            continue
            
        # Format and send the message
        scores = scores_by_game[game_key]
        
        if not scores:
            print(f"No monthly scores for {config['name']}")
            continue
            
        message = f"**📅 Monthly {config['name']} Scores**\n"
        for i, (player, score) in enumerate(scores, 1):
            message += f"{i}. {player}: {score} points\n"
            
        try:
            await channel.send(message)
            print(f"Monthly scores for {config['name']} posted to {channel.name}")
        except Exception as e:
            print(f"Error posting monthly scores for {config['name']}: {e}")

if __name__ == "__main__":
    bot.run(TOKEN)
