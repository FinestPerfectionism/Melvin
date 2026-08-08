import discord
from discord.ext import commands

from globals import MELVIN_EMOJI, PRIMARY, SECONDARY, TERTIARY

primary = f"{PRIMARY}"
secondary = f"{SECONDARY}"  # green
tertiary = f"{TERTIARY}"  # red
message = "**raw ErrorUI class, debug purposes**"


# HelpView Funcs to grasp command group details
def get_cog_commands(cog: commands.Cog) -> list:
    group = cog.__cog_app_commands_group__
    if group is not None:
        return group.commands
    return cog.get_app_commands()


def flatten_commands(cmd) -> list:
    if isinstance(cmd, discord.app_commands.Group):
        result = []
        for sub in cmd.commands:
            result.extend(flatten_commands(sub))
        return result
    return [cmd]


def help_page(cog: commands.Cog) -> str:
    lines = [f"# {MELVIN_EMOJI} {cog.__cog_group_name__} cmds"]
    if cog.__cog_group_description__ and cog.__cog_group_description__ != "…":
        lines.append(f"-# **{cog.__cog_group_description__}**")

    for top_level_cmd in get_cog_commands(cog):
        for cmd in flatten_commands(top_level_cmd):
            lines.append(f"**\n/{cmd.qualified_name}**\n-# **{cmd.description}**")

    return "\n".join(lines)


class HelpView(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.cogs = [c for c in bot.cogs.values() if get_cog_commands(c)]
        print(f"help view found {len(self.cogs)} cogs: {[c.__cog_group_name__ for c in self.cogs]}")
        self.page = 0

        banner_gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(media="https://files.catbox.moe/3dwyry.png"),
        )
        banner_container = discord.ui.Container(banner_gallery)

        self.text_display = discord.ui.TextDisplay(content=help_page(self.cogs[0]))
        separator = discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small)

        self.prev_button = discord.ui.Button(label="prev", style=discord.ButtonStyle.secondary)
        self.next_button = discord.ui.Button(label="next", style=discord.ButtonStyle.secondary)
        self.prev_button.callback = self.on_prev
        self.next_button.callback = self.on_next
        self._update_button_states()

        nav_row = discord.ui.ActionRow(self.prev_button, self.next_button)
        content_container = discord.ui.Container(self.text_display, separator, nav_row)

        self.add_item(banner_container)
        self.add_item(content_container)

    def _update_button_states(self) -> None:
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = self.page == len(self.cogs) - 1

    async def on_prev(self, interaction: discord.Interaction) -> None:
        self.page -= 1
        self._update_button_states()
        self.text_display.content = help_page(self.cogs[self.page])
        await interaction.response.edit_message(view=self)

    async def on_next(self, interaction: discord.Interaction) -> None:
        self.page += 1
        self._update_button_states()
        self.text_display.content = help_page(self.cogs[self.page])
        await interaction.response.edit_message(view=self)


class ThinkingText(discord.ui.TextDisplay):
    def __init__(self) -> None:
        super().__init__(
            content=f"{MELVIN_EMOJI} **Thinking...**",
        )


class SmallSeparator(discord.ui.Separator):
    def __init__(self) -> None:
        super().__init__(
            visible=True,
            spacing=discord.SeparatorSpacing.small,
        )


class LargeSeparator(discord.ui.Separator):
    def __init__(self) -> None:
        super().__init__(
            visible=True,
            spacing=discord.SeparatorSpacing.large,
        )


# ErrorUI
class ErrorUI(discord.ui.LayoutView):
    def __init__(self, message: str) -> None:
        super().__init__()

        text_display = discord.ui.TextDisplay(
            content=f"# error\n\n{message}",
        )

        container = discord.ui.Container(
            text_display,
            SmallSeparator(),
            accent_color=discord.Color.red(),
        )

        self.container = container
        self.add_item(container)


# ResponseUI
class ResponseUI(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__()
        self.text_display = ThinkingText()

        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
        )
        self.container = container
        self.add_item(container)


# AdUI
class AdUI(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__()
        self.text_display = discord.ui.TextDisplay(
            content=f"# {MELVIN_EMOJI} Melvin\nmelvin is an app written using the **discord.py** framework. It features various **user and guild commands**, making it greatly useful as both a personal and server app. It's currently in an **open beta state**, with core moderation commands, and cogs complete with **user utilities**, **speaking utilities**, **encoding and decoding**, and so much more!\n\nMelvin is new to the discord bots realm, and support is **greatly appreciated**! Please feel free to check it out and/or **[contribute](https://github.com/saltgranule/Melvin)!**",
        )

        media_gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(media="https://files.catbox.moe/7e6nw8.png"),
        )
        banner_container = discord.ui.Container(media_gallery)

        adbutton = discord.ui.Button(
            label="support server",
            style=discord.ButtonStyle.link,
            url="https://discord.gg/XejfDTA6QK",
        )
        addbutton = discord.ui.Button(
            label="add melvin",
            style=discord.ButtonStyle.link,
            url="https://discord.com/oauth2/authorize?client_id=1468362201197973756",
        )
        gitbutton = discord.ui.Button(
            label="github",
            style=discord.ButtonStyle.link,
            url="https://github.com/saltgranule/Melvin",
        )
        action_row = discord.ui.ActionRow(adbutton, addbutton, gitbutton)

        content_container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            action_row,
        )
        self.container = content_container

        self.add_item(banner_container)
        self.add_item(content_container)


# ActionUI
class ActionUI(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__()

        self.text_display = ThinkingText()

        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            accent_color=discord.Color.from_str(primary),
        )

        self.container = container
        self.add_item(container)

    def update_text(self, new_content: str) -> None:
        self.text_display.content = new_content


# LoggingClassUI
class MiscLoggingClass(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__()

        self.text_display = ThinkingText()

        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            accent_color=discord.Color.from_str(primary),
        )

        self.container = container
        self.add_item(container)


class NegativeLoggingClass(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__()

        self.text_display = ThinkingText()

        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            accent_color=discord.Color.from_str(tertiary),
        )

        self.container = container
        self.add_item(container)


class PositiveLoggingClass(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__()

        self.text_display = ThinkingText()

        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            accent_color=discord.Color.from_str(secondary),
        )

        self.container = container
        self.add_item(container)
