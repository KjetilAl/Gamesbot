import discord
import re
import asyncio
import datetime
import zoneinfo
from discord.ext import commands, tasks
from database import initialize_db, save_wordle_score, get_recent_scores, get_overall_recent_wordle_scores
from database import save_connections_score, get_wordle_leaderboard, get_connections_leaderboard
from database import get_weekly_scores, get_monthly_scores
from database import get_latest_game_number_from_db, update_latest_game_number_in_db
from config import TOKEN

# Get the CET time zone
cet_timezone = zoneinfo.ZoneInfo("Europe/Berlin") #Berlin is in the CET timezone.

# Get the current time in CET
cet_now = datetime.datetime.now(cet_timezone)

print(cet_now)

# Enable message content intent
intents = discord.Intents.all()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Regular expressions to detect Wordle and Connections results
wordle_pattern = re.compile(r'Wordle\s+(?:#?\s*)(\d+(?:,\d+)?)\s+(\d)/6', re.IGNORECASE)
skill_luck_pattern = re.compile(r'Skill\s+(\d+)/99\s+Luck\s+(\d+)/99', re.MULTILINE | re.IGNORECASE)
connections_pattern = re.compile(r'Connections\nPuzzle #(\d+)')


@bot.event
async def on_ready():
    initialize_db()
    print(f'Logged in as {bot.user}')

    # Start the check tasks (only weekly/monthly scores, no role expiration task now)
    check_weekly_scores.start()
    check_monthly_scores.start()

    # Also check if we should post immediately
    now = datetime.datetime.now(cet_timezone)
    if now.weekday() == 6:  # Sunday
        await post_weekly_scores()
    if now.day == 1:
        await post_monthly_scores()

async def get_members_with_role(guild, role_name):
    """Fetches all members with a specific role."""
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        return [member for member in guild.members if role in member.roles]
    return []

async def remove_game_role(member, game_type):
    """Removes the game role from a member."""
    role_name = "wordle-player" if game_type == "Wordle" else "connections-player"
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role and role in member.roles:
        await member.remove_roles(role)

async def assign_game_role_and_channel(guild, member, game_type):
    """Assigns the game role to a member."""
    role_name = "wordle-player" if game_type == "Wordle" else "connections-player"
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        await member.add_roles(role)

async def get_latest_wordle_game_number_from_messages(channel):
    """
    Scans recent messages in the given channel, parses Wordle scores,
    and returns the highest game number found.
    Returns 0 if no Wordle scores are found or on error.
    """
    latest_game_number = 0
    try:
        async for message in channel.history(limit=200): # Adjust limit as needed
            wordle_match = wordle_pattern.search(message.content)
            if wordle_match:
                try:
                    game_number_str = wordle_match.group(1)
                    game_number = int(game_number_str.replace(",", ""))
                    latest_game_number = max(latest_game_number, game_number) # Find the maximum
                except ValueError:
                    print(f"Warning: Could not parse game number from message: {message.content}")
    except discord.errors.Forbidden:
        print(f"Error: Bot does not have permission to read message history in {channel.name}")
    return latest_game_number


async def get_latest_connections_puzzle_number_from_messages(channel):
    """
    Scans recent messages in the given channel, parses Connections puzzles,
    and returns the highest puzzle number found.
    Returns 0 if no Connections puzzles are found or on error.
    """
    latest_puzzle_number = 0
    try:
        async for message in channel.history(limit=200): # Adjust limit as needed
            if "Connections" in message.content and "Puzzle #" in message.content:
                puzzle_match = re.search(r"Puzzle #(\d+)", message.content)
                if puzzle_match:
                    try:
                        puzzle_number = int(puzzle_match.group(1))
                        latest_puzzle_number = max(latest_puzzle_number, puzzle_number) # Find the maximum
                    except ValueError:
                        print(f"Warning: Could not parse puzzle number from message: {message.content}")
    except discord.errors.Forbidden:
        print(f"Error: Bot does not have permission to read message history in {channel.name}")
    return latest_puzzle_number

