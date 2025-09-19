import re
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta, date
import database

# Regular expressions for game patterns
WORDLE_PATTERN = re.compile(r'Wordle\s+(?:#?\s*)(\d+(?:,\d+)?)\s+([0-6X])/6(\*?)', re.IGNORECASE)
SKILL_LUCK_PATTERN = re.compile(r'Skill\s+(\d+)/99\s+Luck\s+(\d+)/99', re.MULTILINE | re.IGNORECASE)
CONNECTIONS_PATTERN = re.compile(r'Connections\s*Puzzle #(\d+)', re.IGNORECASE)
FRAMED_PATTERN = re.compile(r'Framed\s+#?(\d+)', re.IGNORECASE)
GISNEP_PATTERN = re.compile(r'#Gisnep.*in (\d{1,2}:\d{2})', re.IGNORECASE)
GISNEP_NUMBER_PATTERN = re.compile(r'No\. (\d+)', re.IGNORECASE)
BANDLE_PATTERN = re.compile(r"Bandle\s+#(\d+)\s+([xX]|\d+)/(\d+)", re.IGNORECASE)
BONUS_PATTERN = re.compile(r'Bonus Rounds: (\d+)/(\d+)(?:\s+(.+))?', re.IGNORECASE)
MINUTE_CRYPTIC_HEADER_PATTERN = re.compile(r"Minute Cryptic - (\d+ \w+ \d+)")
MINUTE_CRYPTIC_CLUE_PATTERN = re.compile(r'"(.*?)" \((\d+)\)')
MINUTE_CRYPTIC_SCORE_PATTERN = re.compile(r"I scored: (.*)")
WORD_SALAD_NUMBER_PATTERN = re.compile(r"Word Salad #(\d+)", re.IGNORECASE)
WORD_SALAD_TIME_PATTERN = re.compile(r"⌛(\d+m\s*\d+s)", re.IGNORECASE)
WORD_SALAD_HINTS_PATTERN = re.compile(r"❓(\d+)", re.IGNORECASE)
PIPS_PATTERN = re.compile(r"Pips\s+#(\d+)\s+(Easy|Medium|Hard)\s+(?:🟢|🟡|🔴)\s*\n(\d{1,2}:\d{2})\s*(🍪)?", re.IGNORECASE)

SEXAGINTA_HEADER_REGEX = re.compile(
    r"#SexagintaQuattuordle\s+(\d+).*?(?:\n| )"  # Capture game number, tolerate line breaks or spaces
    r"(?:.*?words unsolved:\s*\d+)?\s*"          # Optionally match the "words unsolved" part
    r"\(score\s*(\d+),\s*([0-9]{1,3})%\)",      # Capture score + percent
    re.IGNORECASE | re.DOTALL
)

def parse_sexaginta_score(content: str) -> Optional[dict]:
    match = SEXAGINTA_HEADER_REGEX.search(content)
    if not match:
        return None

    game_number = int(match.group(1))
    score = int(match.group(2))
    percent_solved = float(match.group(3))

    # Extract seed from URL
    seed_match = re.search(r"https://64ordle\.au/\?seed=(\d+)", content)
    seed = int(seed_match.group(1)) if seed_match else None

    # Return the parsed data, using the score from the post
    return {
        "game_number": game_number,
        "game_score": score,
        "performance_pct": percent_solved,
        "seed": seed,
    }

