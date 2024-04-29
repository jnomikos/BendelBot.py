import yt_dlp

import os  # default module
import json
import asyncio

import discord
from discord.ext import commands


class Client:
    def __init__(self):
        self.queue = []

    async def addSongToQueue(self, url):
        ydl_opts = {
            "format": "bestaudio",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            song_info = ydl.extract_info(url, download=False)
            self.queue.append(song_info)

    async def addSong(self, ctx, url):
        ydl_opts = {
            "format": "bestaudio",
            "extract_info": True,  # Only extract information
            "skip_download": True,  # Do not download the video
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            song_info = ydl.extract_info(url, download=False)
            self.queue.append(song_info)

        # We start playing upon adding the first song
        if len(self.queue) == 1:
            await self.startPlaying(ctx)
        else:
            await ctx.respond(f"Added {song_info['title']} to the queue")

    async def startPlaying(self, ctx):
        ffmpeg_options = {"options": "-vn"}

        song_info = self.queue[0]
        event_loop = asyncio.get_event_loop()
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(song_info["url"], **ffmpeg_options),
            after=lambda audio: asyncio.run_coroutine_threadsafe(
                self.after(ctx), event_loop
            ),
        )

        # code to play the song
        await ctx.respond(f"Playing {song_info['title']}")

    async def after(self, ctx):
        self.queue.pop(0)
        if len(self.queue) > 0:
            await self.startPlaying(ctx)
