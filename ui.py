import discord
from discord.ext import commands

from globals import (
    INVITE_URL,
    MELVIN_CROSS_EMOJI,
    MELVIN_EMOJI,
    PRIMARY,
    SECONDARY,
    TERTIARY,
    MELVIN_HELP_BANNER,
)

primary = f"{PRIMARY}"
secondary = f"{SECONDARY}"  # green
tertiary = f"{TERTIARY}"  # red
message = f"**Something went wrong with that. Please [join the support server]({INVITE_URL}) to report this issue.**"


# HelpView functions to grasp command group details
def get_cog_commands(cog: commands.Cog) -> list:
    group = getattr(cog, "__cog_app_commands_group__", None)
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
    lines = [f"# {MELVIN_EMOJI} {cog.__cog_group_name__} Commands"]
    if (
        hasattr(cog, "__cog_group_description__")
        and cog.__cog_group_description__ != "…"
    ):
        lines.append(f"-# **{cog.__cog_group_description__}**")

    lines.extend(
        f"**\n/{cmd.qualified_name}**\n-# **{cmd.description}**"
        for top_cmd in get_cog_commands(cog)
        for cmd in flatten_commands(top_cmd)
    )

    return "\n".join(lines)


# select menu
class CogSelect(discord.ui.Select):
    def __init__(self, cogs: list[commands.Cog]) -> None:
        self.cogs_map = {cog.__cog_group_name__: cog for cog in cogs}

        options = [
            discord.SelectOption(
                label=cog.__cog_group_name__,
                value=cog.__cog_group_name__,
                description=(
                    cog.__cog_group_description__[:100]
                    if hasattr(cog, "__cog_group_description__")
                    and cog.__cog_group_description__ != "…"
                    else None
                ),
            )
            for cog in cogs
        ]

        super().__init__(
            placeholder="Select a cog category.",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="help_view:cog_select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        selected_cog_name = self.values[0]
        selected_cog = self.cogs_map.get(selected_cog_name)

        if selected_cog and self.view:
            self.view.text_display.content = help_page(selected_cog)
            await interaction.response.edit_message(view=self.view)


class HelpView(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

        banner_gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(f"{MELVIN_HELP_BANNER}"),
        )
        banner_container = discord.ui.Container(banner_gallery)

        cogs = self.get_cogs()
        initial_content = help_page(cogs[0]) if cogs else "No commands available."
        self.text_display = discord.ui.TextDisplay(content=initial_content)
        separator = discord.ui.Separator(
            visible=True, spacing=discord.SeparatorSpacing.small,
        )

        if cogs:
            self.cog_select = CogSelect(cogs)
            select_row = discord.ui.ActionRow(self.cog_select)
            content_container = discord.ui.Container(self.text_display, separator, select_row)
        else:
            content_container = discord.ui.Container(self.text_display, separator)

        self.add_item(banner_container)
        self.add_item(content_container)

    def get_cogs(self) -> list[commands.Cog]:
        return [c for c in self.bot.cogs.values() if get_cog_commands(c)]

    async def on_select_cog(self, interaction: discord.Interaction) -> None:
        selected_cog_name = interaction.data["values"][0]

        cogs_map = {
            getattr(c, "__cog_group_name__", c.qualified_name): c
            for c in self.get_cogs()
        }
        selected_cog = cogs_map.get(selected_cog_name)

        if selected_cog:
            self.text_display.content = help_page(selected_cog)
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.defer()


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
            content=f"# {MELVIN_CROSS_EMOJI} Error\n\n{message}",
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