def parse_wordle_score(message_content: str) -> Optional[Dict[str, Any]]:
    wordle_match = WORDLE_PATTERN.search(message_content)
    skill_luck_match = SKILL_LUCK_PATTERN.search(message_content)
    
    if not wordle_match:
        return None
    
    # Extract game number and attempts
    game_number_str = wordle_match.group(1).replace(",", "")
    game_number = int(game_number_str)
    
    # Handle attempts (could be 'X' or a digit)
    attempts_str = wordle_match.group(2)
    attempts = 7 if attempts_str == 'X' else int(attempts_str)  # Use 7 to represent failure (beyond the 6 allowed attempts)
    
    # Check for hard mode
    hard_mode = wordle_match.group(3) == '*'
    
    # Extract skill and luck if available (optional)
    skill = None
    luck = None
    if skill_luck_match:
        skill = int(skill_luck_match.group(1))
        luck = int(skill_luck_match.group(2))
    
    # Extract the grid
    grid_lines = []
    lines = message_content.split('\n')
    for line in lines:
        # Check if the line consists only of Wordle grid characters
        if line and all(char in "🟩🟨⬜" for char in line):
            grid_lines.append(line)
    grid = '\n'.join(grid_lines)

    return {
        "game_number": game_number,
        "attempts": attempts,
        "solved": attempts <= 6,  # Add a solved flag for clarity
        "hard_mode": hard_mode,  # Add hard_mode flag
        "skill": skill,
        "luck": luck,
        "grid": grid  # Add the grid to the result
    }

# In score_parser.py

def parse_connections_result(message_content: str) -> Optional[Dict[str, Any]]:
    """
    Extract puzzle number, guesses, solve order, and other details from a Connections result.
    """
    lines = message_content.strip().split("\n")
    puzzle_match = re.search(r"Puzzle #(\d+)", message_content)
    if not puzzle_match:
        return None

    puzzle_number = int(puzzle_match.group(1))

    # Process game lines, starting after the puzzle number line
    game_lines = [line.strip() for line in lines if line.strip()]
    puzzle_start_index = -1
    for i, line in enumerate(game_lines):
        if f"Puzzle #{puzzle_number}" in line:
            puzzle_start_index = i
            break
    
    if puzzle_start_index == -1:
        game_lines_to_process = game_lines
    else:
        game_lines_to_process = game_lines[puzzle_start_index + 1:]

    all_guesses = []
    mistakes = 0
    found_colors = set()
    first_successful = {} # Stores the guess index of the first time a color was found
    
    # New: Detect a "Rainbow Wrong" guess
    rainbow_wrong_guess = False
    rainbow_set = {'🟨', '🟩', '🟦', '🟪'}

    for line in game_lines_to_process:
        # Skip metadata lines
        if line.lower().startswith(("skill", "uniqueness", "archive")):
            continue
        
        # Check for a successful group solve
        if len(line) == 4 and len(set(line)) == 1 and line[0] in "🟨🟩🟦🟪":
            color = line[0]
            all_guesses.append(color * 4) # Store the actual solved line
            if color not in found_colors:
                found_colors.add(color)
                first_successful[color] = len(all_guesses)
        # It's a mistake line
        else:
            mistakes += 1
            all_guesses.append(line) # Store the actual mistake content
            # Check if this mistake is a "Rainbow Wrong"
            if len(line) == 4 and set(line) == rainbow_set:
                rainbow_wrong_guess = True

    # New: Determine the solve order
    # Sort the found colors by the index of their first appearance
    sorted_colors = sorted(first_successful.items(), key=lambda item: item[1])
    solve_order = [color for color, index in sorted_colors]

    finished_game = len(found_colors) == 4
    perfect_game = finished_game and mistakes == 0

    return {
        "game_number": puzzle_number,
        "finished_game": finished_game,
        "perfect_game": perfect_game,
        "mistake_count": mistakes,
        "solved_purple_first": solve_order[0] == '🟪' if solve_order else False,
        "solve_order": solve_order,
        "rainbow_wrong_guess": rainbow_wrong_guess,
        "guesses": all_guesses, # Now contains actual guess content
        "num_guesses": len(all_guesses)
    }

def calculate_connections_score(guesses, found_colors, first_successful, mistake_count, skill_score=None):
    """
    Calculate the Connections score based on guesses and optionally Skill value.
    Ensures total_score never drops below 0 before skill is added.
    """
    base_points = {"🟪": 4, "🟦": 3, "🟩": 2, "🟨": 1}
    total_score = sum(base_points[color] for color in found_colors)

    all_groups_found = len(found_colors) == 4
    no_mistakes = mistake_count == 0

    if all_groups_found and no_mistakes:
        total_score += 5

    if first_successful.get("🟪") == 0:
        total_score += 2
    elif first_successful.get("🟦") == 0:
        total_score += 1

    total_score -= mistake_count

    # Ensure minimum score of 0 before skill bonus
    total_score = max(total_score, 0)

    if skill_score is not None:
        total_score += round(skill_score / 20)  # Normalize skill to a bonus (e.g., 0–5)

    return {
        "total_score": total_score,
        "found_colors": list(found_colors),
        "solved_purple_first": first_successful.get("🟪") == 0,
        "solved_blue_first": first_successful.get("🟦") == 0,
        "finished_game": all_groups_found,
        "correct_guesses": len(found_colors),
        "mistake_count": mistake_count,
        "skill": skill_score,
        "perfect_game": all_groups_found and no_mistakes
    }
    
