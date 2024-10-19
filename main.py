import discord
from discord.ext import commands
import os  # default module
from dotenv import load_dotenv
import logging
import colorlog


load_dotenv()  # load all the variables from the env file


### --- Setup logger with colorlog  --- ###
handler = colorlog.StreamHandler()

# Create a formatter
formatter = colorlog.ColoredFormatter(
    "%(log_color)s[%(levelname)s] [%(name)s] %(message)s%(reset)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
    secondary_log_colors={},
    style="%",
)

handler.setFormatter(formatter)

logging.basicConfig(
    format="[%(levelname)s] [%(name)s] [%(message)s]",
    level=logging.INFO,
    handlers=[handler],
)

### ----------------------------------- ###

bot = discord.Bot()
cogs_list = ["music"]

for cog in cogs_list:
    bot.load_extension(f"cogs.{cog}")


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    await bot.change_presence(
        activity=discord.Game(name=f"in {len(bot.guilds)} servers. /play")
    )


@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.mention}! Enjoy your stay here.")


bot.run(os.getenv("DISCORD_TOKEN"))  # run the bot with the token
