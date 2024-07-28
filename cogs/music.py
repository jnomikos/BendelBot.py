import discord
from discord.ext import commands

import re
import os  # default module
import json
import asyncio

import logging
import colorlog

from src.Client import Client


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.clients = {}

        self.bot.loop.create_task(self.client_garbage_collector())

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

    # Clear out clients who are inactive to save resources
    async def client_garbage_collector(self):
        try:
            while True:
                await asyncio.sleep(1)
                logging.debug("Garbage collector heartbeat")
                for guild_id in list(self.clients):
                    if self.clients[guild_id].inactive is True:
                        self.clients.pop(guild_id)
                        logging.info(
                            f"Removed Client for guild {guild_id} due to inactivity"
                        )
        except Exception as e:
            logging.error(f"Error in client garbage collector: {e}")

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

        if self.is_youtube_playlist_url(url_or_search) == True:
            await self.clients[ctx.guild.id].addYoutubePlaylist(ctx, url_or_search)
        elif self.is_youtube_url(url_or_search) == True:
            logging.info("Adding youtube song")
            await self.clients[ctx.guild.id].addYoutubeSong(ctx, url_or_search)
        elif self.is_url(url_or_search) == False:
            logging.info("Searching for song")
            await self.search(ctx, url_or_search)
        else:
            await ctx.respond(
                "<:bendelwhat:894084854185074709> Invalid URL or search query"
            )

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
        if ctx.guild.id not in self.clients:
            await ctx.respond(
                "I have not played any songs recently and am currently not playing."
            )
            return
        await self.clients[ctx.guild.id].skip(ctx)
        await ctx.respond("Skipped the song")

    @discord.slash_command(description="Go back to the previous song")
    async def back(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return
        if ctx.guild.id not in self.clients:
            await ctx.respond(
                "I have not played any songs recently and am currently not playing."
            )
            return
        await self.clients[ctx.guild.id].back(ctx)

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

    @discord.slash_command(description="View the current queue")
    async def queue(self, ctx):
        if ctx.voice_client is None:
            await ctx.respond("I am not in a voice channel")
            return

        await self.clients[ctx.guild.id].view_queue(ctx)

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
                await ctx.respond("You are not connected to a voice channel. IDIOT!")
                raise commands.CommandError("Author not connected to a voice channel.")

    async def disconnect(self, ctx):
        await ctx.voice_client.disconnect()
        self.clients.pop(ctx.guild.id)

    def checkAddClient(self, ctx):
        if ctx.guild.id not in self.clients:
            self.addClient(ctx)

    def addClient(self, ctx):
        client = Client(ctx)
        self.clients[ctx.guild.id] = client

    def removeClient(self, ctx):
        self.clients.pop(ctx.guild.id)

    ### REGEX FUNCTIONS - FOR MATCHING URLS ###
    def is_youtube_playlist_url(self, url):
        youtube_playlist_regex = (
            r"https:\/\/www\.youtube\.com\/watch\?[^ ]*?(&|\?)list=([^&]+)"
        )
        return re.match(youtube_playlist_regex, url) is not None

    def is_youtube_url(self, url):
        youtube_regex = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(?:-nocookie)?\.com|youtu.be))(\/(?!results\?search_query)(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$"
        return re.match(youtube_regex, url) is not None

    def is_url(self, url):
        url_regex = r"^(http|https)://"
        return re.match(url_regex, url) is not None


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Music(bot))  # add the cog to the bot
