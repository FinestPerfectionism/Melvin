import discord
from discord import app_commands
from discord.ext import commands

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
        view = ErrorUI(message="**raw ErrorUI class debug purposes**")
        await interaction.response.send_message(view=view)

    @app_commands.command(name="blue", description="send raw MiscLoggingClass class")
    async def blue(self, interaction: discord.Interaction) -> None:
        view = MiscLoggingClass()
        await interaction.response.send_message(view=view)

    @app_commands.command(name="red", description="send raw NegativeLoggingClass class")
    async def red(self, interaction: discord.Interaction) -> None:
        view = NegativeLoggingClass()
        await interaction.response.send_message(view=view)

    @app_commands.command(name="green", description="send raw PositiveLoggingClass class")
    async def green(self, interaction: discord.Interaction) -> None:
        view = PositiveLoggingClass()
        await interaction.response.send_message(view=view)

    @app_commands.command(name="ad", description="send advertisement")
    async def ad(self, interaction: discord.Interaction) -> None:
        view = AdUI()
        await interaction.response.send_message(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DebugCog(bot))
