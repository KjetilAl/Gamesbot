import discord
import discord.utils # Needed for utcnow

async def build_wordle_leaderboard_embed(title: str, leaderboard_data: dict, period: str, color: discord.Color) -> discord.Embed:
    """
    Builds a Discord embed for the enhanced Wordle leaderboard.
    """
    embed = discord.Embed(
        title=title,
        description=f"Period: {period.capitalize()}",
        color=color
    )

    # Top Players
    top_players = leaderboard_data.get("top_players")
    if top_players:
        medals = ["🥇", "🥈", "🥉"]
        player_list = []
        for i, (player, score) in enumerate(top_players):
            player_list.append(f"{medals[i]} **{player}** - {score} points")
        embed.add_field(name="🏆 Top Players", value="\n".join(player_list), inline=False)
    else:
        embed.add_field(name="🏆 Top Players", value="No scores recorded for this period.", inline=False)


    # Superlatives
    superlatives = []
    einstein = leaderboard_data.get("einstein")
    if einstein:
        player, avg_skill = einstein
        superlatives.append(f"🧠 The Einstein Award to **{player}** for the highest average skill score this period ({avg_skill:.1f}).")

    lucky_charm = leaderboard_data.get("lucky_charm")
    if lucky_charm:
        player, avg_luck = lucky_charm
        superlatives.append(f"🍀 The Lucky Charm Award to **{player}** for riding a wave of good fortune with the highest average luck this period ({avg_luck:.1f}).")

    ironman = leaderboard_data.get("ironman")
    if ironman:
        player, streak = ironman
        if streak > 1:
            superlatives.append(f"🦾 The Ironman Award to **{player}** for maintaining a flawless {streak} game winning streak!")

    if superlatives:
        embed.add_field(name="✨ Superlatives", value="\n".join(superlatives), inline=False)

    emit_footer = f"Posted: {discord.utils.utcnow().strftime('%Y-%m-%d')}"
    embed.set_footer(text=emit_footer)
    return embed

async def build_gisnep_leaderboard_embed(title: str, leaderboard_data: dict, period: str, color: discord.Color) -> discord.Embed:
    """
    Builds a Discord embed for the enhanced Gisnep leaderboard.
    """
    embed = discord.Embed(
        title=title,
        description=f"Period: {period.capitalize()} (Ranked by Average Solve Time)",
        color=color
    )

    # --- Utility function for time formatting ---
    def format_time(seconds):
        if seconds is None:
            return "N/A"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    # Top Players
    top_players = leaderboard_data.get("top_players")
    if top_players:
        medals = ["🥇", "🥈", "🥉"]
        player_list = []
        for i, (player, avg_seconds) in enumerate(top_players):
            medal = medals[i] if i < len(medals) else f"**#{i+1}**"
            player_list.append(f"{medal} **{player}** - ⏱️ Avg Time: {format_time(avg_seconds)}")
        embed.add_field(name="🏆 Top Players", value="\n".join(player_list), inline=False)
    else:
        embed.add_field(name="🏆 Top Players", value="No scores recorded for this period.", inline=False)


    # Weekly Accolades
    if period == 'weekly':
        accolades = []
        mercury_award = leaderboard_data.get("mercury_award")
        if mercury_award:
            player, fastest_time = mercury_award
            accolades.append(f"🏃💨 The Mercury Award to **{player}** for the single fastest solve of the week at a blazing {format_time(fastest_time)}!")

        if accolades:
            embed.add_field(name="✨ Weekly Accolades", value="\n".join(accolades), inline=False)

    emit_footer = f"Posted: {discord.utils.utcnow().strftime('%Y-%m-%d')}"
    embed.set_footer(text=emit_footer)
    return embed

