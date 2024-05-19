import discord
from discord.ext import commands

import re
import os  # default module
import json
import asyncio

from src.Client import Client


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.clients = {}

    @discord.slash_command(
        description="Join the voice channel you are currently in", cog="music"
    )
    async def join(self, ctx):
        channel = ctx.author.voice.channel
        if channel is None:
            await ctx.respond("You are not in a voice channel")
            return False

        # Handle if bot is already in a voice channel
        if ctx.voice_client is not None:
            await self.disconnect(ctx)

        await channel.connect()
        # Respond that bot joined the channel by linking channel
        await ctx.respond(f"Joined {channel}")
        return True

    @discord.slash_command(description="Leave the voice channel")
    async def leave(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return
        await self.disconnect(ctx)
        await ctx.respond("Left the voice channel")

    @discord.slash_command(description="Play a song")
    async def play(self, ctx, url_or_search: str):

        await ctx.defer()

        if ctx.voice_client is None:
            if await self.join(ctx) == False:
                await ctx.respond("Failed to join channel")
                return
        self.checkAddClient(ctx)

        if self.is_youtube_url(url_or_search) == False:
            await self.search(ctx, url_or_search)
            return
        await self.clients[ctx.guild.id].addSong(ctx, url_or_search)

    async def search(self, ctx, query):
        await self.clients[ctx.guild.id].search(ctx, query)

    @discord.slash_command(description="Pause the current song")
    async def pause(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return
        await self.clients[ctx.guild.id].pause(ctx)
        await ctx.respond("Paused the song")

    @discord.slash_command(description="Resume the current song")
    async def resume(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return
        await self.clients[ctx.guild.id].resume(ctx)
        await ctx.respond("Resumed the song")

    @discord.slash_command(description="Skip the current song")
    async def skip(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return
        await self.clients[ctx.guild.id].skip(ctx)
        await ctx.respond("Skipped the song")

    @discord.slash_command(description="Go back to the previous song")
    async def back(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return
        await self.clients[ctx.guild.id].back(ctx)
        await ctx.respond("Went back to the previous song")

    @discord.slash_command(description="Stop the current song")
    async def stop(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return
        await self.clients[ctx.guild.id].stop(ctx)
        await ctx.respond("Stopped the song")

    @discord.slash_command(description="Toggle loop mode")
    async def loop(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return

        if self.clients[ctx.guild.id].loop() is True:
            await ctx.respond("Looping current song")
        else:
            await ctx.respond("Stopped looping current song")

    @discord.slash_command(description="Toggle shuffle mode")
    async def shuffle(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return

        await self.clients[ctx.guild.id].shuffle(ctx)

    @play.before_invoke
    @stop.before_invoke
    @skip.before_invoke
    @pause.before_invoke
    @resume.before_invoke
    @back.before_invoke
    @loop.before_invoke
    @shuffle.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel. IDIOT!")
                raise commands.CommandError("Author not connected to a voice channel.")

    async def disconnect(self, ctx):
        await ctx.voice_client.disconnect()
        self.clients.pop(ctx.guild.id)

    def checkAddClient(self, ctx):
        if ctx.guild.id not in self.clients:
            self.addClient(ctx)

    def addClient(self, ctx):
        client = Client()
        self.clients[ctx.guild.id] = client

    def removeClient(self, ctx):
        self.clients.pop(ctx.guild.id)

    def is_youtube_url(self, url):
        youtube_regex = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(?:-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$"
        return re.match(youtube_regex, url) is not None


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Music(bot))  # add the cog to the bot
