import discord
import aiosqlite
from discord import app_commands
from discord.ext import commands
from globals import INVITE_URL
from ui import ResponseUI, ErrorUI, message


class ModCog(
    commands.GroupCog,
    name="modcog",
    description="some mod cmds",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_path = "data/mod.db"

    async def _ensure_db(self) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mod_cases (
                    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    mod_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            await conn.commit()

    #newer cogwide EH
    async def errorhandler(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            message = "you lack permission(s) required to run this command."
        elif isinstance(error, app_commands.BotMissingPermissions):
            message = "i lack permission(s) required to run this command."
            view = ErrorUI(message)
            if interaction.response.is_done():
                await interaction.followup.send(view=view, ephemeral=True)
            else:
                await interaction.response.send_message(view=view, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModCog(bot))
