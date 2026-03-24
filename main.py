from dotenv import load_dotenv
load_dotenv()
import sys
import os
import asyncio
import traceback
import logging
import aiohttp
import discord
import aiosqlite
from typing import Optional, Any
from datetime import datetime, timezone, timedelta
from discord.ext import commands
from aiohttp import web

# Force Python to find local modules correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load local libraries cautiously for better IDE support
try:
    from core import Context, Yuna
    from utils.Tools import setup_db, updateAllGuildsPrefixFromEnv
    from utils.config import OWNER_IDS, DEV_IDS
    from utils.logger import logger
except Exception:
    # Fallback to prevent linter from crashing on whole file
    pass

# Try to load Jishaku for debugging
try:
    import jishaku
except ImportError:
    jishaku = None

# Jishaku / Global Bot Flags
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "False"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"

# Refresh environment variables
# load_dotenv() - Moved to top

# Logging setup (ensures logs directory exists)
_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(_log_path):
    os.makedirs(_log_path)

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(_log_path, 'discord.log')),
        logging.StreamHandler(sys.stdout)
    ]
)

# Silence noisy discord system logs
for lib_name in ['discord', 'discord.http', 'discord.gateway', 'discord.client']:
    logging.getLogger(lib_name).setLevel(logging.ERROR)

class DatabaseTestFilter(logging.Filter):
    def filter(self, record):
        return 'database connection test successful' not in record.getMessage().lower()

logging.getLogger().addFilter(DatabaseTestFilter())

def utc_to_ist(dt: datetime) -> datetime:
    ist_delta = timedelta(hours=5, minutes=30)
    return dt.replace(tzinfo=timezone.utc).astimezone(timezone(ist_delta))

# ---------------------------------------------------------
# Bot Definition (Rebranded To Support Team)
# ---------------------------------------------------------
class TicketBot(Yuna):
    def __init__(self):
        super().__init__()
        self.db: Any = None 
        self.web_app: Any = None

    async def handle_health(self, request):
        return web.Response(text="Bot is ALIVE and kicking!")

    async def setup_hook(self):
        """Initial startup operations and database sync"""
        logger.info("INIT", "Starting database synchronization...")
        try:
            # Sync global prefixes (utils/Tools.py)
            await setup_db()

            # Connection for main bot operational database
            self.db = await aiosqlite.connect("db/bot_database.db")
            
            # Application of prefix overrides from .env
            await updateAllGuildsPrefixFromEnv()
            
            # Setup core ticket tables
            if self.db:
                await self.db.execute("""
                    CREATE TABLE IF NOT EXISTS tickets (
                        guild_id INTEGER PRIMARY KEY,
                        channel_id INTEGER,
                        role_id INTEGER,
                        category_id INTEGER,
                        log_channel_id INTEGER,
                        ping_role_id INTEGER,
                        embed_title TEXT DEFAULT 'Create a Ticket',
                        embed_description TEXT DEFAULT 'Need assistance? Select a category below to create a ticket!',
                        embed_footer TEXT DEFAULT 'Powered by acp.xz',
                        embed_image_url TEXT,
                        embed_color INTEGER DEFAULT 16711680,
                        panel_type TEXT DEFAULT 'dropdown'
                    )
                """)

                # Table schema verification
                async with self.db.cursor() as cursor:
                    await cursor.execute("PRAGMA table_info(tickets)")
                    current_columns = [col[1] for col in await cursor.fetchall()]
                    if "panel_type" not in current_columns:
                        await cursor.execute("ALTER TABLE tickets ADD COLUMN panel_type TEXT DEFAULT 'dropdown'")
                    if "ping_role_id" not in current_columns:
                        await cursor.execute("ALTER TABLE tickets ADD COLUMN ping_role_id INTEGER")

                # Supporting tables (Blacklist, Tracking, etc)
                await self.db.execute("CREATE TABLE IF NOT EXISTS ticket_categories (guild_id INTEGER, category_name TEXT, PRIMARY KEY (guild_id, category_name))")
                await self.db.execute("CREATE TABLE IF NOT EXISTS ticket_panels (guild_id INTEGER, channel_id INTEGER, message_id INTEGER, PRIMARY KEY (guild_id, message_id))")
                await self.db.execute("CREATE TABLE IF NOT EXISTS guild_blacklist (guild_id INTEGER PRIMARY KEY, reason TEXT, blacklisted_at TEXT)")
                await self.db.execute("CREATE TABLE IF NOT EXISTS user_blacklist (user_id INTEGER PRIMARY KEY, reason TEXT, blacklisted_at TEXT)")
                await self.db.commit()
            
            logger.success("DB", "Database schema initialization complete.")

        except Exception as startup_err:
            logger.error("DB", f"Failed to setup database: {startup_err}")
            raise 

        # Load bot command modules
        logger.info("INIT", "Loading bot extensions...")
        try:
            if jishaku: 
                await self.load_extension("jishaku")
            await self.load_extension("cogs")
            logger.success("INIT", "Modules loaded successfully.")
        except Exception as load_err:
            logger.error("INIT", f"Extension loading error: {load_err}")
            raise 

        # Start Web Server for Render
        try:
            app = web.Application()
            app.router.add_get("/", self.handle_health)
            runner = web.AppRunner(app)
            await runner.setup()
            port = int(os.environ.get("PORT", "8080"))
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            logger.success("WEB", f"Health check server running on port {port}")
        except Exception as e:
            logger.error("WEB", f"Failed to start web server: {e}")

        # Global command tree sync
        logger.info("INIT", "Syncing application commands with Discord...")
        try:
            command_list = await self.tree.sync()
            logger.success("INIT", f"Sync complete: {len(command_list)} commands online.")
        except Exception as sync_err:
            logger.error("INIT", f"Application command sync failed: {sync_err}")
            raise

    async def close(self):
        """Clean shutdown of database and library resources"""
        try:
            if self.db:
                await self.db.close()
                logger.info("DB", "Main database connection closed.")
            
            # Cleanup of latent aiosqlite connection handles
            import gc 
            for active_obj in gc.get_objects():
                try:
                    if hasattr(active_obj, 'close') and 'aiosqlite' in str(type(active_obj)):
                        await active_obj.close()
                except: 
                    pass
        except Exception as close_err:
            logger.error("SHUTDOWN", f"Cleanup error detected: {close_err}")
        finally:
            await super().close()

