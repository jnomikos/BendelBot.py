import asyncio
import cv2
import datetime
import discord
from discord.ext import tasks
import numpy
import urllib.request
import logging

from src.PlayingView import PlayingView
from src.SearchView import SearchView
from src.QueueView import QueueView


class EmbedHelper:
    def __init__(self, client):
        self.client = client

    def generateProgressBar(self, time_spent, duration, bar_length=15):
        # Calculate progress percentage
        progress = (time_spent / duration) * 15

        progress_bar = ""

        # Build progress bar string
        for i in range(15):
            if i < int(progress):
                progress_bar += "█"
            else:
                progress_bar += "▁"

        return progress_bar

    def generatePlayingEmbed(self, ctx, song_info, time_spent=0):

        logging.debug(f"Generate playing embed. Time spent: {time_spent}")

        duration = song_info.get("duration")

        if duration is None:
            duration = 1  # Default to 1 if duration is not available

        progress_bar = self.generateProgressBar(time_spent, duration)

        if self.client.paused is True:
            state = "Paused: "
        else:
            state = "Playing: "

        embed = discord.Embed(
            title=state,
            color=self.getAvgColorOfThumbnail(
                song_info["thumbnail"]
                if "thumbnail" in song_info
                else song_info["thumbnails"][0]["url"]
            ),  # Pycord provides a class with default colors you can choose from
        )

        embed.add_field(
            name=song_info["title"],
            value=song_info["channel"],
            inline=False,
        )

        embed.add_field(
            name=progress_bar,
            value=f"{self.convert_seconds(time_spent)}/{self.convert_seconds(duration)}",
            inline=False,
        )

        embed.set_thumbnail(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Logo_of_YouTube_%282015-2017%29.svg/502px-Logo_of_YouTube_%282015-2017%29.svg.png"
        )

        embed.set_image(
            url=(
                song_info["thumbnail"]
                if "thumbnail" in song_info
                else (
                    song_info["thumbnails"][0]["url"]
                    if "thumbnails" in song_info
                    else ""
                )
            )
        )

        return embed

    @tasks.loop(seconds=1)
    async def refreshPlayingEmbed(self, ctx):
        try:
            if self.client.last_playing_message is not None:
                # We fetch message like this to avoid discord server from throwing stupid 'Invalid Webhook Token' errors
                # If you were to just reply to the ctx, the ctx would eventually become invalid
                latest_message = await ctx.channel.fetch_message(
                    self.client.last_playing_message.id
                )
                await latest_message.edit(
                    content="",
                    embed=self.generatePlayingEmbed(
                        ctx, self.client.queue[0], self.client.time_spent_playing
                    ),
                    view=PlayingView(self.client, ctx),
                )

        except discord.HTTPException as e:
            if e.status == 429:
                retry_after = e.retry_after
                print(f"Rate limited. Retrying after {retry_after} seconds.")
                await asyncio.sleep(retry_after)
        except Exception as e:
            logging.error(
                f"Error editing message: {e}, Time: {datetime.datetime.now()}"
            )

    def generateQueueEmbed(self, ctx):

        embed = discord.Embed(title="Song added to queue")
        embed.set_author(name=ctx.author, icon_url=ctx.user.display_avatar.url)

        return embed

    async def generateQueueViewEmbed(self, ctx, queue, start_index=0):

        embed = discord.Embed(
            title="Queue",
            color=discord.Colour.blurple(),
        )

        if len(self.client.queue) == 0:
            embed.add_field(
                name="Queue is empty",
                value="Add some songs to the queue",
                inline=False,
            )

            return embed

        max_queue_results_per_page = 5
        # First 10 results
        for i in range(start_index, start_index + max_queue_results_per_page):
            if i >= len(queue):
                break

            song = queue[i]
            index = start_index + i
            embed.add_field(
                name=f"{index}: {song['title']}",
                value=f"Channel: {song['channel']}\n",
                inline=False,
            )
            embed.set_footer(text=f"Page {int(i/max_queue_results_per_page) + 1}")
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
            await self.client.last_search_msg.edit(
                "",
                embed=await self.generateSearchEmbed(ctx, search_results, start_index),
                view=SearchView(self.client, ctx, search_results, start_index),
            )
        except Exception as e:
            logging.error(
                f"Error editing message: {e}, Time: {datetime.datetime.now()}"
            )

    async def refreshQueueViewEmbed(self, ctx, queue, start_index=0):
        try:
            await self.client.last_queue_msg.edit(
                embed=await self.generateQueueViewEmbed(ctx, queue, start_index),
                view=self.client.queue_view,
            )
        except Exception as e:

            print("Error editing message: ", e)
            print("Time: ", datetime.datetime.now())

    def getAvgColorOfThumbnail(self, url):
        try:
            req = urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} {e.reason} for URL: {url}")
            # Return a default color or handle the error as needed
            return discord.Color.default()
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason} for URL: {url}")
            return discord.Color.default()
        arr = numpy.asarray(bytearray(req.read()), dtype=numpy.uint8)
        img = cv2.imdecode(arr, -1)  # 'Load it as it is'
        avg_color_per_row = numpy.average(img, axis=0)
        avg_color = numpy.average(avg_color_per_row, axis=0)
        avg_color = avg_color.astype(int).tolist()  # Convert numpy array to list
        return discord.Colour.from_rgb(avg_color[0], avg_color[1], avg_color[2])

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
