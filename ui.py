#ui classes go here!
from globals import PRIMARY, SECONDARY, TERTIARY, MELVIN_EMOJI
import discord

primary = f"{PRIMARY}"
secondary = f"{SECONDARY}"  # green
tertiary = f"{TERTIARY}"    # red
message = '**raw ErrorUI class, debug purposes**'

class ThinkingText(discord.ui.TextDisplay):
    def __init__(self):
        super().__init__(
            content=f"{MELVIN_EMOJI} **Thinking...**",
        )

class SmallSeparator(discord.ui.Separator):
    def __init__(self):
        super().__init__(
            visible=True,
            spacing=discord.SeparatorSpacing.small,
        )

#ErrorUI
class ErrorUI(discord.ui.LayoutView):
    def __init__(self, message: str):
        super().__init__()

        text_display = discord.ui.TextDisplay(
            content=f"# error\n\n{message}"
        )

        container = discord.ui.Container(
            text_display,
            SmallSeparator(),
            accent_color=discord.Color.red()
        )

        self.container = container
        self.add_item(container)


#ResponseUI
class ResponseUI(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()
        self.text_display = ThinkingText()
        
        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
        )
        self.container = container
        self.add_item(container)


#AdUI
class AdUI(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()
        self.text_display = discord.ui.TextDisplay(
            content=f"**Melvin**<:melvin:1535077942739206214> <:melvincanary:1535408831578898432> Melvin is an app built around **Discord.py**. it features various **user and server facing commands**, functional as a user & server app.it's currently in an **open beta state**, with core moderation commands, a bunch of **user utilities**, **speaking utilities**, **encoding and decoding** + so much more.Melvin is super new to the app space, and support is **super appreciated**, feel free to check it out. **[add Melvin](<https://discord.com/oauth2/authorize?client_id=1468362201197973756>)**"
        )
        media_gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(media='https://files.catbox.moe/oj885f.png')
        )
        adbutton = discord.ui.Button(
            label="support server",
            style=discord.ButtonStyle.link,
            url="https://discord.gg/XejfDTA6QK"
        )
        addbutton = discord.ui.Button(
            label="add melvin",
            style=discord.ButtonStyle.link,
            url="https://discord.com/oauth2/authorize?client_id=1468362201197973756"
        )
        action_row = discord.ui.ActionRow(adbutton, addbutton)
        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            media_gallery,
            action_row,
        )
        self.container = container
        self.add_item(container)


#ActionUI
class ActionUI(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()

        self.text_display = ThinkingText()

        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            accent_color=discord.Color.from_str(primary)
        )

        self.container = container
        self.add_item(container)

    def update_text(self, new_content: str):
        self.text_display.content = new_content


#LoggingClassUI
class MiscLoggingClass(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()

        self.text_display = ThinkingText()

        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            accent_color=discord.Color.from_str(primary)
        )

        self.container = container
        self.add_item(container)


class NegativeLoggingClass(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()

        self.text_display = ThinkingText()

        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            accent_color=discord.Color.from_str(tertiary)
        )

        self.container = container
        self.add_item(container)


class PositiveLoggingClass(discord.ui.LayoutView):
    def __init__(self):
        super().__init__()

        self.text_display = ThinkingText()

        container = discord.ui.Container(
            self.text_display,
            SmallSeparator(),
            accent_color=discord.Color.from_str(secondary)
        )

        self.container = container
        self.add_item(container)
