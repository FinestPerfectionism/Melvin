import os
import time
import discord
from discord import app_commands
from discord.ext import commands
from globals import PRIMARY, MELVIN_EMOJI
from ui import ErrorUI, ResponseUI, SmallSeparator
from google import genai
from google.genai import types

primary = f"{PRIMARY}"


class AgentCog(
    commands.GroupCog,
    name="ai",
    description="self explanatory, ask a free AI model some stupid shit",
):
    def __init__(self, bot) -> None:
        self.bot = bot
        # Initialize Google GenAI client using GAPI environment variable
        self.api_key = os.getenv("GAPI")
        self.client = genai.Client(api_key=self.api_key)

    #cogwide error logging
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            msg = "**you're being rate limited.**"
        else:
            msg = f"**something went wrong: {error}**"

        error_ui = ErrorUI(msg)
        if interaction.response.is_done():
            await interaction.followup.send(view=error_ui, ephemeral=True)
        else:
            await interaction.response.send_message(view=error_ui, ephemeral=True)


    async def query_gemini(self, prompt: str) -> str:
        system_instruction = (
            "Try to keep responses tidy, brief, and minimal to stay within Discord's 4000 character limit. "
            "Contain responses in short, yet informative paragraphs, rather than graphs or tables. "
            "Refrain from using emojis unless told to."
        )

        config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.7)

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-3.1-flash-lite", contents=prompt, config=config,
            )

            if response.text:
                return response.text
            else:
                raise RuntimeError("**Gemini returned an empty response.**")

        except Exception as e:
            raise RuntimeError(f"**Gemini API Error, {str(e)}**")

    @app_commands.command(name="ask", description="ask a free AI model some stupid shit")
    @app_commands.checks.cooldown(2, 60)
    async def ask(self, interaction: discord.Interaction, prompt: str) -> None:
        view = ResponseUI()
        await interaction.response.send_message(view=view)
        try:
            start = time.time()
            ai_response = await self.query_gemini(prompt)
            elapsed = time.time() - start

            model_button = discord.ui.Button(label="model", style=discord.ButtonStyle.link, url="https://aistudio.google.com/")
            prompt_section = discord.ui.Section(f"# **prompt:** {prompt}", accessory=model_button)
            response_display = discord.ui.TextDisplay(
                content=f"{ai_response}\n\n"
                        f"-# **{MELVIN_EMOJI} responses may be shortened due to discord UI limitations. took {elapsed:.1f}s**"
            )
            view.container.clear_items()
            view.container.add_item(prompt_section)
            view.container.add_item(SmallSeparator())
            view.container.add_item(response_display)
            await interaction.edit_original_response(view=view)
        except Exception as e:
            print(e)
            await interaction.edit_original_response(view=ErrorUI(str(e)))


async def setup(bot) -> None:
    await bot.add_cog(AgentCog(bot))