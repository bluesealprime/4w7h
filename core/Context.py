from __future__ import annotations 

from discord.ext import commands 
import discord 
import functools 
from typing import Optional,Any 
import asyncio 

__all__ =("Context",)


class Context (commands.Context ):

    def __init__ (self,*args,**kwargs )->None:
        super ().__init__ (*args,**kwargs )

    def __repr__ (self ):
        return "<core.Context>"

    @property 
    async def session (self ):
        return self.bot.session 

    @discord.utils.cached_property 
    def replied_reference (self )->Optional [discord.Message ]:
        ref =self.message.reference 
        if ref and isinstance (ref.resolved,discord.Message ):
            return ref.resolved.to_reference ()
        return None 

    def with_type (func ):

        @functools.wraps (func )
        async def wrapped (self,*args,**kwargs ):
            context =args [0 ]if isinstance (args [0 ],
            commands.Context )else args [1 ]
            try:
                async with context.typing ():
                    await func (*args,**kwargs )
            except discord.Forbidden:
                await func (*args,**kwargs )

        return wrapped 

    async def show_help(self, command: Any = None) -> Any:
        """Shows help for a specific command or group."""
        if command is None:
            command = self.command
        
        # If it's a string, try to find the command
        if isinstance(command, str):
            command = self.bot.get_command(command)
            
        return await super().send_help(command)

    async def send_help(self, command: Any = None) -> Any:
        """Shows help for a specific command or group."""
        return await self.show_help(command)

    async def send (self,
    content:Optional [str ]=None,
    **kwargs )->Optional [discord.Message ]:
        if not (self.channel.permissions_for (self.me )).send_messages:
            try:
                await self.author.send (
                "Bot doesn't have permission to send messages in that channel.")
            except discord.Forbidden:
                pass 
            return 
        try:
            return await super ().send (content,**kwargs )
        except discord.HTTPException:

            return None 

    async def reply (self,
    content:Optional [str ]=None,
    **kwargs )->Optional [discord.Message ]:
        if not (self.channel.permissions_for (self.me )).send_messages:
            try:
                await self.author.send (
                "Bot doesn't have permission to send messages in that channel.")
            except discord.Forbidden:
                pass 
            return 
        try:
            return await super ().reply (content,**kwargs )
        except discord.HTTPException:

            return None 

    async def reply_v2(self, content: str, title: str = None, thumbnail: str = None, accent_color: int = None, **kwargs):
        from discord import ui
        view = ui.LayoutView()
        container = ui.Container(accent_color=accent_color)
        
        if title:
            container.add_item(ui.TextDisplay(f"# {title}"))
            container.add_item(ui.Separator())
            
        if thumbnail:
            container.add_item(ui.Section(
                ui.TextDisplay(content),
                accessory=ui.Thumbnail(thumbnail)
            ))
        else:
            container.add_item(ui.TextDisplay(content))
            
        # Add "Requested by"
        footer_content = f"Requested by: {self.author.name}"
        footer_avatar = self.author.avatar.url if self.author.avatar else self.author.default_avatar.url
        
        container.add_item(ui.Separator())
        container.add_item(ui.Section(
            ui.TextDisplay(footer_content),
            accessory=ui.Thumbnail(footer_avatar)
        ))
        
        view.add_item(container)
        return await self.reply(view=view, **kwargs)

    async def send_v2(self, content: str, title: str = None, thumbnail: str = None, accent_color: int = None, **kwargs):
        from discord import ui
        view = ui.LayoutView()
        container = ui.Container(accent_color=accent_color)
        
        if title:
            container.add_item(ui.TextDisplay(f"# {title}"))
            container.add_item(ui.Separator())
            
        if thumbnail:
            container.add_item(ui.Section(
                ui.TextDisplay(content),
                accessory=ui.Thumbnail(thumbnail)
            ))
        else:
            container.add_item(ui.TextDisplay(content))
            
        # Add "Requested by"
        footer_content = f"Requested by: {self.author.name}"
        footer_avatar = self.author.avatar.url if self.author.avatar else self.author.default_avatar.url
        
        container.add_item(ui.Separator())
        container.add_item(ui.Section(
            ui.TextDisplay(footer_content),
            accessory=ui.Thumbnail(footer_avatar)
        ))
        
        view.add_item(container)
        return await self.send(view=view, **kwargs)

    async def edit_v2(self, message: discord.Message, content: str, title: str = None, thumbnail: str = None, accent_color: int = None, **kwargs):
        from discord import ui
        view = ui.LayoutView()
        container = ui.Container(accent_color=accent_color)
        
        if title:
            container.add_item(ui.TextDisplay(f"# {title}"))
            container.add_item(ui.Separator())
            
        if thumbnail:
            container.add_item(ui.Section(
                ui.TextDisplay(content),
                accessory=ui.Thumbnail(thumbnail)
            ))
        else:
            container.add_item(ui.TextDisplay(content))
            
        # Add "Requested by"
        footer_content = f"Requested by: {self.author.name}"
        footer_avatar = self.author.avatar.url if self.author.avatar else self.author.default_avatar.url
        
        container.add_item(ui.Separator())
        container.add_item(ui.Section(
            ui.TextDisplay(footer_content),
            accessory=ui.Thumbnail(footer_avatar)
        ))
        
        view.add_item(container)
        return await message.edit(view=view, **kwargs)

    async def release (self,delay:Optional [int ]=None )->None:
        delay =delay or 0 
        await asyncio.sleep (delay )
