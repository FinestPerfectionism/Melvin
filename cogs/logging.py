from globals import PRIMARY, SECONDARY, TERTIARY
from ui import ErrorUI, NegativeLoggingClass, PositiveLoggingClass, MiscLoggingClass
import discord
import sqlite3
from discord.ext import commands
from discord import app_commands

#globals (will likely duplicate)
primary = f"{PRIMARY}"
secondary = f"{SECONDARY}" #green
tertiary = f"{TERTIARY}" #red


class LoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "logging.db"

    async def cog_load(self):
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

    log = app_commands.Group(name="log", description="logging config", guild_only=True)

    # app commands will eventually go here
    @log.command(name="channel", description="set the channel for server logs")
    @app_commands.describe(channel="the channel to send logs to")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def channel(
            self,
            interaction: discord.Interaction,
            channel: discord.TextChannel
    ):
        action_ui = MiscLoggingClass()
        action_ui.text_display.content = "<:melvin:1535077942739206214> **thinking...**"
        await interaction.response.send_message(view=action_ui, ephemeral=False)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO log_channels (guild_id, channel_id)
                VALUES (?, ?)
                """,
                (str(interaction.guild.id), str(channel.id))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            error_ui = NegativeLoggingClass()
            error_ui.text_display.content = f"# error\n\ndatabase error: `{e}`"
            await interaction.edit_original_response(view=error_ui)
            return

        action_ui.text_display.content = f"logging channel set to {channel.mention}"
        await interaction.edit_original_response(view=action_ui)

    @channel.error
    async def channel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "you don't have permission to do this."
        elif isinstance(error, app_commands.NoPrivateMessage):
            msg = "this command can only be used in a server."
        else:
            msg = f"something went wrong: `{error}`"

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
                (str(guild_id),)
            )
            row = cursor.fetchone()
            conn.close()
        except Exception:
            return None

        if row is None:
            return None

        return self.bot.get_channel(int(row[0]))

    #events will eventually go here

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
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
    async def on_member_remove(self, member: discord.Member):
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
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content:
            return

        log_channel = await self.get_log_channel(before.guild.id)
        if log_channel is None:
            return
        def trunc(text: str, limit: int = 500) -> str:
            return text if len(text) <= limit else text[:limit] + "…"

        view = MiscLoggingClass()
        view.text_display.content = f"**{before.author}** edited a message in {before.channel.mention}\n**before:** {trunc(before.content)}\n**after:** {trunc(after.content)}"

        jump_button = discord.ui.Button(label="jump to", style=discord.ButtonStyle.link, url=after.jump_url)
        view.container.add_item(discord.ui.ActionRow(jump_button))

        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        if msg.author.bot:
            return
        log_channel = await self.get_log_channel(msg.guild.id)
        if log_channel is None:
            return

        def trunc(text: str, limit: int = 500) -> str:
            return text if len(text) <= limit else text[:limit] + "…"

        view = NegativeLoggingClass()
        view.text_display.content = f"message sent by **{msg.author}** in {msg.channel.mention} was deleted.**\n{trunc(msg.content)}**"

        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
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
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.guild is None:
            return
        log_channel = await self.get_log_channel(before.guild.id)
        if log_channel is None:
            return

        changes = []

        if before.nick != after.nick:
            old_nick = before.nick or before.name
            new_nick = after.nick or after.name
            changes.append(f"**nickname:** {old_nick} to {new_nick}")

        if before.roles != after.roles:
            before_roles = set(before.roles)
            after_roles = set(after.roles)
            added = after_roles - before_roles
            removed = before_roles - after_roles
            if added:
                changes.append(f"**roles added:** {', '.join(r.mention for r in added)}")
            if removed:
                changes.append(f"**roles removed:** {', '.join(r.mention for r in removed)}")

        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until is not None:
                changes.append(f"**timed out until:** {discord.utils.format_dt(after.timed_out_until, style='f')}")
            else:
                changes.append("**timeout removed**")

        if not changes:
            return

        view = MiscLoggingClass()
        view.text_display.content = f"**{after}** was updated\n" + "\n".join(changes)
        view.container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(media=after.display_avatar.url)))
        try:
            await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
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
                changes.append(f"**username:** {before.name} to {after.name}")
            if before.global_name != after.global_name:
                changes.append(
                    f"**display name:** {before.global_name or before.name} to {after.global_name or after.name}")
            if before.avatar != after.avatar:
                changes.append("**avatar changed**")

            if not changes:
                continue

            view = MiscLoggingClass()
            view.text_display.content = f"**{after}** updated their profile\n" + "\n".join(changes)
            view.container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(media=after.display_avatar.url)))
            try:
                await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
            except (discord.Forbidden, discord.HTTPException):
                pass

async def setup(bot):
    await bot.add_cog(LoggingCog(bot))