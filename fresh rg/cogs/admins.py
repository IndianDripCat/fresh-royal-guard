import discord
from discord.ext import commands
from discord import app_commands
from typing import Union
import pymongo

class Admins(commands.Cog):    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.mongodb['atlantisfreshrg']
        self.admins = self.db['admins']
    
    async def get_admin_level(self, guild_id: int, target: Union[discord.Member, discord.Role]) -> int:
        # Check if the target is a role
        if isinstance(target, discord.Role):
            doc = await self.admins.find_one({"GuildID": guild_id, "RoleID": target.id})
        else:
            # First check for user-specific admin
            doc = await self.admins.find_one({"GuildID": guild_id, "UserID": target.id})
            
            # If no user-specific admin, check their roles
            if not doc and hasattr(target, 'roles'):
                role_ids = [role.id for role in target.roles]
                role_admin = await self.admins.find_one({
                    "GuildID": guild_id,
                    "RoleID": {"$in": role_ids}
                })
                if role_admin:
                    return role_admin['AdminLevel']
        
        return doc['AdminLevel'] if doc else 0

    @commands.hybrid_group(
        name='admins',
        description='Admin management commands',
        extras={"category": "Admins", "levelPermissionNeeded": 0},
        with_app_command=True
    )
    async def admins(self, ctx):
        """Admin management commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @admins.command(
        name='view',
        description='View server admins',
        usage="/admins view",
        extras={"category": "Admins", "levelPermissionNeeded": 0},
        enabled=True
    )
    async def view_admins(self, ctx):
        # Get all admins for this server
        cursor = self.admins.find({"GuildID": ctx.guild.id})
        admins = await cursor.to_list(length=None)
        
        if not admins:
            embed = discord.Embed(
                title="Warning - No admins found",
                description="The server you are trying to view has no admins found.",
                color=discord.Color.dark_gold()
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return
        
        # Organize admins by level
        levels = {}
        for admin in admins:
            level = admin['AdminLevel']
            if level not in levels:
                levels[level] = []
            
            guild = self.bot.get_guild(admin['GuildID'])
            if 'UserID' in admin:
                member = guild.get_member(admin['UserID'])
                if member:
                    levels[level].append(f"- {member.mention}")
            elif 'RoleID' in admin:
                role = guild.get_role(admin['RoleID'])
                if role:
                    levels[level].append(f"- {role.mention}")
        
        # Create embed
        embed = discord.Embed(
            title="Server Admins",
            description=f"Listing server level admins for the server {ctx.guild.name}",
            color=discord.Color.dark_blue()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        
        # Add fields for each admin level
        for level in sorted(levels.keys()):
            if levels[level]:  # Only add if there are admins at this level
                value = '\n'.join(levels[level])
                embed.add_field(
                    name=f"Admin Level {level}",
                    value=value or "No admins",
                    inline=True
                )
        
        await ctx.send(embed=embed)
    
    @admins.command(
        name='add',
        description='Add a new role to the level admin.',
        usage="/admins add {member_or_role} {admin_level}",
        extras={"category": "Admins", "levelPermissionNeeded": 5},
        enabled=True
    )
    @app_commands.describe(
        member_or_role="The member or role to make admin",
        admin_level="The admin level to assign"
    )
    async def add_admin(self, ctx, member_or_role: Union[discord.Member, discord.Role], admin_level: int):
        # Check if the user has permission (admin level 5)
        author_level = await self.get_admin_level(ctx.guild.id, ctx.author)
        if author_level < 5:
            embed = discord.Embed(
                title="Warning - Insufficient Permissions",
                description=f"The `add` option of this command is limited to the admin level **5** or higher!",
                color=discord.Color.dark_gold()
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return
        
        # Validate admin level (1-101)
        if admin_level < 1 or admin_level > 101:
            embed = discord.Embed(
                title="Warning - Invalid Admin Level",
                description="Admin level must be between 1 and 101.",
                color=discord.Color.dark_gold()
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return
        
        # Check if the target already has an admin level
        existing = await self.admins.find_one({
            "GuildID": ctx.guild.id,
            "$or": [
                {"UserID": member_or_role.id},
                {"RoleID": member_or_role.id}
            ]
        })
        
        if existing:
            embed = discord.Embed(
                title="Warning - Admin Level Found",
                description="This user or role already has an assigned admin level. Please delete using `/admins delete` and re-add it.",
                color=discord.Color.dark_gold()
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return
        
        # Add the admin
        admin_data = {
            "GuildID": ctx.guild.id,
            "AdminLevel": admin_level
        }
        
        if isinstance(member_or_role, discord.Member):
            admin_data["UserID"] = member_or_role.id
        else:  # It's a role
            admin_data["RoleID"] = member_or_role.id
        
        await self.admins.insert_one(admin_data)
        
        embed = discord.Embed(
            title="Admin Level Added",
            description=f"Successfully added level admin {admin_level} to {member_or_role.mention}",
            color=discord.Color.dark_blue()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
    
    @admins.command(
        name='delete',
        description='Remove an admin',
        usage="/admins delete @user_or_role",
        extras={"category": "Admins", "levelPermissionNeeded": 5},
        enabled=True
    )
    @app_commands.describe(
        member_or_role="The member or role to remove admin from"
    )
    async def delete_admin(self, ctx, member_or_role: Union[discord.Member, discord.Role]):
        # Check if the user has permission (admin level 5)
        author_level = await self.get_admin_level(ctx.guild.id, ctx.author)
        if author_level < 5:
            embed = discord.Embed(
                title="Warning - Insufficient Permissions",
                description="The `delete` option of this command is limited to the admin level **5** or higher!",
                color=discord.Color.dark_gold()
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return
        
        # Find and remove the admin
        query = {
            "GuildID": ctx.guild.id,
            "$or": [
                {"UserID": member_or_role.id},
                {"RoleID": member_or_role.id}
            ]
        }
        
        result = await self.admins.delete_one(query)
        
        if result.deleted_count == 0:
            embed = discord.Embed(
                title="Warning - Admin Level Not Found",
                description="This user or role does not have an assigned admin level.",
                color=discord.Color.dark_gold()
            )
        else:
            embed = discord.Embed(
                title="Admin Level Removed",
                description=f"Successfully removed admin level from {member_or_role.mention}",
                color=discord.Color.dark_blue()
            )
        
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admins(bot))
