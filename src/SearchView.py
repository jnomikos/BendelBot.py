import discord
from discord.ext import commands


class SearchView(
    discord.ui.View
):  # Create a class called MyView that subclasses discord.ui.View
    def __init__(self, client, ctx, search_results, start_index=0):
        self.client = client
        self.ctx = ctx
        self.search_results = search_results
        self.start_index = start_index
        super().__init__()

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="1️⃣")
    async def one_button_callback(self, button, interaction):
        video = self.search_results["videos"][self.start_index]

        await self.client.addSong(
            self.ctx, "https://www.youtube.com" + video["url_suffix"]
        )

        self.disable_all_items()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="2️⃣")
    async def two_button_callback(self, button, interaction):
        video = self.search_results["videos"][self.start_index + 1]

        await self.client.addSong(
            self.ctx, "https://www.youtube.com" + video["url_suffix"]
        )

        self.disable_all_items()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="3️⃣")
    async def three_button_callback(self, button, interaction):
        video = self.search_results["videos"][self.start_index + 2]

        await self.client.addSong(
            self.ctx, "https://www.youtube.com" + video["url_suffix"]
        )

        self.disable_all_items()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="4️⃣")
    async def four_button_callback(self, button, interaction):
        video = self.search_results["videos"][self.start_index + 3]

        await self.client.addSong(
            self.ctx, "https://www.youtube.com" + video["url_suffix"]
        )

        self.disable_all_items()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="5️⃣")
    async def five_button_callback(self, button, interaction):
        video = self.search_results["videos"][self.start_index + 4]

        await self.client.addSong(
            self.ctx, "https://www.youtube.com" + video["url_suffix"]
        )

        self.disable_all_items()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        label="", disabled=True, style=discord.ButtonStyle.secondary, emoji="⬅️"
    )
    async def back_button_callback(self, button, interaction):
        if self.start_index > 0:
            self.start_index -= 5
            await self.client.refreshSearchEmbed(
                self.ctx, self.search_results, self.start_index
            )
        self.next_back_check()
        self.song_available_check()

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def next_button_callback(self, button, interaction):
        if self.start_index + 5 < len(self.search_results["videos"]):
            self.start_index += 5
            await self.client.refreshSearchEmbed(
                self.ctx, self.search_results, self.start_index
            )

        self.next_back_check()
        self.song_available_check()

        await interaction.response.edit_message(view=self)

    # Checks which buttons to disable and enable based on the current index
    def next_back_check(self):
        print("Next back check at index " + str(self.start_index))
        # self.five_button.disabled = True
        if self.start_index + 5 >= len(self.search_results["videos"]):
            self.children[6].disabled = True
            print("Disabled forward button")
        else:
            self.children[6].disabled = False
            print("Enabled forward button")

        if self.start_index == 0:
            self.children[5].disabled = True
            print("Disabled back button")
        else:
            self.children[5].disabled = False
            print("Enabled back button")

        print("Start index: " + str(self.start_index))

    def song_available_check(self):
        # Check if next 5 songs are available
        num_songs_available = len(self.search_results["videos"]) - self.start_index

        for i in range(5):
            if i >= num_songs_available:
                self.children[i].disabled = True
            else:
                self.children[i].disabled = False
