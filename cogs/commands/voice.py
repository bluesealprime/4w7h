import discord 
from discord.ext import commands 
from discord.utils import get 
import os 
import aiosqlite 
import asyncio
from utils.Tools import *
from typing import Optional,Union 
from core import Context 
from utils import Paginator,DescriptionEmbedPaginator,FieldPagePaginator,TextPaginator 
from utils import *


class Voice (commands.Cog ):

    def __init__ (self,bot ):
        self.bot =bot 
        self.color =0x000000 
        self.db_path = "db/vc247.db"
        self.bot.loop.create_task(self.initialize_247())

    async def initialize_247(self):
        """Initial connection check for 24/7 VCs"""
        await self.bot.wait_until_ready()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS vc247 (
                        guild_id INTEGER PRIMARY KEY,
                        channel_id INTEGER
                    )
                """)
                await db.commit()
                async with db.execute("SELECT guild_id, channel_id FROM vc247") as cursor:
                    rows = await cursor.fetchall()
                    for guild_id, channel_id in rows:
                        guild = self.bot.get_guild(guild_id)
                        if guild:
                            channel = guild.get_channel(channel_id)
                            if channel and isinstance(channel, discord.VoiceChannel):
                                try:
                                    if not guild.voice_client:
                                        await channel.connect()
                                except Exception as e:
                                    print(f"Failed to connect to 24/7 VC in {guild.name}: {e}")
        except Exception as e:
            print(f"Database error in initialize_247: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Ensure bot stays in 24/7 VC"""
        if member.id != self.bot.user.id:
            return

        if after.channel is None: # Bot disconnected
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT channel_id FROM vc247 WHERE guild_id = ?", (member.guild.id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        channel_id = row[0]
                        channel = member.guild.get_channel(channel_id)
                        if channel and isinstance(channel, discord.VoiceChannel):
                            try:
                                await channel.connect()
                            except:
                                pass


    @commands.group (name ="voice",invoke_without_command =True,aliases =['vc'])
    @blacklist_check ()
    @ignore_check ()
    async def vc (self,ctx:Context ):
        if ctx.subcommand_passed is None:
            await ctx.send_help (ctx.command )
            ctx.command.reset_cooldown (ctx )

    @vc.command (name ="kick",
    help ="Removes a user from the voice channel.",
    usage ="voice kick <member>")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (administrator =True )
    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _kick (self,ctx,*,member:discord.Member ):
        # Safeguard
        if member.id in self.bot.owner_ids:
            return await ctx.reply_v2("You cannot use this command against my owner or developer!", title="Access Denied")

        if member.voice is None:
            return await ctx.reply_v2(f"{str(member)} is not connected to any voice channel", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        ch =member.voice.channel.mention 
        await member.edit (voice_channel =None,
        reason =f"Disconnected by {str(ctx.author)}")
        return await ctx.reply_v2(f"{str(member)} has been disconnected from {ch}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="kickall",
    help ="Disconnect all members from the voice channel.",
    usage ="voice kick all")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (administrator =True )


    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _kickall (self,ctx ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any voice channels.", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        count =0 
        ch =ctx.author.voice.channel.mention 
        for member in ctx.author.voice.channel.members:
            if member.id not in self.bot.owner_ids:
                await member.edit (
                voice_channel =None,
                reason =f"Disconnect All Command Executed By: {str(ctx.author)}")
                count +=1 
        return await ctx.reply_v2(f"Disconnected {count} members from {ch}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="mute",
    help ="mute a member in voice channel.",
    usage ="voice mute <member>")
    @commands.has_guild_permissions (mute_members =True )
    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _mute (self,ctx,*,member:discord.Member =None ):
        if member is None:
            return await ctx.reply_v2("You need to mention a member to mute.", title="Error")

        # Safeguard
        if member.id in self.bot.owner_ids:
            return await ctx.reply_v2("You cannot use this command against my owner or developer!", title="Access Denied")

        if member.voice is None:
            return await ctx.reply_v2(f"{str(member)} is not connected to any voice channels.", title="Error")

        if member.voice.mute:
            return await ctx.reply_v2(f"{str(member)} is already muted in the voice channel.", title="Information")

        await member.edit (mute =True )
        return await ctx.reply_v2(f"{str(member)} has been muted in {member.voice.channel.mention}.", title="<:icon_tick:1372375089668161597> Success")

    @vc.command (name ="unmute",
    help ="Unmute a member in the voice channel.",
    usage ="voice unmute <member>")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_guild_permissions (mute_members =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def vcunmute (self,ctx,*,member:discord.Member ):
        # Safeguard
        if member.id in self.bot.owner_ids:
            return await ctx.reply_v2("You cannot use this command against my owner or developer!", title="Access Denied")

        if member.voice is None:
            return await ctx.reply_v2(f"{str(member)} is not connected to any voice channel.", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        if member.voice.mute ==False:
            return await ctx.reply_v2(f"{str(member)} is already unmuted in the voice channel.", title="Information", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        ch =member.voice.channel.mention 
        await member.edit (mute =False,reason =f"Unmuted by {str(ctx.author)}")
        return await ctx.reply_v2(f"{str(member)} has been unmuted in {ch}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="muteall",
    help ="Mute all members in a voice channel.",
    usage ="voice muteall")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (administrator =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _muteall (self,ctx ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any voice channel.", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        count =0 
        ch =ctx.author.voice.channel.mention 
        for member in ctx.author.voice.channel.members:
            if member.id not in self.bot.owner_ids and member.voice.mute ==False:
                await member.edit (
                    mute =True,
                    reason = f"voice muteall Command Executed by {str(ctx.author)}"
                )
                count +=1 
        return await ctx.reply_v2(f"Muted {count} members in {ch}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="unmuteall",
    help ="Unmute all members in a voice channel.",
    usage ="voice unmuteall")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (administrator =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _unmuteall (self,ctx ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any of the voice channel", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        count =0 
        ch =ctx.author.voice.channel.mention 
        for member in ctx.author.voice.channel.members:
            if member.voice.mute ==True:
                await member.edit (
                    mute =False,
                    reason = f"Voice unmuteall Command Executed by: {str(ctx.author)}"
                )
                count +=1 
        return await ctx.reply_v2(f"Unmuted {count} members in {ch}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="deafen",
    help ="Deafen a user in a voice channel.",
    usage ="voice deafen <member>")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_guild_permissions (deafen_members =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _deafen (self,ctx,*,member:discord.Member ):
        # Safeguard
        if member.id in self.bot.owner_ids:
            return await ctx.reply_v2("You cannot use this command against my owner or developer!", title="Access Denied")

        if member.voice is None:
            return await ctx.reply_v2(f"{str(member)} is not connected to any of the voice channel", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        if member.voice.deaf ==True:
            return await ctx.reply_v2(f"{str(member)} is already deafened in the voice channel", title="Information", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        ch =member.voice.channel.mention 
        await member.edit (deafen =True,reason =f"Deafen by {str(ctx.author)}")
        return await ctx.reply_v2(f"{str(member)} has been Deafened in {ch}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="undeafen",
    help ="Undeafen a User in a voice channel.",
    usage ="voice undeafen <member>")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_guild_permissions (deafen_members =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _undeafen (self,ctx,*,member:discord.Member ):
        # Safeguard
        if member.id in self.bot.owner_ids:
            return await ctx.reply_v2("You cannot use this command against my owner or developer!", title="Access Denied")

        if member.voice is None:
            return await ctx.reply_v2(f"{str(member)} is not connected to any of the voice channel", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        if member.voice.deaf ==False:
            return await ctx.reply_v2(f"{str(member)} is already undeafened in the voice channel", title="Information", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        ch =member.voice.channel.mention 
        await member.edit (deafen =False, reason =f"Undeafen by {str(ctx.author)}")
        return await ctx.reply_v2(f"{str(member)} has been undeafened in {ch}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="deafenall",
    help ="Deafen all Ussr in a voice channel.",
    usage ="voice deafenall")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (administrator =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _deafenall (self,ctx ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any of the voice channel", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        count =0 
        ch =ctx.author.voice.channel.mention 
        for member in ctx.author.voice.channel.members:
            if member.id not in self.bot.owner_ids and member.voice.deaf ==False:
                await member.edit (
                    deafen =True,
                    reason = f"voice deafenall Command Executed by {str(ctx.author)}"
                )
                count +=1 
        return await ctx.reply_v2(f"Deafened {count} members in {ch}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="undeafenall",
    help ="undeafen all member in a voice channel.",
    usage ="voice undeafenall")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (administrator =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _undeafall (self,ctx ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected in any of the voice channel", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        count =0 
        ch =ctx.author.voice.channel.mention 
        for member in ctx.author.voice.channel.members:
            if member.voice.deaf ==True:
                await member.edit (
                deafen =False,
                reason =
                f"Voice undeafenall Command Executed by: {str(ctx.author)}")
                count +=1 
        return await ctx.reply_v2(f"Undeafened {count} members in {ch}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="moveall",
    help ="Move all members from the voice channel to the specified voice channel.",
    usage ="voice moveall <voice channel>")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (administrator =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _moveall (self,ctx,*,channel:discord.VoiceChannel ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any of the voice channel", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        try:
            ch =ctx.author.voice.channel.mention 
            nch =channel.mention 
            count =0 
            for member in ctx.author.voice.channel.members:
                await member.edit (
                voice_channel =channel,
                reason =
                f"voice moveall Command Executed by: {str(ctx.author)}")
                count +=1 
            return await ctx.reply_v2(f"{count} Members moved from {ch} to {nch}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
        except:
            return await ctx.reply_v2("Invalid Voice channel provided", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")



    @vc.command (name ="pullall",
    help ="Move all members of ALL voice channels to a specified voice channel.",
    usage ="voice pullall <channel>")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (administrator =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _pullall (self,ctx,*,channel:discord.VoiceChannel ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any of the voice channel", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        count =0 
        for vc in ctx.guild.voice_channels:
            for member in vc.members:
                if member !=ctx.author:
                    try:
                        await member.edit (
                        voice_channel =channel,
                        reason =f"Pullall Command Executed by: {str(ctx.author)}")
                        count +=1 
                    except:
                        pass 
        return await ctx.reply_v2(f"Moved {count} members to {channel.mention}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")


    @vc.command (name ="move",
    help ="Move a member from one voice channel to another.",
    usage ="voice move <member> <channel>")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (administrator =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _move (self,ctx,member:discord.Member,channel:discord.VoiceChannel ):
        if member.voice is None:
            return await ctx.reply_v2(f"{str(member)} is not connected to any voice channel.", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        if channel ==member.voice.channel:
            return await ctx.reply_v2(f"{str(member)} is already in {channel.mention}.", title="Information", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        await member.edit (voice_channel =channel,
        reason =f"Moved by {str(ctx.author)}")
        return await ctx.reply_v2(f"{str(member)} has been moved to {channel.mention}", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")


    @vc.command (name ="pull",
    help ="Pull a member from one voice channel to yours.",
    usage ="voice pull <member>")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (administrator =True )

    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _pull (self,ctx,member:discord.Member ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any voice channel.", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        if member.voice is None:
            return await ctx.reply_v2(f"{str(member)} is not connected to any voice channel.", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        if member.voice.channel ==ctx.author.voice.channel:
            return await ctx.reply_v2(f"{str(member)} is already in your voice channel.", title="Information", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        await member.edit (voice_channel =ctx.author.voice.channel,
        reason =f"Pulled by {str(ctx.author)}")
        return await ctx.reply_v2(f"{str(member)} has been pulled to your voice channel.", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="lock",
    help ="Locks the voice channel so no one can join.",
    usage ="voice lock")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (manage_roles =True )
    @commands.bot_has_permissions (manage_roles =True )
    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _lock (self,ctx ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any voice channel.", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        ch =ctx.author.voice.channel.mention 
        await ctx.author.voice.channel.set_permissions (ctx.guild.default_role,
        connect =False,
        reason =f"Locked by {str(ctx.author)}")
        return await ctx.reply_v2(f"{ch} has been locked.", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="unlock",
    help ="Unlocks the voice channel so anyone can join.",
    usage ="voice unlock")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (manage_roles =True )
    @commands.bot_has_permissions (manage_roles =True )
    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _unlock (self,ctx ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any voice channel.", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        ch =ctx.author.voice.channel.mention 
        await ctx.author.voice.channel.set_permissions (ctx.guild.default_role,
        connect =True,
        reason =f"Unlocked by {str(ctx.author)}")
        return await ctx.reply_v2(f"{ch} has been unlocked.", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="private",
    help ="Makes the voice channel private.",
    usage ="voice private")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (manage_roles =True )
    @commands.bot_has_permissions (manage_roles =True )
    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _private (self,ctx ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any voice channel.", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        ch =ctx.author.voice.channel.mention 
        await ctx.author.voice.channel.set_permissions (ctx.guild.default_role,
        connect =False,
        view_channel =False,
        reason =f"Made private by {str(ctx.author)}")
        return await ctx.reply_v2(f"{ch} has been made private.", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @vc.command (name ="unprivate",
    help ="Makes the voice channel public.",
    usage ="voice unprivate")
    @blacklist_check ()
    @ignore_check ()
    @commands.has_permissions (manage_roles =True )
    @commands.bot_has_permissions (manage_roles =True )
    @commands.cooldown (1,10,commands.BucketType.user )
    @commands.max_concurrency (1,per =commands.BucketType.default,wait =False )
    async def _unprivate (self,ctx ):
        if ctx.author.voice is None:
            return await ctx.reply_v2("You are not connected to any voice channel.", title="Error", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")
            
        ch =ctx.author.voice.channel.mention 
        await ctx.author.voice.channel.set_permissions (ctx.guild.default_role,
        connect =True,
        view_channel =True,
        reason =f"Made public by {str(ctx.author)}")
        return await ctx.reply_v2(f"{ch} has been made public.", title="<:icon_tick:1372375089668161597> Success", thumbnail="https://cdn.discordapp.com/emojis/1279464563150032991.png")

    @commands.group(name="247", invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _247(self, ctx: Context):
        """Manage 24/7 Voice Channel feature."""
        from utils.logger import logger
        logger.info("CMD", f"247 group invoked with subcommand: {ctx.invoked_subcommand}")
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @_247.command(name="enable", aliases=["on"])
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _247_enable(self, ctx: Context):
        """Enable 24/7 mode in your current voice channel."""
        if not ctx.author.voice:
            return await ctx.reply_v2("You must be connected to a voice channel to enable 24/7 mode.", title="Voice Required")
        
        channel = ctx.author.voice.channel
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT channel_id FROM vc247 WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return await ctx.reply_v2("24/7 mode is already enabled for this server.", title="Information")

        loading_msg = await ctx.reply_v2(f"Enabling 24/7 mode in {channel.mention}...", title="Wait a moment")
        
        try:
            # Connect bot to channel if not already there
            if not ctx.voice_client:
                await channel.connect()
            elif ctx.voice_client.channel != channel:
                await ctx.voice_client.move_to(channel)
            
            # Save to DB
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("INSERT OR REPLACE INTO vc247 (guild_id, channel_id) VALUES (?, ?)", (ctx.guild.id, channel.id))
                await db.commit()
            
            return await ctx.edit_v2(loading_msg, f"24/7 mode has been **Enabled**. Bot will now stay in {channel.mention} indefinitely.", title="<:icon_tick:1372375089668161597> Success")
        except Exception as e:
            return await ctx.edit_v2(loading_msg, f"An error occurred while enabling 24/7 mode: {e}", title="Error")

    @_247.command(name="disable", aliases=["off"])
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _247_disable(self, ctx: Context):
        """Disable 24/7 mode and allow bot to leave when empty."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT channel_id FROM vc247 WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return await ctx.reply_v2("24/7 mode is not enabled for this server.", title="Information")
        
        loading_msg = await ctx.reply_v2("Disabling 24/7 mode...", title="Wait a moment")
        
        try:
            # Remove from DB
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM vc247 WHERE guild_id = ?", (ctx.guild.id,))
                await db.commit()
            
            return await ctx.edit_v2(loading_msg, "24/7 mode has been **Disabled**. The bot will no longer stay in the voice channel permanently.", title="<:icon_tick:1372375089668161597> Success")
        except Exception as e:
            return await ctx.edit_v2(loading_msg, f"An error occurred while disabling 24/7 mode: {e}", title="Error")
