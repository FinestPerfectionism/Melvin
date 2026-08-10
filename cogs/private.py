import discord
from discord import app_commands
from discord.ext import commands

from globals import INVITE_URL, LOG_CHANNEL, MELVIN_CHECK_EMOJI, MELVIN_WARN_EMOJI
from ui import ResponseUI


class PrivateCog(
    commands.GroupCog,
    name="private",
    description="some prv stuff",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        log_channel = self.bot.get_channel(LOG_CHANNEL)
        if log_channel is None:
            return
        view = ResponseUI()
        view.text_display.content = (
            f"**Melvin was just added to {guild.name}**\n"
            f"Now in **{len(self.bot.guilds)}** guild(s)"
        )
        view.container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media="https://files.catbox.moe/7e6nw8.png")),
        )
        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        log_channel = self.bot.get_channel(LOG_CHANNEL)
        if log_channel is None:
            return
        view = ResponseUI()
        view.text_display.content = (
            f"**Melvin was just removed from {guild.name}**\n"
            f"Now in **{len(self.bot.guilds)}** guild(s)"
        )
        view.container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media="https://files.catbox.moe/7e6nw8.png")),
        )
        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @app_commands.command(name="sync", description="sync command tree")
    async def sync(self, interaction: discord.Interaction) -> None:
        if not await self.bot.is_owner(interaction.user):
            view = ResponseUI()
            view.text_display.content = f"{MELVIN_WARN_EMOJI} **This command is gated, read our documentation in our [support server.]({INVITE_URL})**"
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        view = ResponseUI()
        await interaction.response.send_message(view=view, ephemeral=True)

        try:
            synced = await self.bot.tree.sync()
        except discord.HTTPException as e:
            view.text_display.content = f"**sync failed, {e}**"
            await interaction.edit_original_response(view=view)
            return

        view.text_display.content = f"**{MELVIN_CHECK_EMOJI} synced {len(synced)} command(s)**"
        await interaction.edit_original_response(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PrivateCog(bot))
