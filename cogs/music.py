import discord
from discord.ext import commands
import yt_dlp

import os  # default module
import json
import asyncio

from src.Client import Client


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.clients = {}

    @discord.slash_command(
        description="Join the voice channel you are currently in",
        guild_ids=[os.getenv("GUILD_ID")],
    )
    async def join(self, ctx):
        channel = ctx.author.voice.channel
        if channel is None:
            await ctx.respond("You are not in a voice channel")
            return False
        await channel.connect()
        # Respond that bot joined the channel by linking channel
        await ctx.respond(f"Joined {channel}")
        return True

    @discord.slash_command(
        description="Leave the voice channel", guild_ids=[os.getenv("GUILD_ID")]
    )
    async def leave(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return
        await ctx.voice_client.disconnect()
        await ctx.respond("Left the voice channel")

    @discord.slash_command(description="Play a song", guild_ids=[os.getenv("GUILD_ID")])
    async def play(self, ctx, url: str):
        if ctx.voice_client is None:
            if await self.join(ctx) == False:
                await ctx.respond("Join a voice channel before playing a song")
                return
        self.checkAddClient(ctx)
        await self.clients[ctx.guild.id].addSong(ctx, url)

    def checkAddClient(self, ctx):
        if ctx.guild.id not in self.clients:
            self.addClient(ctx)

    def addClient(self, ctx):
        client = Client()
        self.clients[ctx.guild.id] = client

    def removeClient(self, ctx):
        self.clients.pop(ctx.guild.id)


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Music(bot))  # add the cog to the bot
