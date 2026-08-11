import discord
from discord import app_commands
from discord.ext import commands
from ui import SmallSeparator, ResponseUI


# UI Classes
class AvatarView(discord.ui.LayoutView):
    def __init__(self, target: discord.User | discord.Member) -> None:
        super().__init__()
        text_display = discord.ui.TextDisplay(
            content=f"**{target.display_name}'s current avatar**",
        )
        media_gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(media=target.display_avatar.url),
        )

        if target.avatar is not None:
            formats = ("png", "jpg", "webp", "gif") if target.avatar.is_animated() else ("png", "jpg", "webp")
            buttons = [
                discord.ui.Button(label=fmt, style=discord.ButtonStyle.link, url=target.avatar.with_format(fmt).url)
                for fmt in formats
            ]
        else:
            buttons = [discord.ui.Button(label="web", style=discord.ButtonStyle.link, url=target.display_avatar.url)]

        action_row = discord.ui.ActionRow(*buttons)
        container = discord.ui.Container(
            text_display,
            SmallSeparator(),
            media_gallery,
            action_row,
        )
        self.add_item(container)


class BannerView(discord.ui.LayoutView):
    def __init__(self, target: discord.User | discord.Member, fetched_user: discord.User) -> None:
        super().__init__()
        text_display = discord.ui.TextDisplay(
            content=f"**{target.display_name}'s current banner**",
        )

        banner_url = fetched_user.banner.url if fetched_user.banner else ""

        media_gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(media=banner_url),
        )

        if fetched_user.banner:
            formats = ("png", "jpg", "webp", "gif") if fetched_user.banner.is_animated() else ("png", "jpg", "webp")
            buttons = [
                discord.ui.Button(label=fmt, style=discord.ButtonStyle.link, url=fetched_user.banner.with_format(fmt).url)
                for fmt in formats
            ]
        else:
            buttons = [discord.ui.Button(label="No Banner", style=discord.ButtonStyle.link, disabled=True, url="https://discord.com")]

        action_row = discord.ui.ActionRow(*buttons)
        container = discord.ui.Container(
            text_display,
            SmallSeparator(),
            media_gallery,
            action_row,
        )
        self.add_item(container)


class InfoCog(
    commands.GroupCog,
    name="info",
    description="some info stuff",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="latency", description="bot latency")
    async def latency(self, interaction: discord.Interaction) -> None:
        latency = round(self.bot.latency * 1000)
        view = ResponseUI()
        view.text_display.content = f"**bot's latency is {latency}ms**"
        await interaction.response.send_message(view=view)

    @app_commands.command(name="avatar", description="view user avatar")
    async def avatar(self, interaction: discord.Interaction, user: discord.User | None = None) -> None:
        target = user or interaction.user
        view = AvatarView(target)
        await interaction.response.send_message(view=view)

    @app_commands.command(name="banner", description="view user banner")
    async def banner(self, interaction: discord.Interaction, user: discord.User | None = None) -> None:
        target = user or interaction.user
        fetched_user = await self.bot.fetch_user(target.id)

        if fetched_user.banner is None:
            await interaction.response.send_message(
                f"{target.display_name}'s profile must not have a banner :/",
                ephemeral=True,
            )
            return

        view = BannerView(target, fetched_user)
        await interaction.response.send_message(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InfoCog(bot))
