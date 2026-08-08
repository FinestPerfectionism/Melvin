import sqlite3

import discord
from discord import app_commands
from discord.ext import commands

from ui import (
    ErrorUI,
    LargeSeparator,
    MiscLoggingClass,
    NegativeLoggingClass,
    PositiveLoggingClass,
    primary,
    tertiary,
)


@app_commands.guild_only
class LoggingCog(
    commands.GroupCog,
    name="log",
    description="logging config",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_path = "logging.db"

    def clean_and_truncate(self, text: str, length: int = 500) -> str:
        return discord.utils.escape_markdown(
            (text)[:length - 3] + "..." if len(text) > length else text,
        )

    def format_attachments(self, attachments: list[discord.Attachment]) -> str:
        return "\n".join(f"- {discord.utils.escape_markdown(f"{attachment.filename} | {attachment.url}")}" for attachment in attachments)

    def channel_display(self, channel: discord.abc.Messageable | discord.abc.GuildChannel) -> str:
        if isinstance(channel, discord.Thread):
            parent = channel.parent

            if isinstance(parent, discord.ForumChannel):
                return f"{parent.mention} -> {channel.mention} | {parent.id} -> {channel.mention}"
            if parent is not None:
                return f"{parent.mention} -> {channel.mention} | {parent.id} -> {channel.mention}"

            return channel.mention

        if isinstance(channel, discord.TextChannel):
            return f"{channel.mention} | {channel.id}"

        return "Unknown Channel"

    async def cog_load(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log_channels (
                guild_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    # app commands will eventually go here
    @app_commands.command(name="channel", description="set the channel for server logs")
    @app_commands.describe(channel="the channel to send logs to")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        if not interaction.guild:
            return

        action_ui = MiscLoggingClass()
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO log_channels (guild_id, channel_id)
                VALUES (?, ?)
                """,
                (str(interaction.guild.id), str(channel.id)),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            error_ui = NegativeLoggingClass()
            error_ui.text_display.content = f"**database error, {e}. please [join the support server](https://discord.gg/PfyKM7dyx4) to report this issue.**"
            await interaction.edit_original_response(view=error_ui)
            return

        action_ui.text_display.content = f"logging channel set to {channel.mention}"
        await interaction.edit_original_response(view=action_ui)

    @channel.error
    async def channel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            msg = "**you don't have permission to do this.**"
        elif isinstance(error, app_commands.NoPrivateMessage):
            msg = "**this command can only be used in a server.**"
        else:
            msg = f"something went wrong, **{error}. please [join the support server](https://discord.gg/PfyKM7dyx4) to report this issue.**"

        error_ui = ErrorUI(msg)
        if interaction.response.is_done():
            await interaction.edit_original_response(view=error_ui)
        else:
            await interaction.response.send_message(view=error_ui, ephemeral=False)

    async def get_log_channel(self, guild_id: int) -> discord.TextChannel | None:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT channel_id FROM log_channels WHERE guild_id = ?",
                (str(guild_id),),
            )
            row = cursor.fetchone()
            conn.close()
        except Exception:
            return None

        if row is None:
            return None

        return self.bot.get_channel(int(row[0]))

    # events will eventually go here

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        log_channel = await self.get_log_channel(member.guild.id)
        if log_channel is None:
            return

        view = PositiveLoggingClass()
        view.text_display.content = f"**{member}** joined,\nmember #{member.guild.member_count}"
        view.container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(media=member.display_avatar.url)))

        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        log_channel = await self.get_log_channel(member.guild.id)
        if log_channel is None:
            return

        view = NegativeLoggingClass()
        view.text_display.content = f"**{member}** left the server."
        view.container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(media=member.display_avatar.url)))

        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.author.bot or before.content == after.content:
            return

        if not before.guild:
            return

        log_channel = await self.get_log_channel(before.guild.id)
        if log_channel is None:
            return

        container = discord.ui.Container(
            discord.ui.TextDisplay(f"# Message Edited | {discord.utils.format_dt(after.edited_at or discord.utils.utcnow(), style = "F")}"),
            discord.ui.Section(
                f"**Author:** {before.author.mention} | {before.author.id}\n"
                f"**Channel:** {self.channel_display(after.channel)}",
                accessory=discord.ui.Button(label="Jump to Message", style=discord.ButtonStyle.link, url=after.jump_url),
            ),
            accent_color=discord.Color.from_str(primary),
        )

        if after.attachments:
            container.add_item(
                LargeSeparator(),
            )
            container.add_item(
                discord.ui.TextDisplay(
                    "### Attachments\n"
                    f"{self.format_attachments(after.attachments)}",
                ),
            )

        container.add_item(
            LargeSeparator(),
        )
        container.add_item(
            discord.ui.TextDisplay(
                "### Before\n"
                f"{self.clean_and_truncate(before.content) or "[No content, likely an embed or attachment]"}",
            ),
        )
        container.add_item(
            discord.ui.TextDisplay(
                "### After\n"
                f"{self.clean_and_truncate(after.content) or "[No content, likely an embed or attachment]"}",
            ),
        )
        view = discord.ui.LayoutView()
        view.add_item(container)

        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message) -> None:
        if msg.author.bot:
            return
        if not msg.guild:
            return
        log_channel = await self.get_log_channel(msg.guild.id)
        if log_channel is None:
            return

        container = discord.ui.Container(
            discord.ui.TextDisplay(f"# Message Deleted | {discord.utils.format_dt(discord.utils.utcnow(), style = "F")}"),
            discord.ui.TextDisplay(
                f"**Author:** {msg.author.mention} | {msg.author.id}\n"
                f"**Channel:** {self.channel_display(msg.channel)}",
            ),
            accent_color=discord.Color.from_str(tertiary),
        )

        if msg.attachments:
            container.add_item(
                LargeSeparator(),
            )
            container.add_item(
                discord.ui.TextDisplay(
                    "### Attachments\n"
                    f"{self.format_attachments(msg.attachments)}",
                ),
            )

        container.add_item(
            LargeSeparator(),
        )
        container.add_item(
            discord.ui.TextDisplay(
                "### Content\n"
                f"{self.clean_and_truncate((msg.content) or "[No content, likely an embed or attachment]")}",
            ),
        )
        view = discord.ui.LayoutView()
        view.add_item(container)

        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        log_channel = await self.get_log_channel(member.guild.id)
        if log_channel is None:
            return

        # joined a voice channel
        if before.channel is None and after.channel is not None:
            view = PositiveLoggingClass()
            view.text_display.content = f"**{member}** joined voice channel **{after.channel.name}**"
            view.container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(media=member.display_avatar.url)))
            try:
                await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
            except (discord.Forbidden, discord.HTTPException):
                pass
            return

        # left a voice channel entirely
        if before.channel is not None and after.channel is None:
            view = NegativeLoggingClass()
            view.text_display.content = f"**{member}** left voice channel **{before.channel.name}**"
            view.container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(media=member.display_avatar.url)))
            try:
                await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
            except (discord.Forbidden, discord.HTTPException):
                pass
            return

        # moved between voice channels
        if before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            view = MiscLoggingClass()
            view.text_display.content = f"**{member}** moved from **{before.channel.name}** to **{after.channel.name}**"
            view.container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(media=member.display_avatar.url)))
            try:
                await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
            except (discord.Forbidden, discord.HTTPException):
                pass

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        log_channel = await self.get_log_channel(before.guild.id)
        if log_channel is None:
            return

        changes = []

        if before.nick != after.nick:
            old_nick = before.nick or before.name
            new_nick = after.nick or after.name
            changes.append(f"**Nickname:** {old_nick} | {new_nick}")

        if before.roles != after.roles:
            before_roles = set(before.roles)
            after_roles = set(after.roles)
            added = after_roles - before_roles
            removed = before_roles - after_roles
            if added:
                changes.append(f"**Roles added:** {', '.join(r.mention for r in added)}")
            if removed:
                changes.append(f"**Roles removed:** {', '.join(r.mention for r in removed)}")

        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until is not None:
                changes.append(f"**Timed out until:** {discord.utils.format_dt(after.timed_out_until, style='f')}")
            else:
                changes.append("**Timeout removed**")

        if not changes:
            return

        container = discord.ui.Container(
            discord.ui.TextDisplay(f"# Member Updated | {discord.utils.format_dt(discord.utils.utcnow(), style="F")}"),
            discord.ui.Section(
                f"**Member:** {after.mention} | {after.id}",
                accessory=discord.ui.Thumbnail(media=after.display_avatar.url),
            ),
            accent_color=discord.Color.from_str(primary),
        )

        changes_text = "\n".join(changes)
        container.add_item(
            LargeSeparator(),
        )
        container.add_item(
            discord.ui.TextDisplay(
                "### Changes\n"
                f"{changes_text}",
            ),
        )
        view = discord.ui.LayoutView()
        view.add_item(container)

        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User) -> None:
        if before.name == after.name and before.global_name == after.global_name and before.avatar == after.avatar:
            return

        for guild in self.bot.guilds:
            member = guild.get_member(after.id)
            if member is None:
                continue
            log_channel = await self.get_log_channel(guild.id)
            if log_channel is None:
                continue

            changes = []
            if before.name != after.name:
                changes.append(f"**Username:** {before.name} | {after.name}")
            if before.global_name != after.global_name:
                changes.append(
                    f"**Display name:** {before.global_name or before.name} | {after.global_name or after.name}")
            if before.avatar != after.avatar:
                changes.append("**Avatar changed**")

            if not changes:
                continue

            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    f"# Profile Updated | {discord.utils.format_dt(discord.utils.utcnow(), style="F")}"),
                discord.ui.Section(
                    f"**User:** {after.mention} | {after.id}",
                    accessory=discord.ui.Thumbnail(media=after.display_avatar.url),
                ),
                accent_color=discord.Color.from_str(primary),
            )

            changes_text = "\n".join(changes)
            container.add_item(
                LargeSeparator(),
            )
            container.add_item(
                discord.ui.TextDisplay(
                    "### Changes\n"
                    f"{changes_text}",
                ),
            )
            view = discord.ui.LayoutView()
            view.add_item(container)

            try:
                await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
            except (discord.Forbidden, discord.HTTPException):
                pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LoggingCog(bot))
