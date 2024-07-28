import discord
from discord.ext import commands


class QueueView(
    discord.ui.View
):  # Create a class called MyView that subclasses discord.ui.View
    def __init__(self, client, ctx, queue, start_index=0, timeout=200000):
        self.client = client
        self.ctx = ctx
        self.queue = queue
        self.start_index = start_index
        super().__init__(timeout=timeout)

    async def on_timeout(self):
        self.disable_all_items()

    @discord.ui.button(
        label="", disabled=True, style=discord.ButtonStyle.secondary, emoji="⬅️"
    )
    async def back_button_callback(self, button, interaction):
        if self.start_index > 0:
            self.start_index -= 5
            await self.client.embed_helper.refreshQueueViewEmbed(
                self.ctx, self.queue, self.start_index
            )
        self.next_back_check()

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def next_button_callback(self, button, interaction):
        print("NEXT")
        if self.start_index + 5 < len(self.queue):
            self.start_index += 5
            await self.client.embed_helper.refreshQueueViewEmbed(
                self.ctx, self.queue, self.start_index
            )

        self.next_back_check()

        await interaction.response.edit_message(view=self)

    # Checks which buttons to disable and enable based on the current index
    def next_back_check(self):
        print("Next back check at index " + str(self.start_index))
        # self.five_button.disabled = True
        if self.start_index + 5 >= len(self.queue):
            self.children[1].disabled = True
            print("Disabled forward button")
        else:
            self.children[1].disabled = False
            print("Enabled forward button")

        if self.start_index == 0:
            self.children[0].disabled = True
            print("Disabled back button")
        else:
            self.children[0].disabled = False
            print("Enabled back button")

        print("Start index: " + str(self.start_index))
