import discord
from discord.ext import commands
import os  # default module
from dotenv import load_dotenv


load_dotenv()  # load all the variables from the env file


bot = discord.Bot()
cogs_list = [
    "greetings",
    "music",
]

for cog in cogs_list:
    bot.load_extension(f"cogs.{cog}")


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(
    name="hello", description="Say hello to the bot", guild_ids=[os.getenv("GUILD_ID")]
)
async def hello(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="My Amazing Embed",
        description="Embeds are super easy, barely an inconvenience.",
        color=discord.Colour.blurple(),  # Pycord provides a class with default colors you can choose from
    )
    embed.add_field(
        name="A Normal Field",
        value="A really nice field with some information. **The description as well as the fields support markdown!**",
    )

    embed.add_field(name="Inline Field 1", value="Inline Field 1", inline=True)
    embed.add_field(name="Inline Field 2", value="Inline Field 2", inline=True)
    embed.add_field(name="Inline Field 3", value="Inline Field 3", inline=True)

    embed.set_footer(text="Footer! No markdown here.")  # footers can have icons too
    embed.set_author(
        name="Pycord Team", icon_url="https://example.com/link-to-my-image.png"
    )
    embed.set_thumbnail(url="https://example.com/link-to-my-thumbnail.png")
    embed.set_image(url="https://example.com/link-to-my-banner.png")

    await ctx.respond(
        "Hello! Here's a cool embed.", embed=embed
    )  # Send the embed with some text


@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.mention}! Enjoy your stay here.")


bot.run(os.getenv("DISCORD_TOKEN"))  # run the bot with the token
