import random

def _generate_wordle_post(display_name: str, game_info: dict[str, any], player_stats: dict[str, any]) -> str:
    """
    Generates dynamic, human-like feedback for Wordle results.
    """
    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", 7) # Default to 7 for a failed state
    skill = game_info.get("skill") # Can be None
    luck = game_info.get("luck")   # Can be None

    # --- Part 1: The Opening Line (based on performance) ---
    if attempts > 6:
        return f"**{display_name}** was bested by Wordle #{game_number} today. Better luck tomorrow! 💪"
    
    if attempts == 1:
        opening_line = f"🤯 Legendary! **{display_name}** solved Wordle #{game_number} in a single guess!"
    elif attempts == 2:
        opening_line = f"🧠 Masterful work! **{display_name}** cracked Wordle #{game_number} in just two tries."
    elif attempts == 6:
        opening_line = f"😅 Whew! **{display_name}** clutched it on the final guess for Wordle #{game_number}."
    else: # Neutral case for 3, 4, 5 guesses
        opening_line = f"**{display_name}** solved Wordle #{game_number} in {attempts}/6."

    # --- Part 2: The Stat Spotlight (a single, interesting follow-up) ---
    spotlights = []
    
    # Check for new max streak from player_stats
    if player_stats.get("is_new_max_streak") and player_stats.get("current_streak", 0) > 3:
        spotlights.append(f"🚀 That's a new personal best streak of **{player_stats['current_streak']}**! Unstoppable!")
    
    # Check for exceptional skill or luck from game_info
    if skill is not None:
        if skill > 90:
            spotlights.append("With a **Skill** score of **90+**, that was a masterclass in deduction 🧐")
    
    if luck is not None:
        if luck > 85:
            spotlights.append("A **Luck** score over **85**? The dictionary gods were smiling today! ✨")
        elif luck < 15:
            spotlights.append(f"Only **{luck}** luck? They earned that win the hard way. Pure skill.")

    # Always have a default fallback if no other conditions are met
    if not spotlights:
        current_streak = player_stats.get("current_streak", 0)
        if current_streak > 2:
            spotlights.append(f"They're now on a **{current_streak}-game** winning streak 🔥")
        else:
            # A simple, neutral default
            win_percentage = player_stats.get("win_percentage", 0)
            spotlights.append(f"Their win percentage is holding steady at **{win_percentage:.1f}%**.")

    # Combine the opening line with a randomly chosen spotlight for variety
    return f"{opening_line}\n{random.choice(spotlights)}"
    
# In post_generator.py

def _generate_bandle_post(display_name: str, game_info: dict, player_stats: dict) -> str:
    """Generates a dynamic and tonally appropriate Bandle post."""
    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", 7)
    solved = game_info.get("solved", False)
    bonus_completed = game_info.get("bonus_rounds_completed", 0)
    bonus_total = game_info.get("bonus_rounds_total", 0)

    # --- Part 1: The Opening Line (based on performance) ---
    
    if not solved:
        opening_line = f"A tough one! The artist for Bandle #{game_number} stumped **{display_name}** today."
    elif attempts == 1:
        opening_line = f"🤯 A true music savant! **{display_name}** identified the artist for Bandle #{game_number} in a single guess!"
    elif attempts <= 3:
        opening_line = f"A great ear! **{display_name}** nailed the artist for Bandle #{game_number} in just {attempts} tracks 🎵"
    else: # Neutral case for 4-6 guesses
        opening_line = f"**{display_name}** finished their set for Bandle #{game_number}, getting the artist in {attempts} guesses."

    # --- Part 2: The Stat Spotlight (The Encore) ---
    spotlights = []

    # Spotlight on a perfect bonus round score (highest priority)
    if bonus_total > 0 and bonus_completed == bonus_total:
        emoji_themes = { "🎤": "lyrical knowledge", "🖼️": "artist recognition", "💿": "discography expertise" }
        bonus_emojis = game_info.get("bonus_emojis", "").split()
        if bonus_emojis:
            highlight_emoji = random.choice(bonus_emojis)
            highlight_theme = emoji_themes.get(highlight_emoji, "musical skill")
            spotlights.append(f"They also went a perfect **{bonus_completed}/{bonus_total}** on the bonus rounds, showing off some serious {highlight_theme}! 💯")
        else:
            spotlights.append(f"They also aced the bonus rounds, going a perfect **{bonus_completed}/{bonus_total}**! 💯")

    # Spotlight on streaks from historical player stats
    current_streak = player_stats.get("current_streak", 0)
    if player_stats.get("is_new_max_streak") and current_streak > 3:
        spotlights.append(f"🚀 That's a new personal best streak of **{current_streak}**! The crowd goes wild!")
    elif current_streak > 3:
        spotlights.append(f"That's **{current_streak}** wins in a row! They're on fire! 🔥")
    
    # Default fallback: a simple, informative statement about the bonus rounds
    if not spotlights and bonus_total > 0 and solved:
        spotlights.append(f"On the bonus rounds, they scored **{bonus_completed}/{bonus_total}**.")

    # Combine and return
    if spotlights:
        return f"{opening_line}\n{random.choice(spotlights)}"
        
    return opening_line

