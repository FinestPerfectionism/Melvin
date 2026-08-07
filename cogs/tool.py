from globals import PRIMARY, MELVIN_EMOJI
from ui import ResponseUI, ErrorUI
import discord
import base64
import binascii
from discord import app_commands, Interaction, Guild
from discord.ext import commands
primary = f"#{PRIMARY}"

#custom speak gating
def server_permission(permission: str):
    async def predicate(interaction: discord.Interaction):
        if interaction.guild is None:
            return True

        return getattr(interaction.user.guild_permissions, permission, False)

    return app_commands.check(predicate)


class ToolCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    tool = app_commands.Group(name="tool", description="some more tool stuff")

    @tool.command(name="base64-decode", description="decode a base64 encoded string")
    @app_commands.describe(text="the base64 string to decode")
    async def base64decode(self, interaction: discord.Interaction, text: str):
        view = ResponseUI()
        await interaction.response.send_message(view=view, ephemeral=False)

        try:
            decodedbyte = base64.b64decode(text, validate=True)
            decodedstr = decodedbyte.decode("utf-8")
        except binascii.Error as e:
            await interaction.edit_original_response(
                view=ErrorUI(f"not valid b64, **{e}**")
            )
            return
        except UnicodeDecodeError as e:
            await interaction.edit_original_response(
                view=ErrorUI(f"decoded, but the result isn't valid text, **{e}**")
            )
            return

        view.text_display.content = f"**{decodedstr}** was the attempted decode."
        await interaction.edit_original_response(view=view)

    @tool.command(name="base64-encode", description="encode a string as base64")
    @app_commands.describe(text="the string to encode")
    async def base64encode(self, interaction: discord.Interaction, text: str):
        view = ResponseUI()
        await interaction.response.send_message(view=view, ephemeral=False)

        try:
            encodedbyte = base64.b64encode(text.encode("utf-8"))
            encodedstr = encodedbyte.decode("utf-8")
        except Exception as e:
            await interaction.edit_original_response(
                view=ErrorUI(f"something went wrong encoding this: **{e}**")
            )
            return

        view.text_display.content = f"**{encodedstr}** was the attempted encode."
        await interaction.edit_original_response(view=view)

    @tool.command(name="speak", description="speak through melvin")
    @server_permission("manage_messages")

    async def speak(
            self,
            interaction: discord.Interaction,
            text: str,
            attachment: discord.Attachment = None
    ):
        view = ResponseUI()
        view.text_display.content = text

        if attachment is not None:
            file = await attachment.to_file()
            view.container.add_item(
                discord.ui.MediaGallery(
                    discord.MediaGalleryItem(
                        media=f"attachment://{file.filename}"
                    )
                )
            )
            await interaction.response.send_message(view=view, file=file, allowed_mentions=discord.AllowedMentions.none())
        else:
            await interaction.response.send_message(view=view, allowed_mentions=discord.AllowedMentions.none())

    @speak.error
    async def speak_error(
            self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        # Catches the check failure triggered when server_permission returns False
        if isinstance(error, app_commands.CheckFailure):
            view = ResponseUI()
            view.text_display.content = (
                "**This command is gated, read our documentation in our [support server.](https://discord.gg/PfyKM7dyx4)**"
            )

            if interaction.response.is_done():
                await interaction.followup.send(view=view, ephemeral=True)
            else:
                await interaction.response.send_message(view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ToolCog(bot))