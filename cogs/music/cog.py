import discord
import lavalink
from discord.ext import commands
from discord import ui, app_commands
import asyncio
import aiosqlite
import aiohttp
import re
import logging
import random
from typing import Optional, Any
from core import Context
from core.Cog import Cog
from utils.logger import logger
from utils.config import LAVALINK_HOST, LAVALINK_PORT, LAVALINK_PASSWORD, LAVALINK_SECURE

logging.getLogger('lavalink').setLevel(logging.DEBUG)

EMOJIS = {
    "music": "<:white_musicnote:1430654046657843266>",
    "playing": "<a:playing:1430654136067817595>",
    "nowplaying": "<a:playing:1430654136067817595>",
    "pause": "<:Pause:1428686772665057386>",
    "resume": "<:resume:1430652690433835139>",
    "play": "<:resume:1430652690433835139>",
    "skip": "<:skip:1430652403543183536>",
    "stop": "<:stop:1430652594484678887>",
    "queue": "<:queue:1430772894337728603>",
    "loop": "<:loop:1430652241941102672>",
    "shuffle": "<:white_shuffle:1430775358499717172>",
    "filter": "<:filter:1430653471366840683>",
    "lyrics": "<:lyrics:1430651691899949268>",
    "favorite": "<:favourite:1430652904183693383>",
    "autoplay": "<:AwxLMusicautoplay:1430652085996884210>",
}

url_rx = re.compile(r'https?://(?:www\.)?.+')

class LavalinkVoiceClient(discord.VoiceProtocol):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        super().__init__(client, channel)
        self.client = client
        self.bot = client
        self.channel = channel
        self._lavalink = client.lavalink

    async def on_voice_server_update(self, data):
        await self._lavalink.voice_update_handler({'t': 'VOICE_SERVER_UPDATE', 'd': data})

    async def on_voice_state_update(self, data):
        await self._lavalink.voice_update_handler({'t': 'VOICE_STATE_UPDATE', 'd': data})

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        await self.guild.change_voice_state(channel=self.channel, self_deaf=self_deaf, self_mute=self_mute)

    async def disconnect(self, *, force: bool = False) -> None:
        player = self._lavalink.player_manager.get(self.guild.id)
        if not force and not (player and player.is_connected): return
        await self.guild.change_voice_state(channel=None)
        if player: player.channel_id = None
        self.cleanup()

