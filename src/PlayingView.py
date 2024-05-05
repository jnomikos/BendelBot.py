import discord
from discord.ext import commands


class PlayingView(
    discord.ui.View
):  # Create a class called MyView that subclasses discord.ui.View
    def __init__(self, client, ctx):
        self.client = client
        self.ctx = ctx
        super().__init__()

        if self.client.looping is True:
            self.children[4].style = discord.ButtonStyle.success
        else:
            self.children[4].style = discord.ButtonStyle.secondary
        # discord.ButtonStyle.secondary

    @discord.ui.button(
        label="", style=discord.ButtonStyle.secondary, disabled=True, emoji="⏮"
    )
    async def back_button_callback(self, button, interaction):
        if len(self.client.history) == 0:
            button.disabled = True
            await interaction.response.edit_message(view=self)
        else:
            button.disabled = False
            await self.client.back(self.ctx)
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="⏯")
    async def pause_toggle_button_callback(self, button, interaction):
        if self.client.paused is True:  # Resume
            button.style = discord.ButtonStyle.secondary
            await self.client.resume(self.ctx)
            await interaction.response.edit_message(view=self)
        else:  # Pause
            button.style = discord.ButtonStyle.success
            await self.client.pause(self.ctx)
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="⏭")
    async def skip_button_callback(self, button, interaction):
        await self.client.skip(self.ctx)
        if len(self.client.queue) > 0:
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="⏹")
    async def stop_button_callback(self, button, interaction):
        await self.client.stop(self.ctx)

    def check_back_forward(self):
        if len(self.client.history) == 0:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="🔁")
    async def loop_button_callback(self, button, interaction):
        self.client.loop()

        if self.client.looping is True:
            button.style = discord.ButtonStyle.success
        else:
            button.style = discord.ButtonStyle.secondary

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="🔀")
    async def shuffle_button_callback(self, button, interaction):
        await self.client.shuffle(self.ctx)
        await interaction.response.edit_message(view=self)
