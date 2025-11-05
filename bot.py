import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import aiohttp
import random
import asyncio
from datetime import datetime
import json

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Server ID
MY_SERVER_ID = 980305734342426644

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.presences = True

# Bot con prefix ! en lugar de ?
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# Constants
BADGE_EMOJIS = {
    1 << 0: "<:staff:1434657967659155578>",
    1 << 1: "<:partner:1434657966111330335>",
    1 << 2: "<:hypesquad:1434657982653923469>",
    1 << 3: "<:bughunter1:1434657958108725469>",
    1 << 6: "<:bravery:1434657977939267644>",
    1 << 7: "<:brilliance:1434657980212707350>",
    1 << 8: "<:balance:1434657970180067459>",
    1 << 9: "<:earlysupporter:1434657961690665142>",
    1 << 14: "<:bughunter2:1434657959841108050>",
    1 << 17: "<:developer:1434657956108173523>",
    1 << 18: "<:moderator:1434657963913642034>",
    1 << 22: "<:activedeveloper:1434657953453047858>",
}

STATUS_DISPLAY = {
    'online': 'Online',
    'idle': 'Idle',
    'dnd': 'Do Not Disturb',
    'offline': 'Offline'
}

AUTHORIZED_USER_ID = 985284787252105226

# Counting system
COUNTING_CHANNEL_ID = 1433118356860309536
COUNTING_FILE = "counting.json"

