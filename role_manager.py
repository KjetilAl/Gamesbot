import discord
from typing import List, Dict, Any, Union
from datetime import datetime, date

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
    if role:
        await member.add_roles(role)
        return True
    return False

async def handle_game_role_assignment(
    guild: discord.Guild,
    member: discord.Member,
    game_key: str,
    game_config: Dict[str, Any], # This is the config for the specific game_key
    current_identifier: Any,
    latest_identifier: Any
) -> bool:
    role_name = game_config["player_role_name"]
    game_key = next((key for key, cfg in game_config.GAME_CONFIGS.items() if cfg["name"] == game_config["name"]), None) # Find game key

    newly_assigned = False
    is_newer = False
    is_same = False

    try:
        # --- Use the PASSED-IN game_key directly ---
        if game_key == "minute_cryptic":
            current_date = date.fromisoformat(str(current_identifier))
            latest_date = date.fromisoformat(str(latest_identifier))
            print(f"Role Check (Date): Current={current_date}, Latest={latest_date} for {member.display_name}") # Debug
            if current_date > latest_date:
                is_newer = True
            elif current_date == latest_date:
                is_same = True
        else: # Handle other games (Integer comparison)
             # Convert identifier strings to int for comparison
            current_num = int(current_identifier)
            latest_num = int(latest_identifier) # latest_identifier from DB is already string
            print(f"Role Check (Int): Current={current_num}, Latest={latest_num} for {member.display_name}") # Debug
            if current_num > latest_num:
                is_newer = True
            elif current_num == latest_num:
                is_same = True

    except (ValueError, TypeError) as e:
        print(f"Error comparing identifiers for {game_key}: Current='{current_identifier}', Latest='{latest_identifier}'. Error: {e}")
        return False # Cannot compare, do nothing

    # --- Role Logic ---
    if is_newer:
        # New highest identifier: reset roles for everyone with the role
        members_with_role = await get_members_with_role(guild, role_name)
        for member_to_revoke in members_with_role:
            if member_to_revoke.id != member.id: # Don't revoke from the current poster yet
                 await remove_role(member_to_revoke, role_name)
            #else: # Debug log
                 #print(f"Skipping revoke for current poster: {member.display_name}")

        # Assign role to the current poster
        newly_assigned = await assign_role(member, role_name)

    elif is_same:
        # Same as latest identifier: just assign role if needed
        newly_assigned = await assign_role(member, role_name)

    # else: old identifier, do nothing

    return newly_assigned # Return True only if the role was newly assigned to *this* user

async def introduce_player_in_game_channel(
    guild: discord.Guild,
    display_name: str,
    game_config: Dict[str, Any],
    game_info: Dict[str, Any]
) -> None:
    channel_name = game_config["chat_channel_name"]
    game_channel = discord.utils.get(guild.text_channels, name=channel_name)
    
    if not game_channel:
        print(f"Could not find {channel_name} channel")
        return
    
    intro_message = game_config["create_introduction"](display_name, game_info)
    await game_channel.send(intro_message)
    print(f"Introduction posted for {display_name} in #{channel_name}")
