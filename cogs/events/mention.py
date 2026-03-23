from utils import getConfig 

import discord 

from discord.ext import commands 

from utils.Tools import get_ignore_data 

import aiosqlite 

class Mention (commands.Cog ):

    def __init__ (self,bot ):

        self.bot =bot 

        self.color =0x000000 

        self.bot_name ="4w7h"
        self.bot.loop.create_task (self.setup_database ())

    async def setup_database (self ):
        async with aiosqlite.connect ("db/block.db")as db:
            await db.execute ('''
                CREATE TABLE IF NOT EXISTS user_blacklist (
                    user_id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute ('''
                CREATE TABLE IF NOT EXISTS guild_blacklist (
                    guild_id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit ()

    async def is_blacklisted (self,message ):

        async with aiosqlite.connect ("db/block.db")as db:

            cursor =await db.execute ("SELECT 1 FROM guild_blacklist WHERE guild_id = ?",(message.guild.id,))

            if await cursor.fetchone ():

                return True 



            cursor =await db.execute ("SELECT 1 FROM user_blacklist WHERE user_id = ?",(message.author.id,))

            if await cursor.fetchone ():

                return True 

        return False 

    @commands.Cog.listener ()

    async def on_message (self,message ):

        if message.author.bot or not message.guild:

            return 

        if await self.is_blacklisted (message ):

            return 

        ignore_data =await get_ignore_data (message.guild.id )

        if str (message.author.id )in ignore_data ["user"]or str (message.channel.id )in ignore_data ["channel"]:

            return 

        if message.reference and message.reference.resolved:

            if isinstance (message.reference.resolved,discord.Message ):

                if message.reference.resolved.author.id ==self.bot.user.id:

                    return 

        guild_id =message.guild.id 

        data =await getConfig (guild_id )

        prefix =data ["prefix"]

        if self.bot.user in message.mentions:
            if len (message.content.strip ().split ())==1:

                from discord import ui

                view = ui.LayoutView()
                container = ui.Container(accent_color=None)

                allowed_cogs = {
                    'General', 'Voice', 'Welcome', 'AdvancedTicketSystem', 'StickyNotes',
                    'Automod', 'AntiNuke', 'Extra', 'Fun', 'Moderation', 'Giveaway',
                    'Leveling', 'AI', 'Guild', 'Roleplay', 'Verification',
                    'TrackingCog', 'Logging', 'Counting', 'Backup', 'Crew', 'Ignore'
                }
                total_commands = 0
                for cog in self.bot.cogs.values():
                    if cog.__class__.__name__ in allowed_cogs and hasattr(cog, 'help_custom'):
                        total_commands += len(cog.get_commands())
                
                content = (
                    f"### 👋 Hey [{message.author.display_name}](https://discord.com/users/{message.author.id})!\n"
                    f"I'm **4w7h**, your intelligent and friendly companion.\n"
                    f"> - **Server Prefix:** `{prefix}`\n"
                    f"> - **Total Commands:** `{total_commands}`\n"
                    f"> - **Developer:** [gt4realz_](https://discord.com/users/783953632974471178)\n"
                    f"> - **Owner:** [x12alt](https://discord.com/users/1430989005599805504)"
                )
                container.add_item(ui.TextDisplay(content))
                view.add_item(container)
                await message.channel.send (view=view)
"""
: ! Aegis !
    + Discord: itsfizys
"""
