from globals import PRIMARY, LOG_CHANNEL
from ui import ResponseUI
import discord
from discord.ext import commands
from discord import app_commands

primary = f"#{PRIMARY}"


class PrivateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # app commands will eventually go here
    private = app_commands.Group(name="private", description="some private stuff, gated")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        log_channel = self.bot.get_channel(LOG_CHANNEL)
        if log_channel is None:
            return

        view = ResponseUI()
        view.text_display.content = f"**Melvin was just added to {guild.name}**"
        view.container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media='https://files.catbox.moe/0rgmtr.png'))
        )

        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        log_channel = self.bot.get_channel(LOG_CHANNEL)
        if log_channel is None:
            return

        view = ResponseUI()
        view.text_display.content = f"**Melvin was just removed from {guild.name}**"
        view.container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media='https://files.catbox.moe/0rgmtr.png'))
        )

        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot):
    await bot.add_cog(PrivateCog(bot))