def _generate_gisnep_post(display_name, game_info, player_stats):
    """Generates a dynamic Gisnep post based on the player's score and stats."""
    game_number = game_info.get("game_number")
    completion_time = game_info.get("completion_time")
    server_stats = player_stats.get("server_stats", {})

    import random

    # --- Utility function for time formatting ---
    def format_time(seconds):
        if seconds is None:
            return "N/A"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    time_str = format_time(completion_time)
    player_avg_str = format_time(player_stats.get('avg_seconds'))

    # --- Part A: The Opening Line (Thematic) ---
    openers = [
        "Another chapter closed!",
        "The plot thickens!",
        "A quote for the ages, solved by",
        "Right on the page!",
        "The author would be proud."
    ]
    opening_line = f"{random.choice(openers)} {display_name} solved today's Gisnep in **{time_str}**."

    # --- Part B: The Time Analysis (The Dynamic Element) ---
    analysis_lines = []
    is_new_pb = player_stats.get('is_new_pb', False)
    player_avg = player_stats.get('avg_seconds', 0.0)
    server_avg = server_stats.get('avg_seconds', 0.0)

    # Prioritize the most exciting event: a new Personal Best.
    if is_new_pb:
        analysis_lines.append(f"🚀 **New Personal Best!** They absolutely shattered their old record!")
    else:
        # Compare to the server average for THIS puzzle
        if server_avg > 0:
            time_diff_server = server_avg - completion_time
            if time_diff_server > 60:  # More than a minute faster
                diff_m = int(time_diff_server / 60)
                diff_s = int(time_diff_server % 60)
                analysis_lines.append(f"⚡ They were **{diff_m}m {diff_s}s faster** than the server average today! A true speed reader!")

        # Compare to the player's OWN average
        if player_avg > 0:
            time_diff_player = player_avg - completion_time
            if time_diff_player > 45:
                analysis_lines.append(f"🔥 That's significantly faster than their usual pace. They were in the zone!")

    # Add a general comment based on absolute time
    if completion_time < 180:  # Under 3 minutes
        analysis_lines.append("An incredibly quick solve!")
    elif completion_time > 600:  # Over 10 minutes
        analysis_lines.append("That was a real head-scratcher of a quote, a thoughtful solve. 🧐")

    # If no other conditions met, provide a default summary
    if not analysis_lines:
        analysis_lines.append(f"Their average time is now **{player_avg_str}**.")

    # Choose one line of analysis to post
    time_analysis = random.choice(analysis_lines)

    # Combine and return the final message
    return f"{opening_line}\n{time_analysis}"

# In post_generator.py

