import discord
from discord.ext import commands
from globals import INVITE_URL
from ui import ActionUI, ErrorUI

class ModCog(
    commands.GroupCog,
    name="modcog",
    description="some mod cmds",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModCog(bot))