def parse_framed_score(message_content: str) -> Optional[Dict[str, Any]]:
    """Parses a Framed score from a message."""
    match = FRAMED_PATTERN.search(message_content)
    if not match:
        return None

    game_number = int(match.group(1))
    guess_sequence = re.findall(r'[🟥🟩⬛]', message_content)
    
    # Determine attempts based on the position of the green square
    try:
        attempts = guess_sequence.index("🟩") + 1
        solved = True
    except ValueError:
        # Green square not found, meaning the puzzle was not solved
        attempts = len(guess_sequence)
        solved = False

    # Assign points based on number of attempts
    score = {1: 100, 2: 80, 3: 60, 4: 40, 5: 20, 6: 10}.get(attempts, 0) if solved else 0

    return {
        "game_number": game_number,
        "attempts": attempts,
        "solved": solved,
        "total_score": score
    }

def parse_gisnep_score(message_content: str) -> Optional[Dict[str, Any]]:
    """Parses a Gisnep score from a message."""
    time_match = GISNEP_PATTERN.search(message_content)
    game_match = GISNEP_NUMBER_PATTERN.search(message_content)
    
    if not time_match or not game_match:
        return None

    game_number = int(game_match.group(1))
    time_str = time_match.group(1)

    # Convert time to seconds
    parts = list(map(int, time_str.split(":")))
    if len(parts) == 2:
        minutes, seconds = parts
        total_seconds = minutes * 60 + seconds
    else:
        total_seconds = parts[0]

    return {
        "game_number": game_number,
        "completion_time": total_seconds
    }

def calculate_bandle_score(attempts: int, bonus_rounds_completed: int) -> int:
    """
    Calculates the score for Bandle based on attempts and bonus rounds.
    """
    # Base score: 60 for 1 attempt, 50 for 2, ..., 10 for 6. 0 for failed (7 attempts).
    base_score = max(0, (7 - attempts) * 10)

    # Bonus points for each completed bonus round
    bonus_score = bonus_rounds_completed * 5

    return base_score + bonus_score

def parse_bandle_score(message_content: str) -> Optional[Dict[str, Any]]:
    """Parses a Bandle score from a message, including individual bonus rounds."""
    match = BANDLE_PATTERN.search(message_content)
    bonus_match = BONUS_PATTERN.search(message_content)
    streak_match = re.search(r'Current Streak: (\d+)', message_content)
    max_streak_match = re.search(r'Max Streak: (\d+)', message_content)

    if not match:
        return None

    game_number = int(match.group(1))
    attempts_str = match.group(2).lower()
    found_total = int(match.group(3))
    solved = attempts_str != "x"
    attempts = int(attempts_str) if solved else found_total + 1

    found_percentage = 0
    if found_total > 0:
        found_percentage = (found_total - (attempts - 1)) / found_total if solved else 0

    bonus_rounds_completed = int(bonus_match.group(1)) if bonus_match and bonus_match.group(1) else 0
    bonus_rounds_total = int(bonus_match.group(2)) if bonus_match and bonus_match.group(2) else 0
    bonus_emojis = bonus_match.group(3).strip() if bonus_match and bonus_match.group(3) else ""

    current_streak = int(streak_match.group(1)) if streak_match else 0
    max_streak = int(max_streak_match.group(1)) if max_streak_match else 0

    # Calculate the total score
    total_score = calculate_bandle_score(attempts, bonus_rounds_completed)

    return {
        "game_number": game_number,
        "attempts": attempts,
        "found_total": found_total,
        "found_percentage": found_percentage,
        "current_streak": current_streak,
        "max_streak": max_streak,
        "bonus_rounds_completed": bonus_rounds_completed,
        "bonus_rounds_total": bonus_rounds_total,
        "bonus_emojis": bonus_emojis,
        "solved": solved,
        "total_score": total_score
    }
    