async def handle_game_message(message, game_key, game_config):
    """Generic handler for game messages, using game-specific configuration."""
    guild = message.guild
    member = message.author
    display_name = message.author.display_name
    user_id = message.author.id
    channel = message.channel

    score_regex = game_config["score_regex"]
    save_score_func = game_config["save_score_func"]
    get_latest_game_number_func = game_config["get_latest_game_number_func"]
    introduction_message_func = game_config["introduction_message_func"]
    score_acknowledgement_message_func = game_config["score_acknowledgement_message_func"]


    wordle_match = score_regex.search(message.content) # Use game-specific regex
    skill_luck_match = None # Initialize skill_luck_match to None
    skill = None
    luck = None
    attempts = None

    if game_key == "wordle": # Special handling for wordle skill/luck regex
        skill_luck_regex = game_config["skill_luck_regex"]
        skill_luck_match = skill_luck_regex.search(message.content)

    if wordle_match: # Check if the main score regex matched (Wordle or Connections)
        game_number_str = wordle_match.group(1).replace(",", "")
        game_number = int(game_number_str)
        if game_key == "wordle": # Only wordle has attempts
            attempts = int(wordle_match.group(2))

        if game_key == "wordle" and skill_luck_match: # Process Wordle score with skill/luck
            skill = int(skill_luck_match.group(1))
            luck = int(skill_luck_match.group(2))
            save_score_func(user_id, display_name, game_number, attempts, skill, luck) # Call game-specific save function
        elif game_key == "connections": # Process Connections score
            result_info = await process_connections_result(message) # Connections processing is still separate for now
            if result_info:
                puzzle_number = result_info["puzzle_number"]
                save_score_func(user_id, display_name, puzzle_number, result_info["total_score"], result_info["num_guesses"], result_info["solved_purple_first"], result_info["solved_blue_first"]) # Call game-specific save function
            else:
                await message.channel.send("⚠️ Couldn't fully process your Connections result, but puzzle number was recorded.") # Fallback message if full processing fails

        else: # Just Wordle processing without skill/luck or other game type
            save_score_func(user_id, display_name, game_number, attempts, None, None) # Save Wordle score even if skill/luck is missing

        # Get the latest game number from messages in the channel
        latest_game_number_from_channel = await get_latest_game_number_func(channel) # Use game-specific function

        # Create the base acknowledgement message using the game-specific lambda
        if game_key == "wordle":
            response = score_acknowledgement_message_func(display_name, game_number, attempts, skill, luck)
        elif game_key == "connections":
             response = score_acknowledgement_message_func(display_name, game_number) # Connections ack message

        # If this is the latest game number posted in the channel, add role info
        if game_number >= latest_game_number_from_channel:
            role_name = game_config["player_role_name"]
            chat_channel_name = game_config["chat_channel_name"]

            # Revoke roles and assign new role (using generic functions)
            members_with_role = await get_members_with_role(guild, role_name)
            for member_to_revoke in members_with_role:
                await remove_game_role(member_to_revoke, game_config["name"]) # Use game name in remove_game_role
            await assign_game_role_and_channel(guild, member, game_config["name"]) # Use game name in assign_game_role

            # Append role and channel info to the response message
            response += f"\n\n{member.mention} You now have access to the {chat_channel_name} channel!"

            # Introduce player in game chat channel (using generic function)
            score_info = {} # Create score info dict
            if game_key == "wordle":
                score_info = {"game_number": game_number, "attempts": attempts, "skill": skill, "luck": luck}
            elif game_key == "connections":
                if result_info:
                    score_info = result_info # Use result info dict for connections

            await introduce_player_in_game_channel(guild, display_name, game_config["name"], score_info) # Use game name

        # Send the response message
        await message.channel.send(response)

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    print(f"Received message: {message.content[:30]}...")

    for game_key, game_config in game_configurations.items(): # Iterate through game configurations
        if game_config["name"].lower() in message.content.lower(): # Basic check if game name is in message
            print(f"Detected {game_config['name']} message from {message.author.display_name}")
            await handle_game_message(message, game_key, game_config) # Call generic handler
            return # Stop processing after handling a game message

    await bot.process_commands(message)  # Ensure command processing still happens

async def process_connections_result(message):
    """Processes a Connections result, calculates score, and stores it."""
    user_id = message.author.id
    display_name = message.author.display_name

    parsed_result = parse_connections_result(message.content)
    if not parsed_result:
        await message.channel.send("⚠️ Invalid Connections result format.")
        return None  # Indicate failure

    puzzle_number, guesses = parsed_result

    # Convert puzzle_number to integer if it's a string
    try:
        puzzle_number = int(puzzle_number)
    except ValueError:
        await message.channel.send("⚠️ Invalid puzzle number format.")
        return None

    total_score, num_guesses, solved_purple_first, solved_blue_first, finished_game = calculate_connections_score(guesses)

    save_connections_score(user_id, display_name, puzzle_number, total_score, num_guesses, solved_purple_first, solved_blue_first)

    # We'll return all the information but NOT send a message here
    result_info = {
        "puzzle_number": puzzle_number,
        "total_score": total_score,
        "num_guesses": num_guesses,
        "solved_purple_first": solved_purple_first,
        "solved_blue_first": solved_blue_first,
        "finished_game": finished_game
    }
    
    return result_info  # Return result info to indicate success