async def build_connections_leaderboard_embed(title: str, leaderboard_data: dict, period: str, color: discord.Color) -> discord.Embed:
    """
    Builds a Discord embed for the enhanced Connections leaderboard.
    """
    embed = discord.Embed(
        title=title,
        description=f"Period: {period.capitalize()}",
        color=color
    )

    # Top Players
    top_players = leaderboard_data.get("top_players")
    if top_players:
        medals = ["🥇", "🥈", "🥉"]
        player_list = []
        for i, (player, score) in enumerate(top_players):
            player_list.append(f"{medals[i]} **{player}** - ⭐ Total Score: {score}")
        embed.add_field(name="🏆 Top Players", value="\n".join(player_list), inline=False)
    else:
        embed.add_field(name="🏆 Top Players", value="No scores recorded for this period.", inline=False)

    # Superlatives
    superlatives = []
    perfector = leaderboard_data.get("perfector")
    if perfector and perfector[1] > 0:
        player, count = perfector
        superlatives.append(f"The Perfector 🧑‍🎨: to **{player}** for achieving {count} perfect game{'s' if count > 1 else ''} this period!")

    grandmaster = leaderboard_data.get("grandmaster")
    if grandmaster and grandmaster[1] > 0:
        player, count = grandmaster
        superlatives.append(f"The Grandmaster ♟️: to **{player}** for solving the purple group first {count} time{'s' if count > 1 else ''}!")

    pathfinder = leaderboard_data.get("pathfinder")
    if pathfinder:
        player, uniqueness = pathfinder
        superlatives.append(f"The Pathfinder 🗺️: to **{player}** for their mind-bending solve with a Uniqueness of {uniqueness}, the rarest of the period!")

    if superlatives:
        embed.add_field(name="✨ Superlatives", value="\n".join(superlatives), inline=False)

    emit_footer = f"Posted: {discord.utils.utcnow().strftime('%Y-%m-%d')}"
    embed.set_footer(text=emit_footer)
    return embed