# Bot client creation
bot = TicketBot()

# ---------------------------------------------------------
# Global Event Handlers
# ---------------------------------------------------------
@bot.event 
async def on_ready():
    await bot.wait_until_ready()
    logger.success("READY", f"Client Active: {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message):
    # Log all messages for debugging (only from owners/devs to avoid spam)
    if message.author.id in OWNER_IDS or message.author.id in (DEV_IDS if 'DEV_IDS' in globals() else []):
        logger.debug("MSG", f"Message from {message.author}: {message.content}")
    
    await bot.process_commands(message)

@bot.event 
async def on_interaction(interaction: discord.Interaction):
    """Router for global component interactions (buttons and select menus)"""
    if interaction.type != discord.InteractionType.component:
        return 
    
    id_ref = interaction.data.get("custom_id")
    if not id_ref: 
        return

    try:
        # Handler for Giveaway participation
        if id_ref.startswith("giveaway_"):
            from cogs.commands.giveaway import giveaway_button_callback
            try:
                g_id = int(id_ref.split("_")[1])
                await giveaway_button_callback(interaction, g_id)
            except Exception: 
                pass
            return

        # Handle persistent ui.View callbacks
        if hasattr(interaction.message, 'view') and interaction.message.view:
            if hasattr(interaction.message.view, 'interaction_handler'):
                await interaction.message.view.interaction_handler(interaction)
                return

        # Defer interactions for slow-running moderation commands
        if id_ref in ["ban_user", "unban_user", "delete_message", "confirm_unbanall", "cancel_unbanall"]:
            if not interaction.response.is_done():
                await interaction.response.defer()
            return

    except Exception as interaction_err:
        logger.error("INTERACTION", f"Critical Interaction Error: {interaction_err}")
        try:
            if not interaction.response.is_done():
                error_msg = "An error occurred during this interaction. Please notify the support team."
                await interaction.response.send_message(error_msg, ephemeral=True)
        except Exception: 
            pass

@bot.command()
async def test_debug(ctx):
    await ctx.send_v2("Bot is responsive!", title="DEBUG SUCCESS")

@bot.command()
async def check_perms(ctx):
    perms = ctx.me.guild_permissions
    msg = f"**Administrator:** {perms.administrator}\n**Manage Channels:** {perms.manage_channels}\n**Connect:** {perms.connect}"
    await ctx.reply_v2(msg, title="BOT PERMISSIONS")

@bot.command()
async def join_test(ctx):
    if not ctx.author.voice:
        return await ctx.send("Join a VC!")
    logger.info("TEST", f"Standard join attempt to {ctx.author.voice.channel.name}")
    try:
        vc = await ctx.author.voice.channel.connect(timeout=10.0)
        await ctx.send("Successfully joined!")
        await vc.disconnect()
    except Exception as e:
        logger.error("TEST", f"Standard join failed: {e}")
        await ctx.send(f"Standard join failed: {e}")

@bot.event 
async def on_command_completion(ctx: commands.Context):
    """Webhook logging for command analytics and audits"""
    log_webhook = os.getenv("WEBHOOK_URL")
    if not log_webhook or not ctx.guild: 
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            webhook_client = discord.Webhook.from_url(log_webhook, session=session)
            log_str = (
                f"**Command:** `{ctx.command.qualified_name}`\n"
                f"**Guild:** {ctx.guild.name} (`{ctx.guild.id}`)\n"
                f"**User:** {ctx.author} (`{ctx.author.id}`)"
            )
            await webhook_client.send(content=log_str)
    except Exception: 
        pass

# ---------------------------------------------------------
# CLI Runtime Entry
# ---------------------------------------------------------
async def start_bot_process():
    """Application management loop"""
    bot_token = os.getenv("TOKEN")
    if not bot_token or bot_token == "" or "YOUR_TOKEN" in bot_token:
        logger.error("INIT", "NO TOKEN DETECTED: Initialization aborted.")
        print("\n[!] Please fill in your TOKEN in the .env file to start the bot.")
        return

    try:
        print("[*] Bot connection initiated...")
        await bot.start(bot_token)
    except discord.LoginFailure:
        logger.error("INIT", "CRITICAL ERROR: The bot token in .env is invalid.")
    except Exception as startup_err:
        logger.error("INIT", f"Unexpected runtime error: {startup_err}")
    finally:
        if not bot.is_closed():
            await bot.close()
            logger.info("INIT", "Session ended. Shutdown complete.")

if __name__ == '__main__':
    try:
        # Run main asyncio loop
        asyncio.run(start_bot_process())
    except KeyboardInterrupt:
        logger.info("INIT", "Bot shutdown manually by user.")
    except Exception as fatal_exception:
        logger.error("INIT", f"Critical crash: {fatal_exception}")
        sys.exit(1)
