import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import asyncio
from discord import app_commands, Interaction
from discord.ext import commands
from discord import ui

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()

@bot.command(
    name='sync',
    description='Sync application (slash) commands globally.',
    usage='!sync',
    extras={"category": "Bot Utility", "levelPermissionNeeded": 5},
    enabled=True
)
@commands.is_owner()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("Synced commands globally.")

class VerificationView1(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(VerifyButton())
        self.add_item(UpdateRolesButton())

class VerifyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Verify via ROBLOX Login", style=discord.ButtonStyle.success)
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="BRITISH ARMY VERIFICATION SYSTEM V1",
            description=("Click on the button below to begin verification process\n\n"
                "**Please DO NOT share this link with anyone**\n\nThis link expires in **2 minutes** or once the verification process begins."),
            color=discord.Color.dark_blue(),
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, view=VerificationView2(), ephemeral=True)

class UpdateRolesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Update Roles", style=discord.ButtonStyle.success, disabled=True)

class VerificationView2(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BeginVerificationButton())

class BeginVerificationButton(discord.ui.Button):
    def __init__(self):
        from urllib.parse import urlencode
        redirect_uri = "https://fresh-royal-guard-production.up.railway.app/roblox/callback"
        params = {
            "client_id": "1186155268224623097",
            "response_type": "code",
            "scope": "openid profile",
            "redirect_uri": redirect_uri,
            "state": "discordverif"
        }
        url = f"https://authorize.roblox.com/oauth/authorize?{urlencode(params)}"
        super().__init__(label="Begin Verification", style=discord.ButtonStyle.link, url=url)
    async def callback(self, interaction: discord.Interaction):
        # No need to handle here as Discord handles link buttons automatically
        pass

@bot.command()
async def test(ctx):
    allowed_user_id = 1109257320413798561
    if ctx.author.id != allowed_user_id:
        embed = discord.Embed(
            title="Warning - Insufficient Permissions",
            description="This command is limited to the admin level of **Infinity**!",
            color=discord.Color.dark_gold(),
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return
    embed = discord.Embed(
        title="BRITISH ARMY VERIFICATION SYSTEM V1",
        description="Press the **Verify / Reverify** button to verify or reverify your ROBLOX account.",
        color=discord.Color.dark_blue(),
    )
    embed.set_author(name=bot.user.display_name, icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=embed, view=VerificationView1())

async def main():
    # Load all cogs in the cogs directory
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
