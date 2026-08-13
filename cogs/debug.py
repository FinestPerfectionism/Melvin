import discord
from discord import app_commands
from discord.ext import commands

from globals import INVITE_URL, MELVIN_BANNER, MELVIN_EMOJI
from ui import ErrorUI, ResponseUI, SmallSeparator


# AdUI
class AdUI(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.text_display = discord.ui.TextDisplay(
            content=f"# {MELVIN_EMOJI} Melvin\nYAGPDB written in python under the discord.py framework, by someone still learning python. features user and guild install commands, welcoming configuration, cv2 messages over legacy embeds, and much more. Melvin is open source, and open to contributions, so if you want to contribute, feel free. **[github](https://github.com/saltgranule/Melvin)**\n\n**currently in {len(self.bot.guilds)} guilds.**",
        )
        media_gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(media=f"{MELVIN_BANNER}"),
        )
        banner_container = discord.ui.Container(media_gallery)
        adbutton = discord.ui.Button(
            label="support server",
            style=discord.ButtonStyle.link,
            url=f"{INVITE_URL}",
        )
        addbutton = discord.ui.Button(
            label="add melvin",
            style=discord.ButtonStyle.link,
            url="https://discord.com/oauth2/authorize?client_id=1468362201197973756",
        )
        gitbutton = discord.ui.Button(
            label="github",
            style=discord.ButtonStyle.link,
            url="https://github.com/saltgranule/Melvin",
        )
        action_row = discord.ui.ActionRow(adbutton, addbutton, gitbutton)
        content_container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            action_row,
        )
        self.container = content_container
        self.add_item(banner_container)
        self.add_item(content_container)


class DebugCog(
    commands.GroupCog,
    name="debug",
    description="some debug stuff",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="think", description="send raw ResponseUI class")
    async def think(self, interaction: discord.Interaction) -> None:
        view = ResponseUI()
        await interaction.response.send_message(view=view)

    @app_commands.command(name="error", description="send raw ErrorUI class")
    async def error(self, interaction: discord.Interaction) -> None:
        view = ErrorUI(
            message=f"**something went wrong with that. please [join the support server]({INVITE_URL}) to report this issue.**",
        )
        await interaction.response.send_message(view=view)

    @app_commands.command(name="ad", description="send advertisement")
    async def ad(self, interaction: discord.Interaction) -> None:
        view = AdUI(self.bot)
        await interaction.response.send_message(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DebugCog(bot))
