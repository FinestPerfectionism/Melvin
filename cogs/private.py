import discord
from discord import app_commands
from discord.ext import commands

from globals import (
    INVITE_URL,
    LOG_CHANNEL,
    MELVIN_BANNER,
    MELVIN_CHECK_EMOJI,
    MELVIN_WARN_EMOJI,
    SECONDARY,
)
from ui import ErrorUI, ResponseUI


class PrivateCog(
    commands.GroupCog,
    name="private",
    description="Private administrative and developer utilities.",
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
            f"**Melvin was just added to {guild.name}.**\n"
            f"Now in **{len(self.bot.guilds)}** guild(s)."
        )
        view.container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{MELVIN_BANNER}")),
        )
        try:
            await log_channel.send(
                view=view,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        log_channel = self.bot.get_channel(LOG_CHANNEL)
        if log_channel is None:
            return
        view = ResponseUI()
        view.text_display.content = f"**Melvin was just removed from {guild.name}.**\n Now in **{len(self.bot.guilds)}** guild(s)."
        view.container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media=f"{MELVIN_BANNER}")),
        )
        try:
            await log_channel.send(
                view=view,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

    @app_commands.command(name="sync", description="Sync the application command tree.")
    async def sync(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        if not await self.bot.is_owner(interaction.user):
            view = ResponseUI()
            view.text_display.content = f"{MELVIN_WARN_EMOJI} **This command is gated. Please read our documentation in our [support server]({INVITE_URL}).**"
            await interaction.followup.send(view=view, ephemeral=True)
            return

        try:
            synced = await self.bot.tree.sync()
        except discord.HTTPException as e:
            view = ErrorUI(message=f"**{e}**")
            await interaction.followup.send(view=view, ephemeral=True)
            return

        view = ResponseUI()
        view.text_display.content = (
            f"**{MELVIN_CHECK_EMOJI} Synced {len(synced)} command(s).**"
        )
        view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(view=view, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PrivateCog(bot))
