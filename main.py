import asyncio
import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from errorhandling import report_error
from ui import HelpView

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(
    command_prefix="-",
    intents=intents,
    allowed_contexts=discord.app_commands.AppCommandContext(
        guild=True, dm_channel=True, private_channel=True,
    ),
    allowed_installs=discord.app_commands.AppInstallationType(
        guild=True, user=True,
    ),
)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    await report_error(
        bot, "app command error", error,
        context=f"**command, {interaction.command.qualified_name if interaction.command else 'unknown'}** | **user, {interaction.user}**"
    )

@bot.event
async def on_error(event_method, *args, **kwargs):
    import sys
    exc_type, exc_value, exc_tb = sys.exc_info()
    await report_error(bot, f"**listener error in {event_method}**", exc_value)

@bot.tree.command(name="help", description="take a peek at melvins commands")
async def help_command(interaction: discord.Interaction) -> None:
    view = HelpView(bot)
    await interaction.response.send_message(view=view)


@bot.event
async def on_ready() -> None:
    print(f"{bot.user}")


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
        await bot.start(token)


asyncio.run(main())
