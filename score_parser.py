import re
from typing import Dict, List, Tuple, Optional, Any, Union

# Regular expressions for game patterns
WORDLE_PATTERN = re.compile(r'Wordle\s+(?:#?\s*)(\d+(?:,\d+)?)\s+(\d)/6', re.IGNORECASE)
SKILL_LUCK_PATTERN = re.compile(r'Skill\s+(\d+)/99\s+Luck\s+(\d+)/99', re.MULTILINE | re.IGNORECASE)
CONNECTIONS_PATTERN = re.compile(r'Connections\nPuzzle #(\d+)')
FRAMED_PATTERN = re.compile(r'Framed\s+#?(\d+)', re.IGNORECASE)
GISNEP_PATTERN = re.compile(r'#Gisnep.*in (\d{1,2}:\d{2})', re.IGNORECASE)
GISNEP_NUMBER_PATTERN = re.compile(r'No\. (\d+)', re.IGNORECASE)
BANDLE_PATTERN = re.compile(r'Bandle\s+#?(\d+)\s+(\d|X)/(\d)', re.IGNORECASE)
BONUS_PATTERN = re.compile(r'Bonus Rounds: (\d+)/(\d+)', re.IGNORECASE)

def parse_wordle_score(message_content: str) -> Optional[Dict[str, Any]]:
    """
    Parse a Wordle score from a message.
    
    Args:
        message_content: The content of the message to parse
        
    Returns:
        Dictionary with parsed information or None if not a valid Wordle score
    """
    wordle_match = WORDLE_PATTERN.search(message_content)
    skill_luck_match = SKILL_LUCK_PATTERN.search(message_content)
    
    if not wordle_match:
        return None
        
    # Extract game number and attempts
    game_number_str = wordle_match.group(1).replace(",", "")
    game_number = int(game_number_str)
    attempts = int(wordle_match.group(2))
    
    # Extract skill and luck if available
    skill = None
    luck = None
    if skill_luck_match:
        skill = int(skill_luck_match.group(1))
        luck = int(skill_luck_match.group(2))
    
    return {
        "game_number": game_number,
        "attempts": attempts,
        "skill": skill,
        "luck": luck
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
        return None
    
    puzzle_match = re.search(r"Puzzle #(\d+)", lines[1])
    puzzle_number = puzzle_match.group(1) if puzzle_match else "Unknown"
    
    try:
        puzzle_number = int(puzzle_number)
    except ValueError:
        return None
    
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
    first_group = None
    correct_guesses = 0
    mistake_count = 0
    
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
    attempts = len(guess_sequence)
    solved = "🟩" in guess_sequence

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
    bonus_match = BONUS_PATTERN.search(message_content)
    
    if not match:
        return None
    
    game_number = int(match.group(1))
    attempts = match.group(2)
    max_attempts = int(match.group(3))
    
    solved = attempts != "X"
    attempts = int(attempts) if solved else max_attempts + 1  # If failed, set attempts above max

    # Score based on attempts
    score = max(6 - attempts, 0) if solved else 0

    # Extract bonus rounds
    bonus_completed = int(bonus_match.group(1)) if bonus_match else 0
    bonus_total = int(bonus_match.group(2)) if bonus_match else 0

    return {
        "game_number": game_number,
        "attempts": attempts,
        "solved": solved,
        "total_score": score,
        "bonus_completed": bonus_completed,
        "bonus_total": bonus_total
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
    
def create_wordle_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create acknowledgement message for Wordle scores."""
    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", "?")
    skill = game_info.get("skill", "?")
    luck = game_info.get("luck", "?")
    
    message = f"📊 {display_name}'s Wordle {game_number} recorded!\n"
    message += f"Attempts: {attempts}/6\n"
    
    if skill != "?" and luck != "?":
        message += f"Skill: {skill}/99 | Luck: {luck}/99"
    
    return message

def create_connections_acknowledgement(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create acknowledgement message for Connections scores."""
    puzzle_number = game_info.get("puzzle_number", "?")
    return f"🟨🟩🟦🟪 {display_name}'s Connections Puzzle #{puzzle_number} recorded!"
    
def create_wordle_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create a compact acknowledgement message for Wordle scores."""
    
    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", "?")
    skill = game_info.get("skill", "?")
    luck = game_info.get("luck", "?")
    grid = game_info.get("grid", "⬜⬜⬜⬜⬜")  # Placeholder if no grid available

    message = f"@{display_name} just posted a Wordle score\n"
    message += f"{grid} Wordle {game_number} {attempts}/6*\n"
    message += f"Skill {skill}/99\n"
    message += f"Luck {luck}/99"

    return message

def create_connections_introduction(display_name: str, game_info: Dict[str, Any]) -> str:
    """Create a compact acknowledgement message for Connections scores."""
    
    puzzle_number = game_info.get("puzzle_number", "?")
    total_score = game_info.get("total_score", "?")
    guesses = game_info.get("num_guesses", "?")
    solved_purple_first = game_info.get("solved_purple_first", False)
    solved_blue_first = game_info.get("solved_blue_first", False)
    
    # Construct difficulty sequence
    difficulty_text = "🟪" if solved_purple_first else "🟦" if solved_blue_first else "🟨🟩"
    
    message = f"@{display_name} just posted a Connections score⁠\n"
    message += f"{difficulty_text} Connections Puzzle #{puzzle_number}\n"
    message += f"Total Score: {total_score}\n"
    message += f"Guesses: {guesses}"
    
    return message
