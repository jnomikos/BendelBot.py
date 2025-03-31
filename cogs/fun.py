import discord
from discord.ext import commands

import re
import os  # default module
import json
import asyncio

import logging
import colorlog
import subprocess

from src.Client import Client


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(
        description="Whitelist yourself on minecraft server", cog="fun"
    )
    async def whitelist_mc(self, ctx, ign: str):
        subprocess.run(["bash", "/opt/minecraft/whitelist.sh", ign])
        await ctx.respond(f"Whitelisted {ign}")


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Fun(bot))  # add the cog to the bot