def parse_minute_cryptic_score(message_content: str) -> Optional[Dict[str, Any]]:
    """Parse a Minute Cryptic result message."""
    print(f"Attempting to parse Minute Cryptic content: {message_content}")

    try:
        header_match = MINUTE_CRYPTIC_HEADER_PATTERN.search(message_content)
        clue_match = MINUTE_CRYPTIC_CLUE_PATTERN.search(message_content)
        score_match = MINUTE_CRYPTIC_SCORE_PATTERN.search(message_content)

        if not (header_match and clue_match and score_match):
            print("Could not match all basic patterns.")
            return None

        # Extract Date
        date_str = header_match.group(1)
        try:
            # Attempt to parse the date to validate and standardize
            game_date = datetime.strptime(date_str, '%d %B %Y').date()
        except ValueError:
            print(f"Invalid date format: {date_str}")
            return None # Invalid date format

        # Extract other info
        clue_text = clue_match.group(1).strip()
        word_length = int(clue_match.group(2))
        score_desc = score_match.group(1).strip()

        # Interpret score description into a numerical value
        score_value = 0 # Default to 0 for par or solved
        solved = False
        if "solved" in score_desc.lower() or score_desc.lower() == "par":
            score_value = 0
            solved = True
        elif "over par" in score_desc.lower():
            parts = score_desc.split()
            try:
                number = int(parts[0])
                score_value = -number
            except (ValueError, IndexError):
                score_value = -1 # Failed to parse number, should investigate
        elif "below par" in score_desc.lower():
            parts = score_desc.split()
            try:
                number = int(parts[0])
                score_value = number
            except (ValueError, IndexError):
                score_value = -1 # Failed to parse number, should investigate

        game_info = {
            "game_date": game_date.isoformat(), # Store as ISO 8601 string (YYYY-MM-DD)
            "clue": clue_text,
            "word_length": word_length,
            "score_description": score_desc,
            "score_value": score_value, # Numerical score based on the new logic
            "solved": solved
        }
        print(f"Parsed Minute Cryptic data: {game_info}")
        return game_info

    except Exception as e:
        print(f"Error parsing Minute Cryptic score: {e}")
        import traceback
        traceback.print_exc()
        return None

def score_wordsalad(time_seconds: int, hints_used: int) -> int:
    """
    Calculates the Word Salad score based on completion time and hints used.
    Higher score is better.
    """
    tiers = [
        (30, 20), (60, 18), (120, 15), (300, 10), (600, 8),
        (900, 7), (1200, 6), (1500, 5), (1800, 4), (3600, 3),
        (5400, 2), (float('inf'), 1)
    ]
    # Find the base score for the given time_seconds
    base_score = next(score for limit, score in tiers if time_seconds < limit)
    
    # Deduct points for hints used
    total_score = base_score - hints_used
    
    # Ensure the score does not go below zero
    return max(total_score, 0)

def parse_word_salad_score(message_content: str) -> Optional[Dict[str, Any]]:

    if "word salad" not in message_content.lower():
        print("DEBUG: 'Word Salad' keyword not found in message_content.")
        return None

    puzzle_match = re.search(r"Word Salad\s*#(\d+)", message_content, re.IGNORECASE)
    if not puzzle_match:
        print("DEBUG: Failed to match 'Word Salad #' pattern (e.g., 'Word Salad #123').")
        return None
    game_number = int(puzzle_match.group(1))
    print(f"DEBUG: Game number found: {game_number}")

    time_match = re.search(r"⌛(\d+)m\s*(\d+)s", message_content)
    if not time_match:
        print("DEBUG: Failed to match 'Time' pattern (e.g., '⌛0m 43s').")
        return None
    minutes = int(time_match.group(1))
    seconds = int(time_match.group(2))
    completion_time_seconds = minutes * 60 + seconds
    print(f"DEBUG: Time found: {minutes}m {seconds}s ({completion_time_seconds} seconds)")

    hints_match = re.search(r"❓(\d+)", message_content)
    hints_used = int(hints_match.group(1)) if hints_match else 0
    print(f"DEBUG: Hints found: {hints_used}")

    # Calculate the new Word Salad score
    calculated_score = score_wordsalad(completion_time_seconds, hints_used)
    print(f"DEBUG: Calculated score: {calculated_score}")

    print("DEBUG: Word Salad parsing successful.")
    return {
        "game_number": game_number,
        "completion_time_seconds": completion_time_seconds,
        "hints_used": hints_used,
        "score": calculated_score,
    }

