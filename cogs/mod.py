import discord
import aiosqlite
from discord.ext import commands
from globals import INVITE_URL
from ui import ResponseUI, ErrorUI

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
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kick_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ban_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mute_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    mod_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            await conn.commit()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModCog(bot))