@bot.command()
async def myscore(ctx):
    """Show the user's last 5 Wordle scores."""
    user_id = ctx.author.id
    scores = get_recent_scores(user_id, limit=5)

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
    if game == "wordle":
        leaderboard = get_wordle_leaderboard()
        game_name = "Wordle"
    elif game == "connections":
        leaderboard = get_connections_leaderboard()
        game_name = "Connections"
    else:
        await ctx.send("Invalid game choice! Use 'wordle' or 'connections'.")
        return

    # Format the leaderboard display
    leaderboard_message = f"🏆 **{game_name} Leaderboard** 🏆\n"
    for i, (player, best_score) in enumerate(leaderboard, 1):  # Unpack the tuple correctly
        leaderboard_message += f"{i}. {player} - {best_score} points\n"

    # Send leaderboard to channel
    await ctx.send(leaderboard_message)

def parse_connections_result(message_content):
    """Extract puzzle number and all guesses (valid and invalid) from a Connections result."""
    lines = message_content.split("\n")

    if not (lines[0].strip() == "Connections" and "Puzzle #" in lines[1]):
        return None

    puzzle_match = re.search(r"Puzzle #(\d+)", lines[1])
    puzzle_number = puzzle_match.group(1) if puzzle_match else "Unknown"

    guesses = []
    for line in lines[2:]:
        line = line.strip()
        if len(line) == 4:
            colors = set(line)
            if len(colors) == 1:
                guesses.append(line[0])
            else:
                guesses.append("X")
        elif len(line) > 0: #Handles if the line is not 4 characters long.
            guesses.append("X")

    return puzzle_number, guesses

def calculate_connections_score(guesses):
    """Calculate the Connections score, considering order, correct guesses, and mistakes."""
    base_points = {"🟪": 4, "🟦": 3, "🟩": 2, "🟨": 1}

    total_score = 0
    solved_purple_first = False
    solved_blue_first = False
    first_group = None
    correct_guesses = 0
    mistake_count = 0
    finished_game = True

    for guess in guesses:
        if guess in base_points:
            if first_group is None:
                first_group = guess
            correct_guesses += 1
        elif guess == "X":
            mistake_count += 1

    if first_group == "🟪":
        solved_purple_first = True
        total_score += 2
    elif first_group == "🟦":
        solved_blue_first = True
        total_score += 1

    for guess in guesses:
        if guess in base_points:
            total_score += base_points[guess]

    if correct_guesses == 4 and mistake_count == 0:
        total_score += 5
    else:
        total_score -= mistake_count

    if correct_guesses < 4:
        finished_game = False

    return total_score, len(guesses), solved_purple_first, solved_blue_first, finished_game

@tasks.loop(time=datetime.time(hour=23, minute=59, second=50, tzinfo=cet_timezone))
async def check_weekly_scores():
    now = datetime.datetime.now(cet_timezone)
    if now.weekday() == 6:  # Sunday
        await post_weekly_scores()
        print("Weekly scores posted.")
    else:
        print("Not Sunday, skipping weekly scores.")

async def post_weekly_scores():
    wordle_scores, connections_scores = get_weekly_scores()
    wordle_channel = discord.utils.get(bot.get_all_channels(), name="wordle")
    connections_channel = discord.utils.get(bot.get_all_channels(), name="connections")

    if wordle_channel:
        message = "**📅 Weekly Wordle Scores**\n"
        for i, (player, score) in enumerate(wordle_scores, 1):
            message += f"{i}. {player}: {score} points\n"
        await wordle_channel.send(message)

    if connections_channel:
        message = "**📅 Weekly Connections Scores**\n"
        for i, (player, score) in enumerate(connections_scores, 1):
            message += f"{i}. {player}: {score} points\n"
        await connections_channel.send(message)

@tasks.loop(time=datetime.time(hour=0, minute=1, second=0, tzinfo=cet_timezone))
async def check_monthly_scores():
    now = datetime.datetime.now(cet_timezone)
    if now.day == 1:
        await post_monthly_scores()
        print("Monthly scores posted.")
    else:
        print("Not the first of the month, skipping monthly scores.")