async def build_leaderboard_embed(game_name: str, title: str, rows: list[dict], period: str, color: discord.Color) -> discord.Embed:
    """
    Builds a Discord embed for a game leaderboard, formatted based on game type.
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

    SORT_KEYS = {
        "Wordle": lambda x: float(x.get("avg_attempts", float('inf'))),
        "Connections": lambda x: x.get("avg_score", 0),
        "Framed": lambda x: float(x.get("avg_attempts", float('inf'))),
        "Gisnep": lambda x: float(x.get("avg_time", float('inf'))),
        "Bandle": lambda x: float(x.get("avg_attempts", float('inf'))),
        "Minute Cryptic": lambda x: x.get("avg_score", 0),
        "Word Salad": lambda x: x.get("avg_score", -float('inf')) if x.get("avg_score") is not None else -float('inf'),
        "Pips": lambda x: (x.get("cookie_count", 0), x.get("total_score", 0)),
    }

    reverse_flags = {
        "Connections": True,
        "Minute Cryptic": True,
        "Word Salad": True,
        "Pips": True,
    }

    if game_name in SORT_KEYS:
        rows.sort(key=SORT_KEYS[game_name], reverse=reverse_flags.get(game_name, False))
    else:
        # Fallback for unexpected game names, sorting by a default key like 'games_played'
        rows.sort(key=lambda x: x.get("games_played", 0), reverse=True)

    if game_name == "Pips" and rows:
        max_cookies = rows[0].get("cookie_count", 0)
        if max_cookies > 0:
            for row in rows:
                if row.get("cookie_count") == max_cookies:
                    row["is_cookie_monster"] = True
    
    for i, row in enumerate(rows, start=1):
        medal = medals[i-1] if i <= len(medals) else f"#{i}"
        name = row.get("display_name", "Unknown Player")
        
        # Build field value depending on game type and available stats
        details = []
        
        # Customize the details based on the game name
        if game_name == "Wordle":
            avg_attempts = row.get("avg_attempts")
            avg_attempts_display = f"**{avg_attempts:.2f}**" if avg_attempts is not None else "N/A"
            details.append(f"⏱️ Avg Attempts: {avg_attempts_display}")
            
        elif game_name == "Connections":
            total_score = row.get("total_score", 0)
            purple_first_count = row.get("purple_first_count", 0)
            blue_first_count = row.get("blue_first_count", 0)
            avg_score = row.get("avg_score")
            
            avg_score_display = f"**{avg_score:.2f}**" if avg_score is not None else "N/A"
            details.append(f"⭐ Avg Score: {avg_score_display}")
            details.append(f"⭐ Total Score: **{total_score}**")
            details.append(f"🟪 Purple First: **{purple_first_count}**")
            details.append(f"🟦 Blue First: **{blue_first_count}**")
            
        elif game_name == "Framed":
            total_score = row.get("total_score", 0)
            avg_attempts = row.get("avg_attempts")
            avg_attempts_display = f"**{avg_attempts:.2f}**" if avg_attempts is not None else "N/A"
            details.append(f"⭐ Total Score: **{total_score}**")
            details.append(f"⏱️ Avg Attempts: {avg_attempts_display}")
            
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
            details.append(f"🎁 Bonus:\n{bonus_display}")
            
        elif game_name == "Minute Cryptic":
            solved_count = row.get("solved_count", 0)
            avg_score = row.get("avg_score")
            
            avg_score_display = f"**{avg_score:.2f}**" if avg_score is not None else "N/A"
            details.append(f"🔓 Solved: **{solved_count}**")
            details.append(f"📊 Avg Score: {avg_score_display}")
            
        elif game_name == "Word Salad":
            best_time = row.get("best_time")
            total_score = row.get("total_score", 0)
            avg_score = row.get("avg_score")
            avg_time = row.get("avg_time")

            avg_minutes, avg_seconds = divmod(int(avg_time) if avg_time is not None else 0, 60)
            best_minutes, best_seconds = divmod(int(best_time) if best_time is not None else 0, 60)
            
            best_time_display = f"**{best_minutes:02d}:{best_seconds:02d}**" if best_time is not None else "N/A"
            avg_score_display = f"**{avg_score:.2f}**" if avg_score is not None else "N/A"
            avg_time_display = f"**{avg_minutes:02d}:{avg_seconds:02d}**" if avg_time is not None else "N/A"

            details.append(f"🧠 Avg Score: {avg_score_display}")
            details.append(f"⭐ Total Score: **{total_score}**")
            details.append(f"⏱️ Avg Time: {avg_time_display}")
            details.append(f"🥇 Best Time: {best_time_display}")

        elif game_name == "Pips":
            total_score = row.get("total_score", 0)
            cookie_count = row.get("cookie_count", 0)
            details.append(f"⭐ Total Score: **{total_score}**")
            details.append(f"🍪 Cookies: **{cookie_count}**")
            if row.get("is_cookie_monster"):
                name = name.replace(" 🍪", "")
                name = f"{name} 🍪 (Cookie Monster)"


        field_value = "\n".join(details)
        embed.add_field(
            name=f"{medal} {name}",
            value=field_value,
            inline=True
        )

    emit_footer = f"Posted: {discord.utils.utcnow().strftime('%Y-%m-%d')}"
    embed.set_footer(text=emit_footer)
    return embed

async def build_embed_for_game(game_key, title, leaderboard_data, period, color):
    """
    Dispatcher function to build an embed for a specific game.
    """
    # Moved import here to avoid circular dependency
    import game_config

    try:
        config = game_config.GAME_CONFIGS[game_key]
        builder_func = config["embed_builder_function"]

        # Dedicated builders (e.g., build_wordle_leaderboard_embed)
        if builder_func.__name__.startswith("build_") and "leaderboard_embed" in builder_func.__name__ and builder_func.__name__ != "build_leaderboard_embed":
            return await builder_func(
                title=title,
                leaderboard_data=leaderboard_data,
                period=period,
                color=color
            )

        # Generic builder path
        keys = config.get("leaderboard_keys")
        if not keys:
            raise ValueError(f"Missing leaderboard_keys for generic game {config['name']}")

        rows = [dict(zip(keys, row)) for row in leaderboard_data]
        return await builder_func(
            game_name=config["name"],
            title=title,
            rows=rows,
            period=period.capitalize(),
            color=color
        )
    except KeyError:
        # This case handles if game_key is not in GAME_CONFIGS
        print(f"Error: No game configuration found for key '{game_key}'")
        return None
    except ValueError as e:
        # This case handles missing leaderboard_keys
        print(f"Configuration error for {game_key}: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors during embed building
        print(f"An unexpected error occurred while building embed for {game_key}: {e}")
        return None
