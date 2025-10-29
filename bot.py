import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
import aiohttp
import random
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class StableBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):
        await self.tree.sync()

bot = StableBot()
bot.remove_command('help')

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

@bot.tree.command(name="help", description="Show all available commands")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="BOT COMMANDS",
        description=(
            "`•` /country: Shows a random country with its flag.\n"
            "`•` /gayrate: Shows a random percentage (fun).\n"
            "`•` /memide: Generates a random measurement.\n"
            "`•` /coinflip: Responds Yes / No / Maybe.\n"
            "`•` /bitcoin: Shows the current Bitcoin price.\n"
            "`•` /ping: Checks if the bot is online.\n"
            "`•` /join: Bot joins your voice channel.\n"
        ),
        color=discord.Color.from_rgb(0, 0, 1)
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="country", description="Shows a random country with its flag")
async def country(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    paises = [
        ("boliviano", "🇧🇴"),
        ("peruano", "🇵🇪"),
        ("argentino", "🇦🇷"),
        ("ecuatoriano", "🇪🇨"),
        ("venezolano", "🇻🇪"),
        ("nigeriano", "🇳🇬"),
        ("senegalés", "🇸🇳"),
        ("estadounidense", "🇺🇸")
    ]
    pais, bandera = random.choice(paises)
    await interaction.response.send_message(f"{member.display_name} es {pais} {bandera}")

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

async def get_bitcoin_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['bitcoin']['usd']
                else:
                    return None
    except:
        return None

@bot.tree.command(name="ping", description="Checks if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="bitcoin", description="Shows the current Bitcoin price")
async def bitcoin(interaction: discord.Interaction):
    price = await get_bitcoin_price()
    if price:
        await interaction.response.send_message(f"$ BTC Price: ${price:,.2f} USD")
    else:
        await interaction.response.send_message("Could not get Bitcoin price")

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

@bot.tree.command(name="coinflip", description="Responds Yes / No / Maybe")
async def coinflip(interaction: discord.Interaction):
    respuesta = random.choice(["Sí", "No", "Tal vez"])
    await interaction.response.send_message(respuesta)

@bot.event
async def on_ready():
    keep_voice_alive.start()
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.custom,
            name="Custom Status",
            state="/help | potyh.fun"
        ),
        status=discord.Status.dnd
    )
    
    print(f"Bot connected as {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        original = error.original
        if hasattr(original, 'code') and original.code == 1006:
            print("Handling error 1006 - recovering connection")
            await ctx.send("Connection issue detected, reconnecting...")
            return
    print(f"Error: {error}")

bot.run(TOKEN)
