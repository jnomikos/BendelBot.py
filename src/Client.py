import yt_dlp

import asyncio
import json

import discord
from discord.ext import tasks

import logging
import random
from datetime import datetime, timedelta
from youtube_search import YoutubeSearch

from src.PlayingView import PlayingView
from src.SearchView import SearchView
from src.EmbedHelper import EmbedHelper
from src.QueueView import QueueView


class Client:
    def __init__(self, ctx):
        self.queue = []
        self.history = []
        self.paused = False
        self.last_playing_message = None
        self.last_queue_msg = None
        self.looping = False
        self.embed_helper = EmbedHelper(self)
        self.add_song_task = None
        self.voice_client = None

        self.time_spent_playing = 0
        self.playback_start_time = None
        self.queue_empty_start_time = None
        self.paused_start_time = None

        self.empty_leave_timeout_s = 60 * 10  # 10 minutes empty before leaving
        self.inactive = False

    @tasks.loop(seconds=1)
    async def heartbeat(self, ctx):
        try:
            logging.debug("Heartbeat")

            if (
                self.voice_client is not None
                and len(ctx.voice_client.channel.members) == 1
            ):
                await ctx.send(
                    "No users in channel. I am not going to play for myself. I'm leaving <:Bendel_Okay:1093427064595558470>"
                )

                self.heartbeat.stop()
            elif self.voice_client is not None and (self.voice_client.is_playing()):
                self.inactive = False
                self.queue_empty_start_time = None

                if (
                    self.paused_start_time is not None
                    and self.playback_start_time is not None
                ):
                    time_since_paused = int(
                        (datetime.now() - self.paused_start_time).total_seconds()
                    )

                    self.playback_start_time += timedelta(seconds=time_since_paused)

                    self.paused_start_time = None

                    return

                # If the bot is playing, update the time spent playing the song
                if self.playback_start_time is None:
                    self.playback_start_time = datetime.now()
                self.time_spent_playing = int(
                    (datetime.now() - self.playback_start_time).total_seconds()
                )
            elif self.voice_client is not None and self.voice_client.is_paused():
                logging.info("Client is currently paused")
            elif len(self.queue) > 0:
                logging.info(
                    "Client is not playing, but has songs in queue. Waiting for next song"
                )
                # await self.after(ctx)
            else:
                self.playback_start_time = None

                # Set start time of queue being empty if it is not already set
                if self.queue_empty_start_time is None:
                    self.queue_empty_start_time = datetime.now()

                time_spent_empty = (
                    datetime.now() - self.queue_empty_start_time
                ).total_seconds()

                # Once the bot has been empty past the timeout, disconnect
                if (
                    time_spent_empty > self.empty_leave_timeout_s
                    and self.voice_client is not None
                ):
                    self.heartbeat.stop()
        except Exception as e:
            logging.error(f"Error in heartbeat: {e}")

    @heartbeat.after_loop
    async def clean_and_leave(self):
        logging.warning("Heartbeat loop has stopped. Cleaning up and leaving")
        self.inactive = True
        self.queue = []
        self.history = []
        self.embed_helper.refreshPlayingEmbed.cancel()

        if self.voice_client is not None:
            await self.voice_client.disconnect(force=True)

    async def checkValidAction(self, ctx):
        channel = ctx.author.voice.channel
        if channel is None:
            await ctx.respond(
                "You are not in a voice channel <:Bendel_Okay:1093427064595558470>"
            )
            return False

    async def extract_and_add_song(self, ctx, url):

        ydl_opts = {
            "format": "bestaudio",
            "extract_info": True,  # Only extract information
            "extract_flat": True,  # Extract information in a flat dictionary
            "skip_download": True,  # Do not download the video
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                song_info = ydl.extract_info(url, download=False)
                if "duration" in song_info and song_info["duration"] is not None:
                    self.queue.append(song_info)
                else:
                    logging.warn(f"Video is private or restricted: {url}")
                    await ctx.respond(
                        "<:john2:655678319538470912> CRUD DETECTED! THE VIDEO IS PRIVATE OR RESTRICTED! FAILURE TO ADD!"
                    )
        except Exception as e:
            logging.error(f"Error extracting song info: {e}, Time: {datetime.now()}")
            return

    async def extract_direct_song_info(self, url, ctx):
        logging.info("Extracting song info...")
        try:
            ydl_opts = {
                "format": "bestaudio",
                "extract_info": True,  # Only extract information
                "extract_flat": False,  # Extract information in a flat dictionary
                "skip_download": True,  # Do not download the video
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            logging.error(f"DownloadError while extracting song info: {e}")
            await ctx.send(
                "<:john2:655678319538470912> YOU TRIED TO ADD CRUD! YOU FAILED! THE VIDEO DID NOT WORK!"
            )
            await self.after(ctx)
        except Exception as e:
            logging.error(f"Error extracting song info: {e}")
            await ctx.send(
                "<:john2:655678319538470912> UNEXPECTED CRUD ERROR! IMPRESSIVE! THE VIDEO DID NOT WORK! TRY ANOTHER ONE!"
            )
            await self.after(ctx)

    async def addYoutubeSong(self, ctx, url):
        # We start playing upon adding the first song
        if len(self.queue) > 0:
            await ctx.respond(
                "",
                embed=self.embed_helper.generateQueueEmbed(ctx),
            )
            self.add_song_task = asyncio.create_task(
                self.extract_and_add_song(ctx, url)
            )
        else:
            await ctx.respond(
                f"Started playing in {ctx.author.voice.channel} <a:jonah:857809307591245824>"
            )
            await self.extract_and_add_song(ctx, url)
            await self.startPlaying(ctx)

        logging.info(f"Added song to queue: {url}, {len(self.queue)} songs in queue")

    async def startPlaying(self, ctx):
        if not self.heartbeat.is_running():
            self.heartbeat.start(ctx)

        if not self.embed_helper.refreshPlayingEmbed.is_running():
            self.embed_helper.refreshPlayingEmbed.start(ctx)

        self.voice_client = ctx.voice_client
        # Display user feedback before all else, so the user knows the bot is working
        song_info = self.queue[0]
        if self.last_playing_message is not None:
            try:
                await self.last_playing_message.delete()
            except Exception as e:
                logging.error(f"Error deleting message: {e}, Time: {datetime.now()}")

        try:
            # code to play the song
            self.last_playing_message = await ctx.send(
                f"",
                embed=self.embed_helper.generatePlayingEmbed(ctx, song_info),
                view=PlayingView(self, ctx, timeout=(song_info["duration"] * 250)),
            )
        except Exception as e:
            logging.error(f"Error playing song: {e}, Time: {datetime.now()}")
            await self.handle_playback_error(ctx)
            return

        extracted_song = await self.extract_direct_song_info(self.queue[0]["url"], ctx)

        ffmpeg_options = {
            "options": "-vn",
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        }

        event_loop = asyncio.get_event_loop()

        try:
            self.playback_start_time = datetime.now()
            if self.voice_client is None:
                logging.warning("Lost voice client")
                try:
                    await ctx.send(
                        "Lost voice client. Discord probably booted us out. Exiting"
                    )

                    self.heartbeat.cancel()

                    return
                except Exception as e:
                    logging.error(f"Error sending message: {e}, Time: {datetime.now()}")

            self.voice_client.play(
                discord.FFmpegOpusAudio(extracted_song["url"], **ffmpeg_options),
                after=lambda audio: asyncio.run_coroutine_threadsafe(
                    self.after(ctx), event_loop
                ),
            )
        except Exception as e:
            logging.error(f"Error playing song: {e}, Time: {datetime.now()}")
            await self.handle_playback_error(ctx)

    async def handle_playback_error(self, ctx):
        # Notify the user and proceed to the next song
        await ctx.respond(
            "Failed to play the current song. Skipping to the next song. <:bendelwhat:894084854185074709>"
        )
        await self.after(ctx)

    async def pause(self, ctx):
        try:
            ctx.voice_client.pause()
        except Exception as e:
            await ctx.respond(
                "There was an error pausing the song. Please try again. <:bendelwhat:894084854185074709>"
            )

        self.paused_start_time = datetime.now()
        self.paused = True

    async def resume(self, ctx):
        try:
            ctx.voice_client.resume()
        except Exception as e:
            await ctx.respond(
                "There was an error resuming the song. Please try again. <:bendelwhat:894084854185074709>"
            )

        self.paused = False

    async def skip(self, ctx):
        if self.add_song_task is not None and not self.add_song_task.done():
            logging.warn(
                f"User attempted to skip before the song was added to the queue"
            )
            return

        try:
            ctx.voice_client.stop()
        except Exception as e:
            await ctx.respond(
                "There was an error skipping the song. Please try again. <:bendelwhat:894084854185074709>"
            )

    async def back(self, ctx):
        if len(self.history) == 0:
            await ctx.respond(
                "There are no songs to go back to. <:bendelwhat:894084854185074709>"
            )
            return

        # Add previous song to the front of the queue
        self.queue.insert(1, self.history[-1])

        if len(self.queue) > 1:
            # Add the song currently playing right after it, so that it is not lost
            # This is done so that the song can be skipped back to
            self.queue.insert(2, self.queue[0])

        # Remove the last song from history
        self.history.pop(-1)

        ctx.voice_client.stop()

        await ctx.respond("Went back to the previous song")

    async def stop(self, ctx):

        try:
            ctx.voice_client.stop()
        except Exception as e:
            await ctx.respond("There was an error stopping the song. Please try again.")

        self.queue = []
        self.history = []

        await self.last_playing_message.delete()
        await ctx.respond("Stopped the song. Queue has been terminated")

    async def search(self, ctx, query):
        results = YoutubeSearch(str(query), max_results=30)
        results = json.loads(results.to_json())

        filtered_results = {
            "videos": [
                video
                for video in results["videos"]
                # Livestreams show up with 0 views and 0 duration. This is a good way to filter the crud out
                if str(video.get("duration")) != "0" and str(video.get("views")) != "0"
            ]
        }

        # 5 minutes timeout
        search_embed = await self.embed_helper.generateSearchEmbed(
            ctx, filtered_results
        )

        search_view = (
            SearchView(self, ctx, filtered_results)
            if len(filtered_results["videos"]) > 0
            else None
        )

        self.last_search_msg = await ctx.respond(
            "Search Results:", embed=search_embed, view=search_view
        )

    async def addYoutubePlaylist(self, ctx, url):
        ydl_opts = {
            "format": "bestaudio",
            "extract_info": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(url, download=False)

        start_len = len(self.queue)

        list_of_required_keys = ["duration"]

        invalid_entries = 0

        def is_valid_entry(entry):
            # Check if all required keys are present and have valid values
            return all(key in entry and entry[key] for key in list_of_required_keys)

        if "entries" in playlist_info:
            for entry in playlist_info["entries"]:
                if is_valid_entry(entry):
                    self.queue.append(entry)
                else:
                    invalid_entries += 1
        else:
            logging.info(f"No entries found in playlist: {url}")
            await ctx.respond(
                "No songs found in playlist. Weird playlist <:ben_dell:894078439567544351>"
            )
            return

        if len(self.queue) == start_len:
            await ctx.respond(
                "<:john2:655678319538470912> Your playlist is CRUD. Dumbass! All songs in the playlist are private or restricted. <a:aware:992290356462882917>"
            )
            return

        if start_len == 0:
            await self.startPlaying(ctx)

        if invalid_entries > 0:
            await ctx.respond(
                f"<:bendelwhat:894084854185074709> Successfully added `{len(self.queue) - start_len}` songs to the queue... However... `{invalid_entries}` songs... were... *gasp* CRUD! *wheeze* This means they were likely private or restricted. There are `{len(self.queue)}` songs in the queue now."
            )
        else:
            await ctx.respond(
                f"<:Bendel_Okay:1093427064595558470> Successfully added `{len(self.queue) - start_len}` songs to the queue. Queue now has `{len(self.queue)}` songs. <a:jonah_dance:1264319272918843425>"
            )

    def loop(self):
        self.looping = not self.looping
        return self.looping

    async def shuffle(self, ctx):
        rest = self.queue[1:]
        random.shuffle(rest)
        self.queue = [self.queue[0]] + rest

        await ctx.respond("Shuffled the queue <:bran:655678331643232259>")

    async def view_queue(self, ctx):
        queue_embed = await self.embed_helper.generateQueueViewEmbed(self, self.queue)

        self.queue_view = (
            QueueView(self, ctx, self.queue) if len(self.queue) > 0 else None
        )

        self.last_queue_msg = await ctx.respond(
            f"{len(self.queue)} song(s) in queue <a:jonah_dance:1264319272918843425>",
            embed=queue_embed,
            view=self.queue_view,
        )

    async def after(self, ctx):
        if self.looping is not True:
            # Add the song to history -- So we can skip back to it
            self.history.append(self.queue[0])
            print(self.history[0]["title"])
            # Remove song from Queue
            self.queue.pop(0)

        if len(self.queue) > 0:
            logging.info(f"Playing next song in queue: {self.queue[0]['title']}")
            await self.startPlaying(ctx)
            self.embed_helper.refreshPlayingEmbed.restart(ctx)
        else:
            logging.info("Queue is empty")
            try:
                await self.last_playing_message.delete()
            except Exception as e:
                logging.error(f"Error deleting message: {e}, Time: {datetime.now()}")
            self.embed_helper.refreshPlayingEmbed.cancel()
