import base64
import binascii
import random

import discord
from discord import app_commands
from discord.ext import commands

from globals import INVITE_URL, MELVIN_EMOJI
from ui import ErrorUI, ResponseUI

result = random.choice(["heads", "tails"])


class ToolCog(
    commands.GroupCog,
    name="tool",
    description="some more tool stuff",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="base64-decode", description="decode a base64 encoded string")
    @app_commands.describe(text="the base64 string to decode")
    async def base64decode(self, interaction: discord.Interaction, text: str) -> None:
        view = ResponseUI()
        await interaction.response.send_message(view=view, ephemeral=False)

        try:
            decodedbyte = base64.b64decode(text, validate=True)
            decodedstr = decodedbyte.decode("utf-8")
        except binascii.Error as e:
            await interaction.edit_original_response(
                view=ErrorUI(f"not valid b64, **{e}**"),
            )
            return
        except UnicodeDecodeError as e:
            await interaction.edit_original_response(
                view=ErrorUI(f"decoded, but the result isn't valid text, **{e}**"),
            )
            return

        view.text_display.content = f"**{decodedstr}** was the attempted decode."
        await interaction.edit_original_response(view=view)

    @app_commands.command(name="base64-encode", description="encode a string as base64")
    @app_commands.describe(text="the string to encode")
    async def base64encode(self, interaction: discord.Interaction, text: str) -> None:
        view = ResponseUI()
        await interaction.response.send_message(view=view, ephemeral=False)

        try:
            encodedbyte = base64.b64encode(text.encode("utf-8"))
            encodedstr = encodedbyte.decode("utf-8")
        except Exception as e:
            await interaction.edit_original_response(
                view=ErrorUI(f"something went wrong encoding this: **{e}**"),
            )
            return

        view.text_display.content = f"**{encodedstr}** was the attempted encode."
        await interaction.edit_original_response(view=view)

    @app_commands.command(name="speak", description="speak through melvin")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def speak(
        self,
        interaction: discord.Interaction,
        text: str,
        attachment: discord.Attachment | None = None,
    ) -> None:
        view = ResponseUI()
        view.text_display.content = text

        if attachment is not None:
            file = await attachment.to_file()
            view.container.add_item(
                discord.ui.MediaGallery(
                    discord.MediaGalleryItem(
                        media=f"attachment://{file.filename}",
                    ),
                ),
            )
            await interaction.response.send_message(view=view, file=file, allowed_mentions=discord.AllowedMentions.none())
        else:
            await interaction.response.send_message(view=view, allowed_mentions=discord.AllowedMentions.none())

    @speak.error
    async def speak_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError,
    ) -> None:
        # Catches if the user doesn't have server permissions
        if isinstance(error, app_commands.MissingPermissions):
            view = ResponseUI()
            view.text_display.content = (
                f"**This command is gated, read our documentation in our [support server.]({INVITE_URL})**"
            )

            if interaction.response.is_done():
                await interaction.followup.send(view=view, ephemeral=True)
            else:
                await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="coin", description="flip the coin")
    async def coinflip(self, interaction: discord.Interaction) -> None:
        view = ResponseUI()
        await interaction.response.send_message(view=view)

        result = random.choice(["heads", "tails"])
        view.text_display.content = f"**{MELVIN_EMOJI} the result is... {result}**"
        await interaction.edit_original_response(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ToolCog(bot))
