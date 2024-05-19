import yt_dlp

import asyncio
import json

import discord
from discord.ext import commands

import cv2
import numpy
import random
import urllib.request
import datetime
from youtube_search import YoutubeSearch

from src.PlayingView import PlayingView
from src.SearchView import SearchView


class Client:
    def __init__(self):
        self.queue = []
        self.history = []
        self.paused = False
        self.last_playing_message = None
        self.looping = False

    async def checkValidAction(self, ctx):
        channel = ctx.author.voice.channel
        if channel is None:
            await ctx.respond("You are not in a voice channel")
            return False

    async def extract_and_add_song(self, url):

        ydl_opts = {
            "format": "bestaudio",
            "extract_info": True,  # Only extract information
            "skip_download": True,  # Do not download the video
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            song_info = ydl.extract_info(url, download=False)
            self.queue.append(song_info)

    async def addSong(self, ctx, url):
        print(str(len(self.queue)) + " songs in queue")
        # We start playing upon adding the first song
        if len(self.queue) > 0:
            await ctx.respond(
                "",
                embed=self.generateQueueEmbed(ctx),
            )
            asyncio.create_task(self.extract_and_add_song(url))
        else:
            await self.extract_and_add_song(url)
            await self.startPlaying(ctx)

    async def startPlaying(self, ctx):
        print("Start playing")

        ffmpeg_options = {
            "options": "-vn",
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        }

        song_info = self.queue[0]
        event_loop = asyncio.get_event_loop()

        try:
            ctx.voice_client.play(
                discord.FFmpegPCMAudio(song_info["url"], **ffmpeg_options),
                after=lambda audio: asyncio.run_coroutine_threadsafe(
                    self.after(ctx), event_loop
                ),
            )
        except Exception as e:
            await ctx.respond("There was an error playing this song. Please try again.")
            print("Error playing song: ", e)
            return

        if self.last_playing_message is not None:
            try:
                await self.last_playing_message.delete()
            except Exception as e:
                print("Error deleting message: ", e)
                print("Time: ", datetime.datetime.now())

        # code to play the song
        self.last_playing_message = await ctx.respond(
            f"Playing {song_info['title']}",
            embed=self.generatePlayingEmbed(ctx, song_info),
            view=PlayingView(self, ctx, timeout=(song_info["duration"] * 2)),
        )

    async def pause(self, ctx):
        try:
            ctx.voice_client.pause()
        except Exception as e:
            await ctx.respond("There was an error pausing the song. Please try again.")

        self.paused = True

        await self.refreshPlayingEmbed(ctx)

    async def resume(self, ctx):
        try:
            ctx.voice_client.resume()
        except Exception as e:
            await ctx.respond("There was an error resuming the song. Please try again.")

        self.paused = False

        await self.refreshPlayingEmbed(ctx)

    async def skip(self, ctx):
        try:
            ctx.voice_client.stop()
        except Exception as e:
            await ctx.respond("There was an error skipping the song. Please try again.")

    async def back(self, ctx):
        if len(self.history) == 0:
            await ctx.respond("There are no songs to go back to.")
            return

        # Add the current song to the queue
        self.queue.insert(0, self.history[-1])

        # Remove the last song from history
        self.history.pop(-1)

        # Start playing the song
        await self.startPlaying(ctx)

    async def stop(self, ctx):

        try:
            ctx.voice_client.stop()
        except Exception as e:
            await ctx.respond("There was an error stopping the song. Please try again.")

        self.queue = []
        self.history = []

        channel = ctx.author.voice.channel

        await self.last_playing_message.delete()
        await ctx.respond("Stopped the song, disconnected from voice channel.")
        await ctx.voice_client.disconnect(force=True)

    async def search(self, ctx, query):
        results = YoutubeSearch(str(query), max_results=30)
        results = json.loads(results.to_json())

        # 5 minutes timeout
        search_embed = await self.generateSearchEmbed(ctx, results)

        search_view = (
            SearchView(self, ctx, results) if len(results["videos"]) > 0 else None
        )

        self.last_search_msg = await ctx.respond(
            "Search Results:", embed=search_embed, view=search_view
        )

    def loop(self):
        self.looping = not self.looping
        return self.looping

    async def shuffle(self, ctx):
        rest = self.queue[1:]
        random.shuffle(rest)
        self.queue = [self.queue[0]] + rest

        await ctx.respond("Shuffled the queue")

    def generatePlayingEmbed(self, ctx, song_info):

        if self.paused is True:
            state = "Paused: "
        else:
            state = "Playing: "

        embed = discord.Embed(
            title=state,
            color=self.getAvgColorOfThumbnail(
                song_info["thumbnail"]
            ),  # Pycord provides a class with default colors you can choose from
        )

        embed.add_field(
            name=song_info["title"],
            value=song_info["channel"],
            inline=False,
        )

        embed.add_field(
            name=f"[ 00:00:00/{self.convert_seconds(song_info['duration'])} ]",
            value="\u200B",
            inline=False,
        )

        embed.set_thumbnail(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Logo_of_YouTube_%282015-2017%29.svg/502px-Logo_of_YouTube_%282015-2017%29.svg.png"
        )
        embed.set_image(url=song_info["thumbnail"])

        return embed

    async def refreshPlayingEmbed(self, ctx):
        try:
            await self.last_playing_message.edit(
                "",
                embed=self.generatePlayingEmbed(ctx, self.queue[0]),
                view=PlayingView(self, ctx),
            )
        except Exception as e:
            print("Error editing message: ", e)
            print("Time: ", datetime.datetime.now())

    def generateQueueEmbed(self, ctx):

        embed = discord.Embed(title="Song added to queue")
        embed.set_author(name=ctx.author, icon_url=ctx.user.display_avatar.url)

        return embed

    async def generateSearchEmbed(self, ctx, search_results, start_index=0):

        embed = discord.Embed(
            title="Search Results: ",
            color=discord.Colour.blurple(),
        )

        if len(search_results["videos"]) == 0:
            embed.add_field(
                name="WHAT THE HELL??? No results found 😭😭😭😭😭😭😭😭😭",
                value="Please try searching for something that exists",
                inline=False,
            )

            embed.set_image(url="https://cdn.imgpile.com/f/U2Lhgk.png")

            return embed

        max_search_results_per_page = 5
        # First 10 results
        for i in range(start_index, start_index + max_search_results_per_page):
            if i >= len(search_results["videos"]):
                break

            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

            video = search_results["videos"][i]
            embed.add_field(
                name=f"{emojis[i%max_search_results_per_page]}  {video['title']}",
                value=f"Channel: {video['channel']}\nDuration: {video['duration']}\nViews: {video['views']}\nPublished: {video['publish_time']}",
                inline=False,
            )
            embed.set_footer(text=f"Page {int(i/max_search_results_per_page) + 1}")
        return embed

    async def refreshSearchEmbed(self, ctx, search_results, start_index=0):
        try:
            await self.last_search_msg.edit(
                "",
                embed=await self.generateSearchEmbed(ctx, search_results, start_index),
                view=SearchView(self, ctx, search_results, start_index),
            )
        except Exception as e:
            print("Error editing message: ", e)
            print("Time: ", datetime.datetime.now())

    def getAvgColorOfThumbnail(self, url):
        req = urllib.request.urlopen(url)
        arr = numpy.asarray(bytearray(req.read()), dtype=numpy.uint8)
        img = cv2.imdecode(arr, -1)  # 'Load it as it is'
        avg_color_per_row = numpy.average(img, axis=0)
        avg_color = numpy.average(avg_color_per_row, axis=0)
        print("Average color: ", avg_color)
        avg_color = avg_color.astype(int).tolist()  # Convert numpy array to list
        return discord.Colour.from_rgb(avg_color[0], avg_color[1], avg_color[2])

    async def after(self, ctx):

        if self.looping is True:  # Loop the song
            self.queue.insert(1, self.queue[0])

        # Add the song to history -- So we can skip back to it
        self.history.append(self.queue[0])
        # Remove song from Queue
        self.queue.pop(0)
        if len(self.queue) > 0:
            print("Playing next song")
            await self.startPlaying(ctx)
        else:
            print("Queue is empty")
            try:
                await self.last_playing_message.delete()
                if ctx.voice_client is not None:
                    await ctx.voice_client.disconnect(force=True)
            except Exception as e:
                print("Error deleting message: ", e)
                print("Time: ", datetime.datetime.now())

    def convert_seconds(self, seconds):
        # Create a timedelta object representing the duration
        duration = datetime.timedelta(seconds=seconds)

        # Convert timedelta to a string in HH:MM:SS format
        duration_str = str(duration)

        # If the duration is less than a day, remove the days part
        if duration.days > 0:
            duration_str = str(duration - datetime.timedelta(days=duration.days))

        # Return the formatted string
        return duration_str
