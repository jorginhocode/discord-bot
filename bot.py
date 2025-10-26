import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
import random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot.remove_command('help')

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="BOT COMMANDS",
        description=(
            "`•` country: Shows a random country with its flag.\n"
            "`•` gayrate: Shows a random percentage (fun).\n"
            "`•` memide: Generates a random measurement.\n"
            "`•` coinflip: Responds Yes / No / Maybe.\n"
            "`•` bitcoin: Shows the current Bitcoin price.\n"
            "`•` ping: Checks if the bot is online.\n"
            "`•` join: Bot joins your voice channel.\n\n"
            "**`!` is the prefix to use the commands.**"
        ),
        color=discord.Color.from_rgb(0, 0, 1)  # Color negro
    )

    await ctx.send(embed=embed)



@bot.command()
async def country(ctx, member: discord.Member = None):
    member = member or ctx.author
    paises = [
        ("Bolivia", "🇧🇴"),
        ("Peru", "🇵🇪"),
        ("Argentina", "🇦🇷"),
        ("Ecuador", "🇪🇨"),
        ("Venezuela", "🇻🇪"),
        ("Nigeria", "🇳🇬"),
        ("Senegal", "🇸🇳"),
        ("Congo", "🇨🇬"),
        ("Uganda", "🇺🇬"),
        ("Estados Unidos", "🇺🇸")
    ]
    pais, bandera = random.choice(paises)
    await ctx.send(f"{member.display_name} es de **{pais}** {bandera}")


@bot.command()
async def memide(ctx, member: discord.Member = None):
    member = member or ctx.author
    medida = random.randint(1, 50)
    await ctx.send(f"A {member.display_name} le mide **{medida} cm**")

@bot.command()
async def gayrate(ctx, member: discord.Member = None):
    member = member or ctx.author
    porcentaje = random.randint(1, 100)
    await ctx.send(f"{member.display_name} es **{porcentaje}% gay**")

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

@bot.event
async def on_ready():
    activity = discord.Activity(
        type=discord.ActivityType.streaming,
        name="600 | !help !country !gayrate !bitcoin",
        url="https://www.twitch.tv/potyhw"
    )
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=activity
    )
    print(f"Bot connected as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def bitcoin(ctx):
    price = await get_bitcoin_price()
    
    if price:
        await ctx.send(f"$ BTC Price: **${price:,.2f} USD**")
    else:
        await ctx.send("Could not get Bitcoin price")

@bot.command()
async def join(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_connected():
        await ctx.send(f"Already connected to {voice_client.channel}")
        return

    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"Joined voice channel: {channel}")
    else:
        await ctx.send("You must be in a voice channel to use this command.")

@bot.command()
async def coinflip(ctx):
    respuesta = random.choice(["Sí", "No", "Tal vez"])
    await ctx.send(respuesta)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "!coinflip" in message.content.lower():
        ctx = await bot.get_context(message)
        await coinflip(ctx)
        return

    await bot.process_commands(message)

bot.run(TOKEN)
