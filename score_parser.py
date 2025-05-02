import re
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta, date

# Regular expressions for game patterns
WORDLE_PATTERN = re.compile(r'Wordle\s+(?:#?\s*)(\d+(?:,\d+)?)\s+([0-6X])/6(\*?)', re.IGNORECASE)
SKILL_LUCK_PATTERN = re.compile(r'Skill\s+(\d+)/99\s+Luck\s+(\d+)/99', re.MULTILINE | re.IGNORECASE)
CONNECTIONS_PATTERN = re.compile(r'Connections\s*Puzzle #(\d+)', re.IGNORECASE)
FRAMED_PATTERN = re.compile(r'Framed\s+#?(\d+)', re.IGNORECASE)
GISNEP_PATTERN = re.compile(r'#Gisnep.*in (\d{1,2}:\d{2})', re.IGNORECASE)
GISNEP_NUMBER_PATTERN = re.compile(r'No\. (\d+)', re.IGNORECASE)
BANDLE_PATTERN = re.compile(r"Bandle\s+#(\d+)\s+([xX]|\d+)/(\d+)", re.IGNORECASE)
BONUS_PATTERN = re.compile(r'Bonus Rounds: (\d+)/(\d+)', re.IGNORECASE)
MINUTE_CRYPTIC_HEADER_PATTERN = re.compile(r"Minute Cryptic - (\d+ \w+ \d+)")
MINUTE_CRYPTIC_CLUE_PATTERN = re.compile(r'"(.*?)" \((\d+)\)')
MINUTE_CRYPTIC_SCORE_PATTERN = re.compile(r"I scored: (.*)")
WORD_SALAD_NUMBER_PATTERN = re.compile(r"Word Salad #(\d+)", re.IGNORECASE)
WORD_SALAD_TIME_PATTERN = re.compile(r"⌛(\d+m\s*\d+s)", re.IGNORECASE)
WORD_SALAD_HINTS_PATTERN = re.compile(r"❓(\d+)", re.IGNORECASE)

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

def parse_connections_result(message_content: str) -> Optional[Dict[str, Any]]:
    """
    Extract puzzle number and all guesses from a Connections result (handles older formats).
    """
    lines = message_content.split("\n")
    puzzle_match = None
    puzzle_start_index = -1

    for i, line in enumerate(lines):
        if "Puzzle #" in line:
            puzzle_match = re.search(r"Puzzle #(\d+)", line)
            puzzle_start_index = i
            break

    if not puzzle_match:
        print("Connections - Not a valid Connections result (puzzle number not found)")
        return None

    puzzle_number = int(puzzle_match.group(1))

    # Process the game lines
    game_lines = [line.strip() for line in lines[puzzle_start_index + 1:]
                  if line.strip() and not line.startswith("Archive")]

    # Track successful connections and mistakes
    found_colors = set()
    mistakes = 0
    all_guesses = []
    first_successful = {}

    for line in game_lines:
        # Identify complete color groups (identical emojis in a row)
        if len(line) == 4 and len(set(line)) == 1 and line[0] in "🟨🟪🟩🟦":
            color = line[0]
            all_guesses.append(color)

            # Track when each color was first found
            if color not in found_colors:
                found_colors.add(color)
                first_successful[color] = len(all_guesses) - 1 # Store index based on all_guesses
        else:
            # Not a complete group - this is a mistake
            mistakes += 1
            all_guesses.append("X") # Add mistake to all_guesses list

    # Calculate score details
    # Pass mistake_count to score calculation if needed for total score logic
    score_details = calculate_connections_score(all_guesses, found_colors, first_successful, mistakes)


    return {
        "puzzle_number": puzzle_number,
        "guesses": all_guesses,
        "num_guesses": len(all_guesses),  # <-- Added num_guesses here
        **score_details
    }

