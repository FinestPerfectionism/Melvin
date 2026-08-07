from globals import PRIMARY, SECONDARY, TERTIARY

from ui import ErrorUI, ResponseUI, AdUI, NegativeLoggingClass, PositiveLoggingClass, MiscLoggingClass
import discord
from discord.ext import commands
from discord import app_commands

#globals (will likely duplicate)
primary = f"{PRIMARY}"
secondary = f"{SECONDARY}" #green
tertiary = f"{TERTIARY}" #red
#UI Classes


class DebugCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # app commands will eventually go here
    debug = app_commands.Group(name="debug", description="some debug stuff")

    @debug.command(name="think", description="send raw ResponseUI class")
    async def think(self, interaction: discord.Interaction):
        view = ResponseUI()
        await interaction.response.send_message(view=view)

    @debug.command(name="error", description="send raw ErrorUI class")
    async def think(self, interaction: discord.Interaction):
        view = ErrorUI(message='**raw ErrorUI class debug purposes**')
        await interaction.response.send_message(view=view)

    @debug.command(name="blue", description="send raw MiscLoggingClass class")
    async def think(self, interaction: discord.Interaction):
        view = MiscLoggingClass()
        await interaction.response.send_message(view=view)

    @debug.command(name="red", description="send raw NegativeLoggingClass class")
    async def think(self, interaction: discord.Interaction):
        view = NegativeLoggingClass()
        await interaction.response.send_message(view=view)

    @debug.command(name="green", description="send raw PositiveLoggingClass class")
    async def think(self, interaction: discord.Interaction):
        view = PositiveLoggingClass()
        await interaction.response.send_message(view=view)

    @debug.command(name="ad", description="send advertisement")
    async def think(self, interaction: discord.Interaction):
        view = AdUI()
        await interaction.response.send_message(view=view)



async def setup(bot):
    await bot.add_cog(DebugCog(bot))