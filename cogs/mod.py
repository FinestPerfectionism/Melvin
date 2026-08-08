import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import re
from datetime import timedelta
from ui import ErrorUI, ActionUI

#globals (will likely duplicate)

DURATION_PATTERN = re.compile(r"^(\d+)([smhd])$")
UNIT_MAP = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
}

def parse_duration(duration: str) -> timedelta | None:
    match = DURATION_PATTERN.match(duration.strip().lower())
    if not match:
        return None

    amount, unit = match.groups()
    amount = int(amount)
    if amount <= 0:
        return None

    return timedelta(**{UNIT_MAP[unit]: amount})


class Modcog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "moderation.db"
        self.locked_channels: dict[int, discord.PermissionOverwrite] = {}
        self.sniped_messages: dict[int, dict] = {}

    async def _restore_channel(self, channel: discord.TextChannel, everyone_role: discord.Role):
        """pops the stored overwrite and re-applies it, removing the lock entry"""
        original_overwrite = self.locked_channels.pop(channel.id)
        await channel.set_permissions(
            everyone_role,
            overwrite=original_overwrite,
            reason="channel unlocked"
        )

    async def cog_load(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                moderator_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    # one shared error handler for every command in this cog
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "**you don't have permission to do this.**"
        elif isinstance(error, app_commands.NoPrivateMessage):
            msg = "**this command can only be used in a server.**"
        else:
            msg = "**something went wrong.**\nplease [join the support server](https://discord.gg/PfyKM7dyx4) to report this issue."

        error_ui = ErrorUI(msg)
        if interaction.response.is_done():
            await interaction.edit_original_response(view=error_ui)
        else:
            await interaction.response.send_message(view=error_ui, ephemeral=False)

    #snipe listener
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        self.sniped_messages[message.channel.id] = {
            "author": message.author,
            "content": message.content or "*(no text content — attachment or embed)*",
            "timestamp": message.created_at,
        }


    mod = app_commands.Group(name="mod", description="simple moderative actions", guild_only=True)


    @mod.command(name="warns", description="check you, or someone else's warns")
    @app_commands.guild_only()
    @app_commands.describe(member="the member you're checking, i.e yourself")
    async def warnings(
            self,
            interaction: discord.Interaction,
            member: discord.Member = None
    ):
        action_UI = ActionUI()
        await interaction.response.send_message(view=action_UI, ephemeral=False)

        member = member or interaction.user

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT moderator_id, reason, timestamp FROM warnings
                WHERE guild_id = ? AND user_id = ?
                ORDER BY timestamp DESC
                """,
                (str(interaction.guild.id), str(member.id))
            )
            rows = cursor.fetchall()
            conn.close()
        except Exception:
            await interaction.edit_original_response(view=ErrorUI("**there was a problem with the database.\nplease [join the support server](https://discord.gg/PfyKM7dyx4) to report this issue.**"))
            return

        if not rows:
            action_UI.update_text(f"{member.mention} has no warns.")
            await interaction.edit_original_response(view=action_UI)
            return

        entries = []
        for moderator_id, reason, timestamp in rows:
            entries.append(
                f"**mod:** <@{moderator_id}>\n**reason:** {reason}\n**when:** {timestamp}"
            )

        action_UI.update_text(
            f"**warns for {member.mention}** ({len(rows)})\n\n" + "\n\n".join(entries)
        )
        await interaction.edit_original_response(view=action_UI)


    @mod.command(name="lock", description="lock a channel, or unlock it if already locked")
    @app_commands.guild_only()
    @app_commands.describe(channel="the channel to lock (defaults to this channel)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(
            self,
            interaction: discord.Interaction,
            channel: discord.TextChannel = None
    ):
        action_ui = ActionUI()
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        channel = channel or interaction.channel
        everyone_role = interaction.guild.default_role

        # toggle: if already locked, unlock instead
        if channel.id in self.locked_channels:
            try:
                await self._restore_channel(channel, everyone_role)
            except discord.Forbidden:
                await interaction.edit_original_response(
                    view=ErrorUI("**i don't have permission to edit this channel's permissions.**")
                )
                return
            except discord.HTTPException:
                await interaction.edit_original_response(view=ErrorUI("**couldn't unlock that channel.**\nplease [join the support server](https://discord.gg/PfyKM7dyx4) to report this issue."))
                return

            action_ui.update_text(f"**unlocked** {channel.mention}")
            await interaction.edit_original_response(view=action_ui)
            return

        # not locked yet — capture current state before touching anything
        original_overwrite = channel.overwrites_for(everyone_role)
        new_overwrite = discord.PermissionOverwrite.from_pair(*original_overwrite.pair())
        new_overwrite.send_messages = False

        try:
            await channel.set_permissions(
                everyone_role,
                overwrite=new_overwrite,
                reason=f"locked by {interaction.user}"
            )
        except discord.Forbidden:
            await interaction.edit_original_response(
                view=ErrorUI("**i don't have permission to edit this channel's permissions.**")
            )
            return
        except discord.HTTPException:
            await interaction.edit_original_response(view=ErrorUI("**couldn't lock that channel.**\nplease [join the support server](https://discord.gg/PfyKM7dyx4) to report this issue."))
            return

        self.locked_channels[channel.id] = original_overwrite

        action_ui.update_text(f"**locked** {channel.mention}")
        await interaction.edit_original_response(view=action_ui)


    @mod.command(name="unlock", description="unlock a previously locked channel")
    @app_commands.guild_only()
    @app_commands.describe(channel="the channel to unlock (defaults to this channel)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(
            self,
            interaction: discord.Interaction,
            channel: discord.TextChannel = None
    ):
        action_ui = ActionUI()
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        channel = channel or interaction.channel
        everyone_role = interaction.guild.default_role

        if channel.id not in self.locked_channels:
            await interaction.edit_original_response(
                view=ErrorUI(f"**{channel.mention} isn't locked.**")
            )
            return

        try:
            await self._restore_channel(channel, everyone_role)
        except discord.Forbidden:
            await interaction.edit_original_response(
                view=ErrorUI("**i don't have permission to edit this channel's permissions.**")
            )
            return
        except discord.HTTPException:
            await interaction.edit_original_response(view=ErrorUI("**couldn't unlock that channel.**\nplease [join the support server](https://discord.gg/PfyKM7dyx4) to report this issue."))
            return

        action_ui.update_text(f"**unlocked** {channel.mention}")
        await interaction.edit_original_response(view=action_ui)


    @mod.command(name="warn", description="warn a member")
    @app_commands.guild_only()
    @app_commands.describe(member="the member to warn", reason="why they're being warned", dm="whether to notify the member via dm (default: false)")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            reason: str,
            dm: bool = False
    ):
        action_ui = ActionUI()
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        if member.bot:
            await interaction.edit_original_response(view=ErrorUI("**you can't warn a bot.**"))
            return

        if member.id == interaction.user.id:
            await interaction.edit_original_response(view=ErrorUI("**you can't warn yourself.**"))
            return

        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.edit_original_response(
                view=ErrorUI("**you can't warn someone with an equal or higher role.**")
            )
            return

        if member.top_role >= interaction.guild.me.top_role:
            await interaction.edit_original_response(
                view=ErrorUI("**this user has a higher or equal role to the bot.**")
            )
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES (?, ?, ?, ?)
                """,
                (str(interaction.guild.id), str(member.id), str(interaction.user.id), reason)
            )
            conn.commit()
            conn.close()
        except Exception:
            await interaction.edit_original_response(view=ErrorUI("**there was a problem with the database.\nplease [join the support server](https://discord.gg/PfyKM7dyx4) to report this issue.**"))
            return

        dm_note = ""
        if dm:
            try:
                await member.send(
                    f"# you were warned in **{interaction.guild.name}**\n**reason:** {reason}"
                )
            except discord.Forbidden:
                dm_note = "**couldn't dm this user, their dms may be closed**"
            except discord.HTTPException:
                dm_note = "**couldn't send the dm.**"

        action_ui.update_text(
            f"**warned {member.mention}**\n\n**reason:** {reason}{dm_note}"
        )
        await interaction.edit_original_response(view=action_ui)


    @mod.command(name="kick", description="kick a member")
    @app_commands.guild_only()
    @app_commands.describe(member="the member to kick", reason="why they're being kicked", dm="whether to notify the member via dm (default: false)")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            reason: str,
            dm: bool = False
    ):
        action_ui = ActionUI()
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        if member.id == interaction.user.id:
            await interaction.edit_original_response(view=ErrorUI("**you can't kick yourself.**"))
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.edit_original_response(
                view=ErrorUI("**you can't kick someone with an equal or higher role.**")
            )
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.edit_original_response(
                view=ErrorUI("**this user has a higher or equal role to the bot.**")
            )
            return

        dm_note = ""
        if dm:
            try:
                await member.send(
                    f"# you were kicked from **{interaction.guild.name}**\n**reason:** {reason}"
                )
            except discord.Forbidden:
                dm_note = "**couldn't dm this user, their dms may be closed**"
            except discord.HTTPException:
                dm_note = "**couldn't send the dm.**"

        try:
            await member.kick(reason=reason)
        except discord.Forbidden:
            await interaction.edit_original_response(
                view=ErrorUI("**i don't have permission to kick this member.**")
            )
            return
        except discord.HTTPException:
            await interaction.edit_original_response(view=ErrorUI("**couldn't kick this member.**"))
            return

        db_note = ""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES (?, ?, ?, ?)
                """,
                (str(interaction.guild.id), str(member.id), str(interaction.user.id),
                 f"{reason} (this action was a kick)")
            )
            conn.commit()
            conn.close()
        except Exception as e:
            db_note = f"\n\n**couldn't log this action: {e}**"

        action_ui.update_text(
            f"**kicked {member.mention}**\n\n**reason:** {reason}{dm_note}{db_note}"
        )
        await interaction.edit_original_response(view=action_ui)


    @mod.command(name="ban", description="ban a member")
    @app_commands.guild_only()
    @app_commands.describe(member="the member to ban", reason="why they're being banned", dm="whether to notify the member via dm (default: false)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            reason: str,
            dm: bool = False
    ):
        action_ui = ActionUI()
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        if member.id == interaction.user.id:
            await interaction.edit_original_response(view=ErrorUI("**you can't ban yourself.**"))
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.edit_original_response(
                view=ErrorUI("**you can't ban someone with an equal or higher role.**")
            )
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.edit_original_response(
                view=ErrorUI("**this user has a higher or equal role to the bot.**")
            )
            return

        dm_note = ""
        if dm:
            try:
                await member.send(
                    f"# you were banned from **{interaction.guild.name}**\n**reason:** {reason}"
                )
            except discord.Forbidden:
                dm_note = "**couldn't dm this user, their dms may be closed**"
            except discord.HTTPException:
                dm_note = "**couldn't send the dm.**"

        try:
            await member.ban(reason=reason)
        except discord.Forbidden:
            await interaction.edit_original_response(
                view=ErrorUI("**i don't have permission to ban this member.**")
            )
            return
        except discord.HTTPException:
            await interaction.edit_original_response(view=ErrorUI("**couldn't ban this member.**"))
            return

        db_note = ""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES (?, ?, ?, ?)
                """,
                (str(interaction.guild.id), str(member.id), str(interaction.user.id),
                 f"{reason} (this action was a ban)")
            )
            conn.commit()
            conn.close()
        except Exception as e:
            db_note = f"\n\n**couldn't log this action: {e}**"

        action_ui.update_text(
            f"**banned {member.mention}**\n\n**reason:** {reason}{dm_note}{db_note}"
        )
        await interaction.edit_original_response(view=action_ui)

    @ban.error
    async def ban_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "**you don't have permission to ban members**"
        else:
            msg = f"**error, {error}. please [join the support server](https://discord.gg/PfyKM7dyx4) to report this issue.**"
        if interaction.response.is_done():
            await interaction.edit_original_response(view=ErrorUI(msg))
        else:
            await interaction.response.send_message(view=ErrorUI(msg), ephemeral=False)






    #reskinned ban command, ignore
    @mod.command(name="lynch", description="lynch a member")
    @app_commands.guild_only()
    @app_commands.describe(member="the member to lynch", reason="why they're being lynched", dm="whether to notify the member via dm (default: false)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def lynch(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            reason: str,
            dm: bool = False
    ):
        action_ui = ActionUI()
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        if member.id == interaction.user.id:
            await interaction.edit_original_response(view=ErrorUI("**you can't lynch yourself.**"))
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.edit_original_response(
                view=ErrorUI("**you can't lynch someone with an equal or higher role.**")
            )
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.edit_original_response(
                view=ErrorUI("**this user has a higher or equal role to the bot.**")
            )
            return

        dm_note = ""
        if dm:
            try:
                await member.send(
                    f"# you were lynched, burned, stoned, and removed from **{interaction.guild.name}**\n**reason:** {reason}"
                )
            except discord.Forbidden:
                dm_note = "**couldn't dm this user, their dms may be closed**"
            except discord.HTTPException:
                dm_note = "**couldn't send the dm.**"

        try:
            await member.ban(reason=reason)
        except discord.Forbidden:
            await interaction.edit_original_response(
                view=ErrorUI("**i don't have permission to lynch this member.**")
            )
            return
        except discord.HTTPException:
            await interaction.edit_original_response(view=ErrorUI("**couldn't lynch this member.**"))
            return

        db_note = ""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES (?, ?, ?, ?)
                """,
                (str(interaction.guild.id), str(member.id), str(interaction.user.id),
                 f"{reason} (this action was a ban)")
            )
            conn.commit()
            conn.close()
        except Exception as e:
            db_note = f"\n\n**couldn't log this action: {e}**"

        action_ui.update_text(
            f"**lynched {member.mention}**\n\n**reason:** {reason}{dm_note}{db_note}"
        )
        await interaction.edit_original_response(view=action_ui)


    @mod.command(name="mute", description="mute a member")
    @app_commands.guild_only()
    @app_commands.describe(member="the member to mute", reason="why they're being muted", dm="whether to notify the member via dm (default: false)", duration="how long the mute is")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            reason: str,
            duration: str,
            dm: bool = False

    ):

        action_ui = ActionUI()
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        delta = parse_duration(duration)
        if delta is None:
            await interaction.edit_original_response(
                view=ErrorUI("**invalid duration format**")
            )
            return

        until = discord.utils.utcnow() + delta

        if delta > timedelta(days=28):
            await interaction.edit_original_response(
                view=ErrorUI("**timeout duration can't exceed 28 days.**")
            )
            return

        if member.id == interaction.user.id:
            await interaction.edit_original_response(view=ErrorUI("**you can't mute yourself.**"))
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.edit_original_response(
                view=ErrorUI("**you can't mute someone with an equal or higher role.**")
            )
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.edit_original_response(
                view=ErrorUI("**this user has a higher or equal role to the bot.**")
            )
            return

        dm_note = ""
        if dm:
            try:
                await member.send(
                    f"# you were muted in **{interaction.guild.name}**\n**reason:** {reason}"
                )
            except discord.Forbidden:
                dm_note = "**couldn't dm this user, their dms may be closed**"
            except discord.HTTPException:
                dm_note = "**couldn't send the dm.**"

        try:
            await member.timeout(until, reason=reason)
        except discord.Forbidden:
            await interaction.edit_original_response(
                view=ErrorUI("**i don't have permission to mute this member.**")
            )
            return
        except discord.HTTPException:
            await interaction.edit_original_response(view=ErrorUI("**couldn't mute this member.**"))
            return

        db_note = ""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES (?, ?, ?, ?)
                """,
                (str(interaction.guild.id), str(member.id), str(interaction.user.id),
                 f"{reason} (this action was a mute)")
            )
            conn.commit()
            conn.close()
        except Exception as e:
            db_note = f"\n\n**couldn't log this action: {e}**"

        action_ui.update_text(
            f"**muted {member.mention}**\n\n**reason:** {reason}{dm_note}{db_note}"
        )
        await interaction.edit_original_response(view=action_ui)


    @mod.command(name="unmute", description="unmute a member")
    @app_commands.guild_only()
    @app_commands.describe(member="the member to mute", reason="why they're being muted", dm="whether to notify the member via dm (default: false)",)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            reason: str,
            dm: bool = False

    ):

        action_ui = ActionUI()
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        if member.id == interaction.user.id:
            await interaction.edit_original_response(view=ErrorUI("**you can't unmute yourself.**"))
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.edit_original_response(
                view=ErrorUI("**you can't unmute someone with an equal or higher role.**")
            )
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.edit_original_response(
                view=ErrorUI("**this user has a higher or equal role to the bot.**")
            )
            return

        dm_note = ""
        if dm:
            try:
                await member.send(
                    f"# you were unmuted in **{interaction.guild.name}**\n**reason:** {reason}"
                )
            except discord.Forbidden:
                dm_note = "**couldn't dm this user, their dms may be closed**"
            except discord.HTTPException:
                dm_note = "**couldn't send the dm.**"

        try:
            await member.timeout(None, reason=reason)
        except discord.Forbidden:
            await interaction.edit_original_response(
                view=ErrorUI("**i don't have permission to unmute this member.**")
            )
            return
        except discord.HTTPException:
            await interaction.edit_original_response(view=ErrorUI("**couldn't unmute this member.**"))
            return


        action_ui.update_text(
            f"**unmuted {member.mention}**\n\n**reason:** {reason}{dm_note}"
        )
        await interaction.edit_original_response(view=action_ui)

    @unmute.error
    async def unmute_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "**you don't have permission to unmute members**"
        else:
            msg = f"**error, {error}. please [join the support server](https://discord.gg/PfyKM7dyx4) to report this issue.**"
        if interaction.response.is_done():
            await interaction.edit_original_response(view=ErrorUI(msg))
        else:
            await interaction.response.send_message(view=ErrorUI(msg), ephemeral=False)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        self.sniped_messages[message.channel.id] = {
            "author": message.author,
            "content": message.content or "*(no text content — attachment or embed)*",
            "timestamp": message.created_at,
        }

    @mod.command(name="snipe", description="see the last deleted message in this channel")
    @app_commands.describe(channel="the channel to snipe (defaults to this channel)")
    @app_commands.guild_only()
    async def snipe(
            self,
            interaction: discord.Interaction,
            channel: discord.TextChannel = None
    ):
        action_ui = ActionUI()
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        channel = channel or interaction.channel
        sniped = self.sniped_messages.get(channel.id)

        if sniped is None:
            action_ui.update_text(f"nothing to snipe in {channel.mention}.")
            await interaction.edit_original_response(view=action_ui)
            return

        action_ui.update_text(
            f"{sniped['author'].mention} "
            f"{discord.utils.format_dt(sniped['timestamp'], style='R')}\n"
            f"||{sniped['content']}||"
        )
        await interaction.edit_original_response(view=action_ui)

async def setup(bot):
    await bot.add_cog(Modcog(bot))