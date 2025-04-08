import re
from typing import Dict, List, Tuple, Optional, Any, Union

# Regular expressions for game patterns
WORDLE_PATTERN = re.compile(r'Wordle\s+(?:#?\s*)(\d+(?:,\d+)?)\s+([0-6X])/6(\*?)', re.IGNORECASE)
SKILL_LUCK_PATTERN = re.compile(r'Skill\s+(\d+)/99\s+Luck\s+(\d+)/99', re.MULTILINE | re.IGNORECASE)
CONNECTIONS_PATTERN = re.compile(r'Connections\nPuzzle #(\d+)')
FRAMED_PATTERN = re.compile(r'Framed\s+#?(\d+)', re.IGNORECASE)
GISNEP_PATTERN = re.compile(r'#Gisnep.*in (\d{1,2}:\d{2})', re.IGNORECASE)
GISNEP_NUMBER_PATTERN = re.compile(r'No\. (\d+)', re.IGNORECASE)
BANDLE_PATTERN = re.compile(r"Bandle\s+#(\d+)\s+([xX]|\d+)/(\d+)", re.IGNORECASE)
BONUS_PATTERN = re.compile(r'Bonus Rounds: (\d+)/(\d+)', re.IGNORECASE)
MINUTE_CRYPTIC_HEADER_PATTERN = re.compile(r'Minute Cryptic - (\d{1,2} \w+ \d{4})', re.IGNORECASE)
MINUTE_CRYPTIC_CLUE_PATTERN = re.compile(r'"(.*)" \((\d+)\)', re.IGNORECASE) # Extracts clue and word length
MINUTE_CRYPTIC_GRID_PATTERN = re.compile(r'([⚪️🟡🟣]+)', re.IGNORECASE) # Simplified grid capture
MINUTE_CRYPTIC_SCORE_PATTERN = re.compile(r'I scored: (.*)', re.IGNORECASE) # Captures the score description

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
    Extract puzzle number and all guesses from a Connections result.
    Args:
        message_content: The content of the message to parse

    Returns:
        Dictionary with puzzle number and guesses or None if not a valid Connections result
    """
    lines = message_content.split("\n")

    if not (lines[0].strip() == "Connections" and "Puzzle #" in lines[1]):
        print("Connections - Not a valid Connections result (header mismatch)")
        return None

    puzzle_match = re.search(r"Puzzle #(\d+)", lines[1])
    if not puzzle_match:
        print("Connections - Not a valid Connections result (puzzle number not found)")
        return None

    puzzle_number = int(puzzle_match.group(1))

    guesses = []
    for line in lines[2:]:
        line = line.strip()
        if len(line) == 4:
            colors = set(line)
            if len(colors) == 1:
                guesses.append(line[0])
            else:
                guesses.append("X")
        elif len(line) > 0:  # Handles if the line is not 4 characters long
            guesses.append("X")

    # Calculate the score details
    score_details = calculate_connections_score(guesses)

    return {
        "puzzle_number": puzzle_number,
        "guesses": guesses,
        **score_details  # Unpack the calculated score details
    }

def calculate_connections_score(guesses: List[str]) -> Dict[str, Any]:
    """
    Calculate the Connections score based on guesses.

    Args:
        guesses: List of guesses (🟪, 🟦, 🟩, 🟨, or X for mistakes)

    Returns:
        Dictionary with score details
    """
    base_points = {"🟪": 4, "🟦": 3, "🟩": 2, "🟨": 1}

    total_score = 0
    solved_purple_first = False
    solved_blue_first = False
    first_group = ""
    correct_guesses = 0
    mistake_count = 0

    for guess in guesses:
        if guess in base_points:
            if not first_group:
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

    finished_game = correct_guesses == 4

    return {
        "total_score": total_score,
        "num_guesses": len(guesses),
        "solved_purple_first": solved_purple_first,
        "solved_blue_first": solved_blue_first,
        "finished_game": finished_game,
        "correct_guesses": correct_guesses,
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
    """Parses a Bandle score from a message."""
    match = BANDLE_PATTERN.search(message_content)
    bonus_match = BONUS_PATTERN.search(message_content)  # Restore bonus round matching

    if not match:
        return None  # If no match, return nothing

    game_number = int(match.group(1))
    attempts_str = match.group(2).lower()  # Normalize to lowercase
    max_attempts = int(match.group(3))

    # Determine if the puzzle was solved
    solved = attempts_str != "x"
    attempts = int(attempts_str) if solved else max_attempts + 1  # Assign max+1 if failed

    # Score calculation
    score = max(6 - attempts, 0) if solved else 0

    # ✅ Extract bonus rounds
    bonus_completed = int(bonus_match.group(1)) if bonus_match else 0
    bonus_total = int(bonus_match.group(2)) if bonus_match else 0

    print(f"Bandle: Game #{game_number}, Attempts: {attempts}, Solved: {solved}, Score: {score}, Bonus Completed: {bonus_completed}/{bonus_total}")  # Debug logging

    return {
        "game_number": game_number,
        "attempts": attempts,
        "solved": solved,
        "total_score": score,
        "bonus_completed": bonus_completed,  # ✅ Fix KeyError
        "bonus_total": bonus_total          # ✅ Fix KeyError
    }
    
def parse_minute_cryptic_score(message_content: str) -> Optional[Dict[str, Any]]:
    """Parses a Minute Cryptic score message."""
    header_match = MINUTE_CRYPTIC_HEADER_PATTERN.search(message_content)
    clue_match = MINUTE_CRYPTIC_CLUE_PATTERN.search(message_content)
    grid_match = MINUTE_CRYPTIC_GRID_PATTERN.search(message_content)
    score_match = MINUTE_CRYPTIC_SCORE_PATTERN.search(message_content)

    if not (header_match and clue_match and grid_match and score_match):
        return None

    # Extract Date
    date_str = header_match.group(1)
    try:
        # Attempt to parse the date to validate and standardize
        game_date = datetime.strptime(date_str, '%d %B %Y').date()
    except ValueError:
        return None # Invalid date format

    # Extract other info
    clue = clue_match.group(1)
    word_length = int(clue_match.group(2))
    grid = grid_match.group(1) # This captures the sequence of circles
    score_desc = score_match.group(1).strip()

    # Interpret score description into a numerical value
    # Lower is better. Solved = 0, 1 over = 1, etc.
    # This logic might need refinement based on actual possible scores
    score_value = -1 # Default/unknown
    if "solved" in score_desc.lower():
        score_value = 0
    elif "over par" in score_desc.lower():
        parts = score_desc.split()
        try:
            score_value = int(parts[0])
        except (ValueError, IndexError):
            score_value = -1 # Failed to parse number

    return {
        "game_date": game_date.isoformat(), # Store as ISO string YYYY-MM-DD
        "clue": clue,
        "word_length": word_length,
        "grid": grid,
        "score_description": score_desc,
        "score_value": score_value, # Numerical score for ranking
        "solved": score_value == 0
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
    
def create_wordle_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create acknowledgement message for Wordle scores."""
    game_number = game_info.get("game_number", "?")
    hard_mode = game_info.get("hard_mode", False)

    # Add hard mode indicator
    hard_mode_text = " (Hard Mode)" if hard_mode else ""
    return f"📊 {display_name}'s Wordle {game_number}{hard_mode_text} recorded!\n"
  
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
    """Create acknowledgement message for Connections scores."""
    puzzle_number = game_info.get("puzzle_number", "?")
    return f"🟪 {display_name}'s Connections Puzzle #{puzzle_number} recorded!"

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
    """Create acknowledgement message for Framed scores."""
    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", "?")
    total_score = game_info.get("total_score", "?")

    return f"🎥 @{display_name} just posted a Framed score!⁠"

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
    """Create acknowledgement message for Gisnep scores."""
    game_number = game_info.get("game_number", "?")
    completion_time = game_info.get("completion_time", "?")

    return f"🎬 @{display_name} just posted a Gisnep score!"

