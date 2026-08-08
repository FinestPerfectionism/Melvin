from globals import LOG_CHANNEL
from ui import ResponseUI
import discord
from discord.ext import commands

class PrivateCog(
    commands.GroupCog,
    name="private",
    description="some private stuff, gated",
):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild) -> None:
        log_channel = self.bot.get_channel(LOG_CHANNEL)
        if log_channel is None:
            return
        view = ResponseUI()
        view.text_display.content = (
            f"**Melvin was just added to {guild.name}**\n"
            f"Now in **{len(self.bot.guilds)}** guild(s)"
        )
        view.container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media='https://files.catbox.moe/0rgmtr.png'))
        )
        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild) -> None:
        log_channel = self.bot.get_channel(LOG_CHANNEL)
        if log_channel is None:
            return
        view = ResponseUI()
        view.text_display.content = (
            f"**Melvin was just removed from {guild.name}**\n"
            f"Now in **{len(self.bot.guilds)}** guild(s)"
        )
        view.container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media='https://files.catbox.moe/0rgmtr.png'))
        )
        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot) -> None:
    await bot.add_cog(PrivateCog(bot))