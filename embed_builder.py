import discord
import discord.utils # Needed for utcnow

async def build_leaderboard_embed(game_name: str, title: str, rows: list[dict], period: str, color: discord.Color) -> discord.Embed:
    """
    Builds a Discord embed for a game leaderboard, formatted based on game type.
    Args:
        game_name: The key of the game (e.g., "Wordle", "Connections").
        title: The title of the embed.
        rows: A list of dictionaries, where each dictionary contains a player's stats.
              The keys in the dictionaries should match the stats fetched by the database functions.
        period: The time period for the leaderboard ("Overall", "Weekly", "Monthly").
        color: The color of the embed.
    Returns:
        A discord.Embed object.
    """
    embed = discord.Embed(
        title=title,
        description=f"Period: {period}",
        color=color
    )
    medals = ["🥇", "🥈", "🥉"]
    
    if not rows:
        embed.description += "\n\nNo scores recorded for this period."
        return embed
    
    # SORT THE ROWS BASED ON GAME TYPE AND PERFORMANCE
    if game_name == "Wordle":
        # For Wordle: Lower average attempts is better
        rows.sort(key=lambda x: x.get("avg_attempts", float('inf')))
    elif game_name == "Connections":
        # For Connections: Higher average score is better
        rows.sort(key=lambda x: x.get("avg_score", 0), reverse=True)
    elif game_name == "Framed":
        # For Framed: Lower average attempts is better
        rows.sort(key=lambda x: x.get("avg_attempts", float('inf')))
    elif game_name == "Gisnep":
        # For Gisnep: Lower average time is better
        rows.sort(key=lambda x: x.get("avg_time", float('inf')))
    elif game_name == "Bandle":
        # For Bandle: Lower average attempts is better
        rows.sort(key=lambda x: x.get("avg_attempts", float('inf')))
    elif game_name == "Minute Cryptic":
        # For Minute Cryptic: Higher average score is better
        rows.sort(key=lambda x: x.get("avg_score", 0), reverse=True)
    elif game_name == "Word Salad":
        # For Word Salad: Lower average time is better
        rows.sort(key=lambda x: x.get("avg_time", float('inf')))
    
    for i, row in enumerate(rows, start=1):
        medal = medals[i-1] if i <= len(medals) else f"#{i}"
        name = row.get("display_name", "Unknown Player")
        played = row.get("games_played", 0)
        
        # Build field value depending on game type and available stats
        details = []
        details.append(f"▶️ Played: **{played}**")
        
        # Customize the details based on the game name
        if game_name == "Wordle":
            avg_attempts = row.get("avg_attempts")
            solved_count = row.get("solved_count", 0)
            hard_mode_count = row.get("hard_mode_count", 0)
            best_score = row.get("best_score", 0)
            
            avg_attempts_display = f"**{avg_attempts:.2f}**" if avg_attempts is not None else "N/A"
            details.append(f"⏱️ Avg Attempts: {avg_attempts_display}")
            details.append(f"🔓 Solved: **{solved_count}**")
            details.append(f"🛠️ Hard Mode: **{hard_mode_count}**")
            
        elif game_name == "Connections":
             total_score = row.get("total_score", 0)
             avg_score = row.get("avg_score")
             solved_count = row.get("solved_count", 0)
             purple_first_count = row.get("purple_first_count", 0)
             blue_first_count = row.get("blue_first_count", 0)
             
             avg_score_display = f"**{avg_score:.2f}**" if avg_score is not None else "N/A"
             details.append(f"⭐ Total Score: **{total_score}**")
             details.append(f"📊 Avg Score: {avg_score_display}")
             details.append(f"🔓 Solved: **{solved_count}**")
             details.append(f"🟪 Purple First: **{purple_first_count}**")
             details.append(f"🟦 Blue First: **{blue_first_count}**")
             
        elif game_name == "Framed":
             total_score = row.get("total_score", 0)
             avg_attempts = row.get("avg_attempts")
             solved_count = row.get("solved_count", 0)
             avg_attempts_display = f"**{avg_attempts:.2f}**" if avg_attempts is not None else "N/A"
             details.append(f"⭐ Total Score: **{total_score}**")
             details.append(f"⏱️ Avg Attempts: {avg_attempts_display}")
             details.append(f"🔓 Solved: **{solved_count}**")
             
        elif game_name == "Gisnep":
             avg_time = row.get("avg_time")
             best_time = row.get("best_time")
             avg_minutes, avg_seconds = divmod(int(avg_time) if avg_time is not None else 0, 60)
             best_minutes, best_seconds = divmod(int(best_time) if best_time is not None else 0, 60)
             avg_time_display = f"**{avg_minutes:02d}:{avg_seconds:02d}**" if avg_time is not None else "N/A"
             best_time_display = f"**{best_minutes:02d}:{best_seconds:02d}**" if best_time is not None else "N/A"
             details.append(f"⏱️ Avg Time: {avg_time_display}")
             details.append(f"🥇 Best Time: {best_time_display}")
             
        elif game_name == "Bandle":
             total_score = row.get("total_score", 0)
             avg_attempts = row.get("avg_attempts")
             solved_count = row.get("solved_count", 0)
             bonus_counts = [
                 row.get("bonus_microphone_count", 0), row.get("bonus_frame_count", 0), row.get("bonus_person_count", 0),
                 row.get("bonus_globe_count", 0), row.get("bonus_puzzle_count", 0), row.get("bonus_calendar_count", 0),
                 row.get("bonus_cd_count", 0), row.get("bonus_timer_count", 0), row.get("bonus_guitar_count", 0)
             ]
             bonus_emojis = ["🎤", "🖼️", "🧑", "🌍", "🧩", "📅", "💿", "⏱️", "🎸"]
             
             bonus_display_parts = []
             for emoji, count in zip(bonus_emojis, bonus_counts):
                 if count > 0:
                     bonus_display_parts.append(f"{emoji} {count}")
             bonus_display = " ".join(bonus_display_parts) if bonus_display_parts else "None"
             avg_attempts_display = f"**{avg_attempts:.2f}**" if avg_attempts is not None else "N/A"
             details.append(f"⭐ Total Score: **{total_score}**")
             details.append(f"⏱️ Avg Attempts: {avg_attempts_display}")
             details.append(f"🔓 Solved: **{solved_count}**")
             details.append(f"🎁 Bonus:\n{bonus_display}")
             
        elif game_name == "Minute Cryptic":
             solved_count = row.get("solved_count", 0)
             avg_score = row.get("avg_score")
             
             avg_score_display = f"**{avg_score:.2f}**" if avg_score is not None else "N/A"
             details.append(f"🔓 Solved: **{solved_count}**")
             details.append(f"📊 Avg Score: {avg_score_display}")
             
        elif game_name == "Word Salad":
             avg_time = row.get("avg_time")
             best_time = row.get("best_time")
             avg_hints = row.get("avg_hints")
             avg_minutes, avg_seconds = divmod(int(avg_time) if avg_time is not None else 0, 60)
             best_minutes, best_seconds = divmod(int(best_time) if best_time is not None else 0, 60)
             
             avg_time_display = f"**{avg_minutes:02d}:{avg_seconds:02d}**" if avg_time is not None else "N/A"
             best_time_display = f"**{best_minutes:02d}:{best_seconds:02d}**" if best_time is not None else "N/A"
             avg_hints_display = f"**{avg_hints:.2f}**" if avg_hints is not None else "N/A"
             details.append(f"⏱️ Avg Time: {avg_time_display}")
             details.append(f"🥇 Best Time: {best_time_display}")
             details.append(f"❓ Avg Hints: {avg_hints_display}")
             
        field_value = "\n".join(details)
        embed.add_field(
            name=f"{medal} {name}",
            value=field_value,
            inline=True
        )
        
    emit_footer = f"Posted: {discord.utils.utcnow().strftime('%Y-%m-%d')}"
    embed.set_footer(text=emit_footer)
    return embed
