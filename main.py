import discord
from discord.ext import commands
import os  # default module
from dotenv import load_dotenv


load_dotenv()  # load all the variables from the env file


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
