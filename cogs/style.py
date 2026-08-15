import re

import discord
from discord import app_commands
from discord.ext import commands

from globals import MELVIN_CHECK_EMOJI, SECONDARY, DisplayNameEffect, DisplayNameFont
from main import Melvin
from ui import ErrorUI, ResponseUI

COLOR_PATTERN = re.compile(r"^[0-9a-fA-F]{6}(?:-[0-9a-fA-F]{6})?$")


@app_commands.guild_only
class StyleCog(
    commands.GroupCog,
    name="style",
    description="Name style configuration commmands.",
):
    def __init__(self, bot: Melvin) -> None:
        self.bot = bot

    @app_commands.command(name="reset", description="Reset Melvin's name style for this guild.")
    async def reset(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return

        await self.bot.reset_name_style(guild=interaction.guild)
        view = ResponseUI()
        view.text_display.content = f"{MELVIN_CHECK_EMOJI} Style Reset\nMelvin's display name style has been reset for this server."
        view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.response.send_message(view=view)

    @app_commands.command(name="set", description="Set Melvin's name style for this guild.")
    @app_commands.describe(
        font="The display name's font.",
        effect="The display name's effect.",
        colors="The display name's colors.",
    )
    @app_commands.choices(
        font=[
            # app_commands.Choice(name="Bangers", value="bangers"),
            # app_commands.Choice(name="Bio Rhyme", value="bio_rhyme"),
            app_commands.Choice(name="Cherry Bomb", value="cherry_bomb"),
            app_commands.Choice(name="Chicle", value="chicle"),
            # app_commands.Choice(name="Compagnon", value="compagnon"),
            app_commands.Choice(name="Museo Moderno", value="museo_moderno"),
            app_commands.Choice(name="Neo Castel", value="neo_castel"),
            app_commands.Choice(name="Pixelify", value="pixelify"),
            # app_commands.Choice(name="Ribes", value="ribes"),
            app_commands.Choice(name="Sinistre", value="sinistre"),
            app_commands.Choice(name="Default", value="default"),
            app_commands.Choice(name="Zilla Slab", value="zilla_slab"),
        ],
        effect=[
            app_commands.Choice(name="Solid", value="solid"),
            app_commands.Choice(name="Gradient", value="gradient"),
            app_commands.Choice(name="Neon", value="neon"),
            app_commands.Choice(name="Toon", value="toon"),
            app_commands.Choice(name="Pop", value="pop"),
            # app_commands.Choice(name="Glow", value="glow"),
        ],
    )
    async def set(
        self,
        interaction: discord.Interaction,
        font: str,
        effect: str,
        colors: str,
    ) -> None:
        if interaction.guild is None:
            return

        is_valid = bool(COLOR_PATTERN.match(colors))
        has_dash = "-" in colors

        if not is_valid or (effect == "gradient" and not has_dash) or (effect != "gradient" and has_dash):
            error = (
                "Gradient must be of the form `ABCDEF-123456`."
                if effect == "gradient" else
                "Color must be of the form `ABCDEF`."
            )

            view = ErrorUI(error)
            await interaction.response.send_message(view=view)
            return

        color_list = colors.split("-")

        await self.bot.set_name_style(
            guild=interaction.guild,
            font_id=DisplayNameFont[font],
            effect_id=DisplayNameEffect[effect],
            colors=color_list,
        )
        view = ResponseUI()
        view.text_display.content = f"{MELVIN_CHECK_EMOJI} Style Set\nMelvin's display name style has been set for this server."
        view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.response.send_message(view=view)


async def setup(bot: Melvin) -> None:
    await bot.add_cog(StyleCog(bot))
