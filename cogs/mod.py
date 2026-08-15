import datetime

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

from globals import (
    MELVIN_CHECK_EMOJI,
    MELVIN_MISC_EMOJI,
    PRIMARY,
    SECONDARY,
)
from ui import CasesView, ErrorUI, ResponseUI


class ModCog(
    commands.GroupCog,
    name="mod",
    description="Guild moderation commands.",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_path = "data/mod.db"

    # duration parsing
    def parseduration(self, durationstr: str) -> int | None:
        unit = durationstr[-1].lower()
        if unit not in {"s", "m", "h", "d"}:
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
                """,
            )
            await conn.commit()

    async def dmhandling(
        self,
        user: discord.User | discord.Member,
        action_type: str,
        case_id: int,
        guild_name: str,
        reason: str,
    ) -> None:
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"**{MELVIN_MISC_EMOJI} You received a {action_type} in {guild_name} for {reason}. Case {case_id}.**"
            view.container.accent_color = discord.Color.from_str(PRIMARY)
        try:
            await user.send(
                view=view,
                allowed_mentions=discord.AllowedMentions(users=False, roles=False),
            )
        except (discord.Forbidden, discord.HTTPException):
            pass
            # only failing silently here because idk where to put the EH for it

    async def cog_load(self) -> None:
        await self._ensure_db()

    # newer cogwide EH
    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            message = "**You lack permission(s) required to run this command.**"
        elif isinstance(error, app_commands.BotMissingPermissions):
            message = "**I lack permission(s) required to run this command.**"
        else:
            message = "**An unexpected error occurred.**"

        view = ErrorUI(message)

        if interaction.response.is_done():
            await interaction.followup.send(view=view, ephemeral=True)
        else:
            await interaction.response.send_message(view=view, ephemeral=True)

    # cases cmd
    @app_commands.command(name="cases", description="View moderation cases for a user.")
    @app_commands.describe(target="The target user to view cases for.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def cases(
        self, interaction: discord.Interaction, target: discord.User | discord.Member
    ) -> None:
        await interaction.response.defer()

        view = CasesView(target_user=target, db_path=self.db_path)
        await view.build_components(interaction.guild_id)

        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # case remove cmd
    @app_commands.command(
        name="case-remove",
        description="Remove a mod action from a users account, takes the ID.",
    )
    @app_commands.describe(
        case_id="takes the CaseID typically dmed to the user, find it by using /case [user]"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def case_remove(self, interaction: discord.Interaction, case_id: int) -> None:
        await interaction.response.defer()

        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(
                "SELECT user_id, action_type FROM mod_cases WHERE guild_id = ? AND case_id = ?",
                (interaction.guild_id, case_id),
            ) as cursor:
                case = await cursor.fetchone()

            if not case:
                await interaction.followup.send(
                    view=ErrorUI(f"**Case #{case_id} was not found in this server.**"),
                )
                return

            user_id, action_type = case
            await conn.execute(
                "DELETE FROM mod_cases WHERE guild_id = ? AND case_id = ?",
                (interaction.guild_id, case_id),
            )
            await conn.commit()

        # case remove UI
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = (
                f"# {MELVIN_CHECK_EMOJI} Case Removed\n "
                f"**Removed case #{case_id} ({action_type.upper()}) for <@{user_id}>.**"
            )
            view.container.accent_color = discord.Color.from_str(SECONDARY)

        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # warn cmd
    @app_commands.command(name="warn", description="Warn someone.")
    @app_commands.describe(
        member="The member to warn.",
        reason="The reason for the warning.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided.",
    ) -> None:
        await interaction.response.defer()
        # guard clause
        if member.bot:
            await interaction.followup.send(
                view=ErrorUI("**You tried to warn an app.**"),
            )
            return
        if member.id == interaction.user.id:
            await interaction.followup.send(
                view=ErrorUI("**You tried to warn yourself.**"),
            )
            return
        if member.id == interaction.guild.owner_id:
            await interaction.followup.send(
                view=ErrorUI("**You tried to warn the guild owner.**"),
            )
            return

        # warn db call
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

        # try dm
        await self.dmhandling(
            user=member,
            action_type="warning",
            case_id=case_id,
            guild_name=interaction.guild.name,
            reason=reason,
        )

        # warn msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"# {MELVIN_CHECK_EMOJI} Warning\n **{member.mention}, you have been warned. Case {case_id}.**"
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # kick cmd
    @app_commands.command(name="kick", description="Kick a member.")
    @app_commands.describe(
        member="The member to kick.",
        reason="The reason for the kick.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided.",
    ) -> None:
        await interaction.response.defer()
        # guard clause
        if member.bot:
            await interaction.followup.send(
                view=ErrorUI("**You tried to kick an app.**"),
            )
            return
        if member.id == interaction.user.id:
            await interaction.followup.send(
                view=ErrorUI("**You tried to kick yourself.**"),
            )
            return
        if member.id == interaction.guild.owner_id:
            await interaction.followup.send(
                view=ErrorUI("**You tried to kick the guild owner.**"),
            )
            return
        if (
            member.top_role >= interaction.user.top_role
            and interaction.user.id != interaction.guild.owner_id
        ):
            await interaction.followup.send(
                view=ErrorUI("**You tried to kick someone equal to or above you.**"),
            )
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(
                view=ErrorUI("**I tried to kick someone equal to or above me.**"),
            )
            return

        # kick db call
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

        # try dm
        await self.dmhandling(
            user=member,
            action_type="kick",
            case_id=case_id,
            guild_name=interaction.guild.name,
            reason=reason,
        )

        # the actual kick part
        await member.kick(
            reason=f"Kicked by Melvin using {interaction.user.name} with the reason: {reason}",
        )

        # kick msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"# {MELVIN_CHECK_EMOJI} Kicked\n **{member.mention} has been kicked. Case {case_id}.**"
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # ban cmd
    @app_commands.command(name="ban", description="Ban a member.")
    @app_commands.describe(
        member="The member to ban.",
        reason="The reason for the ban.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided.",
    ) -> None:
        await interaction.response.defer()
        # guard clause
        if member.bot:
            await interaction.followup.send(
                view=ErrorUI("**You tried to ban an app.**"),
            )
            return
        if member.id == interaction.user.id:
            await interaction.followup.send(
                view=ErrorUI("**You tried to ban yourself.**"),
            )
            return
        if member.id == interaction.guild.owner_id:
            await interaction.followup.send(
                view=ErrorUI("**You tried to ban the guild owner.**"),
            )
            return
        if (
            member.top_role >= interaction.user.top_role
            and interaction.user.id != interaction.guild.owner_id
        ):
            await interaction.followup.send(
                view=ErrorUI("**You tried to ban someone equal to or above you.**"),
            )
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(
                view=ErrorUI("**I tried to ban someone equal to or above me.**"),
            )
            return

        # ban db call
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

        # try dm
        await self.dmhandling(
            user=member,
            action_type="ban",
            case_id=case_id,
            guild_name=interaction.guild.name,
            reason=reason,
        )

        # the actual ban part
        await member.ban(
            reason=f"Banned by Melvin using {interaction.user.name} with the reason: {reason}",
            delete_message_days=7,
        )

        # ban msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"# {MELVIN_CHECK_EMOJI} Banned\n **{member.mention} has been banned. Case {case_id}.**"
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    @app_commands.command(name="unban", description="Unban a user.")
    @app_commands.describe(
        user="The user to unban.",
        reason="The reason for the unban.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        reason: str = "No reason provided.",
    ) -> None:
        await interaction.response.defer()

        # guard clause
        try:
            await interaction.guild.fetch_ban(user)
        except discord.NotFound:
            await interaction.followup.send(
                view=ErrorUI("**That user is not banned.**"),
            )
            return
        except discord.HTTPException as e:
            await interaction.followup.send(
                view=ErrorUI(f"**Failed to check ban status: {e!s}.**"),
            )
            return

        # unban db call
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                """
                INSERT INTO mod_cases (guild_id, user_id, mod_id, action_type, reason)
                VALUES (?, ?, ?, 'unban', ?)
                """,
                (interaction.guild_id, user.id, interaction.user.id, reason),
            )
            case_id = cursor.lastrowid
            await conn.commit()

        # the actual unban part
        await interaction.guild.unban(
            user,
            reason=f"Unbanned using Melvin by {interaction.user.name} with the reason: {reason}",
        )

        # unban msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"# {MELVIN_CHECK_EMOJI} Unbanned\n **{user.mention} has been unbanned. Case {case_id}.**"
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # mute cmd
    @app_commands.command(name="mute", description="Mute a member.")
    @app_commands.describe(
        member="The member to mute.",
        duration="The duration of the mute (e.g., 10m, 2h, 1d).",
        reason="The reason for the mute.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: str,
        reason: str = "No reason provided.",
    ) -> None:
        await interaction.response.defer()

        # guard clause
        seconds = self.parseduration(duration)
        if not seconds:
            await interaction.followup.send(
                view=ErrorUI("**Not a valid duration format.**"),
            )
            return
        if seconds > 28 * 86400:
            await interaction.followup.send(
                view=ErrorUI("**Duration cannot surpass 28 days.**"),
            )
            return
        if member.bot:
            await interaction.followup.send(
                view=ErrorUI("**You tried to mute an app.**"),
            )
            return
        if member.id == interaction.user.id:
            await interaction.followup.send(
                view=ErrorUI("**You tried to mute yourself.**"),
            )
            return
        if member.id == interaction.guild.owner_id:
            await interaction.followup.send(
                view=ErrorUI("**You tried to mute the guild owner.**"),
            )
            return
        if (
            member.top_role >= interaction.user.top_role
            and interaction.user.id != interaction.guild.owner_id
        ):
            await interaction.followup.send(
                view=ErrorUI("**You tried to mute someone equal to or above you.**"),
            )
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(
                view=ErrorUI("**I tried to mute someone equal to or above me.**"),
            )
            return

        # mute db call
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

        # try dm
        await self.dmhandling(
            user=member,
            action_type="mute",
            case_id=case_id,
            guild_name=interaction.guild.name,
            reason=reason,
        )

        # the actual mute part
        until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
        await member.timeout(
            until,
            reason=f"Muted by Melvin using {interaction.user.name} with the reason: {reason}",
        )

        # mute msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"# {MELVIN_CHECK_EMOJI} Muted\n **{member.mention} has been muted. Case {case_id}.**"
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # unmute cmd
    @app_commands.command(name="unmute", description="Unmute a member.")
    @app_commands.describe(
        member="The member to unmute.",
        reason="The reason for the unmute.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason given.",
    ) -> None:
        await interaction.response.defer()

        # guard clause
        if not member.is_timed_out():
            await interaction.followup.send(
                view=ErrorUI("**Member is not timed out.**")
            )
            return
        if (
            member.top_role >= interaction.user.top_role
            and interaction.user.id != interaction.guild.owner_id
        ):
            await interaction.followup.send(
                view=ErrorUI("**You tried to unmute someone equal to or above you.**"),
            )
            return

        # unmute db call
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

        # try dm
        await self.dmhandling(
            user=member,
            action_type="unmute",
            case_id=case_id,
            guild_name=interaction.guild.name,
            reason=reason,
        )

        # the actual unmute part
        await member.timeout(
            None,
            reason=f"Unmuted by Melvin using {interaction.user.name} with the reason: {reason}",
        )

        # unmute msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"# {MELVIN_CHECK_EMOJI} Unmuted\n **{member.mention} has been unmuted. Case {case_id}.**"
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # lock cmd
    @app_commands.command(name="lock", description="Lock a channel.")
    @app_commands.describe(
        channel="The channel or thread to lock.",
        reason="The reason for locking.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
        | discord.VoiceChannel
        | discord.Thread
        | None = None,
        reason: str = "No reason given.",
    ) -> None:
        await interaction.response.defer()
        target_channel = channel or interaction.channel

        # guard clause
        if not isinstance(
            target_channel,
            (discord.TextChannel, discord.VoiceChannel, discord.Thread),
        ):
            await interaction.followup.send(
                view=ErrorUI(
                    "**This can only be used in a text channel, voice channel, or thread.**",
                ),
            )
            return

        if isinstance(target_channel, discord.Thread):
            if target_channel.locked:
                await interaction.followup.send(
                    view=ErrorUI("**This thread is already locked.**"),
                )
                return

            # the actual thread locking
            await target_channel.edit(
                locked=True,
                reason=f"Locked using Melvin by {interaction.user.name} for the reason: {reason}",
            )
        else:
            current_overwrite = target_channel.overwrites_for(
                interaction.guild.default_role,
            )
            if current_overwrite.send_messages is False:
                await interaction.followup.send(
                    view=ErrorUI("**This channel is already locked.**"),
                )
                return

            # the actual channel locking
            current_overwrite.send_messages = False
            await target_channel.set_permissions(
                interaction.guild.default_role,
                overwrite=current_overwrite,
                reason=f"Locked using Melvin by {interaction.user.name} for the reason: {reason}",
            )

        # lock msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"# {MELVIN_CHECK_EMOJI} Locked\n **{target_channel.mention} has been locked.**"
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # unlock cmd
    @app_commands.command(name="unlock", description="Unlock a channel.")
    @app_commands.describe(
        channel="The channel or thread to unlock.",
        reason="The reason for unlocking.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
        | discord.VoiceChannel
        | discord.Thread
        | None = None,
        reason: str = "No reason given.",
    ) -> None:
        await interaction.response.defer()
        target_channel = channel or interaction.channel

        # guard clause
        if not isinstance(
            target_channel,
            (discord.TextChannel, discord.VoiceChannel, discord.Thread),
        ):
            await interaction.followup.send(
                view=ErrorUI(
                    "**This can only be used in either a text channel, voice channel, or thread.**",
                ),
            )
            return

        if isinstance(target_channel, discord.Thread):
            if not target_channel.locked:
                await interaction.followup.send(
                    view=ErrorUI("**This thread is not locked.**"),
                )
                return

            # the actual thread unlocking
            await target_channel.edit(
                locked=False,
                reason=f"Unlocked using Melvin by {interaction.user.name} with the reason: {reason}",
            )
        else:
            current_overwrite = target_channel.overwrites_for(
                interaction.guild.default_role,
            )
            if (
                current_overwrite.send_messages is None
                or current_overwrite.send_messages is True
            ):
                await interaction.followup.send(
                    view=ErrorUI("**This channel is not locked.**"),
                )
                return

            # the actual channel unlocking (sets overwrite back to neutral/inherit)
            current_overwrite.send_messages = None
            await target_channel.set_permissions(
                interaction.guild.default_role,
                overwrite=current_overwrite,
                reason=f"Unlocked using Melvin by {interaction.user.name} with the reason: {reason}",
            )

        # unlock msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"# {MELVIN_CHECK_EMOJI} Unlocked\n **Unlocked {target_channel.mention}.**"
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # role add cmd
    @app_commands.command(name="role-add", description="Add a role to a member.")
    @app_commands.describe(
        member="The member to give the role to.",
        role="The role to add.",
        reason="The reason for adding the role.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_add(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
        reason: str = "No reason provided.",
    ) -> None:
        await interaction.response.defer()

        # guard clause
        if member.bot:
            await interaction.followup.send(
                view=ErrorUI("**You tried to add a role to an app.**"),
            )
            return
        if role in member.roles:
            await interaction.followup.send(
                view=ErrorUI("**That member already has this role.**"),
            )
            return
        if (
            role.position >= interaction.user.top_role.position
            and interaction.user.id != interaction.guild.owner_id
        ):
            await interaction.followup.send(
                view=ErrorUI(
                    "**You tried to manage a role equal to or above your top role.**",
                ),
            )
            return
        if role.position >= interaction.guild.me.top_role.position:
            await interaction.followup.send(
                view=ErrorUI(
                    "**I tried to manage a role equal to or above my top role.**",
                ),
            )
            return

        # role db call
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                """
                INSERT INTO mod_cases (guild_id, user_id, mod_id, action_type, reason)
                VALUES (?, ?, ?, 'role_add', ?)
                """,
                (interaction.guild_id, member.id, interaction.user.id, reason),
            )
            case_id = cursor.lastrowid
            await conn.commit()

        # the actual role part
        await member.add_roles(
            role,
            reason=f"Role added by Melvin using {interaction.user.name} with the reason: {reason}",
        )

        # role add msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"# {MELVIN_CHECK_EMOJI} Role Added\n **{role.mention} added to {member.mention}. Case {case_id}.**"
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # role remove cmd
    @app_commands.command(
        name="role-remove", description="Remove a role from a member."
    )
    @app_commands.describe(
        member="The member to remove the role from.",
        role="The role to remove.",
        reason="The reason for removing the role.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_remove(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
        reason: str = "No reason provided.",
    ) -> None:
        await interaction.response.defer()

        # guard clause
        if member.bot:
            await interaction.followup.send(
                view=ErrorUI("**You tried to remove a role from an app.**"),
            )
            return
        if role not in member.roles:
            await interaction.followup.send(
                view=ErrorUI("**That member does not have this role.**"),
            )
            return
        if (
            role.position >= interaction.user.top_role.position
            and interaction.user.id != interaction.guild.owner_id
        ):
            await interaction.followup.send(
                view=ErrorUI(
                    "**You tried to manage a role equal to or above your top role.**",
                ),
            )
            return
        if role.position >= interaction.guild.me.top_role.position:
            await interaction.followup.send(
                view=ErrorUI(
                    "**I tried to manage a role equal to or above my top role.**",
                ),
            )
            return

        # role db call
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                """
                INSERT INTO mod_cases (guild_id, user_id, mod_id, action_type, reason)
                VALUES (?, ?, ?, 'role_remove', ?)
                """,
                (interaction.guild_id, member.id, interaction.user.id, reason),
            )
            case_id = cursor.lastrowid
            await conn.commit()

        # the actual role part
        await member.remove_roles(
            role,
            reason=f"Role removed by Melvin using {interaction.user.name} with the reason: {reason}",
        )

        # role remove msg
        view = ResponseUI()
        if hasattr(view.text_display, "content"):
            view.text_display.content = f"# {MELVIN_CHECK_EMOJI} Role Removed\n **{role.mention} removed from {member.mention}. Case {case_id}.**"
            view.container.accent_color = discord.Color.from_str(SECONDARY)
        await interaction.followup.send(
            view=view,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ModCog(bot))
