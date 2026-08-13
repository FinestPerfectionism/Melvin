import asyncio
import logging
import os

import aiodns
import discord
from discord.ext import commands
from dotenv import load_dotenv

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

    async def setup_hook(self) -> None:
        loop = asyncio.get_running_loop()
        loop.set_debug(True)
        try:
            resolver = aiodns.DNSResolver(nameservers=["1.1.1.1", "8.8.8.8"])
            bot.http._HTTPClient__session._connector._resolver._resolver = resolver
            log.info("successful resolve")
        except Exception as e:
            log.info(f"could not resolve {e}")
        log.info("logging started")

    async def on_ready(self) -> None:
        print(f"{bot.user}")
        await bot.tree.sync()


bot = Melvin()


@bot.tree.command(name="help", description="take a peek at melvins commands")
async def help_command(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    view = HelpView(bot)
    await interaction.followup.send(view=view)


async def main() -> None:
    load_dotenv()
    token = os.getenv("token")

    if not token:
        raise RuntimeError("Token is not set")

    async with bot:
        await bot.load_extension("cogs.info")
        await bot.load_extension("cogs.agent")
        await bot.load_extension("cogs.mod")
        await bot.load_extension("cogs.logging")
        await bot.load_extension("cogs.tool")
        await bot.load_extension("cogs.debug")
        await bot.load_extension("cogs.welcome")
        await bot.load_extension("cogs.private")
        await bot.load_extension("cogs.timezone")
        await bot.start(token)


asyncio.run(main())