def load_counting_data():
    """Load counting data from JSON file."""
    try:
        with open(COUNTING_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default data structure
        return {str(MY_SERVER_ID): {"last_number": 0, "last_user": None}}

def save_counting_data():
    """Save counting data to JSON file."""
    with open(COUNTING_FILE, 'w') as f:
        json.dump(counting_data, f, indent=4)

# Load counting data at startup
counting_data = load_counting_data()

def check_server(interaction: discord.Interaction) -> bool:
    """Check if the command is being used in the authorized server."""
    return interaction.guild and interaction.guild.id == MY_SERVER_ID

async def send_unauthorized_message(interaction: discord.Interaction):
    """Send message when command is used in unauthorized server."""
    embed = discord.Embed(
        title="Command Not Available",
        description=(
            "This command is only available in the official server.\n"
            f"Join here: **[www.potyh.fun](https://www.potyh.fun)**"
        ),
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def get_user_complete_info_api(user_id: int) -> dict:
    """Get complete user information via direct API call."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://discord.com/api/v10/users/{user_id}",
                headers={"Authorization": f"Bot {TOKEN}"}
            ) as response:
                return await response.json() if response.status == 200 else {}
    except Exception as e:
        print(f"Error fetching user info via API: {e}")
        return {}

async def get_user_badges_with_emojis(public_flags: int) -> str:
    """Get user badges with custom emojis displayed horizontally."""
    if not public_flags:
        return "**No badges**"
    
    user_badges = [
        emoji for flag, emoji in BADGE_EMOJIS.items() 
        if public_flags & flag
    ]
    
    return f">>> {''.join(user_badges)}" if user_badges else "**No badges**"

def format_date(dt) -> str:
    """Format datetime object to readable string."""
    return dt.strftime("%B %d, %Y %I:%M %p") if dt else "Unknown"

def create_footer() -> str:
    """Create standardized footer text."""
    return f"by @potyhx  •  {datetime.now().strftime('Today at %H:%M')}"

@tasks.loop(seconds=120)
async def keep_voice_alive():
    """Keep voice connection alive by playing silent audio."""
    for vc in bot.voice_clients:
        if vc.is_connected() and not vc.is_playing():
            try:
                if os.path.exists("notification.mp3"):
                    source = discord.FFmpegPCMAudio("notification.mp3")
                    audio_source = discord.PCMVolumeTransformer(source, volume=0.0001)
                    vc.play(audio_source)
                    print(f"Playing silent audio in {vc.channel}")
                else:
                    print("notification.mp3 file not found")
            except Exception as e:
                print(f"Audio playback error: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    """Auto-reconnect bot if disconnected from voice channel."""
    if member == bot.user and before.channel and not after.channel:
        print(f"Bot disconnected from {before.channel.name}")
        await asyncio.sleep(3)
        try:
            await before.channel.connect()
            print("Auto-reconnected after disconnect")
        except Exception as e:
            print(f"Auto-reconnection error: {e}")

async def get_member_info(interaction: discord.Interaction, target_user: discord.User) -> tuple:
    """Get server-specific member information."""
    if not interaction.guild:
        return None, None
    
    target_member = interaction.guild.get_member(target_user.id)
    if not target_member:
        return None, None
    
    joined_date = format_date(target_member.joined_at)
    roles = [role.name for role in target_member.roles[1:]]
    roles_text = ", ".join(roles) if roles else "None"
    
    server_texto = (
        f">>> **Found in Server:** {interaction.guild.name}\n"
        f"**Joined Server:** `{joined_date}`\n"
        f"**Roles:** {roles_text}"
    )
    
    return server_texto, target_member

async def get_status_activity(target_member: discord.Member) -> str:
    """Get member status and custom activity."""
    if not target_member:
        return ""
    
    status_text = STATUS_DISPLAY.get(str(target_member.status), 'Offline')
    custom_status = next(
        (activity.name for activity in target_member.activities 
         if isinstance(activity, discord.CustomActivity)),
        None
    )
    
    status_activity_text = f">>> **Status:** {status_text}\n"
    if custom_status:
        status_activity_text += f"**Custom Status:** {custom_status}"
    
    return status_activity_text

async def get_decorative_items(api_data: dict, target_user: discord.User) -> tuple:
    """Get avatar, banner and decoration links."""
    avatar_hash = api_data.get('avatar')
    avatar_url = (f"https://cdn.discordapp.com/avatars/{target_user.id}/{avatar_hash}.png?size=1024" 
                 if avatar_hash else target_user.display_avatar.url)
    avatar_link = f"[**Avatar**]({avatar_url})"

    banner_hash = api_data.get('banner')
    banner_url = f"https://cdn.discordapp.com/banners/{target_user.id}/{banner_hash}.png?size=1024" if banner_hash else None
    banner_link = f"[**Banner**]({banner_url})" if banner_url else "**No banner**"

    decoration_data = api_data.get('avatar_decoration_data')
    decoration_link = "**No avatar decoration**"
    if decoration_data and decoration_data.get('asset'):
        decoration_asset = decoration_data['asset']
        decoration_url = f"https://cdn.discordapp.com/avatar-decorations/{target_user.id}/{decoration_asset}.png"
        decoration_link = f"[**Avatar Decoration**]({decoration_url})"

    return avatar_link, banner_link, decoration_link, avatar_url, banner_url

async def get_clan_info(api_data: dict) -> str:
    """Get clan information from API data."""
    clan_data = api_data.get('clan') or api_data.get('primary_guild')
    if not clan_data:
        return "**No Clan Tag**"
    
    clan_info_parts = []
    
    if clan_tag := clan_data.get('tag'):
        clan_info_parts.append(f"> **Tag:** {clan_tag}")
    
    if guild_id := clan_data.get('identity_guild_id'):
        clan_info_parts.append(f"> **Server ID:** `{guild_id}`")
    
    if badge_hash := clan_data.get('badge'):
        if guild_id:
            badge_url = f"https://cdn.discordapp.com/clan-badges/{guild_id}/{badge_hash}.png"
            clan_info_parts.append(f"> **[Badge]({badge_url})**")
        else:
            clan_info_parts.append(f"> **Badge Hash:** {badge_hash}")
    
    return "\n".join(clan_info_parts) if clan_info_parts else "**No Clan Tag**"

@bot.tree.command(name="userinfo", description="Get detailed information about a user.")
async def userinfo(interaction: discord.Interaction, user: discord.User = None):
    # Check if command is used in authorized server
    if not check_server(interaction):
        await send_unauthorized_message(interaction)
        return

    target_user = user or interaction.user

    api_data = await get_user_complete_info_api(target_user.id)
    if not api_data:
        await interaction.response.send_message("Error: Could not fetch user data.", ephemeral=True)
        return

    # Basic user info
    account_type = "Bot Account" if target_user.bot else "User Account"
    discriminator_text = f"**Discriminator:** `#{target_user.discriminator}`\n" if hasattr(target_user, 'discriminator') and target_user.discriminator != '0' else ""
    
    global_name = api_data.get('global_name')
    global_name = "None" if not global_name or global_name == target_user.name else global_name

    info_texto = (
        f">>> **Type:** {account_type}\n"
        f"**Mention:** {target_user.mention}\n"
        f"**Username:** {target_user.name}\n"
        f"{discriminator_text}"
        f"**Global Name:** {global_name}\n"
        f"**User ID:** `{target_user.id}`\n"
        f"**Created:** `{format_date(target_user.created_at)}`"
    )

    # Get additional information
    server_texto, target_member = await get_member_info(interaction, target_user)
    status_activity_text = await get_status_activity(target_member)
    avatar_link, banner_link, decoration_link, avatar_url, banner_url = await get_decorative_items(api_data, target_user)
    badges_text = await get_user_badges_with_emojis(api_data.get('public_flags', 0))
    clan_text = await get_clan_info(api_data)

    decorative_texto = f">>> {avatar_link}\n{banner_link}\n{decoration_link}"

    # Create embed
    embed = discord.Embed(title="User Information", color=discord.Color.from_rgb(88, 101, 242))
    
    # Add fields conditionally
    embed.add_field(name="General Info", value=info_texto, inline=False)
    if badges_text != "**No badges**":
        embed.add_field(name="Badges", value=badges_text, inline=False)
    if clan_text != "**No Clan Tag**":
        embed.add_field(name="Clan Info", value=clan_text, inline=False)
    if status_activity_text.strip():
        embed.add_field(name="Status & Activities", value=status_activity_text, inline=False)
    if server_texto:
        embed.add_field(name="Server Info", value=server_texto, inline=False)
    embed.add_field(name="Decorative Items", value=decorative_texto, inline=False)
    
    # Set images and footer
    embed.set_thumbnail(url=avatar_url)
    if banner_url:
        embed.set_image(url=banner_url)
    embed.set_footer(text=create_footer(), icon_url=bot.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Show all available commands.")
async def help(interaction: discord.Interaction):
    # Check if command is used in authorized server
    if not check_server(interaction):
        await send_unauthorized_message(interaction)
        return

    embed = discord.Embed(
        title="Command List",
        description="*Only available in this server.*",
        color=discord.Color.from_rgb(88, 101, 242)
    )
    
    commands_list = """>>> `-` **/userinfo:** Get detailed info about a user.\n`-` **/memide:** Generates a random measurement.\n`-` **/gayrate:** Shows a random percentage (fun).\n`-` **/dado:** Roll a dice from 1 to 6.\n`-` **/ping:** Checks if the bot is online."""
    
    embed.add_field(name="", value=commands_list, inline=False)
    embed.set_footer(text=create_footer(), icon_url=bot.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="memide", description="Generates a random measurement.")
async def memide(interaction: discord.Interaction, member: discord.Member = None):
    # Check if command is used in authorized server
    if not check_server(interaction):
        await send_unauthorized_message(interaction)
        return

    member = member or interaction.user
    await interaction.response.send_message(f"A {member.display_name} le mide **{random.randint(1, 23)} cm**")

@bot.tree.command(name="gayrate", description="Shows a random percentage (fun).")
async def gayrate(interaction: discord.Interaction, member: discord.Member = None):
    # Check if command is used in authorized server
    if not check_server(interaction):
        await send_unauthorized_message(interaction)
        return

    member = member or interaction.user
    await interaction.response.send_message(f"{member.display_name} es {random.randint(1, 100)}% gay")

@bot.tree.command(name="ping", description="Checks if the bot is online.")
async def ping(interaction: discord.Interaction):
    # Check if command is used in authorized server
    if not check_server(interaction):
        await send_unauthorized_message(interaction)
        return

    await interaction.response.send_message("Pong!")

@bot.tree.command(name="join", description="Bot joins your voice channel.")
async def join(interaction: discord.Interaction):
    # Check if command is used in authorized server
    if not check_server(interaction):
        await send_unauthorized_message(interaction)
        return

    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_connected():
        await interaction.response.send_message(f"Already connected to {voice_client.channel}")
        return

    if not interaction.user.voice:
        await interaction.response.send_message("You must be in a voice channel to use this command.")
        return

    try:
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message(f"Joined voice channel: {channel}")
        print(f"Connected to {channel.name}")
    except Exception as e:
        await interaction.response.send_message(f"Error connecting: {str(e)}")

@bot.tree.command(name="dado", description="Roll a dice from 1 to 6.")
async def dado(interaction: discord.Interaction):
    # Check if command is used in authorized server
    if not check_server(interaction):
        await send_unauthorized_message(interaction)
        return

    await interaction.response.send_message(f"🎲 El dado cayó en el número {random.randint(1, 6)}")

@bot.event
async def on_message(message):
    """Handle counting system and process commands."""
    if message.author.bot:
        return
    
    # Counting system
    if message.channel.id == COUNTING_CHANNEL_ID:
        await handle_counting(message)
    
    # Process commands
    await bot.process_commands(message)

async def handle_counting(message):
    """Handle counting channel messages - simplified version."""
    server_id = str(message.guild.id)
    
    # Initialize server data if not exists
    if server_id not in counting_data:
        counting_data[server_id] = {"last_number": 0, "last_user": None}
    
    current_data = counting_data[server_id]
    
    try:
        # Try to convert message to number
        number = int(message.content.strip())
        
        expected_number = current_data["last_number"] + 1
        
        # Check if it's the correct number and not the same user
        if number == expected_number and message.author.id != current_data["last_user"]:
            # Correct count - update data
            current_data["last_number"] = number
            current_data["last_user"] = message.author.id
            save_counting_data()
        else:
            # Wrong number or same user - delete message silently
            await message.delete()
            
    except ValueError:
        # Message is not a number - delete it silently
        await message.delete()

@bot.command()
async def embed(ctx):
    if ctx.author.id != AUTHORIZED_USER_ID:
        return
    
    embed = discord.Embed(
        title="Choose Your Color",
        description="*Choose a color role you'd like. Your username will change to the color you select.*",
        color=discord.Color.from_rgb(88, 101, 242)
    )
    
    rules_part1 = """>>> `-` <@&1341481118112940032>
`-` <@&1341481117525479474>
`-` <@&1341481118708269096>
`-` <@&1341481102732431371>
`-` <@&1341481568090329199>"""
    
    embed.add_field(name="", value=rules_part1, inline=False)
    embed.add_field(name="", value="**Note:** Select the same color again to remove the color role.", inline=False)
    
    embed.set_footer(text=create_footer(), icon_url=bot.user.display_avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def embed2(ctx):
    if ctx.author.id != AUTHORIZED_USER_ID:
        return

    embed = discord.Embed(
        title="Verification",
        description="Click the button below to verify your account and get full server access.",
        color=discord.Color.from_rgb(88, 101, 242)
    )
    
    react_section = """>>> React with ⚔️ to get <@&1060288557949927524> rank and see all channels."""
    
    embed.add_field(name="", value=react_section, inline=False)
    embed.set_image(url="https://i.imgur.com/YlpLaUk.png")
    embed.set_footer(text=create_footer(), icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print("Sincronizando comandos...")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos:")
        for cmd in synced:
            print(f" - /{cmd.name}")
    except Exception as e:
        print(f"Error sincronizando: {e}")
    
    keep_voice_alive.start()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.custom,
            name="Custom Status",
            state="/help | www.potyh.fun"
        ),
        status=discord.Status.dnd
    )
    print(f"Bot conectado como {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        original = error.original
        if hasattr(original, 'code') and original.code == 1006:
            print("Handling error 1006 - recovering connection")
            return
    print(f"Error: {error}")

bot.run(TOKEN)