# Keep your calculate_connections_score function as is if it correctly uses the parameters passed
def calculate_connections_score(guesses, found_colors, first_successful, mistake_count):
    """
    Calculate the Connections score based on guesses.
    """
    base_points = {"🟪": 4, "🟦": 3, "🟩": 2, "🟨": 1}
    total_score = 0

    # Add base points for each color found
    for color in found_colors:
        total_score += base_points[color]

    # Bonus points
    all_groups_found = len(found_colors) == 4
    no_mistakes = mistake_count == 0

    # Bonus for solving all in just 4 attempts (no mistakes)
    if all_groups_found and no_mistakes:
        total_score += 5

    # Bonus for getting purple or blue first
    # Check if keys exist before accessing
    if "🟪" in first_successful and first_successful["🟪"] == 0:
        total_score += 2  # +2 for getting purple in first attempt
    elif "🟦" in first_successful and first_successful["🟦"] == 0:
        total_score += 1  # +1 for getting blue in first attempt


    # Penalty for mistakes
    total_score -= mistake_count

    return {
        "total_score": total_score,
        "found_colors": list(found_colors),
        "solved_purple_first": "🟪" in first_successful and first_successful.get("🟪", -1) == 0, # Use .get() for safety
        "solved_blue_first": "🟦" in first_successful and first_successful.get("🟦", -1) == 0, # Use .get() for safety
        "finished_game": len(found_colors) == 4,
        "correct_guesses": len(found_colors), # This might be correct based on the logic, or it should be len(guesses) - mistake_count if guesses includes X
        "mistake_count": mistake_count
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

def parse_bandle_score(message_content: str) -> Optional[Dict[str, Any]]:
    """Parses a Bandle score from a message, including individual bonus rounds."""
    match = BANDLE_PATTERN.search(message_content)
    bonus_match = BONUS_PATTERN.search(message_content)

    if not match:
        return None

    game_number = int(match.group(1))
    attempts_str = match.group(2).lower()
    max_attempts = int(match.group(3))
    solved = attempts_str != "x"
    attempts = int(attempts_str) if solved else max_attempts + 1
    score = max(6 - attempts, 0) if solved else 0

    bonus_completed = int(bonus_match.group(1)) if bonus_match and bonus_match.group(1) else 0
    bonus_total = int(bonus_match.group(2)) if bonus_match and bonus_match.group(2) else 0
    bonus_emojis_str = bonus_match.group(3).strip() if bonus_match and bonus_match.group(3) else ""

    # Define the bonus category emojis
    bonus_category_emojis = ["🎤", "🖼️", "🧑", "🌍", "🧩", "📅", "💿", "⏱️", "🎸"]

    # Check for the presence of each bonus emoji
    bonus_categories_completed = {emoji: emoji in bonus_emojis_str for emoji in bonus_category_emojis}

    print(f"Bandle: Game #{game_number}, Attempts: {attempts}, Solved: {solved}, Score: {score}, Bonus Completed: {bonus_completed}/{bonus_total}, Bonus Categories: {bonus_categories_completed}")

    return {
        "game_number": game_number,
        "attempts": attempts,
        "solved": solved,
        "total_score": score,
        "bonus_completed": bonus_completed,
        "bonus_total": bonus_total,
        "bonus_categories": bonus_categories_completed, # Dictionary of individual category completion
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

def parse_word_salad_score(message_content: str) -> Optional[Dict[str, Any]]:
    """Parses a Word Salad score from a message."""
    print(f"Attempting to parse Word Salad content: {message_content}")

    number_match = WORD_SALAD_NUMBER_PATTERN.search(message_content)
    time_match = WORD_SALAD_TIME_PATTERN.search(message_content)
    hints_match = WORD_SALAD_HINTS_PATTERN.search(message_content)

    if not (number_match and time_match and hints_match):
        print("Word Salad - Could not match all basic patterns.")
        return None

    game_number = int(number_match.group(1))
    time_str = time_match.group(1)
    hints_used = int(hints_match.group(1))

    # Convert time string (e.g., "2m 33s") to total seconds
    total_seconds = 0
    time_parts = time_str.replace('m', 'm ').replace('s', '').split()
    for part in time_parts:
        if 'm' in part:
            total_seconds += int(part.replace('m', '')) * 60
        elif part: # Handle seconds part
             total_seconds += int(part)

    print(f"Parsed Word Salad data: Game #{game_number}, Time: {total_seconds}s, Hints: {hints_used}")

    return {
        "game_number": game_number,
        "completion_time_seconds": total_seconds,
        "hints_used": hints_used,
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
    
def create_wordle_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"
  
def create_wordle_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create a compact acknowledgement message for Wordle scores."""
    
    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", "?")
    skill = game_info.get("skill", "?")
    luck = game_info.get("luck", "?")
    grid = game_info.get("grid", "⬜⬜⬜⬜⬜")  # Placeholder if no grid available
    hard_mode = game_info.get("hard_mode", False)
    
    # Add hard mode indicator
    hard_mode_text = " (Hard Mode)" if hard_mode else ""

    # Handle missing skill and luck
    skill_text = f"Skill: {skill}/99" if skill is not None else "Skill: N/A"
    luck_text = f"Luck: {luck}/99" if luck is not None else "Luck: N/A"

    # Build the message
    message = f"@{display_name} just posted Wordle {game_number} {attempts}/6{hard_mode_text}\n"
    message += f"{grid}\n"
    message += f"{skill_text} | {luck_text}"

    return message

def create_connections_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_connections_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create a compact acknowledgement message for Connections scores."""
    
    puzzle_number = game_info.get("puzzle_number", "?")
    total_score = game_info.get("total_score", "?")
    guesses = game_info.get("num_guesses", "?")
    solved_purple_first = game_info.get("solved_purple_first", False)
    solved_blue_first = game_info.get("solved_blue_first", False)
    
    # Construct difficulty sequence
    difficulty_text = "🟪" if solved_purple_first else "🟦" if solved_blue_first else "🟨🟩"
    
    message = f"{difficulty_text} @{display_name} just posted Connections Puzzle #{puzzle_number}\n"
    message += f"Total Score: {total_score}\n"
    message += f"Guesses: {guesses}"
    
    return message

def create_framed_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_framed_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create introduction message for Framed players."""
    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", "?")
    solved = game_info.get("solved", False)
    
    if solved:
        return f"🎥 **{display_name}** solved Framed #{game_number} in {attempts} guess{'es' if attempts != 1 else ''}!"
    else:
        return f"🎥 **{display_name}** just played Framed #{game_number} but couldn't figure it out!"

def create_gisnep_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_gisnep_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create introduction message for Gisnep players."""
    game_number = game_info.get("game_number", "?")
    completion_time = game_info.get("completion_time", "?")

    return f"🎬 **{display_name}** just completed Gisnep #{game_number} in {completion_time} seconds!"

def create_bandle_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_bandle_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create introduction message for Bandle players."""
    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", "?")
    solved = game_info.get("solved", False)
    bonus_completed = game_info.get("bonus_completed", "?")
    bonus_total = game_info.get("bonus_total", "?")
    
    if solved:
        message = f"🎵 **{display_name}** just played Bandle #{game_number} and got it in {attempts}!"
    else:
        message = f"🎵 **{display_name}** just played Bandle #{game_number} but didn't get it!"
    
    if bonus_total > 0:
        message += f"\nBonus score: {bonus_completed}/{bonus_total}"
    return message

def create_minute_cryptic_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"
    
def create_minute_cryptic_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create introduction message for Minute Cryptic players."""
    game_date = game_info.get("game_date", "?")
    score_desc = game_info.get("score_description", "?")
    grid = game_info.get("grid", "")

    return (f"🤔 **{display_name}** just finished the Minute Cryptic for {game_date}!\n"
            f"Score: {score_desc}\n"
            f"{grid}")

def create_word_salad_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    return "🤖"

def create_word_salad_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create introduction message for Word Salad players."""
    game_number = game_info.get("game_number", "?")
    completion_time_seconds = game_info.get("completion_time_seconds", "?")
    hints_used = game_info.get("hints_used", "?")

    message = f"🥗 **{display_name}** just finished Word Salad #{game_number} in {completion_time_seconds} seconds with {hints_used} hints."

    return message
