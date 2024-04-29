import discord
from discord.ext import commands

import os  # default module


class Greetings(commands.Cog):

    def __init__(
        self, bot
    ):  # this is a special method that is called when the cog is loaded
        self.bot = bot

    @discord.slash_command(
        description="Goodbye!", guild_ids=[os.getenv("GUILD_ID")]
    )  # we can also add application commands
    async def goodbye(self, ctx):
        await ctx.respond("Goodbye!")


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Greetings(bot))  # add the cog to the bot