def _generate_connections_post(display_name: str, game_info: dict, player_stats: dict) -> str:
    """Generates nuanced Connections feedback based on detailed solve patterns."""
    game_number = game_info.get("game_number", "?")
    finished = game_info.get("finished_game", False)
    perfect = game_info.get("perfect_game", False)
    solve_order = game_info.get("solve_order", [])
    mistakes = game_info.get("mistake_count", 0)

    opening_line = ""
    
    # --- Part 1: The Opening Line (based on your specific rules) ---
    
    # Rule 6: Player struck out
    if not finished:
        opening_line = f"Oof, the board was a minefield for **{display_name}** on Connections #{game_number} today."
    
    # Rule 1: The "True Perfect" solution
    elif perfect and solve_order == ['🟪', '🟦', '🟩', '🟨']:
        opening_line = f"👑 Flawless! **{display_name}** solved Connections #{game_number} in perfect reverse difficulty order."
    
    # Rule 2: "Close to Perfect" (Purple first, but not perfect order)
    elif perfect and solve_order and solve_order[0] == '🟪':
        opening_line = f"Excellent work by **{display_name}** on Connections #{game_number}, nailing the tricky purple group first."

    # Rule 3: "Pretty Good" (Blue first, Purple second)
    elif perfect and solve_order[:2] == ['🟦', '🟪']:
        opening_line = f"A solid solve for **{display_name}** on Connections #{game_number}, tackling the two hardest groups first."

    # Rule 5: Struggled with hard categories
    elif mistakes > 0 and len(solve_order) >= 2 and set(solve_order[:2]) == {'🟩', '🟨'}:
        opening_line = f"**{display_name}** cleared the easier groups on Connections #{game_number}, but the blue and purple categories put up a fight."

    # Fallback for any other standard win
    else:
        opening_line = f"**{display_name}** solved Connections #{game_number} with {mistakes} mistake{'s' if mistakes != 1 else ''}."

    # --- Part 2: The Stat Spotlight ---
    spotlights = []

    # Rule 7: "Rainbow Wrong" guess (high priority)
    if game_info.get("rainbow_wrong_guess"):
        spotlights.append("That first guess of one of each color is a classic 'Rainbow Wrong' 🌈")
    
    # Historical context for perfect games
    total_perfects = player_stats.get("total_perfects", 0)
    if perfect and total_perfects > 1:
        spotlights.append(f"That marks their **{total_perfects}th** game without mistakes 🧑‍🎨")

    # If there's a spotlight, add it.
    if spotlights:
        return f"{opening_line}\n{random.choice(spotlights)}"
    
    return opening_line

# In post_generator.py

def _format_salad_time(seconds: int) -> str:
    """Helper function to format seconds into a M_s string."""
    minutes, sec = divmod(seconds, 60)
    return f"{minutes}m {sec}s"

def _generate_word_salad_post(display_name: str, game_info: dict, player_stats: dict) -> str:
    """Generates dynamic feedback for Word Salad based on completion time."""
    game_number = game_info.get("game_number", "?")
    time_seconds = game_info.get("completion_time_seconds", 0)
    hints_used = game_info.get("hints_used", 0)
    score = game_info.get("score", 0)
    time_str = _format_salad_time(time_seconds)

    # --- Part 1: The Opening Line (based on your time thresholds) ---

    if time_seconds > 1200: # Over 20 minutes
        opening_line = f"Did they take a nap halfway through? 😴 **{display_name}** finished Word Salad #{game_number} in a leisurely **{time_str}**."
    elif time_seconds > 600: # Over 10 minutes
        opening_line = f"That was a real head-scratcher! **{display_name}** wrestled with Word Salad #{game_number}, finishing in **{time_str}**."
    elif time_seconds < 120: # Under 2 minutes
        opening_line = f"⚡ Incredible speed! **{display_name}** blitzed through Word Salad #{game_number} in just **{time_str}**!"
    else: # Neutral case for 2-10 minutes
        opening_line = f"**{display_name}** solved Word Salad #{game_number} in **{time_str}**."

    # --- Part 2: The Stat Spotlight ---
    spotlights = []

    # Add a spotlight for a new Personal Best time
    if player_stats.get('is_new_pb'):
        spotlights.append("🚀 A new personal best time!")

    # Add context about hints used
    if hints_used == 0 and time_seconds < 300: # No hints on a good time is impressive
        spotlights.append("And they did it with **no hints**! Pure brainpower.")
    elif hints_used > 0:
        spotlights.append(f"They used **{hints_used}** hint{'s' if hints_used > 1 else ''} to solve it.")
    
    # Default fallback that mentions the score
    if not spotlights:
        spotlights.append(f"Their final score for the puzzle was **{score}** points.")
    
    # Combine and return
    return f"{opening_line}\n{random.choice(spotlights)}"

# In post_generator.py

