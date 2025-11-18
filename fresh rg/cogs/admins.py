import discord
from discord.ext import commands
from discord import app_commands
import os
import pymongo
from pymongo import MongoClient

class Admins(commands.Cog):
    admins_group = app_commands.Group(name="admins", description="Admin management commands")

    def __init__(self, bot):
        self.bot = bot
        mongo_url = os.getenv("MONGO_URL") or "mongodb://localhost:27017/"
        self.client = MongoClient(mongo_url)
        self.db = self.client["atlantisfreshrg"]
        self.admins_collection = self.db["admins"]

    def _get_user_admin_level(self, guild_id, user_id):
        item = self.admins_collection.find_one({"guild_id": guild_id, "user_or_role_id": user_id})
        return item["AdminLevel"] if item else 0

    @admins_group.command(name="view", description="View all server admins")
    @app_commands.guild_only()
    async def admins_view(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        admins = list(self.admins_collection.find({"guild_id": guild_id}))
        author = interaction.user
        if not admins:
            embed = discord.Embed(
                title="Warning - No admins found",
                description="The server you are trying to view has no admins found.",
                color=discord.Color.dark_gold()
            )
            embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
        else:
            levels = {}
            for entry in admins:
                lvl = entry["AdminLevel"]
                if lvl not in levels:
                    levels[lvl] = []
                levels[lvl].append(entry["user_or_role_name"])
            embed = discord.Embed(
                title="Server Admins",
                description=f"Listing server level admins for the server {interaction.guild.name}",
                color=discord.Color.dark_blue()
            )
            embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
            for lvl in sorted(levels.keys()):
                if len(levels[lvl]) > 0:
                    embed.add_field(
                        name=f"Admin Level {lvl}",
                        value="\n".join(f"- {entry}" for entry in levels[lvl]),
                        inline=True
                    )
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @admins_group.command(name="add", description="Add admin user or role")
    @app_commands.describe(member_or_role="Select a member", admin_level="Admin level to assign")
    @app_commands.guild_only()
    async def admins_add(self, interaction: discord.Interaction, member_or_role: discord.Member, admin_level: int):
        guild_id = interaction.guild.id
        author = interaction.user
        required_level = 5
        user_level = self._get_user_admin_level(guild_id, author.id)
        coll = self.admins_collection
        exists = coll.find_one({"guild_id": guild_id, "user_or_role_id": member_or_role.id})
        if user_level < required_level:
            embed = discord.Embed(
                title="Warning - Insufficient Permissions",
                description=f"The member option of this command is limited to the admin level **{required_level}**!",
                color=discord.Color.dark_gold()
            )
        elif exists:
            embed = discord.Embed(
                title="Warning - Admin Level Found",
                description="This user or role already has an assigned level admin. Please delete using /admins delete and re-add it.",
                color=discord.Color.dark_gold()
            )
        else:
            coll.insert_one({
                "guild_id": guild_id,
                "user_or_role_id": member_or_role.id,
                "user_or_role_name": member_or_role.mention,
                "AdminLevel": admin_level
            })
            embed = discord.Embed(
                title="Admin Level Added",
                description=f"Successfully added level admin {admin_level} to {member_or_role.mention}",
                color=discord.Color.dark_blue()
            )
        embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admins_group.command(name="delete", description="Remove admin user or role")
    @app_commands.describe(member_or_role="Select a member to remove")
    @app_commands.guild_only()
    async def admins_delete(self, interaction: discord.Interaction, member_or_role: discord.Member):
        guild_id = interaction.guild.id
        author = interaction.user
        required_level = 5
        user_level = self._get_user_admin_level(guild_id, author.id)
        coll = self.admins_collection
        item = coll.find_one({"guild_id": guild_id, "user_or_role_id": member_or_role.id})
        if user_level < required_level:
            embed = discord.Embed(
                title="Warning - Insufficient Permissions",
                description=f"The delete option of this command is limited to the admin level **{required_level}**!",
                color=discord.Color.dark_gold()
            )
        elif not item:
            embed = discord.Embed(
                title="Warning - Admin Level Not Found",
                description="This user or role does not have an assigned level admin, if you wish to change it, please add using /admins add.",
                color=discord.Color.dark_gold()
            )
        else:
            coll.delete_one({"guild_id": guild_id, "user_or_role_id": member_or_role.id})
            embed = discord.Embed(
                title="Admin Level Removed",
                description=f"Successfully removed level admin {item['AdminLevel']} to {member_or_role.mention}",
                color=discord.Color.dark_blue()
            )
        embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admins(bot))
