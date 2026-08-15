import asyncio
import logging
import os

import aiodns
import discord
from discord.ext import commands
from dotenv import load_dotenv

from globals import DisplayNameEffect, DisplayNameFont
from ui import HelpView

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

log = logging.getLogger(__name__)


class Melvin(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix="-",
            intents=intents,
            allowed_contexts=discord.app_commands.AppCommandContext(
                guild=True,
                dm_channel=True,
                private_channel=True,
            ),
            allowed_installs=discord.app_commands.AppInstallationType(
                guild=True,
                user=True,
            ),
        )

    async def set_name_style(
        self,
        *,
        guild: discord.Guild,
        font_id: DisplayNameFont,
        effect_id: DisplayNameEffect,
        colors: list[str],
    ) -> None:
        color_integers = [int(hex_code, 16) for hex_code in colors]

        await self.http.request(
            route=discord.http.Route("PATCH", "/guilds/{guild_id}/members/@me", guild_id=guild.id),
            json={
              "display_name_font_id": font_id.value,
              "display_name_effect_id": effect_id.value,
              "display_name_colors": color_integers,
            },
        )

    async def reset_name_style(self, *, guild: discord.Guild) -> None:
        await self.set_name_style(
            guild=guild,
            font_id=DisplayNameFont.default,
            effect_id=DisplayNameEffect.solid,
            colors=["FFFFFF", "FFFFFF"],
        )

    async def setup_hook(self) -> None:
        loop = asyncio.get_running_loop()
        loop.set_debug(True)
        try:
            resolver = aiodns.DNSResolver(nameservers=["1.1.1.1", "8.8.8.8"])
            self.http._HTTPClient__session._connector._resolver._resolver = resolver
            log.info("DNS resolver successfully configured.")
        except Exception as e:
            log.info(f"Could not configure DNS resolver: {e}.")
        log.info("Logging started.")

    async def on_ready(self) -> None:
        log.info(f"Logged in as {self.user}.")
        await self.tree.sync()


bot = Melvin()


@bot.tree.command(name="help", description="Take a peek at Melvin's commands.")
async def help_command(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    view = HelpView(bot)
    await interaction.followup.send(view=view)


async def main() -> None:
    load_dotenv()
    token = os.getenv("token")

    if not token:
        raise RuntimeError("Token is not set.")

    async with bot:
        await bot.load_extension("cogs.info")
        await bot.load_extension("cogs.agent")
        await bot.load_extension("cogs.mod")
        await bot.load_extension("cogs.audit")
        await bot.load_extension("cogs.tool")
        await bot.load_extension("cogs.debug")
        await bot.load_extension("cogs.welcome")
        await bot.load_extension("cogs.private")
        await bot.load_extension("cogs.timezone")
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
