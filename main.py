import os
import discord
import asyncio
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
from discord.ext import commands
bot = commands.Bot(
    command_prefix="-",
    intents=intents,
    allowed_contexts=discord.app_commands.AppCommandContext(
        guild=True, dm_channel=True, private_channel=True
    ),
    allowed_installs=discord.app_commands.AppInstallationType(
        guild=True, user=True
    ),
)

load_dotenv()
token = os.getenv('token')

@bot.event
async def on_ready():
    print(f"{bot.user}")
    await  bot.tree.sync()
    print("bot.tree.sync()")


async def main():
    async with bot:
        await bot.load_extension("cogs.util")
        await bot.load_extension("cogs.agent")
        await bot.load_extension("cogs.mod")
        await bot.load_extension("cogs.logging")
        await bot.load_extension("cogs.tool")
        await bot.load_extension("cogs.debug")
        await bot.load_extension("cogs.welcome")
        await bot.load_extension("cogs.private")
        await bot.start(token)



asyncio.run(main())