import discord
from discord import app_commands
from discord.ext import commands

from globals import INVITE_URL
from ui import (
    AdUI,
    ErrorUI,
    MiscLoggingClass,
    NegativeLoggingClass,
    PositiveLoggingClass,
    ResponseUI,
)


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
        view = ErrorUI(message=f"**something went wrong with that. please [join the support server]({INVITE_URL}) to report this issue.**")
        await interaction.response.send_message(view=view)

    @app_commands.command(name="ad", description="send advertisement")
    async def ad(self, interaction: discord.Interaction) -> None:
        view = AdUI()
        await interaction.response.send_message(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DebugCog(bot))
