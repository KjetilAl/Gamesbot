import discord
from typing import List, Dict, Any, Union
from datetime import datetime, date
import database

async def get_members_with_role(guild: discord.Guild, role_name: str) -> List[discord.Member]:
    role = discord.utils.get(guild.roles, name=role_name)
    return [member for member in guild.members if role in member.roles] if role else []

async def remove_role(member: discord.Member, role_name: str) -> bool:
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role and role in member.roles:
        await member.remove_roles(role)
        return True
    return False

async def assign_role(member: discord.Member, role_name: str) -> bool:
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role and role not in member.roles:
        await member.add_roles(role)
        return True # Role was newly assigned
    return False # Role not assigned (or already present)

async def handle_game_role_assignment(
    guild: discord.Guild,
    member: discord.Member,
    game_key: str,
    game_config: Dict[str, Any],
    current_identifier: Any,
    latest_identifier: Any,
    all_game_configs: Dict[str, Dict[str, Any]] = None
) -> bool:
    """
    Handles role assignment logic and determines if an introduction is needed.
    Returns True if an introduction message should be posted.
    """
    role_name = game_config["player_role_name"]
    
    is_newer = False
    is_same = False
    
    try:
        # For Minute Cryptic, compare ISO date strings
        if game_key == "minute_cryptic":
            current_date_str = str(current_identifier) if current_identifier else ""
            latest_date_str = str(latest_identifier) if latest_identifier else ""
            if not latest_date_str:
                is_newer = True
            else:
                try:
                    current_date = date.fromisoformat(current_date_str)
                    latest_date = date.fromisoformat(latest_date_str)
                    if current_date > latest_date:
                        is_newer = True
                    elif current_date == latest_date:
                        is_same = True
                except ValueError as e:
                    print(f"Date parsing error: {e}")
                    return False
        else:
            # Handle other games via integer comparison
            current_num = int(current_identifier) if current_identifier else 0
            latest_num = int(latest_identifier) if latest_identifier else 0
            if current_num > latest_num:
                is_newer = True
            elif current_num == latest_num:
                is_same = True
    except (ValueError, TypeError) as e:
        print(f"Error comparing identifiers for {game_key}: {e}")
        return False

    # --- Role Assignment Logic ---
    should_process = is_newer or is_same
    if not should_process:
        return False

    # For Pips, role is only granted after all difficulties are completed.
    if game_key == 'pips':
        completed_difficulties = database.get_pips_completed_difficulties(member.id, int(current_identifier))
        if {'easy', 'medium', 'hard'}.issubset(set(completed_difficulties)):
            # If conditions are met, assign role and return True if it was newly assigned (for intro)
            was_newly_assigned = await assign_role(member, role_name)
            return was_newly_assigned
        else:
            # If conditions aren't met, do nothing and don't introduce.
            return False

    # --- Logic for all other games ---
    if is_newer:
        # Revoke role from others only if it's a new high score
        members_with_role = await get_members_with_role(guild, role_name)
        for m in members_with_role:
            if m.id != member.id:
                await remove_role(m, role_name)

    # Assign the role to the current member
    await assign_role(member, role_name)

    # For other games, introduction is based on posting a new or same score.
    return True

async def introduce_player_in_game_channel(
    guild: discord.Guild,
    member: discord.Member,
    game_config: Dict[str, Any],
    game_info: Dict[str, Any]
) -> None:
    channel_name = game_config["chat_channel_name"]
    game_channel = discord.utils.get(guild.text_channels, name=channel_name)
    
    if not game_channel:
        print(f"Could not find {channel_name} channel")
        return

    # Add user_id to game_info so all games can fetch more data for the intro message
    game_info['user_id'] = member.id
    
    intro_message = game_config["create_introduction"](member.display_name, game_info)
    await game_channel.send(intro_message)
    print(f"Introduction posted for {member.display_name} in #{channel_name}")