def _generate_framed_post(display_name: str, game_info: dict, player_stats: dict) -> str:
    """Generates dynamic feedback for Framed based on the number of guesses."""
    game_number = game_info.get("game_number", "?")
    attempts = game_info.get("attempts", 0)
    solved = game_info.get("solved", False)
    total_score = game_info.get("total_score", 0)

    # --- Part 1: The Opening Line (based on your rules) ---

    if not solved:
        opening_line = f"🤔 An obscure one today! **{display_name}** couldn't quite place the movie in Framed #{game_number}."
    elif attempts == 1:
        opening_line = f"🎬 Incredible! **{display_name}** guessed the movie for Framed #{game_number} from the very first frame!"
    elif attempts == 6:
        opening_line = f"🍿 Just in time! **{display_name}** got the movie on the final frame for Framed #{game_number}."
    else: # Neutral case for 2-5 guesses
        opening_line = f"**{display_name}** solved Framed #{game_number} in {attempts} guesses."

    # --- Part 2: The Stat Spotlight ---
    spotlights = []

    # Spotlight on a new max streak
    if player_stats.get("is_new_max_streak") and player_stats.get("current_streak", 0) > 3:
        spotlights.append(f"🚀 That's a new personal best streak of **{player_stats['current_streak']}**!")
    
    # Spotlight comparing to their average
    avg_score = player_stats.get("avg_score", 0)
    if solved and total_score > avg_score and avg_score > 0:
        spotlights.append(f"That's higher than their average score of {avg_score:.1f} points. Nice one!")

    # Default fallback mentioning the point score, if the game was won
    if not spotlights and solved:
        spotlights.append(f"Their score for today's puzzle is **{total_score}** points.")
        
    # Combine and return
    if spotlights:
        return f"{opening_line}\n{random.choice(spotlights)}"

    return opening_line

def _generate_sexaginta_post(display_name: str, game_info: dict, player_stats: dict) -> str:
    """
    Generates welcoming feedback for 64ordle that acknowledges the challenge.
    """
    game_number = game_info.get("game_number", "?")
    guesses_used = game_info.get("guesses_used")
    words_unsolved = game_info.get("words_unsolved")
    score = game_info.get("game_score", "?")
    percent_solved = game_info.get("percent_solved", 0)

    # --- Welcome with performance context ---
    if words_unsolved is not None and words_unsolved > 0:
        opening = f"Welcome **{display_name}**! Sexaginta-Quattuordle #{game_number} was a beast, and left you with **{words_unsolved}** words unsolved."
    elif guesses_used is not None and guesses_used <= 70:
        opening = f"Welcome **{display_name}**! You finished #{game_number} in **{guesses_used}** guesses."
    else:
        opening = f"Welcome **{display_name}**! You tackled #{game_number} with a score of **{score}**."

    # --- Discussion starters ---
    starters = []
    
    if guesses_used is not None and guesses_used <= 70:
        starters.append(f"That's a fantastic effort! What's your strategy for managing 64 boards?")
    elif words_unsolved is not None and words_unsolved > 0:
        starters.append("Which words gave you the most trouble?")
    else:
        # Generic prompt for solved puzzles
        starters.append("How do you keep track of all 64 boards?")
    
    return f"{opening}\n{random.choice(starters)}"

def _generate_minute_cryptic_post(display_name: str, game_info: dict, player_stats: dict) -> str:
    """Generates a dynamic post for Minute Cryptic scores."""
    game_date = game_info.get("game_date", "a recent puzzle")
    score_desc = game_info.get("score_description", "a score")
    solved = game_info.get("solved", False)

    if solved:
        opening_line = f"🕵️‍♀️ A clever solve! **{display_name}** cracked the Minute Cryptic for {game_date}."
    else:
        opening_line = f"🤔 That was a tricky one! **{display_name}** tackled the Minute Cryptic for {game_date}."

    spotlights = []
    if solved:
        spotlights.append(f"Their final score was **{score_desc}**.")

    avg_score = player_stats.get("avg_score")
    if avg_score is not None:
        spotlights.append(f"Their average score is now **{avg_score:.2f}**.")

    if not spotlights:
        spotlights.append("Another puzzle in the books!")

    return f"{opening_line}\n{random.choice(spotlights)}"

