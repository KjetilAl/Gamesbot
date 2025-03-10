import discord
from typing import List, Dict, Any

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
    game_config: Dict[str, Any],
    current_game_number: int,
    latest_game_number: int
) -> bool:
    role_name = game_config["player_role_name"]
    
    if current_game_number > latest_game_number:
        # New highest game number: reset roles
        members_with_role = await get_members_with_role(guild, role_name)
        for member_to_revoke in members_with_role:
            await remove_role(member_to_revoke, role_name)
        return await assign_role(member, role_name)
    
    elif current_game_number == latest_game_number:
        # Same as latest game: just assign role
        return await assign_role(member, role_name)
    
    return False  # Old game, do nothing

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
    try:
        await game_channel.send(intro_message)
        print(f"Sent introduction message to {channel_name}")
    except Exception as e:
        print(f"Error sending introduction to {channel_name}: {e}")