# Dictionary to keep track of the latest game and puzzle number for each player
player_scores = {}

game_configurations = {
    "wordle": {
        "name": "Wordle",
        "score_channel_name": "wordle-score",
        "chat_channel_name": "wordle-chat",
        "player_role_name": "wordle-player",
        "score_regex": re.compile(r'Wordle\s+(?:#?\s*)(\d+(?:,\d+)?)\s+(\d)/6', re.IGNORECASE),
        "skill_luck_regex": re.compile(r'Skill\s+(\d+)/99\s+Luck\s+(\d+)/99', re.MULTILINE | re.IGNORECASE),
        "save_score_func": save_wordle_score,  # Function from database.py
        "get_leaderboard_func": get_wordle_leaderboard, # Function from database.py
        "get_latest_game_number_func": get_latest_wordle_game_number_from_messages, # Function to get latest game number
        "introduction_message_func": lambda display_name, score_info: # Inline function for intro message
            f"👋 **{display_name}** just completed Wordle #{score_info.get('game_number', '?')} in {score_info.get('attempts', '?')}/6 attempts!",
        "score_acknowledgement_message_func": lambda display_name, game_number, attempts, skill, luck:
            f"📊 {display_name}'s Wordle {game_number} recorded!\nAttempts: {attempts}/6\nSkill: {skill}/99 | Luck: {luck}/99",

    },
    "connections": {
        "name": "Connections",
        "score_channel_name": "connections-score",
        "chat_channel_name": "connections-chat",
        "player_role_name": "connections-player",
        "score_regex": connections_pattern, # Using existing connections_pattern regex
        "save_score_func": save_connections_score, # Function from database.py
        "get_leaderboard_func": get_connections_leaderboard, # Function from database.py
        "get_latest_game_number_func": get_latest_connections_puzzle_number_from_messages, # Function to get latest puzzle number
        "introduction_message_func": lambda display_name, score_info:
            f"👋 **{display_name}** just solved Connections Puzzle #{score_info.get('puzzle_number', '?')} with a score of {score_info.get('total_score', '?')}!",
        "score_acknowledgement_message_func": lambda display_name, puzzle_number:
            f"🟨🟩🟦🟪 {display_name}'s Connections Puzzle #{puzzle_number} recorded!",
    },
    # ... more games can be added here ...
}


async def post_monthly_scores():
    wordle_scores, connections_scores = get_monthly_scores()
    wordle_channel = discord.utils.get(bot.get_all_channels(), name="wordle")
    connections_channel = discord.utils.get(bot.get_all_channels(), name="connections")

    if wordle_channel:
        message = "**📅 Monthly Wordle Scores**\n"
        for i, (player, score) in enumerate(wordle_scores, 1):
            message += f"{i}. {player}: {score} points\n"
        await wordle_channel.send(message)

    if connections_channel:
        message = "**📅 Monthly Connections Scores**\n"
        for i, (player, score) in enumerate(connections_scores, 1):
            message += f"{i}. {player}: {score} points\n"
        await connections_channel.send(message)

async def introduce_player_in_game_channel(guild, player_name, game_type, score_info):
    """
    Sends a brief introduction message to the game's channel when a player posts a new score.
    
    Parameters:
    guild (discord.Guild): The server where the message was posted
    player_name (str): The display name of the player
    game_type (str): Either "wordle" or "connections"
    score_info (dict): Information about the player's score
    """
    # Find the appropriate channel
    channel_name = "wordle-chat" if game_type.lower() == "wordle" else "connections-chat"
    game_channel = discord.utils.get(guild.text_channels, name=channel_name)
    
    if not game_channel:
        print(f"Could not find {channel_name} channel")
        return
    
    # Craft a brief introduction message
    if game_type.lower() == "wordle":
        game_number = score_info.get("game_number", "?")
        attempts = score_info.get("attempts", "?")
        intro_message = f"👋 **{player_name}** just completed Wordle #{game_number} in {attempts}/6 attempts!"
    else:  # connections
        puzzle_number = score_info.get("puzzle_number", "?")
        total_score = score_info.get("total_score", "?")
        intro_message = f"👋 **{player_name}** just solved Connections Puzzle #{puzzle_number} with a score of {total_score}!"
    
    # Send the introduction to the game channel
    try:
        await game_channel.send(intro_message)
        print(f"Sent introduction message to {channel_name} ")
    except Exception as e:
        print(f"Error sending introduction to {channel_name} : {e}")

bot.run(TOKEN)
