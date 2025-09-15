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
        opening_line = f"🤯 Incredible! **{display_name}** solved Wordle #{game_number} in a single guess!"
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
            spotlights.append("With a **Skill** score of **90+**, that was a masterclass in deduction. 🧐")
    
    if luck is not None:
        if luck > 85:
            spotlights.append("A **Luck** score over **85**? The dictionary gods were smiling today! ✨")
        elif luck < 15:
            spotlights.append("Only **{luck}** luck? They earned that win the hard way. Pure skill.")

    # Always have a default fallback if no other conditions are met
    if not spotlights:
        current_streak = player_stats.get("current_streak", 0)
        if current_streak > 2:
            spotlights.append(f"They're now on a **{current_streak}-game** winning streak! 🔥")
        else:
            # A simple, neutral default
            win_percentage = player_stats.get("win_percentage", 0)
            spotlights.append(f"Their win percentage is holding steady at **{win_percentage:.1f}%**.")

    # Combine the opening line with a randomly chosen spotlight for variety
    return f"{opening_line}\n{random.choice(spotlights)}"
    
def _generate_bandle_post(display_name, game_info, player_stats):
    """Generates a dynamic Bandle post based on the player's score and stats."""
    game_number = game_info.get("game_number")
    attempts = game_info.get("attempts")
    bonus_rounds_completed = game_info.get("bonus_rounds_completed")
    bonus_rounds_total = game_info.get("bonus_rounds_total")
    bonus_emojis = game_info.get("bonus_emojis")
    current_streak = game_info.get("current_streak")

    # --- Opening Line ---
    opening_line = f"{display_name} just finished their set for Bandle #{game_number}!"

    # --- Stat Spotlight / Encore ---
    spotlights = []

    # Streaks
    if current_streak and current_streak > 2:
        spotlights.append(f"They're on a {current_streak}-day streak! The crowd goes wild! 🔥")

    # Quick guess
    if attempts == 1:
        spotlights.append("In ONE guess! A true music savant! 🤯")
    elif attempts and attempts <= 3:
        spotlights.append(f"A great ear! They only needed {attempts} tracks to nail it. 🎵")

    # Bonus rounds
    emoji_themes = {
        "🎤": "lyrical knowledge", "🖼️": "artist recognition", "🌍": "music geography",
        "🧩": "trivia mastery", "📅": "historical timeline", "⏱️": "rhythmic sense",
        "🎸": "instrumental ear", "🧑": "band member knowledge", "💿": "discography expertise"
    }

    if bonus_rounds_completed and bonus_rounds_completed > 0:
        completed_emojis = bonus_emojis.split()
        if completed_emojis:
            highlight_emoji = random.choice(completed_emojis)
            highlight_theme = emoji_themes.get(highlight_emoji, "musical skill")

            if bonus_rounds_completed == bonus_rounds_total:
                spotlights.append(f"A perfect score on the bonus rounds! Their {highlight_theme} {highlight_emoji} was especially impressive! 💯")
            else:
                spotlights.append(f"Great work on the bonus rounds! They showed off some serious {highlight_theme} {highlight_emoji}.")

    # Fallback/default spotlight
    if not spotlights:
        player_avg_attempts = player_stats.get("avg_attempts", 0)
        if player_avg_attempts > 0 and attempts < player_avg_attempts:
            spotlights.append(f"That's faster than their average of {player_avg_attempts:.2f} guesses! They're getting better and better! 📈")
        else:
            spotlights.append("Another great performance in the books. 🤘")

    # --- Combine and return ---
    encore = random.choice(spotlights)
    return f"{opening_line}\n{encore}"

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

def _generate_connections_post(display_name, game_info, player_stats):
    """Generates a dynamic Connections post based on the player's score and stats."""
    game_number = game_info.get("game_number")
    perfect_game = game_info.get("perfect_game", False)
    solved_purple_first = game_info.get("solved_purple_first", False)
    mistake_count = game_info.get("mistake_count", 0)
    finished_game = game_info.get("finished_game", False)
    total_score = game_info.get("total_score", 0)
    uniqueness = game_info.get("uniqueness")
    skill = game_info.get("skill")

    total_perfects = player_stats.get("total_perfects", 0)
    total_purples = player_stats.get("total_purples", 0)

    # Part A: The Opening Line (Performance-based)
    if perfect_game:
        opening_line = f"A perfect grid! {display_name} solved Connections #{game_number} without a single mistake! ✨"
    elif solved_purple_first:
        opening_line = f"A bold strategy! {display_name} tackled the trickiest purple group first to solve Connections #{game_number}! ♟️"
    elif mistake_count >= 3 and finished_game:
        opening_line = f"Down to the wire! {display_name} navigated a tricky board to solve Connections #{game_number}. 😮‍💨"
    elif not finished_game:
        opening_line = f"The categories were elusive today! A valiant effort on Connections #{game_number} from {display_name}. Better luck next time! 🤔"
    else: # A standard win
        opening_line = f"{display_name} has solved Connections #{game_number} with a score of {total_score}! ✅"

    # Part B: The Stat Spotlight (The "Charm" Element)
    spotlights = []

    # Uniqueness is the most interesting stat, so prioritize it
    if uniqueness:
        spotlights.append(f"Their solve path has a **Uniqueness of {uniqueness}**! Truly a one-of-a-kind brain. 🧠")
    if skill and skill > 90:
        spotlights.append(f"With a **Skill** score of **{skill}**, that was some serious lateral thinking! 🧐")
    if perfect_game and total_perfects > 0:
        spotlights.append(f"That's their **{total_perfects}th** perfect game! A true Connections connoisseur. 🧑‍🎨")
    if solved_purple_first and total_purples > 0:
        spotlights.append(f"That's the **{total_purples}th** time they've solved purple first. No fear! 😎")

    # Default fallback
    if not spotlights:
        spotlights.append(f"They navigated the puzzle with only **{mistake_count}** mistake{'s' if mistake_count != 1 else ''}. Nice!")

    # Choose one spotlight to show
    stat_spotlight = random.choice(spotlights)

    # Combine and return the final message
    return f"{opening_line}\n{stat_spotlight}"

def generate_post(game_name: str, display_name: str, game_info: dict, player_stats: dict) -> str:
    """Routes the request to the appropriate sub-generator for the given game."""

    game_generators = {
        "wordle": _generate_wordle_post,
        "connections": _generate_connections_post,
        "gisnep": _generate_gisnep_post,
        "bandle": _generate_bandle_post,
    }

    generator_func = game_generators.get(game_name.lower())

    if generator_func:
        return generator_func(display_name, game_info, player_stats)
    else:
        # Return None instead of an error message to be handled by the bot
        return None