def calculate_pips_score(difficulty: str, time_seconds: int) -> int:
    """Calculates the score for Pips based on difficulty and time."""
    difficulty = difficulty.lower()
    if difficulty == 'easy':
        if time_seconds <= 20:
            return 10
        elif time_seconds <= 40:
            return 8
        elif time_seconds <= 60:
            return 6
        elif time_seconds <= 120:
            return 4
        elif time_seconds <= 180:
            return 2
        else:
            return 1
    elif difficulty == 'medium':
        if time_seconds <= 40:
            return 10
        elif time_seconds <= 80:
            return 8
        elif time_seconds <= 120:
            return 6
        elif time_seconds <= 160:
            return 4
        elif time_seconds <= 200:
            return 2
        else:
            return 1
    elif difficulty == 'hard':
        if time_seconds <= 60:
            return 10
        elif time_seconds <= 120:
            return 8
        elif time_seconds <= 180:
            return 6
        elif time_seconds <= 240:
            return 4
        elif time_seconds <= 300:
            return 2
        else:
            return 1
    return 0

def parse_pips_score(message_content: str) -> Optional[Dict[str, Any]]:
    """Parses a Pips score from a message."""
    match = PIPS_PATTERN.search(message_content)
    if not match:
        return None

    game_number = int(match.group(1))
    difficulty = match.group(2).lower()
    time_str = match.group(3)
    cookie = match.group(4) is not None

    # Convert time to seconds
    minutes, seconds = map(int, time_str.split(':'))
    completion_time = minutes * 60 + seconds

    # Calculate score
    score = calculate_pips_score(difficulty, completion_time)

    return {
        "game_number": game_number,
        "difficulty": difficulty,
        "completion_time": completion_time,
        "score": score,
        "cookie": cookie
    }

def is_bandle_message(message_content: str) -> bool:
    """Checks if a message contains a Bandle score."""
    return "bandle" in message_content.lower() and BANDLE_PATTERN.search(message_content) is not None

def is_gisnep_message(message_content: str) -> bool:
    """Checks if a message contains a Gisnep score."""
    return "#gisnep" in message_content.lower() and GISNEP_PATTERN.search(message_content) is not None

def is_framed_message(message_content: str) -> bool:
    """Checks if a message contains a Framed score."""
    return "framed" in message_content.lower() and FRAMED_PATTERN.search(message_content) is not None

def is_wordle_message(message_content: str) -> bool:
    """Check if a message contains Wordle results."""
    return "wordle" in message_content.lower() and WORDLE_PATTERN.search(message_content) is not None

def is_connections_message(message_content: str) -> bool:
    """Check if a message contains Connections results."""
    return "connections" in message_content.lower() and CONNECTIONS_PATTERN.search(message_content) is not None

def is_minute_cryptic_message(message_content: str) -> bool:
    """Checks if a message contains a Minute Cryptic score."""
    # Check for key phrases and patterns
    return "Minute Cryptic" in message_content and \
           MINUTE_CRYPTIC_HEADER_PATTERN.search(message_content) is not None and \
           MINUTE_CRYPTIC_SCORE_PATTERN.search(message_content) is not None

def is_word_salad_message(message_content: str) -> bool:
    """Checks if a message contains a Word Salad score."""
    # Look for the game name and game number pattern
    return "word salad #" in message_content.lower() and \
           WORD_SALAD_NUMBER_PATTERN.search(message_content) is not None