class Music(Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(
                LAVALINK_HOST, int(LAVALINK_PORT), LAVALINK_PASSWORD, 'us', 'default-node', ssl=LAVALINK_SECURE
            )

        self.lavalink = bot.lavalink
        self.lavalink.add_event_hook(self.event_handler)

    @commands.Cog.listener()
    async def on_socket_response(self, data):
        if data.get('t') in ['VOICE_SERVER_UPDATE', 'VOICE_STATE_UPDATE']:
            await self.lavalink.voice_update_handler(data)

    def cog_unload(self):
        self.lavalink._event_hooks.clear()

    async def event_handler(self, event):
        try:
            if isinstance(event, lavalink.events.NodeConnectedEvent):
                logger.success("MUSIC", f"Lavalink Node connected: {event.node.name}")
            elif isinstance(event, lavalink.events.TrackStartEvent):
                await self.on_track_start(event)
            elif isinstance(event, lavalink.events.TrackEndEvent):
                await self.on_track_end(event)
            elif isinstance(event, lavalink.events.TrackExceptionEvent):
                logger.error("MUSIC", f"Track exception: {event.exception}")
        except Exception as e: logger.error("MUSIC", f"Event handler error: {e}")

    async def on_track_start(self, event):
        try:
            player = event.player
            text_channel_id = player.fetch('text_channel_id')
            if not text_channel_id: return
            text_channel = self.bot.get_channel(text_channel_id)
            if not text_channel: return
            old_msg = player.fetch('np_msg')
            if old_msg:
                try: await old_msg.delete()
                except: pass
            view = await self.get_music_view(player, event.track)
            msg = await text_channel.send(view=view)
            player.store('np_msg', msg)
        except Exception as e: logger.error("MUSIC", f"Track start error: {e}")

    async def on_track_end(self, event):
        player = event.player
        if not player.queue:
            if player.fetch('autoplay_enabled'):
                await self.handle_autoplay(player)
            else:
                # Return to 24/7 VC if enabled
                try:
                    async with aiosqlite.connect("db/vc247.db") as db:
                        async with db.execute("SELECT channel_id FROM vc247 WHERE guild_id = ?", (player.guild_id,)) as cursor:
                            row = await cursor.fetchone()
                            if row:
                                home_channel_id = row[0]
                                if int(player.channel_id) != home_channel_id:
                                    guild = self.bot.get_guild(player.guild_id)
                                    home_channel = guild.get_channel(home_channel_id)
                                    if home_channel:
                                        await guild.change_voice_state(channel=home_channel, self_deaf=True)
                                        logger.info("MUSIC", f"Returning to 24/7 VC in {guild.name}")
                except Exception as e:
                    logger.error("MUSIC", f"Error returning to 24/7 VC: {e}")

    async def handle_autoplay(self, player):
        last_track = getattr(player, 'current', None)
        if not last_track: return
        query = f"ytsearch:{last_track.author}"
        results = await self.lavalink.get_tracks(query)
        if results and results.tracks:
            for track in results.tracks:
                if track.identifier != last_track.identifier:
                    player.add(requester=0, track=track)
                    if not player.is_playing: await player.play()
                    break

    async def get_music_view(self, player: lavalink.BasePlayer, track: lavalink.AudioTrack):
        container = ui.Container(accent_color=None)
        nowPlayingText = f"## {EMOJIS['nowplaying']} Now Playing... \n[{track.title}]({track.uri}) \n\n"
        container.add_item(ui.TextDisplay(nowPlayingText))
        container.add_item(ui.Separator(spacing=ui.SeparatorSpacingSize.Small, divider=True))
        
        row1 = ui.ActionRow(
            ui.Button(emoji=EMOJIS['pause'] if not player.paused else EMOJIS['play'], style=discord.ButtonStyle.secondary, custom_id="music_pause_resume"),
            ui.Button(emoji=EMOJIS['skip'], style=discord.ButtonStyle.secondary, custom_id="music_skip"),
            ui.Button(emoji=EMOJIS['stop'], style=discord.ButtonStyle.secondary, custom_id="music_stop"),
            ui.Button(emoji=EMOJIS['loop'], style=discord.ButtonStyle.secondary, custom_id="music_loop"),
            ui.Button(emoji=EMOJIS['autoplay'], style=discord.ButtonStyle.primary if player.fetch('autoplay_enabled') else discord.ButtonStyle.secondary, custom_id="music_autoplay")
        )
        container.add_item(row1)
        
        row2 = ui.ActionRow(
            ui.Button(emoji=EMOJIS['lyrics'], style=discord.ButtonStyle.secondary, custom_id="music_lyrics"),
            ui.Button(emoji=EMOJIS['queue'], style=discord.ButtonStyle.secondary, custom_id="music_queue"),
            ui.Button(emoji=EMOJIS['shuffle'], style=discord.ButtonStyle.secondary, custom_id="music_shuffle"),
            ui.Button(emoji=EMOJIS['filter'], style=discord.ButtonStyle.secondary, custom_id="music_filter"),
            ui.Button(emoji=EMOJIS['favorite'], style=discord.ButtonStyle.secondary, custom_id="music_favorite_add")
        )
        container.add_item(row2)
        container.add_item(ui.Separator(spacing=ui.SeparatorSpacingSize.Small, divider=True))
        
        view = ui.LayoutView(); view.add_item(container)
        async def interaction_handler(interaction: discord.Interaction):
            if interaction.user.id not in self.bot.owner_ids and (not interaction.user.voice or interaction.user.voice.channel.id != int(player.channel_id)):
                return await interaction.response.send_message("Join my VC!", ephemeral=True)
            cid = interaction.data['custom_id']
            if cid == "music_pause_resume":
                await player.set_pause(not player.paused)
                await interaction.response.send_message(f"Music {'paused' if player.paused else 'resumed'}.", ephemeral=True)
            elif cid == "music_skip":
                await player.skip()
                await interaction.response.send_message("Skipped track.", ephemeral=True)
            elif cid == "music_stop":
                player.queue.clear()
                await player.stop()
                if interaction.guild.voice_client:
                    await interaction.guild.voice_client.disconnect(force=True)
                await interaction.response.send_message("Stopped music.", ephemeral=True)
            elif cid == "music_loop":
                if player.loop == 0: player.set_loop(1); msg = "Loop Track enabled."
                elif player.loop == 1: player.set_loop(2); msg = "Loop Queue enabled."
                else: player.set_loop(0); msg = "Loop disabled."
                await interaction.response.send_message(msg, ephemeral=True)
            elif cid == "music_autoplay":
                current = player.fetch('autoplay_enabled'); player.store('autoplay_enabled', not current)
                await interaction.response.send_message(f"Autoplay {'enabled' if not current else 'disabled'}.", ephemeral=True)
            elif cid == "music_lyrics":
                await interaction.response.defer(ephemeral=True)
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://lrclib.net/api/search?q={track.title}") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data and data[0].get('plainLyrics'):
                                return await interaction.followup.send(f"## Lyrics for {track.title}\n{data[0]['plainLyrics'][:1500]}...")
                await interaction.followup.send("Lyrics not found.")
            elif cid == "music_queue":
                if not player.queue: return await interaction.response.send_message("Queue is empty!", ephemeral=True)
                q_text = "\n".join([f"**{i+1}.** {t.title}" for i, t in enumerate(player.queue[:10])])
                await interaction.response.send_message(f"## Current Queue\n{q_text}", ephemeral=True)
            elif cid == "music_shuffle":
                random.shuffle(player.queue)
                await interaction.response.send_message("Queue shuffled.", ephemeral=True)
            elif cid == "music_filter": await interaction.response.send_message("Filters coming soon...", ephemeral=True)
            elif cid == "music_favorite_add":
                async with aiosqlite.connect("db/bot_database.db") as db:
                    await db.execute("INSERT OR IGNORE INTO music_favorites (user_id, identifier, title, author, uri) VALUES (?, ?, ?, ?, ?)",
                                     (interaction.user.id, track.identifier, track.title, track.author, track.uri)); await db.commit()
                await interaction.response.send_message(f"Added **{track.title}** to favorites.", ephemeral=True)
        view.interaction_handler = interaction_handler; return view

    @commands.hybrid_command(name="play", aliases=["p"])
    async def play(self, ctx: Context, *, query: str):
        """Play music in your voice channel"""
        if not ctx.author.voice: return await ctx.reply_v2("Join a voice channel first!", title="VOICE REQUIRED")
        
        player = self.lavalink.player_manager.get(ctx.guild.id) or self.lavalink.player_manager.create(ctx.guild.id)
        
        # Connect or move if not in the same channel
        if not ctx.voice_client or ctx.voice_client.channel.id != ctx.author.voice.channel.id:
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient, self_deaf=True)
            
        # Always update text channel for controls
        player.store('text_channel_id', ctx.channel.id)
        
        query = query.strip('<>')
        if not url_rx.match(query): query = f'ytsearch:{query}'
        results = await self.lavalink.get_tracks(query)
        if not results or not results.tracks: return await ctx.reply_v2("Nothing found!", title="ERROR")
        
        track = results.tracks[0]
        player.add(requester=ctx.author.id, track=track)
        await ctx.reply_v2(f"Added **{track.title}** to queue.", title="TRACK ADDED")
        if not player.is_playing: await player.play()

    @commands.hybrid_command(name="stop", aliases=["dc"])
    async def stop(self, ctx: Context):
        """Stop and disconnect"""
        player = self.lavalink.player_manager.get(ctx.guild.id)
        if player: player.queue.clear(); await player.stop()
        if ctx.voice_client: await ctx.voice_client.disconnect(force=True)
        await ctx.reply_v2("Stopped and disconnected.", title="STOPPED")

    @commands.is_owner()
    @commands.command(name="nodes")
    async def nodes(self, ctx: Context):
        """Check Lavalink node status"""
        nodes = self.lavalink.node_manager.nodes
        if not nodes: return await ctx.send("No nodes connected.")
        msg = ""
        for node in nodes:
            msg += f"**{node.name}**: {'Connected' if node.available else 'Disconnected'}\n"
        await ctx.reply_v2(msg, title="LAVALINK NODES")

async def setup(bot): await bot.add_cog(Music(bot))
