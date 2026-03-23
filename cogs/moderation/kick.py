import discord 
from discord.ext import commands 
from discord import ui 
from utils.Tools import *

class KickView (ui.View ):
    def __init__ (self,member ):
        super ().__init__ (timeout =120 )
        self.member =member 
        self.message =None 

    async def interaction_check (self,interaction:discord.Interaction )->bool:
        return True 

    async def on_timeout (self ):
        for item in self.children:
            item.disabled =True 
        if self.message:
            try:
                await self.message.edit (view =self )
            except Exception as e:
                pass 

    @ui.button (style =discord.ButtonStyle.gray,emoji ="<:delete:1372988987836469450>")
    async def delete (self,interaction:discord.Interaction,button:discord.ui.Button ):
        await interaction.message.delete ()

class Kick (commands.Cog ):
    def __init__ (self,bot ):
        self.bot =bot 
        self.color =discord.Color.from_rgb (0,0,0 )

    @commands.hybrid_command (
    name ="kick",
    help ="Kicks a member from the server.",
    usage ="kick <member> [reason]",
    aliases =["kickmember"])
    @blacklist_check ()
    @ignore_check ()
    @top_check ()
    @commands.has_permissions (kick_members =True )
    @commands.bot_has_permissions (kick_members =True )
    @commands.guild_only ()
    async def kick_command (self,ctx,member:discord.Member,*,reason:str =None ):
        reason =reason or "No reason provided"

        if member ==ctx.author:
            return await ctx.reply_v2 (
                title="Error",
                content="You cannot kick yourself."
            )

        if member ==ctx.bot.user:
            return await ctx.reply_v2 (
                title="Error",
                content="You cannot kick me."
            )

        if not ctx.author ==ctx.guild.owner:
            if member ==ctx.guild.owner:
                return await ctx.reply_v2 (
                    title="Error",
                    content="I cannot kick the server owner."
                )

            if ctx.author.top_role <=member.top_role:
                return await ctx.reply_v2 (
                    title="Error",
                    content="You cannot kick a member with a higher or equal role."
                )

        if ctx.guild.me.top_role <=member.top_role:
            return await ctx.reply_v2 (
                title="Error",
                content="I cannot kick a member with a higher or equal role."
            )

        if member not in ctx.guild.members:
            await ctx.reply_v2 (
                title="Member Not Found",
                content="The specified member does not exist in this server."
            )
            return 


        dm_status ="Yes"
        try:
            await member.send (f"You have been kicked from **{ctx.guild.name}**.Reason: {reason}")
        except discord.Forbidden:
            dm_status ="No"
        except discord.HTTPException:
            dm_status ="No"


        await member.kick (reason =f"Kicked by {ctx.author} | Reason: {reason}")



        await ctx.reply_v2(
            title=f"Successfully Kicked {member.name}",
            content=(
                f"**Target User:** [{member}](https://discord.com/users/{member.id})\n"
                f"**User Mention:** {member.mention}\n"
                f"**Reason:** {reason}\n"
                f"**DM Sent:** {dm_status}\n\n"
                f"**Moderator:** {ctx.author.mention}"
            ),
            thumbnail=member.avatar.url if member.avatar else member.default_avatar.url
        )
