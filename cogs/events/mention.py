from utils import getConfig 

import discord 

from discord.ext import commands 

import aiosqlite 
from utils.Tools import get_ignore_data, get_total_commands
from discord import ui

class Mention (commands.Cog ):

    def __init__ (self,bot ):

        self.bot =bot 

        self.color =0x000000 

        self.bot_name ="acp.xz"
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
                view = ui.LayoutView()
                container = ui.Container(accent_color=None)

                total_commands = get_total_commands(self.bot)
                
                content = (
                    f"###  Hey [{message.author.display_name}](https://discord.com/users/{message.author.id})!\n"
                    f"I'm **acp.xz**, your intelligent and friendly companion.\n"
                    f"> - **Server Prefix:** `{prefix}`\n"
                    f"> - **Total Commands:** `{total_commands}`\n"
                    f"> - **Developer:** [gt4realz_](https://discord.com/users/783953632974471178)\n"
                    f"> - **Owner:** [x12alt](https://discord.com/users/1430989005599805504)"
                )
                container.add_item(ui.TextDisplay(content))
                view.add_item(container)
                await message.channel.send (view=view)
        
        # New Tag Notification Feature
        if not message.author.bot and message.guild:
            # Avoid duplicate notifications for same user in one message
            unique_mentions = set(message.mentions)
            for member in unique_mentions:
                if member.bot or member.id == message.author.id:
                    continue
                
                try:
                    view = ui.LayoutView()
                    container = ui.Container(accent_color=None)
                    
                    container.add_item(ui.TextDisplay(f"### Tagged in : {message.guild.name}"))
                    container.add_item(ui.Separator())
                    
                    notification_text = (
                        f"### Notification\n"
                        f"You were tagged in **{message.guild.name}**!\n\n"
                        f"**Tagged by :** {message.author.mention}\n\n"
                        f"**Channel :** {message.channel.mention}\n"
                        f"**Message :**\n"
                        f"> {message.content[:1000] if message.content else '*No message content*'}"
                    )
                    
                    author_avatar = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
                    container.add_item(ui.Section(
                        ui.TextDisplay(notification_text),
                        accessory=ui.Thumbnail(author_avatar)
                    ))
                    
                    view.add_item(container)
                    await member.send(view=view)
                except discord.Forbidden:
                    pass
                except Exception as e:
                    # Log other errors but don't crash
                    from utils.logger import logger
                    logger.error("MENTION", f"Failed to send tag DM to {member}: {e}")
"""
: ! Aegis !
    + Discord: itsfizys
"""
