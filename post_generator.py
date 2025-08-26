import random

def generate_wordle_post(display_name, game_number, attempts, skill, luck, updated_stats):
    """Generates a dynamic Wordle post based on the player's score and stats."""

    # Use 0 if skill or luck is None
    skill = skill or 0
    luck = luck or 0

    # Part A: The Opening Line (Flavor Text)
    if attempts == 1:
        opening_line = f"A miracle! {display_name} solved Wordle {game_number} in ONE GUESS! 🤯"
    elif attempts == 2:
        opening_line = f"Pure genius! {display_name} cracked Wordle {game_number} in just two tries! 🧠"
    elif attempts == 6:
        opening_line = f"Whew! {display_name} clutched it on the final guess for Wordle {game_number}! 😅"
    elif attempts > 6: # A loss
        opening_line = f"Oof, a tough one today. {display_name} was bested by Wordle {game_number}. You'll get it tomorrow! 💪"
    else: # For 3, 4, 5
        opening_line = f"Nice one! {display_name} finished Wordle {game_number} in {attempts}/6. ✅"

    # Part B: The Stat Spotlight (The Dynamic Element)
    spotlights = []
    new_streak = updated_stats["new_streak"]
    is_new_max_streak = updated_stats["is_new_max_streak"]
    win_percentage = updated_stats["win_percentage"]
    total_plays = updated_stats["total_plays"]

    # Add spotlights based on conditions
    if skill > 90:
        spotlights.append(f"With a **Skill** score of **{skill}**, that was a masterclass in deduction! 🧐")
    if luck > 75:
        spotlights.append(f"A **Luck** score of **{luck}**? The dictionary gods smiled upon you today! ✨")
    if luck < 25:
        spotlights.append(f"Only **{luck}** luck? You earned that win the hard way!  मेहनत (meh·nat - 'hard work')")
    if new_streak > 3:
        spotlights.append(f"That's **{new_streak}** wins in a row! They're on fire! 🔥")
    if is_new_max_streak:
        spotlights.append(f"That's a new personal best streak of **{new_streak}**! Unstoppable! 🚀")

    # Always have a default option
    if not spotlights:
        spotlights.append(f"They've played **{total_plays}** games with a **{win_percentage:.2f}%** win rate. Keep it up!")

    # Choose one spotlight to show
    stat_spotlight = random.choice(spotlights)

    # Combine and return the final message
    return f"{opening_line}\n{stat_spotlight}"

def generate_gisnep_post(display_name, game_number, completion_time, player_stats, server_stats):
    """Generates a dynamic Gisnep post based on the player's score and stats."""

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

def generate_connections_post(display_name, game_number, game_info, updated_stats):
    """Generates a dynamic Connections post based on the player's score and stats."""

    perfect_game = game_info.get("perfect_game", False)
    solved_purple_first = game_info.get("solved_purple_first", False)
    mistake_count = game_info.get("mistake_count", 0)
    finished_game = game_info.get("finished_game", False)
    total_score = game_info.get("total_score", 0)
    uniqueness = game_info.get("uniqueness")
    skill = game_info.get("skill")

    total_perfects = updated_stats.get("total_perfects", 0)
    total_purples = updated_stats.get("total_purples", 0)

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