def is_pips_message(message_content: str) -> bool:
    """Checks if a message contains a Pips score."""
    return "pips #" in message_content.lower() and PIPS_PATTERN.search(message_content) is not None

def is_sexaginta_message(message_content: str) -> bool:
    """Checks if a message contains a Sexaginta-quattuordle score."""
    return "sexagintaquattuordle" in message_content.lower() and SEXAGINTA_HEADER_REGEX.search(message_content) is not None
    
def create_wordle_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_connections_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_framed_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_framed_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create an informative introduction message for Framed players."""
    user_id = game_info.get("user_id")
    stats = database.get_framed_stats(user_id)

    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", "?")
    
    message = (f"**{display_name}** solved Framed #{game_number} in {attempts} guesses!\n"
               f"They have played {stats['games_played']} games with an average score of {stats['avg_score']:.2f}.")
    return message

def create_gisnep_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_gisnep_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create an informative introduction message for Gisnep players."""
    user_id = game_info.get("user_id")
    stats = database.get_gisnep_stats(user_id)

    game_number = game_info.get("game_number", "?")
    completion_time = game_info.get("completion_time", 0)
    time_str = f"{completion_time // 60}:{completion_time % 60:02d}"

    message = (f"**{display_name}** finished Gisnep #{game_number} in {time_str}!\n"
               f"They have played {stats['games_played']} games with an average time of {stats['avg_time']:.2f}s.")
    return message

def create_bandle_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_bandle_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create an informative introduction message for Bandle players."""
    user_id = game_info.get("user_id")
    stats = database.get_bandle_stats(user_id)

    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", "?")
    
    message = (f"**{display_name}** finished Bandle #{game_number} in {attempts} attempts!\n"
               f"They have played {stats['games_played']} games and earned a total of {stats['total_bonus']} bonus points.")
    return message

def create_minute_cryptic_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"
    
def create_minute_cryptic_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create an informative introduction message for Minute Cryptic players."""
    user_id = game_info.get("user_id")
    stats = database.get_minute_cryptic_stats(user_id)

    game_date = game_info.get("game_date", "?")
    score_desc = game_info.get("score_description", "?")

    message = (f"**{display_name}** finished the Minute Cryptic for {game_date} with a score of {score_desc}!\n"
               f"They have played {stats['games_played']} games with an average score of {stats['avg_score']:.2f}.")
    return message

def create_word_salad_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_word_salad_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create an informative introduction message for Word Salad players."""
    user_id = game_info.get("user_id")
    stats = database.get_word_salad_stats(user_id)

    game_number = game_info.get("game_number", "?")
    score = game_info.get("score", "?")

    message = (f"**{display_name}** finished Word Salad #{game_number} with a score of {score}!\n"
               f"They have played {stats['games_played']} games with an average score of {stats['avg_score']:.2f}.")
    return message

def create_pips_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_pips_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create introduction message for Pips players."""
    game_number = game_info.get("game_number", "?")
    user_id = game_info.get("user_id")

    if user_id is None:
        return f"🏆 **{display_name}** just completed all Pips difficulties for game #{game_number}!"

    scores = database.get_pips_scores_for_game(user_id, game_number)

    if not scores:
         return f"🏆 **{display_name}** just completed all Pips difficulties for game #{game_number}!"

    total_score = sum(s['score'] for s in scores)
    cookie_count = sum(s['cookie'] for s in scores)

    message = f"🏆 **{display_name}** has completed all Pips difficulties for game #{game_number} with a total score of **{total_score}**!\n\n"

    for score in scores:
        time_min = score['completion_time'] // 60
        time_sec = score['completion_time'] % 60
        time_str = f"{time_min}:{time_sec:02d}"
        message += f"**{score['difficulty'].capitalize()}**: {time_str} ({score['score']} pts)"
        if score['cookie']:
            message += " 🍪"
        message += "\n"

    if cookie_count > 0:
        message += f"\nWow, {cookie_count} cookie{'s' if cookie_count > 1 else ''}! You're a top performer! 🍪"

    return message