def create_gisnep_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create introduction message for Gisnep players."""
    game_number = game_info.get("game_number", "?")
    completion_time = game_info.get("completion_time", "?")

    return f"🎬 **{display_name}** just completed Gisnep #{game_number} in {completion_time} seconds!"

def create_bandle_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create acknowledgement message for Bandle scores."""
    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", "?")
    total_score = game_info.get("total_score", "?")
    bonus_completed = game_info.get("bonus_completed", "?")
    bonus_total = game_info.get("bonus_total", "?")

    message = f"🎵 @{display_name} just posted a Bandle score!⁠"

    return message

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
    """Create acknowledgement message for Minute Cryptic scores."""
    game_date = game_info.get("game_date", "?")
    score_desc = game_info.get("score_description", "score recorded")
    # Format date back for display if needed, or keep as ISO
    return f"📝 {display_name}'s Minute Cryptic for {game_date} score recorded: {score_desc}."
    
def create_minute_cryptic_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create introduction message for Minute Cryptic players."""
    game_date = game_info.get("game_date", "?")
    score_desc = game_info.get("score_description", "?")
    grid = game_info.get("grid", "")

    return (f"🤔 **{display_name}** just finished the Minute Cryptic for {game_date}!\n"
            f"Score: {score_desc}\n"
            f"{grid}")
