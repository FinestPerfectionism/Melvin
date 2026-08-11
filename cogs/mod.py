import datetime
import discord
import aiosqlite
from discord import app_commands
from discord.ext import commands
from globals import INVITE_URL, MELVIN_CROSS_EMOJI, MELVIN_CHECK_EMOJI, SECONDARY, MELVIN_WARN_EMOJI, PRIMARY, \
    MELVIN_MISC_EMOJI
from ui import ResponseUI, ErrorUI, message


class ModCog(
    commands.GroupCog,
    name="mod",
    description="some mod cmds",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_path = "data/mod.db"

    #duration parsing
    def parseduration(self, durationstr: str):
        unit = durationstr[-1].lower()
        if unit not in ("s", "m", "h", "d"):
            return None
        try:
            value = int(durationstr[:-1])
            if value <= 0:
                return None
        except ValueError:
                return None
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return value * multipliers[unit]

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

    async def dmhandling(self, user: discord.User | discord.Member, action_type: str, case_id: int, guild_name: str,
                         reason: str) -> None:
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"**{MELVIN_MISC_EMOJI} you received a {action_type} in {guild_name} for {reason}. case {case_id}**"
            view.container.accent_color = discord.Color.from_str(PRIMARY)
        try:
            await user.send(view=view, allowed_mentions=discord.AllowedMentions(users=False, roles=False))
        except (discord.Forbidden, discord.HTTPException):
            pass
            #only failing silently here because idk where to put the EH for it

    async def cog_load(self) -> None:
        await self._ensure_db()

    #newer cogwide EH
    async def cog_app_command_error(self, interaction: discord.Interaction,
                                    error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            message = "**you lack permission(s) required to run this command.**"
        elif isinstance(error, app_commands.BotMissingPermissions):
            message = "**i lack permission(s) required to run this command.**"
        else:
            message = "**an unexpected error occurred.**"

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
        await interaction.response.defer()
        #guard clause
        if member.bot:
            await interaction.followup.send(view = ErrorUI("**you tried to warn an app.**"))
            return
        if member.id == interaction.user.id:
            await interaction.followup.send(view = ErrorUI("**you tried to warn yourself.**"))
            return
        if member.id == interaction.guild.owner_id:
            await interaction.followup.send(view = ErrorUI("**you tried to warn the guild owner.**"))
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

            await conn.commit()

        #try dm
        await self.dmhandling(
            user=member,
            action_type="warning",
            case_id=case_id,
            guild_name=interaction.guild.name,
            reason=reason,
        )

        #warn msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = (f"# {MELVIN_CHECK_EMOJI} warning\n **{member.mention}, you have been warned, case {case_id}**")
            view.container.accent_color=discord.Color.from_str(SECONDARY)
        await interaction.followup.send(view = view, allowed_mentions=discord.AllowedMentions(users=False, roles=False))

    #kick cmd
    @app_commands.command(name="kick", description="kick a member")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        await interaction.response.defer()
        #guard clause
        if member.bot:
            await interaction.followup.send(view = ErrorUI("**you tried to kick an app.**"))
            return
        if member.id == interaction.user.id:
            await interaction.followup.send(view = ErrorUI("**you tried to kick yourself.**"))
            return
        if member.id == interaction.guild.owner_id:
            await interaction.followup.send(view = ErrorUI("**you tried to kick the guild owner.**"))
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send(view = ErrorUI("**you tried to kick someone equal to / above you.**"))
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(view = ErrorUI("**i tried to kick someone equal to / above me.**"))
            return

        #kick db call
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                """
                INSERT INTO mod_cases (guild_id, user_id, mod_id, action_type, reason)
                VALUES (?, ?, ?, 'kick', ?)
                """,
                (interaction.guild_id, member.id, interaction.user.id, reason),
            )
            case_id = cursor.lastrowid
            await conn.commit()

        #try dm
        await self.dmhandling(
            user=member,
            action_type="kick",
            case_id=case_id,
            guild_name=interaction.guild.name,
            reason=reason,
        )

        #the actual kick part
        await member.kick(reason=f"kicked by melvin using {interaction.user} with the reason {reason}")

        #kick msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = (f"# {MELVIN_CHECK_EMOJI} kicked\n **{member.mention} has been kicked, case {case_id}**")
            view.container.accent_color=discord.Color.from_str(SECONDARY)
        await interaction.followup.send(view = view, allowed_mentions=discord.AllowedMentions(users=False, roles=False))

    #ban cmd
    @app_commands.command(name="ban", description="ban a member")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        await interaction.response.defer()
        #guard clause
        if member.bot:
            await interaction.followup.send(view = ErrorUI("**you tried to ban an app.**"))
            return
        if member.id == interaction.user.id:
            await interaction.followup.send(view = ErrorUI("**you tried to ban yourself.**"))
            return
        if member.id == interaction.guild.owner_id:
            await interaction.followup.send(view = ErrorUI("**you tried to ban the guild owner.**"))
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send(view = ErrorUI("**you tried to ban someone equal to / above you.**"))
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(view = ErrorUI("**i tried to ban someone equal to / above me.**"))
            return

        #ban db call
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                """
                INSERT INTO mod_cases (guild_id, user_id, mod_id, action_type, reason)
                VALUES (?, ?, ?, 'ban', ?)
                """,
                (interaction.guild_id, member.id, interaction.user.id, reason),
            )
            case_id = cursor.lastrowid
            await conn.commit()

        #try dm
        await self.dmhandling(
            user=member,
            action_type="ban",
            case_id=case_id,
            guild_name=interaction.guild.name,
            reason=reason,
        )

        #the actual ban part
        await member.ban(reason=f"banned by melvin using {interaction.user} with the reason {reason}", delete_message_days=30)

        #ban msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = (f"# {MELVIN_CHECK_EMOJI} banned\n **{member.mention} has been banned, case {case_id}**")
            view.container.accent_color=discord.Color.from_str(SECONDARY)
        await interaction.followup.send(view = view, allowed_mentions=discord.AllowedMentions(users=False, roles=False))

    #mute cmd
    @app_commands.command(name="mute", description="mute a member")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, reason: str, duration: str) -> None:
        await interaction.response.defer()

        #guard clause
        seconds = self.parseduration(duration)
        if not seconds:
            await interaction.followup.send(view = ErrorUI("**not a valid duration format.**"))
            return
        if seconds > 28 * 86400:
            await interaction.followup.send(view = ErrorUI("**duration cannot surpass 28 days.**"))
            return
        if member.bot:
            await interaction.followup.send(view = ErrorUI("**you tried to mute an app.**"))
            return
        if member.id == interaction.user.id:
            await interaction.followup.send(view = ErrorUI("**you tried to mute yourself.**"))
            return
        if member.id == interaction.guild.owner_id:
            await interaction.followup.send(view = ErrorUI("**you tried to mute the guild owner.**"))
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send(view = ErrorUI("**you tried to mute someone equal to / above you.**"))
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(view = ErrorUI("**i tried to mute someone equal to / above me.**"))
            return

        #mute db call
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                """
                INSERT INTO mod_cases (guild_id, user_id, mod_id, action_type, reason)
                VALUES (?, ?, ?, 'mute', ?)
                """,
                (interaction.guild_id, member.id, interaction.user.id, reason),
            )
            case_id = cursor.lastrowid
            await conn.commit()

        #try dm
        await self.dmhandling(
            user=member,
            action_type="mute",
            case_id=case_id,
            guild_name=interaction.guild.name,
            reason=reason,
        )

        #the actual mute part
        until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
        await member.timeout(until, reason=f"muted by melvin using {interaction.user} with the reason {reason}")

        #mute msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = (f"# {MELVIN_CHECK_EMOJI} muted\n **{member.mention} has been muted, case {case_id}**")
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(view=view, allowed_mentions=discord.AllowedMentions(users=False, roles=False))


    #unmute cmd
    @app_commands.command(name="unmute", description="unmute a member")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "no reason given") -> None:
        await interaction.response.defer()

        #guard clause
        if not member.is_timed_out():
            await interaction.followup.send(view = ErrorUI("**member is not timed out**"))
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send(view = ErrorUI("**you tried to unmute someone equal to / above you.**"))
            return

        #unmute db call
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                """
                INSERT INTO mod_cases (guild_id, user_id, mod_id, action_type, reason)
                VALUES (?, ?, ?, 'unmute', ?)
                """,
                (interaction.guild_id, member.id, interaction.user.id, reason),
            )
            case_id = cursor.lastrowid
            await conn.commit()

        #try dm
        await self.dmhandling(
            user=member,
            action_type="unmute",
            case_id=case_id,
            guild_name=interaction.guild.name,
            reason=reason,
        )

        #the actual unmute part
        await member.timeout(None, reason=f"unmuted by melvin using {interaction.user} with the reason {reason}")

        #unmute msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = (f"# {MELVIN_CHECK_EMOJI} unmuted\n **{member.mention} has been unmuted, case {case_id}**")
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(view=view, allowed_mentions=discord.AllowedMentions(users=False, roles=False))

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModCog(bot))