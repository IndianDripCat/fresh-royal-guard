import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import motor.motor_asyncio
import random
import string
from urllib.parse import urlencode

# Load environment variables from .env file
load_dotenv()

# Create a new Discord client with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class VerifyButton(discord.ui.Button):    
    def __init__(self, bot, user_id, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot
        self.user_id = user_id
        self.verification_tokens = {}

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("This is not your verification!", ephemeral=True)
            
        if self.label == "Verify via ROBLOX Login":
            # Generate a random state token
            state = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            self.verification_tokens[interaction.user.id] = state
            
            # Create Roblox OAuth URL
            params = {
                'client_id': '5367039638538336991',  # You'll need to set this up in Roblox Creator Dashboard
                'redirect_uri': 'http://localhost:5000/auth/roblox/callback',   # Your redirect URI (must be configured in Roblox)
                'response_type': 'code',
                'scope': 'openid profile:read',
                'state': state
            }
            auth_url = f"https://authorize.roblox.com/?{urlencode(params)}"
            
            embed = discord.Embed(
                title="BRITISH ARMY VERIFICATION SYSTEM V1",
                description="Click on the button below to begin verification process\n\n**Please DO NOT share this link with anyone**\n\nThis link expires in **2 minutes** or once the verification process begins.",
                color=discord.Color.blue()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Begin Verification", url=auth_url, style=discord.ButtonStyle.gray))
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
            # Remove the token after 2 minutes
            await asyncio.sleep(120)
            if interaction.user.id in self.verification_tokens:
                del self.verification_tokens[interaction.user.id]
        
        elif self.label == "Update Roles":
            # Add your role update logic here
            await interaction.response.send_message("Role update functionality coming soon!", ephemeral=True)

class MyBot(commands.Bot):    
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            application_id=os.getenv('APPLICATION_ID')
        )
        self.initial_extensions = [
            'cogs.admins'
        ]
        
        # Initialize MongoDB
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        self.mongodb = motor.motor_asyncio.AsyncIOMotorClient(self.mongodb_uri)
        self.verification_tokens = {}
        
    async def is_owner(self, user):
        # Check if the user is the bot owner
        return user.id == self.owner_id
    
    async def setup_hook(self):
        # Load all extensions
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"Loaded extension: {extension}")
            except Exception as e:
                print(f"Failed to load extension {extension}: {e}")
        
        # Sync application commands
        await self.tree.sync()
        print("Commands synced!")

# Create bot instance
bot = MyBot()

@bot.command(name='test')
async def test(ctx):
    """Test command for bot owner"""
    # Check if the user is the bot owner
    if not await bot.is_owner(ctx.author):
        embed = discord.Embed(
            title="Warning - Insufficient Permissions",
            description="This command is limited to the admin level **Infinity**!",
            color=discord.Color.dark_gold()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        return
    
    # Create the verification embed
    embed = discord.Embed(
        title="BRITISH ARMY VERIFICATION SYSTEM V1",
        description="Press the **Verify / Reverify** button to verify or reverify your ROBLOX account.",
        color=discord.Color.green()
    )
    embed.set_author(name=bot.user.display_name, icon_url=bot.user.display_avatar.url)
    
    # Create buttons
    view = discord.ui.View()
    view.add_item(VerifyButton(bot, ctx.author.id, label="Verify via ROBLOX Login", style=discord.ButtonStyle.green))
    view.add_item(VerifyButton(bot, ctx.author.id, label="Update Roles", style=discord.ButtonStyle.blurple))
    
    await ctx.send(embed=embed, view=view)

# Run the bot
if __name__ == "__main__":
    bot.owner_id = int(os.getenv('OWNER_ID', '0'))  # Set your Discord user ID in .env
    bot.run(os.getenv('DISCORD_TOKEN'))