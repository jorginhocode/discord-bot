import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import aiohttp
import random
import asyncio
from datetime import datetime
from typing import Optional

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.presences = True

bot = commands.Bot(
    command_prefix="?",
    intents=intents,
    help_command=None
)

async def get_user_complete_info_api(user_id: int) -> dict:
    """Get complete user information via direct API call."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://discord.com/api/v10/users/{user_id}",
                headers={"Authorization": f"Bot {TOKEN}"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"API returned status {response.status} for user {user_id}")
                    return {}
    except Exception as e:
        print(f"Error fetching user info via API: {e}")
        return {}

async def get_user_badges_with_emojis(public_flags: int) -> str:
    """Get user badges with custom emojis displayed horizontally."""
    if not public_flags:
        return "**No badges**"
    
    # Discord User Flags with custom emoji IDs
    # REEMPLAZA ESTOS IDs CON LOS IDs REALES DE TUS EMOJIS
    badge_emojis = {
        1 << 0: "<:staff:1434603572376506388>",  # Staff - Reemplaza con ID real
        1 << 1: "<:partner:1434603570426282165>",  # Partner - Reemplaza con ID real
        1 << 2: "<:hypesquad:1434603578210652342>",  # Hypesquad Events - Reemplaza con ID real
        1 << 3: "<:bughunter1:1434603560603222279>",  # Bug Hunter Level 1 - Reemplaza con ID real
        1 << 6: "<:bravery:1434596677670670468>",  # HypeSquad Bravery - Ya tienes este ID
        1 << 7: "<:brilliance:1434603619977793767>",  # HypeSquad Brilliance - Reemplaza con ID real
        1 << 8: "<:balance:1434603574012280922>",  # HypeSquad Balance - Reemplaza con ID real
        1 << 9: "<:earlysupporter:1434603563841224764>",  # Early Supporter - Reemplaza con ID real
        1 << 14: "<:bughunter2:1434603562205188297>",  # Bug Hunter Level 2 - Reemplaza con ID real
        1 << 17: "<:developer:1434603558631768216>",  # Early Verified Bot Developer - Reemplaza con ID real
        1 << 18: "<:moderator:1434603566290702489>",  # Discord Certified Moderator - Reemplaza con ID real
        1 << 22: "<:activedeveloper:1434603554974466189>",  # Active Developer - Reemplaza con ID real
    }
    
    # Check which badges the user has
    user_badges = []
    for flag, emoji in badge_emojis.items():
        if public_flags & flag:
            user_badges.append(emoji)
    
    if not user_badges:
        return "**No badges**"
    
    # Create horizontal display with emojis
    badges_display = " ".join(user_badges)
    return badges_display

@tasks.loop(seconds=120)
async def keep_voice_alive():
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
    if member == bot.user:
        if before.channel and not after.channel:
            print(f"Bot disconnected from {before.channel.name}")
            await asyncio.sleep(3)
            try:
                await before.channel.connect()
                print("Auto-reconnected after disconnect")
            except Exception as e:
                print(f"Auto-reconnection error: {e}")

@bot.tree.command(name="userinfo", description="Get detailed information about a user")
async def userinfo(interaction: discord.Interaction, user: discord.User = None):
    target_user = user or interaction.user

    # Get complete user data from API
    api_data = await get_user_complete_info_api(target_user.id)
    
    if not api_data:
        await interaction.response.send_message("Error: Could not fetch user data.", ephemeral=True)
        return

    def format_date(dt):
        if not dt:
            return "Unknown"
        return dt.strftime("%B %d, %Y %I:%M %p")

    created_date = format_date(target_user.created_at)
    account_type = "Bot Account" if target_user.bot else "User Account"

    discriminator_text = ""
    if hasattr(target_user, 'discriminator') and target_user.discriminator != '0':
        discriminator_text = f"**Discriminator:** `#{target_user.discriminator}`\n"

    server_texto = None
    target_member = None

    # Global Name handling - show "None" if same as username
    global_name = api_data.get('global_name')
    if global_name and global_name == target_user.name:
        global_name = "None"
    elif not global_name:
        global_name = "None"

    if interaction.guild:
        target_member = interaction.guild.get_member(target_user.id)
        if target_member:
            joined_date = format_date(target_member.joined_at) if target_member.joined_at else "Unknown"
            roles = [role.name for role in target_member.roles[1:]]
            roles_text = ", ".join(roles) if roles else "None"
            
            # Get server information
            server_name = interaction.guild.name
            
            server_texto = (
                f">>> **Found in Server:** {server_name}\n"
                f"**Roles:** {roles_text}\n"
                f"**Joined Server:** `{joined_date}`"
            )

    status_activity_text = ""
    if target_member:
        status = str(target_member.status)
        status_display = {
            'online': 'Online',
            'idle': 'Idle',
            'dnd': 'Do Not Disturb',
            'offline': 'Offline'
        }
        status_text = status_display.get(status, 'Offline')

        custom_status = None
        for activity in target_member.activities:
            if isinstance(activity, discord.CustomActivity):
                custom_status = activity.name
                break

        status_activity_text = f">>> **Status:** {status_text}\n"
        if custom_status:
            status_activity_text += f"**Custom Status:** {custom_status}"

    # Avatar from API data
    avatar_hash = api_data.get('avatar')
    avatar_url = f"https://cdn.discordapp.com/avatars/{target_user.id}/{avatar_hash}.png?size=1024" if avatar_hash else target_user.display_avatar.url
    avatar_link = f"[**Avatar**]({avatar_url})"

    # Banner from API data
    banner_hash = api_data.get('banner')
    banner_url = f"https://cdn.discordapp.com/banners/{target_user.id}/{banner_hash}.png?size=1024" if banner_hash else None
    banner_link = f"[**Banner**]({banner_url})" if banner_url else "**No banner**"

    # Avatar decoration from API data
    decoration_data = api_data.get('avatar_decoration_data')
    decoration_link = "**No avatar decoration**"
    if decoration_data and decoration_data.get('asset'):
        decoration_asset = decoration_data['asset']
        decoration_url = f"https://cdn.discordapp.com/avatar-decorations/{target_user.id}/{decoration_asset}.png"
        decoration_link = f"[**Avatar Decoration**]({decoration_url})"

    # --- Badges with custom emojis ---
    public_flags = api_data.get('public_flags', 0)
    badges_text = await get_user_badges_with_emojis(public_flags)

    # --- Clan Information from API data ---
    clan_text = "**No Clan Tag**"
    
    clan_data = api_data.get('clan') or api_data.get('primary_guild')
    if clan_data:
        clan_info_parts = []
        
        clan_tag = clan_data.get('tag')
        if clan_tag:
            clan_info_parts.append(f"> **Tag:** {clan_tag}")
            
        guild_id = clan_data.get('identity_guild_id')
        if guild_id:
            clan_info_parts.append(f"> **Server ID:** {guild_id}")
            
        badge_hash = clan_data.get('badge')
        if badge_hash and guild_id:
            badge_url = f"https://cdn.discordapp.com/clan-badges/{guild_id}/{badge_hash}.png"
            clan_info_parts.append(f"> **[Badge]({badge_url})**")
        elif badge_hash:
            clan_info_parts.append(f"> **Badge Hash:** {badge_hash}")
            
        if clan_info_parts:
            clan_text = "\n".join(clan_info_parts)

    info_texto = (
        f">>> **Type:** {account_type}\n"
        f"**Mention:** {target_user.mention}\n"
        f"**Username:** {target_user.name}\n"
        f"{discriminator_text}"
        f"**Global Name:** {global_name}\n"
        f"**User ID:** {target_user.id}\n"
        f"**Created:** `{created_date}`"
    )

    decorative_texto = (
        f">>> {avatar_link}\n"
        f"{banner_link}\n"
        f"{decoration_link}"
    )

    embed = discord.Embed(
        title="User Information",
        color=discord.Color.from_rgb(88, 101, 242)
    )

    embed.add_field(name="General Info", value=info_texto, inline=False)

    # Add Badges field
    if badges_text != "**No badges**":
        embed.add_field(name="Badges", value=badges_text, inline=False)

    # Add Clan Info field if available
    if clan_text != "**No Clan Tag**":
        embed.add_field(name="Clan Info", value=clan_text, inline=False)

    if status_activity_text.strip():
        embed.add_field(name="Status & Activities", value=status_activity_text, inline=False)

    if server_texto:
        embed.add_field(name="Server Info", value=server_texto, inline=False)

    embed.add_field(name="Decorative Items", value=decorative_texto, inline=False)
    embed.set_thumbnail(url=avatar_url)

    if banner_url:
        embed.set_image(url=banner_url)

    current_time = datetime.now().strftime("Today at %H:%M")
    embed.set_footer(text=f"by @potyhx  •  {current_time}")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Show all available commands")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="BOT COMMANDS",
        description=(
            "`•` /userinfo: Get detailed info about a user.\n"
            "`•` /gayrate: Shows a random percentage (fun).\n"
            "`•` /memide: Generates a random measurement.\n"
            "`•` /ping: Checks if the bot is online.\n"
            "`•` /join: Bot joins your voice channel.\n"
            "`•` /dado: Tira un dado del 1 al 6.\n"
        ),
        color=discord.Color.from_rgb(0, 0, 1)
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="memide", description="Generates a random measurement")
async def memide(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    medida = random.randint(1, 50)
    await interaction.response.send_message(f"A {member.display_name} le mide **{medida} cm**")

@bot.tree.command(name="gayrate", description="Shows a random percentage (fun)")
async def gayrate(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    porcentaje = random.randint(1, 100)
    await interaction.response.send_message(f"{member.display_name} es {porcentaje}% gay")

@bot.tree.command(name="ping", description="Checks if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="join", description="Bot joins your voice channel")
async def join(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_connected():
        await interaction.response.send_message(f"Already connected to {voice_client.channel}")
        return

    if interaction.user.voice:
        try:
            channel = interaction.user.voice.channel
            await channel.connect()
            await interaction.response.send_message(f"Joined voice channel: {channel}")
            print(f"Connected to {channel.name}")
        except Exception as e:
            await interaction.response.send_message(f"Error connecting: {str(e)}")
    else:
        await interaction.response.send_message("You must be in a voice channel to use this command.")

@bot.tree.command(name="dado", description="Tira un dado del 1 al 6")
async def dado(interaction: discord.Interaction):
    numero = random.randint(1, 6)
    await interaction.response.send_message(f"🎲 El dado cayó en el número {numero}")

@bot.event
async def on_ready():
    print("Sincronizando comandos...")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Sincronizados {len(synced)} comandos:")
        for cmd in synced:
            print(f" - /{cmd.name}")
    except Exception as e:
        print(f"❌ Error sincronizando: {e}")
    
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

@bot.event
async def on_message(message):
    if message.author.bot:
        return

bot.run(TOKEN)