def _generate_strands_post(display_name: str, game_info: dict, player_stats: dict) -> str:
    """Generates dynamic feedback for Strands."""
    game_number = game_info.get("game_number", "?")
    solved = game_info.get("solved", False)
    total_score = game_info.get("total_score", 0)
    hint_count = game_info.get("hint_count", 0)
    spangram_position = game_info.get("spangram_position")

    if not solved:
        opening_line = f"🧶 Oh no! **{display_name}** got tangled up in Strands #{game_number} today."
    elif total_score == 20:
        opening_line = f"🧵 A flawless weave! **{display_name}** scored a perfect 20 on Strands #{game_number}!"
    else:
        opening_line = f"**{display_name}** threaded together Strands #{game_number}."

    spotlights = []

    if solved:
        if hint_count == 0 and spangram_position == 1:
            spotlights.append("Finding the spangram first with absolutely no hints? Incredible vision! 👀")
        elif hint_count > 0:
            spotlights.append(f"They used {hint_count} hint{'s' if hint_count > 1 else ''} along the way.")
        elif spangram_position and spangram_position > 3:
            spotlights.append("The spangram proved elusive, but they got there in the end!")

        spotlights.append(f"Final score: **{total_score}** points.")

    if not spotlights:
        spotlights.append(f"Final score: **{total_score}** points.")

    return f"{opening_line}\n{random.choice(spotlights)}"

def _generate_pips_post(display_name: str, game_info: dict, player_stats: dict) -> str:
    """Generates a post for a completed Pips game."""
    game_number = game_info.get("game_number", "?")
    scores = player_stats.get("scores")

    if not scores:
        return f"🏆 **{display_name}** is making progress on Pips #{game_number}!"

    total_score = sum(s['score'] for s in scores)
    cookie_count = sum(s['cookie'] for s in scores)

    message = f"🏆 **{display_name}** has completed all Pips difficulties for game #{game_number} with a total score of **{total_score}**!\n\n"

    for score in scores:
        time_min = score['completion_time'] // 60
        time_sec = score['completion_time'] % 60
        time_str = f"{time_min}:{time_sec:02d}"
        message += f"**{score['difficulty'].capitalize()}**: {time_str} ({score['score']} pts)"
        if score.get('cookie'):
            message += " 🍪"
        message += "\n"

    if cookie_count > 0:
        message += f"\nWow, {cookie_count} cookie{'s' if cookie_count > 1 else ''}! You're a top performer! 🍪"

    return message


def _build_personal_stat_spotlight(game_name: str, player_stats: dict, game_info: dict) -> str | None:
    """Build one extra personal stat line for chat engagement."""
    if not player_stats:
        return None

    if player_stats.get("is_new_pb"):
        return "📌 New personal best unlocked!"

    if player_stats.get("is_new_max_streak") and player_stats.get("current_streak", 0) >= 3:
        return f"🔥 New best streak: **{player_stats['current_streak']}**."

    total_plays = player_stats.get("total_plays")
    if isinstance(total_plays, int) and total_plays in {10, 25, 50, 100}:
        return f"🎉 Milestone reached: **{total_plays}** registered games."

    if game_name == "wordle":
        win_pct = player_stats.get("win_percentage")
        if isinstance(win_pct, (int, float)) and win_pct >= 80:
            return f"📊 Win rate is now **{win_pct:.1f}%**. Elite consistency."

    if game_name == "pips":
        total_cookies = player_stats.get("total_cookies")
        if isinstance(total_cookies, int) and total_cookies > 0 and total_cookies % 5 == 0:
            return f"🍪 Cookie milestone: **{total_cookies}** total cookies."

    return None

def generate_post(game_name: str, display_name: str, game_info: dict, player_stats: dict) -> str:
    """Routes the request to the appropriate sub-generator for the given game."""

    game_generators = {
        "wordle": _generate_wordle_post,
        "connections": _generate_connections_post,
        "gisnep": _generate_gisnep_post,
        "bandle": _generate_bandle_post,
        "word_salad": _generate_word_salad_post,
        "framed": _generate_framed_post,
        "sexaginta": _generate_sexaginta_post,
        "minute_cryptic": _generate_minute_cryptic_post,
        "pips": _generate_pips_post,
        "strands": _generate_strands_post,
    }

    generator_func = game_generators.get(game_name.lower())

    if generator_func:
        base_message = generator_func(display_name, game_info, player_stats)
        spotlight = _build_personal_stat_spotlight(game_name.lower(), player_stats, game_info)
        if base_message and spotlight and spotlight not in base_message:
            return f"{base_message}\n{spotlight}"
        return base_message
    else:
        # Return None instead of an error message to be handled by the bot
        return None
