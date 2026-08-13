import discord
from discord.ext import commands

from globals import (
    INVITE_URL,
    MELVIN_CROSS_EMOJI,
    MELVIN_EMOJI,
    PRIMARY,
    SECONDARY,
    TERTIARY,
)

primary = f"{PRIMARY}"
secondary = f"{SECONDARY}"  # green
tertiary = f"{TERTIARY}"  # red
message = f"**something went wrong with that. please [join the support server]({INVITE_URL}) to report this issue.**"


# HelpView Funcs to grasp command group details
def get_cog_commands(cog: commands.Cog) -> list:
    group = cog.__cog_app_commands_group__
    if group is not None:
        return group.commands
    return cog.get_app_commands()


def flatten_commands(cmd: object) -> list:
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

    lines.extend(
        f"**\n/{cmd.qualified_name}**\n-# **{cmd.description}**"
        for top_cmd in get_cog_commands(cog)
        for cmd in flatten_commands(top_cmd)
    )

    return "\n".join(lines)


class HelpView(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.page = 0

        banner_gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(media="https://files.catbox.moe/3dwyry.png"),
        )
        banner_container = discord.ui.Container(banner_gallery)

        # 2. Add fixed custom_id parameters to both buttons
        self.prev_button = discord.ui.Button(
            label="prev",
            style=discord.ButtonStyle.secondary,
            custom_id="help_view:prev",
        )
        self.next_button = discord.ui.Button(
            label="next",
            style=discord.ButtonStyle.secondary,
            custom_id="help_view:next",
        )
        self.prev_button.callback = self.on_prev
        self.next_button.callback = self.on_next

        # Initial text display setup
        cogs = self.get_cogs()
        initial_content = help_page(cogs[0]) if cogs else "No commands available."
        self.text_display = discord.ui.TextDisplay(content=initial_content)
        separator = discord.ui.Separator(
            visible=True, spacing=discord.SeparatorSpacing.small
        )

        self._update_button_states()

        nav_row = discord.ui.ActionRow(self.prev_button, self.next_button)
        content_container = discord.ui.Container(self.text_display, separator, nav_row)

        self.add_item(banner_container)
        self.add_item(content_container)

    def get_cogs(self) -> list:
        return [c for c in self.bot.cogs.values() if get_cog_commands(c)]

    def _update_button_states(self) -> None:
        cogs = self.get_cogs()
        total_pages = len(cogs)
        if total_pages <= 1:
            self.prev_button.disabled = True
            self.next_button.disabled = True
        else:
            self.prev_button.disabled = self.page == 0
            self.next_button.disabled = self.page >= total_pages - 1

    async def on_prev(self, interaction: discord.Interaction) -> None:
        cogs = self.get_cogs()
        if not cogs:
            await interaction.response.defer()
            return

        self.page = max(0, self.page - 1)
        self._update_button_states()
        self.text_display.content = help_page(cogs[self.page])
        await interaction.response.edit_message(view=self)

    async def on_next(self, interaction: discord.Interaction) -> None:
        cogs = self.get_cogs()
        if not cogs:
            await interaction.response.defer()
            return

        self.page = min(len(cogs) - 1, self.page + 1)
        self._update_button_states()
        self.text_display.content = help_page(cogs[self.page])
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
            content=f"# {MELVIN_CROSS_EMOJI} error\n\n{message}",
        )

        container = discord.ui.Container(
            text_display,
            SmallSeparator(),
            accent_color=discord.Color.from_str(tertiary),
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
