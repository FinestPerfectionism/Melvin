import discord
import traceback
from discord import app_commands
from globals import ERROR_CHANNEL

async def report_error(bot: discord.Client, title: str, error: Exception, context: str = ""):
    channel=bot.get_channel(ERROR_CHANNEL)
    if channel is None:
        return

    tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    tb = tb[-1500:]
    content = f"# {title}\n{context}\n```py\n{tb}\n```"
