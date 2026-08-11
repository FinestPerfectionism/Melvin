import discord
import aiosqlite
from discord import app_commands
from discord.ext import commands
from globals import INVITE_URL, MELVIN_CROSS_EMOJI, MELVIN_CHECK_EMOJI, SECONDARY
from ui import ResponseUI, ErrorUI, message


class ModCog(
    commands.GroupCog,
    name="mod",
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

    async def cog_load(self) -> None:
        await self._ensure_db()

    #newer cogwide EH
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            message = f"**you lack permission(s) required to run this command.**"
        elif isinstance(error, app_commands.BotMissingPermissions):
            message = f"**i lack permission(s) required to run this command.**"
        else:
            message = f"**an unexpected error occurred.**"

        view = ErrorUI(message)
        if interaction.response.is_done():
            await interaction.followup.send(view=view, ephemeral=True)
        else:
            await interaction.response.send_message(view=view, ephemeral=True)

    #warn cmd
    @app_commands.command(name="warn", description="warn someone")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        #guard clause
        if member.bot:
            await interaction.response.send_message(view = ErrorUI("**you tried to warn an app.**"))
            return
        if member.id == interaction.user.id:
            await interaction.response.send_message(view = ErrorUI("**you tried to warn yourself.**"))
            return

        #warn db call
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                """
                INSERT INTO mod_cases (guild_id, user_id, mod_id, action_type, reason)
                VALUES (?, ?, ?, 'warn', ?)
                """,
                (interaction.guild_id, member.id, interaction.user.id, reason),
            )
            case_id = cursor.lastrowid

            async with conn.execute(
                    """
                    SELECT COUNT(*) FROM mod_cases
                    WHERE guild_id = ? AND user_id = ? AND action_type = 'warn'
                    """,
                    (interaction.guild_id, member.id),
            ) as count_cursor:
                row = await count_cursor.fetchone()
                total_warns = row[0] if row else 1

            await conn.commit()

        #warn msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = (f"# {MELVIN_CHECK_EMOJI} warning\n **{member.mention}, you have been warned, case {case_id}**")
            view.container.accent_color=discord.Color.from_str(SECONDARY)
        await interaction.response.send_message(view = view, allowed_mentions=discord.AllowedMentions(users=False, roles=False))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModCog(bot))
