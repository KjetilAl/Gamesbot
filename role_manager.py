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
    latest_identifier: Any,
    all_game_configs: Dict[str, Dict[str, Any]] = None  # Add this optional parameter
) -> bool:
    role_name = game_config["player_role_name"]
    
    newly_assigned = False
    is_newer = False
    is_same = False
    
    try:
        # For Minute Cryptic, we need to compare ISO date strings
        if game_key == "minute_cryptic":
            # Make sure we're working with strings
            current_date_str = str(current_identifier) if current_identifier else ""
            latest_date_str = str(latest_identifier) if latest_identifier else ""
            
            # Handle case where we have no latest date yet
            if not latest_date_str:
                is_newer = True
            else:
                # Proper date comparison
                try:
                    current_date = date.fromisoformat(current_date_str)
                    latest_date = date.fromisoformat(latest_date_str)
                    print(f"Role Check (Date): Current={current_date}, Latest={latest_date} for {member.display_name}")
                    
                    if current_date > latest_date:
                        is_newer = True
                    elif current_date == latest_date:
                        is_same = True
                except ValueError as e:
                    print(f"Date parsing error: {e} for values current={current_date_str}, latest={latest_date_str}")
                    return False
        else:
            # Handle other games (Integer comparison)
            # Convert to integers for comparison, handling None/empty values
            current_num = int(current_identifier) if current_identifier else 0
            latest_num = int(latest_identifier) if latest_identifier else 0
            
            print(f"Role Check ({game_key}): Current={current_num}, Latest={latest_num} for {member.display_name}")
            
            if current_num > latest_num:
                is_newer = True
            elif current_num == latest_num:
                is_same = True
    except (ValueError, TypeError) as e:
        print(f"Error comparing identifiers for {game_key}: Current='{current_identifier}', Latest='{latest_identifier}'. Error: {e}")
        return False # Cannot compare, do nothing
    
    print(f"Role decision for {member.display_name} ({game_key}): is_newer={is_newer}, is_same={is_same}")
    
    # --- Role Logic ---
    should_assign_role = False
    if is_newer:
        # New highest identifier: reset roles for everyone with the role
        members_with_role = await get_members_with_role(guild, role_name)
        for member_to_revoke in members_with_role:
            if member_to_revoke.id != member.id: # Don't revoke from the current poster yet
                 await remove_role(member_to_revoke, role_name)
                 print(f"Revoked {role_name} from {member_to_revoke.display_name}")
        should_assign_role = True

    elif is_same:
        # Same as latest identifier: just assign role if needed
        if role_name not in [role.name for role in member.roles]:
            should_assign_role = True

    if should_assign_role:
        can_receive_role = False
        if game_key == 'pips':
            # For Pips, role is granted only after completing all three difficulties for the current game number.
            completed_difficulties = database.get_pips_completed_difficulties(member.id, int(current_identifier))
            if {'easy', 'medium', 'hard'}.issubset(set(completed_difficulties)):
                can_receive_role = True
                print(f"Pips role condition met for {member.display_name} (completed all difficulties for #{current_identifier})")
            else:
                print(f"Pips role condition not met for {member.display_name} (difficulties completed: {completed_difficulties})")
        else:
            can_receive_role = True

        if can_receive_role:
            newly_assigned = await assign_role(member, role_name)
            if newly_assigned:
                print(f"Assigned {role_name} to {member.display_name}")
    
    return newly_assigned

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

    # Add user_id to game_info for Pips, so it can fetch all scores for the intro message
    if game_config.get("name") == "Pips":
        game_info['user_id'] = member.id
    
    intro_message = game_config["create_introduction"](member.display_name, game_info)
    await game_channel.send(intro_message)
    print(f"Introduction posted for {member.display_name} in #{channel_name}")
