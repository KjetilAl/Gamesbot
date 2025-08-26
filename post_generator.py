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
