from globals import PRIMARY
import discord
from discord.ext import commands
from discord import app_commands

from ui import SmallSeparator

primary = f"#{PRIMARY}"

#UI Classes
class PingUI(discord.ui.LayoutView):
    def __init__(self, content: str):
        super().__init__()

        self.text_display = discord.ui.TextDisplay(
            content=content
        )

        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
        )

        self.add_item(container)



class AvatarView(discord.ui.LayoutView):
    def __init__(self, target: discord.User):
        super().__init__()
        text_display = discord.ui.TextDisplay(
            content=f"**{target.display_name}'s current avatar**"
        )
        media_gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(media=target.display_avatar.url)
        )

        if target.avatar is not None:
            buttons = [
                discord.ui.Button(label=fmt, style=discord.ButtonStyle.link, url=target.avatar.with_format(fmt).url)
                for fmt in ("png", "jpg", "webp")
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
    def __init__(self, target: discord.Member, fetched_user: discord.User):
        super().__init__()
        text_display = discord.ui.TextDisplay(
            content=f"**{target.display_name}'s current banner**"
        )
        media_gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(media=fetched_user.banner.url)
        )
        buttons = [
            discord.ui.Button(label=fmt, style=discord.ButtonStyle.link, url=fetched_user.banner.with_format(fmt).url)
            for fmt in ("png", "jpg", "webp")
        ]
        action_row = discord.ui.ActionRow(*buttons)
        container = discord.ui.Container(
            text_display,
            SmallSeparator(),
            media_gallery,
            action_row,
        )
        self.add_item(container)


class UtilCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # app commands will eventually go here
    util = app_commands.Group(name="util", description="some utility stuff")

    @util.command(name="latency", description="bot latency")
    async def latency(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        view = PingUI(f"bot's latency is **{latency}ms**")

        try:
            await interaction.response.send_message(view=view)
        except (discord.Forbidden, discord.HTTPException):
            pass


    @util.command(name="avatar", description="view user avatar")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        view = AvatarView(target)
        await interaction.response.send_message(view=view)

    @util.command(name="banner", description="view user banner")
    async def banner(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        fetched_user = await self.bot.fetch_user(target.id)

        if fetched_user.banner is None:
            await  interaction.response.send_message(
                f"{target.display_name}'s profile must not have a banner :/",
                ephemeral=True
            )
            return

        view = BannerView(target, fetched_user)
        await interaction.response.send_message(view=view)


async def setup(bot):
    await bot.add_cog(UtilCog(bot))
