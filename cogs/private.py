from globals import PRIMARY, LOG_CHANNEL
from ui import ResponseUI
import discord
from discord.ext import commands
from discord import app_commands
primary = f"#{PRIMARY}"


class PrivateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel = self.bot.get_channel(LOG_CHANNEL)

    # app commands will eventually go here
    private = app_commands.Group(name="private", description="some private stuff, gated")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if self.log_channel is None:
            return

        view = ResponseUI()
        view.text_display.content = f"**Melvin was just added to {guild.name}**"

        if guild.icon:
            view.container.add_item(
                discord.ui.MediaGallery(discord.MediaGalleryItem(media=guild.icon.url))
            )

        try:
            await self.log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if self.log_channel is None:
            return

        view = ResponseUI()
        view.text_display.content = f"**Melvin was just removed from {guild.name}**"

        if guild.icon:
            view.container.add_item(
                discord.ui.MediaGallery(discord.MediaGalleryItem(media='https://media.discordapp.net/attachments/1535283696242794627/1535360840809840700/melvinbanner.png?ex=6a777bb6&is=6a762a36&hm=839da661d7fc65b9918e4ee1dd4dbcf1d6a4477e1f1d3da247e06de67028a066&=&format=webp&quality=lossless'))
            )

        try:
            await self.log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot):
    await bot.add_cog(PrivateCog(bot))